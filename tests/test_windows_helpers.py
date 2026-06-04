from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.single_instance import SingleInstance
from lol_im_afk.windows_startup import startup_command


class WindowsHelpersTest(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows mutex test")
    def test_second_windows_instance_is_rejected(self) -> None:
        mutex_name = "Local\\lol-im-afk-test-mutex"
        with SingleInstance(mutex_name) as first:
            with SingleInstance(mutex_name) as second:
                self.assertTrue(first.acquired)
                self.assertFalse(second.acquired)

    def test_single_instance_is_noop_outside_windows(self) -> None:
        with patch("lol_im_afk.single_instance.sys.platform", "linux"):
            with SingleInstance() as instance:
                self.assertTrue(instance.acquired)

    def test_source_startup_command_uses_module(self) -> None:
        with (
            patch("lol_im_afk.windows_startup.sys.executable", "C:/Python/python.exe"),
            patch("lol_im_afk.windows_startup.sys.frozen", False, create=True),
        ):
            command = startup_command()

        self.assertEqual(command, '"C:\\Python\\python.exe" -m lol_im_afk --tray')

    def test_frozen_startup_command_uses_executable(self) -> None:
        with (
            patch("lol_im_afk.windows_startup.sys.executable", "C:/Apps/lol-im-afk.exe"),
            patch("lol_im_afk.windows_startup.sys.frozen", True, create=True),
        ):
            command = startup_command()

        self.assertEqual(command, '"C:\\Apps\\lol-im-afk.exe" --tray')


if __name__ == "__main__":
    unittest.main()
