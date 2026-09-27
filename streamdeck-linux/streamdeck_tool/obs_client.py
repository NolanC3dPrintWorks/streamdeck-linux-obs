"""Thin, reconnecting wrapper around obsws-python (OBS websocket v5 protocol,
built into OBS Studio 28+)."""
from __future__ import annotations

import logging
import threading
import time

import obsws_python as obs

log = logging.getLogger(__name__)


class OBSClient:
    def __init__(self, host: str, port: int, password: str):
        self.host = host
        self.port = port
        self.password = password
        self._client: obs.ReqClient | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._connect_thread = threading.Thread(target=self._keep_connected, daemon=True)

    def start(self) -> None:
        self._connect_thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._client:
            try:
                self._client.disconnect()
            except Exception:
                pass

    def _keep_connected(self) -> None:
        while not self._stop.is_set():
            if self._client is None:
                try:
                    self._client = obs.ReqClient(
                        host=self.host, port=self.port, password=self.password, timeout=3
                    )
                    log.info("Connected to OBS at %s:%s", self.host, self.port)
                except Exception as e:
                    log.warning("OBS not reachable (%s). Retrying in 5s...", e)
                    self._client = None
                    time.sleep(5)
                    continue
            time.sleep(2)
            try:
                self._client.get_version()
            except Exception:
                log.warning("Lost OBS connection, will reconnect")
                self._client = None

    def _call(self, fn_name: str, *args, **kwargs):
        if self._client is None:
            log.warning("OBS action '%s' skipped: not connected", fn_name)
            return None
        try:
            with self._lock:
                return getattr(self._client, fn_name)(*args, **kwargs)
        except Exception as e:
            log.error("OBS call '%s' failed: %s", fn_name, e)
            self._client = None
            return None

    # -- convenience actions used by actions.py -----------------------------

    def set_scene(self, scene: str) -> None:
        self._call("set_current_program_scene", scene)

    def get_current_scene(self) -> str | None:
        resp = self._call("get_current_program_scene")
        return getattr(resp, "current_program_scene_name", None) if resp else None

    def toggle_source(self, scene: str, source: str) -> None:
        item_id = self._get_scene_item_id(scene, source)
        if item_id is None:
            return
        resp = self._call("get_scene_item_enabled", scene, item_id)
        enabled = getattr(resp, "scene_item_enabled", True) if resp else True
        self._call("set_scene_item_enabled", scene, item_id, not enabled)

    def _get_scene_item_id(self, scene: str, source: str) -> int | None:
        resp = self._call("get_scene_item_id", scene, source)
        return getattr(resp, "scene_item_id", None) if resp else None

    def toggle_mute_input(self, input_name: str) -> None:
        self._call("toggle_input_mute", input_name)

    def toggle_stream(self) -> None:
        self._call("toggle_stream")

    def toggle_record(self) -> None:
        self._call("toggle_record")
