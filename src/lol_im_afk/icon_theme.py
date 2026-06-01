from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw


@dataclass(frozen=True)
class IconTheme:
    key: str
    label: str


ICON_THEMES: tuple[IconTheme, ...] = (
    IconTheme("status", "Status: check / pause"),
    IconTheme("runner_seat", "AFK runner / seat"),
    IconTheme("smoke_game", "AFK smoke / gamepad"),
)


def icon_theme_by_key(key: str) -> IconTheme:
    return next((theme for theme in ICON_THEMES if theme.key == key), ICON_THEMES[0])


def icon_theme_key_from_label(label: str) -> str:
    return next((theme.key for theme in ICON_THEMES if theme.label == label), ICON_THEMES[0].key)


def icon_theme_label_from_key(key: str) -> str:
    return icon_theme_by_key(key).label


def create_icon_image(enabled: bool, theme_key: str) -> Image.Image:
    if icon_theme_by_key(theme_key).key == "runner_seat":
        return _runner_seat_icon(enabled)
    if icon_theme_by_key(theme_key).key == "smoke_game":
        return _smoke_game_icon(enabled)
    return _status_icon(enabled)


def _base(fill: tuple[int, int, int, int]) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((4, 4, 60, 60), fill=fill)
    draw.ellipse((4, 4, 60, 60), outline=(255, 255, 255, 230), width=4)
    return image, draw


def _status_icon(enabled: bool) -> Image.Image:
    fill = (0, 170, 85, 255) if enabled else (220, 40, 40, 255)
    image, draw = _base(fill)

    if enabled:
        draw.line((19, 33, 28, 43, 46, 22), fill=(255, 255, 255, 255), width=8, joint="curve")
    else:
        draw.rounded_rectangle((18, 18, 27, 46), radius=3, fill=(255, 255, 255, 255))
        draw.rounded_rectangle((37, 18, 46, 46), radius=3, fill=(255, 255, 255, 255))

    return image


def _runner_seat_icon(enabled: bool) -> Image.Image:
    fill = (0, 150, 95, 255) if enabled else (60, 100, 210, 255)
    image, draw = _base(fill)

    if enabled:
        draw.ellipse((27, 12, 39, 24), fill=(255, 255, 255, 255))
        draw.line((32, 25, 25, 38), fill=(255, 255, 255, 255), width=6)
        draw.line((29, 29, 17, 27), fill=(255, 255, 255, 255), width=5)
        draw.line((27, 38, 18, 51), fill=(255, 255, 255, 255), width=6)
        draw.line((27, 38, 42, 48), fill=(255, 255, 255, 255), width=6)
        draw.line((35, 28, 47, 21), fill=(255, 255, 255, 255), width=5)
    else:
        draw.rounded_rectangle((18, 20, 43, 36), radius=5, fill=(255, 255, 255, 255))
        draw.rounded_rectangle((20, 35, 48, 45), radius=4, fill=(255, 255, 255, 255))
        draw.line((24, 45, 20, 53), fill=(255, 255, 255, 255), width=5)
        draw.line((44, 45, 49, 53), fill=(255, 255, 255, 255), width=5)

    return image


def _smoke_game_icon(enabled: bool) -> Image.Image:
    fill = (95, 105, 115, 255) if enabled else (120, 65, 200, 255)
    image, draw = _base(fill)

    if enabled:
        draw.rounded_rectangle((15, 35, 47, 43), radius=3, fill=(255, 255, 255, 255))
        draw.rectangle((40, 35, 47, 43), fill=(245, 180, 65, 255))
        draw.arc((27, 13, 47, 35), start=95, end=250, fill=(255, 255, 255, 220), width=4)
        draw.arc((37, 9, 56, 31), start=95, end=250, fill=(255, 255, 255, 180), width=3)
    else:
        draw.rounded_rectangle((14, 27, 50, 45), radius=9, fill=(255, 255, 255, 255))
        draw.ellipse((20, 33, 27, 40), fill=fill)
        draw.ellipse((37, 31, 43, 37), fill=fill)
        draw.ellipse((44, 36, 49, 41), fill=fill)
        draw.line((16, 24, 23, 17), fill=(255, 255, 255, 255), width=4)
        draw.line((48, 24, 41, 17), fill=(255, 255, 255, 255), width=4)

    return image
