from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from pathlib import Path


def default_lockfile_paths() -> tuple[Path, ...]:
    env_path = os.environ.get("LOL_IM_AFK_LOCKFILE")
    paths: list[Path] = []

    if env_path:
        paths.append(Path(env_path))

    paths.append(Path("C:/Riot Games/League of Legends/lockfile"))
    return tuple(paths)


def default_log_file() -> Path:
    return Path.home() / ".lol-im-afk" / "lol-im-afk.log"


@dataclass
class AppConfig:
    delay_min_seconds: float = 1.5
    delay_max_seconds: float = 5.5
    poll_interval_seconds: float = 1.0
    reconnect_interval_seconds: float = 3.0
    request_timeout_seconds: float = 1.5
    accept_cooldown_seconds: float = 10.0
    lockfile_paths: tuple[Path, ...] = field(default_factory=default_lockfile_paths)
    log_file: Path = field(default_factory=default_log_file)

    def validate(self) -> None:
        for name in (
            "delay_min_seconds",
            "delay_max_seconds",
            "poll_interval_seconds",
            "reconnect_interval_seconds",
            "request_timeout_seconds",
            "accept_cooldown_seconds",
        ):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f"{name} must be finite")
        if self.delay_min_seconds < 0:
            raise ValueError("delay_min_seconds cannot be negative")
        if self.delay_max_seconds < self.delay_min_seconds:
            raise ValueError("delay_max_seconds must be >= delay_min_seconds")
        if self.poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be positive")
        if self.reconnect_interval_seconds <= 0:
            raise ValueError("reconnect_interval_seconds must be positive")
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")
        if self.accept_cooldown_seconds < 0:
            raise ValueError("accept_cooldown_seconds cannot be negative")


def lockfile_paths_from_setting(lockfile_path: str | None) -> tuple[Path, ...]:
    if not lockfile_path:
        return default_lockfile_paths()

    configured = Path(lockfile_path)
    if configured.name.lower() != "lockfile":
        configured = configured / "lockfile"

    return (configured, *default_lockfile_paths())
