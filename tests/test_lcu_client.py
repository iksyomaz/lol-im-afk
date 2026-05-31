import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.lcu_client import parse_lockfile_text


class LockfileParsingTest(unittest.TestCase):
    def test_parses_valid_lockfile(self) -> None:
        info = parse_lockfile_text("LeagueClient:1234:45678:secret:https")

        self.assertEqual(info.name, "LeagueClient")
        self.assertEqual(info.pid, 1234)
        self.assertEqual(info.port, 45678)
        self.assertEqual(info.password, "secret")
        self.assertEqual(info.protocol, "https")

    def test_rejects_invalid_field_count(self) -> None:
        with self.assertRaises(ValueError):
            parse_lockfile_text("LeagueClient:1234:45678")

    def test_rejects_invalid_protocol(self) -> None:
        with self.assertRaises(ValueError):
            parse_lockfile_text("LeagueClient:1234:45678:secret:ftp")


if __name__ == "__main__":
    unittest.main()
