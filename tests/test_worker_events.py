import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.config import AppConfig
from lol_im_afk.events import AppEvent, EventKind
from lol_im_afk.status import StatusStore
from lol_im_afk.worker import AutoAcceptWorker


class WorkerEventTest(unittest.TestCase):
    def test_matchmaking_phase_emits_queue_started(self) -> None:
        events: list[AppEvent] = []
        worker = AutoAcceptWorker(
            config=AppConfig(),
            lcu_client=object(),  # type: ignore[arg-type]
            status_store=StatusStore(),
            event_callback=events.append,
        )

        worker._handle_phase("Matchmaking")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, EventKind.QUEUE_STARTED)
        self.assertIn("Queue started", events[0].message)

    def test_champ_select_phase_emits_event(self) -> None:
        events: list[AppEvent] = []
        worker = AutoAcceptWorker(
            config=AppConfig(),
            lcu_client=object(),  # type: ignore[arg-type]
            status_store=StatusStore(),
            event_callback=events.append,
        )

        worker._handle_phase("ChampSelect")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, EventKind.CHAMP_SELECT_STARTED)
        self.assertIn("Champion select started", events[0].message)

    def test_ready_check_returning_to_matchmaking_emits_back_in_queue(self) -> None:
        events: list[AppEvent] = []
        worker = AutoAcceptWorker(
            config=AppConfig(),
            lcu_client=object(),  # type: ignore[arg-type]
            status_store=StatusStore(),
            event_callback=events.append,
        )

        worker._handle_phase("ReadyCheck")
        worker._handle_phase("Matchmaking")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, EventKind.BACK_IN_QUEUE)
        self.assertIn("Back in queue", events[0].message)

    def test_ready_check_returning_to_lobby_emits_sadder_failure(self) -> None:
        events: list[AppEvent] = []
        worker = AutoAcceptWorker(
            config=AppConfig(),
            lcu_client=object(),  # type: ignore[arg-type]
            status_store=StatusStore(),
            event_callback=events.append,
        )

        worker._handle_phase("ReadyCheck")
        worker._handle_phase("Lobby")

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].kind, EventKind.READY_CHECK_FAILED_LOBBY)
        self.assertIn("Ready check failed; lobby returned", events[0].message)


if __name__ == "__main__":
    unittest.main()
