from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

from lol_im_afk.config import AppConfig
from lol_im_afk.events import AppEvent, EventKind
from lol_im_afk.lcu_client import LcuApiError, LcuClient, LcuUnavailableError
from lol_im_afk.ready_check import has_player_accepted, random_accept_delay, should_accept_ready_check
from lol_im_afk.status import StatusStore


LOGGER = logging.getLogger(__name__)


class AutoAcceptWorker:
    def __init__(
        self,
        config: AppConfig,
        lcu_client: LcuClient,
        status_store: StatusStore,
        event_callback: Callable[[AppEvent], None] | None = None,
    ) -> None:
        self._config = config
        self._lcu_client = lcu_client
        self._status_store = status_store
        self._event_callback = event_callback
        self._stop_event = threading.Event()
        self._enabled_lock = threading.Lock()
        self._enabled = True
        self._thread = threading.Thread(target=self._run, name="lol-im-afk-worker", daemon=True)
        self._cooldown_until = 0.0
        self._last_phase: str | None = None
        self._ready_check_seen = False
        self._accepted_notified = False

    def set_event_callback(self, event_callback: Callable[[AppEvent], None] | None) -> None:
        self._event_callback = event_callback

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=5)

    def is_enabled(self) -> bool:
        with self._enabled_lock:
            return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        with self._enabled_lock:
            self._enabled = enabled
        self._status_store.set_enabled(enabled)
        LOGGER.info("Auto-accept %s", "enabled" if enabled else "disabled")
        kind = EventKind.AUTO_ACCEPT_ENABLED if enabled else EventKind.AUTO_ACCEPT_DISABLED
        self._emit_event(kind, f"Auto-accept {'enabled' if enabled else 'disabled'}")

    def toggle_enabled(self) -> None:
        self.set_enabled(not self.is_enabled())

    def update_timing(self, delay_min_seconds: float, delay_max_seconds: float) -> None:
        self._config.delay_min_seconds = delay_min_seconds
        self._config.delay_max_seconds = delay_max_seconds
        self._config.validate()
        LOGGER.info("Updated accept delay range to %.2f-%.2f seconds", delay_min_seconds, delay_max_seconds)

    def update_lockfile_paths(self, lockfile_paths) -> None:
        self._config.lockfile_paths = lockfile_paths
        self._lcu_client.set_lockfile_paths(lockfile_paths)
        LOGGER.info("Updated League lockfile paths")

    def test_connection(self) -> str:
        return self._lcu_client.get_gameflow_phase()

    def _run(self) -> None:
        LOGGER.info("Worker started")
        while not self._stop_event.is_set():
            if not self.is_enabled():
                self._status_store.set_text("Paused")
                self._sleep(self._config.poll_interval_seconds)
                continue

            try:
                self._poll_once()
                self._sleep(self._config.poll_interval_seconds)
            except LcuUnavailableError as exc:
                LOGGER.debug("League client unavailable: %s", exc)
                self._reset_client_state()
                self._status_store.set_text("Waiting for League client")
                self._sleep(self._config.reconnect_interval_seconds)
            except LcuApiError as exc:
                LOGGER.warning("League client API error: %s", exc)
                self._status_store.set_text(f"LCU error: HTTP {exc.status_code}")
                self._sleep(self._config.poll_interval_seconds)
            except Exception:
                LOGGER.exception("Unexpected worker error")
                self._status_store.set_text("Unexpected error; see log")
                self._sleep(self._config.reconnect_interval_seconds)

        LOGGER.info("Worker stopped")

    def _poll_once(self) -> None:
        phase = self._lcu_client.get_gameflow_phase()
        self._handle_phase(phase)
        ready_check = self._lcu_client.get_ready_check()

        if should_accept_ready_check(ready_check):
            if time.monotonic() < self._cooldown_until:
                self._status_store.set_text("Ready check seen; cooldown active")
                return

            self._accept_after_delay()
            return
        if phase == "ReadyCheck" and has_player_accepted(ready_check):
            self._mark_manually_accepted()

        self._status_store.set_text(f"Connected; phase: {phase}")

    def _handle_phase(self, phase: str) -> None:
        if phase == self._last_phase:
            return

        self._last_phase = phase
        LOGGER.info("League gameflow phase changed to %s", phase)

        if phase == "ChampSelect":
            self._emit_event(EventKind.CHAMP_SELECT_STARTED, "Champion select started")
            self._ready_check_seen = False
            self._accepted_notified = False
        elif phase == "Matchmaking":
            if self._ready_check_seen:
                self._emit_event(EventKind.BACK_IN_QUEUE, "Back in queue; ready check failed")
            else:
                self._emit_event(EventKind.QUEUE_STARTED, "Queue started")
            self._ready_check_seen = False
            self._accepted_notified = False
        elif phase in {"Lobby", "None"} and self._ready_check_seen:
            self._emit_event(EventKind.READY_CHECK_FAILED_LOBBY, "Ready check failed; lobby returned")
            self._ready_check_seen = False
            self._accepted_notified = False
        elif phase == "ReadyCheck":
            self._ready_check_seen = True

    def _accept_after_delay(self) -> None:
        delay = random_accept_delay(
            self._config.delay_min_seconds,
            self._config.delay_max_seconds,
        )
        self._status_store.set_text(f"Ready check found; accepting in {delay:.1f}s")
        LOGGER.info("Ready check found; accepting in %.2f seconds", delay)
        self._ready_check_seen = True
        self._accepted_notified = False
        self._emit_event(EventKind.MATCH_FOUND, f"Match found; accepting in {delay:.1f}s")

        if self._sleep(delay):
            return

        if not self.is_enabled():
            LOGGER.info("Skipped accept because auto-accept is disabled")
            self._status_store.set_text("Skipped accept; disabled")
            self._emit_event(EventKind.SKIPPED_DISABLED, "Skipped accept; auto-accept is disabled")
            return

        ready_check = self._lcu_client.get_ready_check()
        if has_player_accepted(ready_check):
            self._mark_manually_accepted()
            return

        if not should_accept_ready_check(ready_check):
            phase = self._lcu_client.get_gameflow_phase()
            self._handle_phase(phase)
            if phase == "ChampSelect":
                self._status_store.set_text("Champion select started")
                return

            if phase == "ReadyCheck":
                LOGGER.info("Ready check ended before app accept; waiting for outcome")
                self._status_store.set_text("Ready check answered; waiting for outcome")
            else:
                self._status_store.set_text(f"Connected; phase: {phase}")
            self._cooldown_until = time.monotonic() + self._config.accept_cooldown_seconds
            return

        try:
            self._lcu_client.accept_ready_check()
        except LcuApiError:
            ready_check = self._lcu_client.get_ready_check()
            if has_player_accepted(ready_check):
                self._mark_manually_accepted()
                return
            phase = self._lcu_client.get_gameflow_phase()
            if phase == "ChampSelect":
                self._handle_phase(phase)
                return
            if phase == "ReadyCheck" and ready_check is None:
                LOGGER.info("Accept request raced with ready-check completion; waiting for outcome")
                self._status_store.set_text("Ready check answered; waiting for outcome")
                self._cooldown_until = time.monotonic() + self._config.accept_cooldown_seconds
                return
            raise

        self._accepted_notified = True
        self._cooldown_until = time.monotonic() + self._config.accept_cooldown_seconds
        LOGGER.info("Accepted League ready check")
        self._status_store.set_text("Accepted match")
        self._emit_event(EventKind.ACCEPTED_AUTOMATICALLY, "Accepted match automatically")

    def _sleep(self, seconds: float) -> bool:
        return self._stop_event.wait(seconds)

    def _mark_manually_accepted(self) -> None:
        self._cooldown_until = time.monotonic() + self._config.accept_cooldown_seconds
        if self._accepted_notified:
            return
        self._accepted_notified = True
        self._status_store.set_text("Accepted match manually")
        LOGGER.info("Detected manual ready-check acceptance")
        self._emit_event(EventKind.ACCEPTED_MANUALLY, "Accepted match manually")

    def _reset_client_state(self) -> None:
        self._last_phase = None
        self._ready_check_seen = False
        self._accepted_notified = False
        self._cooldown_until = 0.0

    def _emit_event(self, kind: EventKind, message: str) -> None:
        event = AppEvent(kind=kind, message=message)
        LOGGER.info(event.display_text)
        if self._event_callback is not None:
            self._event_callback(event)
