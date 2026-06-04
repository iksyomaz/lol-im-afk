import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.events import EventKind
from lol_im_afk.sound import EVENT_CUES, _clamp_volume


class SoundCueTest(unittest.TestCase):
    def test_maps_positive_progression_events(self) -> None:
        self.assertEqual(EVENT_CUES[EventKind.QUEUE_STARTED], "queue_started")
        self.assertEqual(EVENT_CUES[EventKind.MATCH_FOUND], "match_found")
        self.assertEqual(EVENT_CUES[EventKind.ACCEPTED_AUTOMATICALLY], "accepted")
        self.assertEqual(EVENT_CUES[EventKind.ACCEPTED_MANUALLY], "accepted")
        self.assertEqual(EVENT_CUES[EventKind.CHAMP_SELECT_STARTED], "champ_select")

    def test_maps_failure_events_to_lower_cues(self) -> None:
        self.assertEqual(EVENT_CUES[EventKind.BACK_IN_QUEUE], "back_in_queue")
        self.assertEqual(EVENT_CUES[EventKind.READY_CHECK_FAILED_LOBBY], "failed_lobby")
        self.assertEqual(EVENT_CUES[EventKind.SKIPPED_DISABLED], "failed")

    def test_clamps_volume(self) -> None:
        self.assertEqual(_clamp_volume(-10), 0)
        self.assertEqual(_clamp_volume(70), 70)
        self.assertEqual(_clamp_volume(120), 100)


if __name__ == "__main__":
    unittest.main()
