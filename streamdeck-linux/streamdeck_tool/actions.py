"""Dispatches key presses to the right handler based on each button's
'type' field, and figures out what each button should show/highlight."""
from __future__ import annotations

import logging
import shlex
import subprocess
from typing import Any, Callable

from .audio import AudioController
from .obs_client import OBSClient

log = logging.getLogger(__name__)


def _run_detached(command: str) -> None:
    try:
        subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as e:
        log.error("Failed to run command '%s': %s", command, e)


def _playerctl(*args: str) -> None:
    _run_detached("playerctl " + " ".join(args))


class ActionRouter:
    """Holds the shared clients and exposes handle(button_cfg) / page navigation."""

    def __init__(self, obs_client: OBSClient, audio: AudioController, on_page_change: Callable[[str], None]):
        self.obs = obs_client
        self.audio = audio
        self.on_page_change = on_page_change
        self._handlers: dict[str, Callable[[dict], None]] = {
            "obs_scene": self._obs_scene,
            "obs_toggle_source": self._obs_toggle_source,
            "obs_toggle_mute_input": self._obs_toggle_mute_input,
            "obs_start_stop_stream": self._obs_start_stop_stream,
            "obs_start_stop_record": self._obs_start_stop_record,
            "volume_mute": self._volume_mute,
            "volume_adjust": self._volume_adjust,
            "volume_set": self._volume_set,
            "media_play_pause": self._media_play_pause,
            "media_next": self._media_next,
            "media_prev": self._media_prev,
            "launch_app": self._run_command,
            "run_command": self._run_command,
            "page": self._page,
        }

    def handle(self, button: dict[str, Any]) -> None:
        btype = button.get("type")
        handler = self._handlers.get(btype)
        if handler is None:
            log.warning("Unknown button type: %s", btype)
            return
        try:
            handler(button)
        except Exception:
            log.exception("Error handling button of type %s", btype)

    # -- handlers -------------------------------------------------------

    def _obs_scene(self, b: dict) -> None:
        self.obs.set_scene(b["scene"])

    def _obs_toggle_source(self, b: dict) -> None:
        self.obs.toggle_source(b["scene"], b["source"])

    def _obs_toggle_mute_input(self, b: dict) -> None:
        self.obs.toggle_mute_input(b["input"])

    def _obs_start_stop_stream(self, b: dict) -> None:
        self.obs.toggle_stream()

    def _obs_start_stop_record(self, b: dict) -> None:
        self.obs.toggle_record()

    def _volume_mute(self, b: dict) -> None:
        self.audio.set_mute(b["app"])

    def _volume_adjust(self, b: dict) -> None:
        self.audio.adjust_volume(b["app"], b.get("delta", 0))

    def _volume_set(self, b: dict) -> None:
        self.audio.set_volume(b["app"], b.get("percent", 100))

    def _media_play_pause(self, b: dict) -> None:
        _playerctl("play-pause")

    def _media_next(self, b: dict) -> None:
        _playerctl("next")

    def _media_prev(self, b: dict) -> None:
        _playerctl("previous")

    def _run_command(self, b: dict) -> None:
        _run_detached(b["command"])

    def _page(self, b: dict) -> None:
        self.on_page_change(b["target"])
