"""Renders button icons (label text, optional image, active-state color) into
the pixel format each StreamDeck key expects."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from StreamDeck.Devices.StreamDeck import StreamDeck
from StreamDeck.ImageHelpers import PILHelper

DEFAULT_BG = (20, 20, 24)
ACTIVE_BG = (0, 120, 90)
TEXT_COLOR = (235, 235, 235)


class Renderer:
    def __init__(self, deck: StreamDeck, font_path: str | None):
        self.deck = deck
        self._font_path = font_path
        self._font_cache: dict[int, ImageFont.FreeTypeFont] = {}

    def _font(self, size: int) -> ImageFont.FreeTypeFont:
        if size not in self._font_cache:
            try:
                self._font_cache[size] = ImageFont.truetype(self._font_path, size)
            except Exception:
                self._font_cache[size] = ImageFont.load_default()
        return self._font_cache[size]

    def render_key(
        self,
        label: str = "",
        icon_path: str | None = None,
        active: bool = False,
        bg: tuple[int, int, int] | None = None,
    ):
        """Returns a native image ready for deck.set_key_image()."""
        image = PILHelper.create_key_image(self.deck)
        draw = ImageDraw.Draw(image)
        bg_color = bg or (ACTIVE_BG if active else DEFAULT_BG)
        draw.rectangle((0, 0, image.width, image.height), fill=bg_color)

        icon_bottom = 0
        if icon_path and Path(icon_path).exists():
            try:
                icon = Image.open(icon_path).convert("RGBA")
                max_h = int(image.height * 0.6)
                ratio = min(image.width / icon.width, max_h / icon.height)
                icon = icon.resize((int(icon.width * ratio), int(icon.height * ratio)))
                x = (image.width - icon.width) // 2
                image.paste(icon, (x, 4), icon)
                icon_bottom = icon.height + 4
            except Exception:
                pass

        if label:
            lines = label.split("\n")
            font_size = 15 if len(lines) > 1 else 16
            font = self._font(font_size)
            total_h = len(lines) * (font_size + 2)
            y = max(icon_bottom + 2, image.height - total_h - 6)
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                x = (image.width - w) // 2
                draw.text((x, y), line, font=font, fill=TEXT_COLOR)
                y += font_size + 2

        return PILHelper.to_native_key_format(self.deck, image)
