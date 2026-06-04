import sys
import math
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.config import AppConfig, lockfile_paths_from_setting


class ConfigTest(unittest.TestCase):
    def test_directory_setting_appends_lockfile(self) -> None:
        paths = lockfile_paths_from_setting("C:/Games/League")

        self.assertEqual(paths[0], Path("C:/Games/League/lockfile"))

    def test_lockfile_setting_is_used_directly(self) -> None:
        paths = lockfile_paths_from_setting("C:/Games/League/lockfile")

        self.assertEqual(paths[0], Path("C:/Games/League/lockfile"))

    def test_rejects_non_finite_timing(self) -> None:
        with self.assertRaises(ValueError):
            AppConfig(delay_min_seconds=math.nan).validate()


if __name__ == "__main__":
    unittest.main()
