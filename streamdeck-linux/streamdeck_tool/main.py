from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from .actions import ActionRouter
from .audio import AudioController
from .config import ConfigError, ConfigWatcher, load_config
from .deck import DeckManager, open_first_deck
from .obs_client import OBSClient


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Elgato Stream Deck controller for Linux")
    p.add_argument(
        "-c", "--config",
        type=Path,
        default=Path.home() / ".config" / "streamdeck-tool" / "config.yaml",
        help="Path to config.yaml (default: ~/.config/streamdeck-tool/config.yaml)",
    )
    p.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    log = logging.getLogger("streamdeck_tool")

    try:
        config = load_config(args.config)
    except ConfigError as e:
        log.error(str(e))
        return 1

    try:
        deck = open_first_deck()
    except RuntimeError as e:
        log.error(str(e))
        return 1

    obs_cfg = config.get("obs", {})
    obs_client = OBSClient(
        host=obs_cfg.get("host", "localhost"),
        port=obs_cfg.get("port", 4455),
        password=obs_cfg.get("password", ""),
    )
    obs_client.start()

    audio = AudioController(config.get("audio_apps", {}))

    manager_holder: dict[str, DeckManager] = {}

    def go_to_page(name: str) -> None:
        manager_holder["manager"].go_to_page(name)

    router = ActionRouter(obs_client, audio, on_page_change=go_to_page)

    font_path = config.get("deck", {}).get("font")
    manager = DeckManager(deck, config, router, font_path)
    manager_holder["manager"] = manager
    manager.draw_page()

    watcher = ConfigWatcher(args.config, manager.update_config)
    watcher.start()

    stop = {"flag": False}

    def handle_sigint(signum, frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    log.info("Stream Deck controller running. Press Ctrl+C to quit.")
    try:
        while not stop["flag"]:
            signal.pause()
    finally:
        watcher.stop()
        obs_client.stop()
        try:
            deck.reset()
            deck.close()
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
