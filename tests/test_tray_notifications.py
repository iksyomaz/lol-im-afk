import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.tray import _should_notify_event


class TrayNotificationTest(unittest.TestCase):
    def test_notifies_for_match_timing_events(self) -> None:
        self.assertTrue(_should_notify_event("12:00:00 Queue started"))
        self.assertTrue(_should_notify_event("12:00:00 Match found; accepting in 3.1s"))
        self.assertTrue(_should_notify_event("12:00:03 Accepted match"))
        self.assertTrue(_should_notify_event("12:00:07 Champion select started"))
        self.assertTrue(_should_notify_event("12:00:08 Back in queue; ready check failed"))
        self.assertTrue(_should_notify_event("12:00:08 Ready check failed; lobby returned"))

    def test_skips_phase_noise(self) -> None:
        self.assertFalse(_should_notify_event("12:00:00 Phase: Lobby"))


if __name__ == "__main__":
    unittest.main()
