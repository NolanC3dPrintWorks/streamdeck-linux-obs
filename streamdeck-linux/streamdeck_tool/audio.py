"""Per-application volume/mute control via pulsectl.
Works against PulseAudio directly, and against PipeWire through its
pipewire-pulse compatibility layer (the default on most current distros)."""
from __future__ import annotations

import logging

import pulsectl

log = logging.getLogger(__name__)


class AudioController:
    def __init__(self, app_name_map: dict[str, str]):
        """app_name_map: friendly key -> substring to match against
        sink-input application.name / process.binary (case-insensitive)."""
        self.app_name_map = app_name_map

    def _matching_inputs(self, pulse: pulsectl.Pulse, app_key: str):
        needle = self.app_name_map.get(app_key, app_key).lower()
        for si in pulse.sink_input_list():
            name = (si.proplist.get("application.name") or "").lower()
            binary = (si.proplist.get("application.process.binary") or "").lower()
            if needle in name or needle in binary:
                yield si

    def set_mute(self, app_key: str, mute: bool | None = None) -> None:
        """mute=None toggles; True/False sets explicitly."""
        with pulsectl.Pulse("streamdeck-tool") as pulse:
            matched = False
            for si in self._matching_inputs(pulse, app_key):
                matched = True
                target = (not si.mute) if mute is None else mute
                pulse.mute(si, target)
            if not matched:
                log.warning("No running audio stream matched '%s'", app_key)

    def adjust_volume(self, app_key: str, delta_percent: float) -> None:
        with pulsectl.Pulse("streamdeck-tool") as pulse:
            matched = False
            for si in self._matching_inputs(pulse, app_key):
                matched = True
                pulse.volume_change_all_chans(si, delta_percent / 100.0)
            if not matched:
                log.warning("No running audio stream matched '%s'", app_key)

    def set_volume(self, app_key: str, percent: float) -> None:
        with pulsectl.Pulse("streamdeck-tool") as pulse:
            matched = False
            for si in self._matching_inputs(pulse, app_key):
                matched = True
                pulse.volume_set_all_chans(si, percent / 100.0)
            if not matched:
                log.warning("No running audio stream matched '%s'", app_key)

    def is_muted(self, app_key: str) -> bool | None:
        with pulsectl.Pulse("streamdeck-tool") as pulse:
            for si in self._matching_inputs(pulse, app_key):
                return bool(si.mute)
        return None
