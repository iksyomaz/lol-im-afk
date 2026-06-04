import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.events import AppEvent, EventKind
from lol_im_afk.tray import _should_notify_event


class TrayNotificationTest(unittest.TestCase):
    def test_notifies_for_match_timing_events(self) -> None:
        for kind in (
            EventKind.QUEUE_STARTED,
            EventKind.MATCH_FOUND,
            EventKind.ACCEPTED_AUTOMATICALLY,
            EventKind.ACCEPTED_MANUALLY,
            EventKind.CHAMP_SELECT_STARTED,
            EventKind.BACK_IN_QUEUE,
            EventKind.READY_CHECK_FAILED_LOBBY,
        ):
            with self.subTest(kind=kind):
                self.assertTrue(_should_notify_event(AppEvent(kind, "message")))

    def test_skips_phase_noise(self) -> None:
        self.assertFalse(_should_notify_event(AppEvent(EventKind.AUTO_ACCEPT_ENABLED, "enabled")))


if __name__ == "__main__":
    unittest.main()
