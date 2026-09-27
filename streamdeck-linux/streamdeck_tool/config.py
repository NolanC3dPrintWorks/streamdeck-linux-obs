"""Load and hot-reload the YAML configuration file."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any, Callable

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

log = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(
            f"Config file not found: {path}\n"
            f"Copy config.example.yaml to {path.name} and edit it first."
        )
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}

    if "pages" not in data or not data["pages"]:
        raise ConfigError("Config must define at least one page under 'pages:'")
    for page in data["pages"]:
        if "name" not in page:
            raise ConfigError("Every page needs a 'name'")
        page.setdefault("buttons", {})
        # YAML loads numeric-looking keys as ints already, but normalize
        # in case the user quoted them as strings.
        page["buttons"] = {int(k): v for k, v in page["buttons"].items()}
    return data


class ConfigWatcher:
    """Watches config.yaml on disk and calls on_change(new_config) when it's edited."""

    def __init__(self, path: Path, on_change: Callable[[dict], None]):
        self.path = path
        self.on_change = on_change
        self._observer: Observer | None = None

    def start(self) -> None:
        handler = _Handler(self.path, self._handle_change)
        self._observer = Observer()
        self._observer.schedule(handler, str(self.path.parent), recursive=False)
        self._observer.start()

    def stop(self) -> None:
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=2)

    def _handle_change(self) -> None:
        try:
            cfg = load_config(self.path)
        except ConfigError as e:
            log.error("Config reload failed, keeping previous config: %s", e)
            return
        log.info("Config reloaded from %s", self.path)
        self.on_change(cfg)


class _Handler(FileSystemEventHandler):
    def __init__(self, path: Path, callback: Callable[[], None]):
        self.path = path.resolve()
        self.callback = callback
        self._lock = threading.Lock()
        self._timer: threading.Timer | None = None

    def on_modified(self, event) -> None:
        if Path(event.src_path).resolve() != self.path:
            return
        # Debounce: editors often fire several events per save.
        with self._lock:
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(0.3, self.callback)
            self._timer.start()
