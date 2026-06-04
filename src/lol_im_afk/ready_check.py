from __future__ import annotations

import random
from typing import Any


READY_CHECK_ACTIVE_STATES = {"inprogress", "in_progress"}
UNANSWERED_PLAYER_RESPONSES = {"none", "notresponded", "not_responded", ""}
ACCEPTED_PLAYER_RESPONSES = {"accepted", "accept"}


def random_accept_delay(min_seconds: float, max_seconds: float) -> float:
    return random.uniform(min_seconds, max_seconds)


def should_accept_ready_check(payload: dict[str, Any] | None) -> bool:
    if not payload:
        return False

    state = _normalize(payload.get("state"))
    player_response = _normalize(payload.get("playerResponse"))

    return state in READY_CHECK_ACTIVE_STATES and player_response in UNANSWERED_PLAYER_RESPONSES


def has_player_accepted(payload: dict[str, Any] | None) -> bool:
    if not payload:
        return False

    return _normalize(payload.get("playerResponse")) in ACCEPTED_PLAYER_RESPONSES


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().replace("-", "_").lower()
