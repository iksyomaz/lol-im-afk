from __future__ import annotations

import json
import math
import os
from datetime import datetime
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from lol_im_afk.icon_theme import icon_theme_by_key


SETTINGS_VERSION = 2


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
    icon_theme: str = "status"
    start_with_windows: bool = False


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_settings_file()
        self.settings = self._load()

    def save(self) -> None:
        self.settings = _sanitize_settings(self.settings)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(asdict(self.settings), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(temporary_path, self.path)

    def _load(self) -> UserSettings:
        if not self.path.is_file():
            return UserSettings()

        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._backup_invalid_settings()
            return UserSettings()

        if not isinstance(payload, dict):
            self._backup_invalid_settings()
            return UserSettings()

        return _sanitize_settings(
            UserSettings(
                version=SETTINGS_VERSION,
                lockfile_path=_optional_string(payload.get("lockfile_path")),
                delay_min_seconds=_float_or_default(payload.get("delay_min_seconds"), 1.5),
                delay_max_seconds=_float_or_default(payload.get("delay_max_seconds"), 5.5),
                sound_enabled=_bool_or_default(payload.get("sound_enabled"), True),
                sound_volume_percent=_int_or_default(payload.get("sound_volume_percent"), 70),
                icon_theme=str(payload.get("icon_theme") or "status"),
                start_with_windows=_bool_or_default(payload.get("start_with_windows"), False),
            )
        )

    def _backup_invalid_settings(self) -> None:
        if not self.path.is_file():
            return
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup = self.path.with_name(f"{self.path.stem}.invalid-{timestamp}{self.path.suffix}")
        try:
            self.path.replace(backup)
        except OSError:
            pass


def _sanitize_settings(settings: UserSettings) -> UserSettings:
    delay_min = settings.delay_min_seconds if math.isfinite(settings.delay_min_seconds) else 1.5
    delay_max = settings.delay_max_seconds if math.isfinite(settings.delay_max_seconds) else 5.5
    delay_min = max(0.0, delay_min)
    delay_max = max(delay_min, delay_max)
    return UserSettings(
        version=SETTINGS_VERSION,
        lockfile_path=_optional_string(settings.lockfile_path),
        delay_min_seconds=delay_min,
        delay_max_seconds=delay_max,
        sound_enabled=bool(settings.sound_enabled),
        sound_volume_percent=max(0, min(100, int(settings.sound_volume_percent))),
        icon_theme=icon_theme_by_key(settings.icon_theme).key,
        start_with_windows=bool(settings.start_with_windows),
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


def _bool_or_default(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default
