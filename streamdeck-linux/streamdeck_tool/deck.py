"""Owns the physical StreamDeck device: draws the active page's buttons and
routes key-press callbacks to the ActionRouter."""
from __future__ import annotations

import logging
import threading

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices.StreamDeck import StreamDeck

from .actions import ActionRouter
from .renderer import Renderer

log = logging.getLogger(__name__)


def open_first_deck() -> StreamDeck:
    decks = DeviceManager().enumerate()
    if not decks:
        raise RuntimeError(
            "No Stream Deck found. Check the USB cable, and that the udev rule "
            "in install/udev/99-streamdeck.rules is installed (see README)."
        )
    deck = decks[0]
    deck.open()
    deck.reset()
    log.info("Opened %s (%s keys)", deck.deck_type(), deck.key_count())
    return deck


class DeckManager:
    def __init__(self, deck: StreamDeck, config: dict, router: ActionRouter, font_path: str | None):
        self.deck = deck
        self.config = config
        self.router = router
        self.renderer = Renderer(deck, font_path)
        self.pages: dict[str, dict] = {p["name"]: p for p in config["pages"]}
        self.current_page = config["pages"][0]["name"]
        self._lock = threading.Lock()

        brightness = config.get("deck", {}).get("brightness", 70)
        deck.set_brightness(brightness)
        deck.set_key_callback(self._on_key_change)

    def update_config(self, config: dict) -> None:
        with self._lock:
            self.config = config
            self.pages = {p["name"]: p for p in config["pages"]}
            if self.current_page not in self.pages:
                self.current_page = config["pages"][0]["name"]
            self.deck.set_brightness(config.get("deck", {}).get("brightness", 70))
        self.draw_page()

    def go_to_page(self, page_name: str) -> None:
        with self._lock:
            if page_name not in self.pages:
                log.warning("Unknown page '%s'", page_name)
                return
            self.current_page = page_name
        self.draw_page()

    def draw_page(self) -> None:
        with self._lock:
            page = self.pages[self.current_page]
            buttons = page.get("buttons", {})
            key_count = self.deck.key_count()
        for i in range(key_count):
            btn = buttons.get(i)
            if not btn:
                image = self.renderer.render_key()
            else:
                image = self.renderer.render_key(
                    label=btn.get("label", ""), icon_path=btn.get("icon")
                )
            with self.deck:
                self.deck.set_key_image(i, image)

    def _on_key_change(self, deck: StreamDeck, key: int, state: bool) -> None:
        if not state:  # only act on press, not release
            return
        with self._lock:
            page = self.pages[self.current_page]
            btn = page.get("buttons", {}).get(key)
        if not btn:
            return
        log.info("Key %s pressed on page '%s': %s", key, self.current_page, btn.get("type"))
        self._flash(key)
        self.router.handle(btn)

    def _flash(self, key: int) -> None:
        """Briefly highlight the pressed key for visual feedback."""
        with self._lock:
            page = self.pages[self.current_page]
            btn = page.get("buttons", {}).get(key, {})
        image = self.renderer.render_key(label=btn.get("label", ""), icon_path=btn.get("icon"), active=True)
        with self.deck:
            self.deck.set_key_image(key, image)

        def restore():
            with self._lock:
                same_page = self.pages.get(self.current_page)
            still_there = same_page and same_page.get("buttons", {}).get(key) is btn
            if still_there:
                normal = self.renderer.render_key(label=btn.get("label", ""), icon_path=btn.get("icon"))
                with self.deck:
                    self.deck.set_key_image(key, normal)

        threading.Timer(0.15, restore).start()
