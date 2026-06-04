from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventKind(str, Enum):
    AUTO_ACCEPT_ENABLED = "auto_accept_enabled"
    AUTO_ACCEPT_DISABLED = "auto_accept_disabled"
    QUEUE_STARTED = "queue_started"
    MATCH_FOUND = "match_found"
    ACCEPTED_AUTOMATICALLY = "accepted_automatically"
    ACCEPTED_MANUALLY = "accepted_manually"
    CHAMP_SELECT_STARTED = "champ_select_started"
    BACK_IN_QUEUE = "back_in_queue"
    READY_CHECK_FAILED_LOBBY = "ready_check_failed_lobby"
    SKIPPED_DISABLED = "skipped_disabled"
    TEST_NOTIFICATION = "test_notification"


@dataclass(frozen=True)
class AppEvent:
    kind: EventKind
    message: str
    occurred_at: datetime = field(default_factory=datetime.now)

    @property
    def display_text(self) -> str:
        return f"{self.occurred_at:%H:%M:%S} {self.message}"
