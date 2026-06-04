import sys
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.ready_check import has_player_accepted, random_accept_delay, should_accept_ready_check


class ReadyCheckDecisionTest(unittest.TestCase):
    def test_accepts_active_unanswered_ready_check(self) -> None:
        payload = {"state": "InProgress", "playerResponse": "None"}

        self.assertTrue(should_accept_ready_check(payload))

    def test_skips_when_already_accepted(self) -> None:
        payload = {"state": "InProgress", "playerResponse": "Accepted"}

        self.assertFalse(should_accept_ready_check(payload))
        self.assertTrue(has_player_accepted(payload))

    def test_skips_finished_ready_check(self) -> None:
        payload = {"state": "EveryoneReady", "playerResponse": "None"}

        self.assertFalse(should_accept_ready_check(payload))

    def test_random_delay_uses_configured_range(self) -> None:
        with patch("lol_im_afk.ready_check.random.uniform", return_value=2.75) as uniform:
            delay = random_accept_delay(1.5, 5.5)

        uniform.assert_called_once_with(1.5, 5.5)
        self.assertEqual(delay, 2.75)


if __name__ == "__main__":
    unittest.main()
