import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.sound import _clamp_volume, cue_key_for_event


class SoundCueTest(unittest.TestCase):
    def test_maps_positive_progression_events(self) -> None:
        self.assertEqual(cue_key_for_event("12:00:00 Queue started"), "queue_started")
        self.assertEqual(cue_key_for_event("12:00:01 Match found; accepting in 2.0s"), "match_found")
        self.assertEqual(cue_key_for_event("12:00:03 Accepted match"), "accepted")
        self.assertEqual(cue_key_for_event("12:00:05 Champion select started"), "champ_select")

    def test_maps_failure_events_to_lower_cues(self) -> None:
        self.assertEqual(cue_key_for_event("12:00:06 Back in queue; ready check failed"), "back_in_queue")
        self.assertEqual(cue_key_for_event("12:00:06 Ready check ended before accept"), "failed")
        self.assertEqual(cue_key_for_event("12:00:06 Ready check failed; lobby returned"), "failed_lobby")

    def test_clamps_volume(self) -> None:
        self.assertEqual(_clamp_volume(-10), 0)
        self.assertEqual(_clamp_volume(70), 70)
        self.assertEqual(_clamp_volume(120), 100)


if __name__ == "__main__":
    unittest.main()
