from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont
from pystray import Icon, Menu, MenuItem

from lol_im_afk.desktop_ui import DesktopUi
from lol_im_afk.status import StatusStore
from lol_im_afk.worker import AutoAcceptWorker


TRAY_NOTIFICATION_EVENTS = (
    "Match found",
    "Accepted match",
    "Champion select started",
    "Ready check ended",
    "Skipped accept",
)


def run_tray(worker: AutoAcceptWorker, status_store: StatusStore, desktop_ui: DesktopUi) -> None:
    image = _create_icon_image(worker.is_enabled())

    def status_text(_: MenuItem) -> str:
        snapshot = status_store.snapshot()
        enabled_text = "on" if snapshot.enabled else "off"
        return f"Status: {snapshot.text} ({enabled_text})"

    def toggle(_: Icon, __: MenuItem) -> None:
        worker.toggle_enabled()
        _.icon = _create_icon_image(worker.is_enabled())

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
    worker.set_event_callback(lambda event: _notify_event(desktop_ui, event))
    icon.run()


def _notify_event(desktop_ui: DesktopUi, event: str) -> None:
    if not _should_notify_event(event):
        return

    desktop_ui.notify(event)


def _should_notify_event(event: str) -> bool:
    return any(message in event for message in TRAY_NOTIFICATION_EVENTS)


def _create_icon_image(enabled: bool) -> Image.Image:
    size = 64
    image = Image.new("RGBA", (size, size), (22, 22, 22, 255))
    draw = ImageDraw.Draw(image)
    color = (0, 145, 70, 255) if enabled else (190, 35, 35, 255)
    text = "AFK" if enabled else "OFF"
    draw.rounded_rectangle((2, 2, 62, 62), radius=8, fill=color)
    draw.text(
        (32, 32),
        text,
        fill=(255, 255, 255, 255),
        font=_icon_font(),
        anchor="ma",
    )
    return image


def _icon_font() -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arialbd.ttf", 20)
    except OSError:
        return ImageFont.load_default()
