from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class StatusSnapshot:
    enabled: bool
    text: str


class StatusStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._enabled = True
        self._text = "Starting"

    def set_enabled(self, enabled: bool) -> None:
        with self._lock:
            self._enabled = enabled

    def set_text(self, text: str) -> None:
        with self._lock:
            self._text = text

    def snapshot(self) -> StatusSnapshot:
        with self._lock:
            return StatusSnapshot(enabled=self._enabled, text=self._text)
