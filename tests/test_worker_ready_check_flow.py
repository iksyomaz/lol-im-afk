from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.config import AppConfig
from lol_im_afk.events import AppEvent, EventKind
from lol_im_afk.status import StatusStore
from lol_im_afk.worker import AutoAcceptWorker


ACTIVE_READY_CHECK = {"state": "InProgress", "playerResponse": "None"}
ACCEPTED_READY_CHECK = {"state": "InProgress", "playerResponse": "Accepted"}


class FakeLcuClient:
    def __init__(self, phases: list[str], ready_checks: list[dict[str, Any] | None]) -> None:
        self.phases = phases
        self.ready_checks = ready_checks
        self.accept_count = 0

    def get_gameflow_phase(self) -> str:
        return self.phases.pop(0)

    def get_ready_check(self) -> dict[str, Any] | None:
        return self.ready_checks.pop(0)

    def accept_ready_check(self) -> None:
        self.accept_count += 1


def create_worker(client: FakeLcuClient) -> tuple[AutoAcceptWorker, list[AppEvent], StatusStore]:
    events: list[AppEvent] = []
    status = StatusStore()
    worker = AutoAcceptWorker(
        config=AppConfig(delay_min_seconds=0, delay_max_seconds=0),
        lcu_client=client,  # type: ignore[arg-type]
        status_store=status,
        event_callback=events.append,
    )
    worker._sleep = lambda _: False  # type: ignore[method-assign]
    return worker, events, status


class WorkerReadyCheckFlowTest(unittest.TestCase):
    def test_automatically_accepts_once(self) -> None:
        client = FakeLcuClient(
            ["ReadyCheck", "ReadyCheck"],
            [ACTIVE_READY_CHECK, ACTIVE_READY_CHECK, ACCEPTED_READY_CHECK],
        )
        worker, events, status = create_worker(client)

        worker._poll_once()
        worker._poll_once()

        self.assertEqual(client.accept_count, 1)
        self.assertEqual(
            [event.kind for event in events],
            [EventKind.MATCH_FOUND, EventKind.ACCEPTED_AUTOMATICALLY],
        )
        self.assertEqual(status.snapshot().text, "Connected; phase: ReadyCheck")

    def test_detects_manual_accept_during_delay_without_posting(self) -> None:
        client = FakeLcuClient(["ReadyCheck"], [ACTIVE_READY_CHECK, ACCEPTED_READY_CHECK])
        worker, events, status = create_worker(client)

        worker._poll_once()

        self.assertEqual(client.accept_count, 0)
        self.assertEqual(
            [event.kind for event in events],
            [EventKind.MATCH_FOUND, EventKind.ACCEPTED_MANUALLY],
        )
        self.assertEqual(status.snapshot().text, "Accepted match manually")

    def test_champ_select_race_is_success_not_failure(self) -> None:
        client = FakeLcuClient(["ReadyCheck", "ChampSelect"], [ACTIVE_READY_CHECK, None])
        worker, events, _ = create_worker(client)

        worker._poll_once()

        self.assertEqual(client.accept_count, 0)
        self.assertEqual(
            [event.kind for event in events],
            [EventKind.MATCH_FOUND, EventKind.CHAMP_SELECT_STARTED],
        )

    def test_missing_ready_check_waits_for_phase_outcome(self) -> None:
        client = FakeLcuClient(["ReadyCheck", "ReadyCheck"], [ACTIVE_READY_CHECK, None])
        worker, events, status = create_worker(client)

        worker._poll_once()

        self.assertEqual(client.accept_count, 0)
        self.assertEqual([event.kind for event in events], [EventKind.MATCH_FOUND])
        self.assertEqual(status.snapshot().text, "Ready check answered; waiting for outcome")

    def test_disconnect_resets_phase_tracking(self) -> None:
        client = FakeLcuClient([], [])
        worker, _, _ = create_worker(client)
        worker._last_phase = "Matchmaking"
        worker._ready_check_seen = True
        worker._accepted_notified = True
        worker._cooldown_until = 123

        worker._reset_client_state()

        self.assertIsNone(worker._last_phase)
        self.assertFalse(worker._ready_check_seen)
        self.assertFalse(worker._accepted_notified)
        self.assertEqual(worker._cooldown_until, 0)


if __name__ == "__main__":
    unittest.main()
