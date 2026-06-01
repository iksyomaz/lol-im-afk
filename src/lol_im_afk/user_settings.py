from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SETTINGS_VERSION = 1


def default_settings_file() -> Path:
    return Path.home() / ".lol-im-afk" / "settings.json"


@dataclass
class UserSettings:
    version: int = SETTINGS_VERSION
    lockfile_path: str | None = None
    delay_min_seconds: float = 1.5
    delay_max_seconds: float = 5.5
    sound_enabled: bool = True
    sound_volume_percent: int = 70


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_settings_file()
        self.settings = self._load()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(self.settings), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _load(self) -> UserSettings:
        if not self.path.is_file():
            return UserSettings()

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return UserSettings()

        if not isinstance(payload, dict):
            return UserSettings()

        return UserSettings(
            version=SETTINGS_VERSION,
            lockfile_path=_optional_string(payload.get("lockfile_path")),
            delay_min_seconds=_float_or_default(payload.get("delay_min_seconds"), 1.5),
            delay_max_seconds=_float_or_default(payload.get("delay_max_seconds"), 5.5),
            sound_enabled=bool(payload.get("sound_enabled", True)),
            sound_volume_percent=_int_or_default(payload.get("sound_volume_percent"), 70),
        )


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _float_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int_or_default(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
