from __future__ import annotations

import math
import sys
import wave
from dataclasses import dataclass
from pathlib import Path


try:
    import winsound
except ImportError:  # pragma: no cover - non-Windows fallback
    winsound = None


SAMPLE_RATE = 44_100


@dataclass(frozen=True)
class SoundCue:
    key: str
    label: str
    notes: tuple[tuple[float, float], ...]


SOUND_CUES: tuple[SoundCue, ...] = (
    SoundCue("queue_started", "Queue started", ((523, 0.07), (659, 0.08))),
    SoundCue("match_found", "Match found", ((659, 0.06), (784, 0.08), (988, 0.10))),
    SoundCue("accepted", "Accepted by me", ((784, 0.06), (988, 0.08), (1319, 0.12))),
    SoundCue("champ_select", "Champion select", ((880, 0.06), (1109, 0.08), (1568, 0.16))),
    SoundCue("back_in_queue", "Back in queue", ((494, 0.06), (622, 0.08), (740, 0.10))),
    SoundCue("failed", "Failed", ((330, 0.12), (247, 0.18))),
    SoundCue("failed_lobby", "Failed to lobby", ((247, 0.14), (196, 0.25))),
)


def cue_by_key(key: str) -> SoundCue:
    return next((cue for cue in SOUND_CUES if cue.key == key), SOUND_CUES[0])


def cue_key_for_event(event: str) -> str:
    if "Champion select started" in event:
        return "champ_select"
    if "Accepted match" in event:
        return "accepted"
    if "Match found" in event:
        return "match_found"
    if "Back in queue" in event:
        return "back_in_queue"
    if "Queue started" in event:
        return "queue_started"
    if "lobby returned" in event:
        return "failed_lobby"
    if "Ready check ended" in event or "Skipped accept" in event:
        return "failed"
    return "queue_started"


class SoundPlayer:
    def __init__(self, sound_dir: Path, enabled: bool = True, volume_percent: int = 70) -> None:
        self.sound_dir = sound_dir
        self.enabled = enabled
        self.volume_percent = _clamp_volume(volume_percent)
        self.ensure_sound_files()

    def set_sound(self, enabled: bool, volume_percent: int) -> None:
        self.enabled = enabled
        self.volume_percent = _clamp_volume(volume_percent)
        self.ensure_sound_files()

    def preview(self, cue_key: str, volume_percent: int | None = None) -> None:
        self._play(cue_key, volume_percent=volume_percent)

    def play_for_event(self, event: str) -> None:
        if self.enabled:
            self._play(cue_key_for_event(event))

    def ensure_sound_files(self) -> None:
        self.sound_dir.mkdir(parents=True, exist_ok=True)
        for cue in SOUND_CUES:
            self._ensure_cue_file(cue.key, self.volume_percent)

    def path_for(self, cue_key: str, volume_percent: int | None = None) -> Path:
        volume = self.volume_percent if volume_percent is None else _clamp_volume(volume_percent)
        return self.sound_dir / f"{cue_by_key(cue_key).key}-{volume}.wav"

    def _play(self, cue_key: str, volume_percent: int | None = None) -> None:
        if sys.platform != "win32" or winsound is None:
            return

        volume = self.volume_percent if volume_percent is None else _clamp_volume(volume_percent)
        self._ensure_cue_file(cue_key, volume)
        winsound.PlaySound(
            str(self.path_for(cue_key, volume)),
            winsound.SND_FILENAME | winsound.SND_ASYNC,
        )

    def _ensure_cue_file(self, cue_key: str, volume_percent: int) -> None:
        path = self.path_for(cue_key, volume_percent)
        if not path.is_file():
            _write_cue(path, cue_by_key(cue_key), volume_percent)


def _write_cue(path: Path, cue: SoundCue, volume_percent: int) -> None:
    frames = bytearray()
    amplitude = int(11_000 * (_clamp_volume(volume_percent) / 100))

    for frequency, duration in cue.notes:
        total = max(1, int(SAMPLE_RATE * duration))
        for index in range(total):
            envelope = min(1.0, index / max(1, SAMPLE_RATE * 0.01))
            envelope *= max(0.0, 1.0 - index / total)
            sample = int(amplitude * envelope * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE))
            frames.extend(sample.to_bytes(2, byteorder="little", signed=True))

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(bytes(frames))


def _clamp_volume(volume_percent: int) -> int:
    return max(0, min(100, int(volume_percent)))
