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
class SoundPreset:
    key: str
    label: str
    notes: tuple[tuple[float, float], ...]


SOUND_PRESETS: tuple[SoundPreset, ...] = (
    SoundPreset("soft_ping", "Soft ping", ((880, 0.07), (1320, 0.10))),
    SoundPreset("low_blip", "Low blip", ((392, 0.08), (523, 0.12))),
    SoundPreset("bright_confirm", "Bright confirm", ((660, 0.05), (990, 0.06), (1320, 0.10))),
    SoundPreset("quiet_pluck", "Quiet pluck", ((740, 0.04), (587, 0.10))),
)


def preset_by_key(key: str) -> SoundPreset:
    return next((preset for preset in SOUND_PRESETS if preset.key == key), SOUND_PRESETS[0])


class SoundPlayer:
    def __init__(self, sound_dir: Path, sound_name: str, enabled: bool = True) -> None:
        self.sound_dir = sound_dir
        self.sound_name = sound_name
        self.enabled = enabled
        self.ensure_sound_files()

    def set_sound(self, sound_name: str, enabled: bool) -> None:
        self.sound_name = preset_by_key(sound_name).key
        self.enabled = enabled

    def preview(self, sound_name: str | None = None) -> None:
        self._play(sound_name or self.sound_name)

    def play_notification(self) -> None:
        if self.enabled:
            self._play(self.sound_name)

    def ensure_sound_files(self) -> None:
        self.sound_dir.mkdir(parents=True, exist_ok=True)
        for preset in SOUND_PRESETS:
            path = self.path_for(preset.key)
            if not path.is_file():
                _write_preset(path, preset)

    def path_for(self, sound_name: str) -> Path:
        return self.sound_dir / f"{preset_by_key(sound_name).key}.wav"

    def _play(self, sound_name: str) -> None:
        if sys.platform != "win32" or winsound is None:
            return

        winsound.PlaySound(
            str(self.path_for(sound_name)),
            winsound.SND_FILENAME | winsound.SND_ASYNC,
        )


def _write_preset(path: Path, preset: SoundPreset) -> None:
    frames = bytearray()
    amplitude = 11_000

    for frequency, duration in preset.notes:
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
