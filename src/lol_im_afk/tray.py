from __future__ import annotations

from pystray import Icon, Menu, MenuItem

from lol_im_afk.desktop_ui import DesktopUi
from lol_im_afk.events import AppEvent, EventKind
from lol_im_afk.icon_theme import create_icon_image
from lol_im_afk.status import StatusStore
from lol_im_afk.user_settings import SettingsStore
from lol_im_afk.worker import AutoAcceptWorker


TRAY_NOTIFICATION_EVENTS = {
    EventKind.QUEUE_STARTED,
    EventKind.MATCH_FOUND,
    EventKind.ACCEPTED_AUTOMATICALLY,
    EventKind.ACCEPTED_MANUALLY,
    EventKind.CHAMP_SELECT_STARTED,
    EventKind.BACK_IN_QUEUE,
    EventKind.READY_CHECK_FAILED_LOBBY,
    EventKind.SKIPPED_DISABLED,
    EventKind.TEST_NOTIFICATION,
}


def run_tray(
    worker: AutoAcceptWorker,
    status_store: StatusStore,
    desktop_ui: DesktopUi,
    settings_store: SettingsStore,
) -> None:
    image = create_icon_image(worker.is_enabled(), settings_store.settings.icon_theme)

    def update_icon(icon: Icon) -> None:
        icon.icon = create_icon_image(worker.is_enabled(), settings_store.settings.icon_theme)

    def status_text(_: MenuItem) -> str:
        snapshot = status_store.snapshot()
        enabled_text = "on" if snapshot.enabled else "off"
        return f"Status: {snapshot.text} ({enabled_text})"

    def toggle(_: Icon, __: MenuItem) -> None:
        worker.toggle_enabled()
        update_icon(_)

    def open_settings(_: Icon, __: MenuItem) -> None:
        desktop_ui.open_settings()

    def is_checked(_: MenuItem) -> bool:
        return worker.is_enabled()

    def quit_app(icon: Icon, _: MenuItem) -> None:
        worker.stop()
        desktop_ui.stop()
        icon.stop()

    icon = Icon(
        "lol-im-afk",
        image,
        "lol-im-afk",
        Menu(
            MenuItem("Toggle Enabled", toggle, default=True, visible=False),
            MenuItem(status_text, None, enabled=False),
            MenuItem("Enabled", toggle, checked=is_checked),
            MenuItem("Settings", open_settings),
            MenuItem("Quit", quit_app),
        ),
    )
    desktop_ui.set_icon_theme_changed_callback(lambda: update_icon(icon))
    worker.set_event_callback(lambda event: _notify_event(desktop_ui, event))
    icon.run()


def _notify_event(desktop_ui: DesktopUi, event: AppEvent) -> None:
    if not _should_notify_event(event):
        return

    desktop_ui.notify(event)


def _should_notify_event(event: AppEvent) -> bool:
    return event.kind in TRAY_NOTIFICATION_EVENTS
