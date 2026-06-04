from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.user_settings import SettingsStore


class SettingsStoreTest(unittest.TestCase):
    def test_corrupt_settings_are_backed_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("{broken", encoding="utf-8")

            store = SettingsStore(path)

            self.assertEqual(store.settings.delay_min_seconds, 1.5)
            self.assertFalse(path.exists())
            self.assertEqual(len(list(path.parent.glob("settings.invalid-*.json"))), 1)

    def test_non_object_settings_are_backed_up(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("[]", encoding="utf-8")

            SettingsStore(path)

            self.assertFalse(path.exists())
            self.assertEqual(len(list(path.parent.glob("settings.invalid-*.json"))), 1)

    def test_load_sanitizes_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(
                json.dumps(
                    {
                        "delay_min_seconds": -4,
                        "delay_max_seconds": -9,
                        "sound_volume_percent": 140,
                        "icon_theme": "missing",
                    }
                ),
                encoding="utf-8",
            )

            settings = SettingsStore(path).settings

            self.assertEqual(settings.delay_min_seconds, 0)
            self.assertEqual(settings.delay_max_seconds, 0)
            self.assertEqual(settings.sound_volume_percent, 100)
            self.assertEqual(settings.icon_theme, "status")

    def test_save_is_atomic_and_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            store = SettingsStore(path)
            store.settings.delay_min_seconds = float("nan")
            store.settings.sound_volume_percent = -1

            store.save()

            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["delay_min_seconds"], 1.5)
            self.assertEqual(payload["sound_volume_percent"], 0)
            self.assertFalse(path.with_suffix(".json.tmp").exists())


if __name__ == "__main__":
    unittest.main()
