import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lol_im_afk.icon_theme import (
    ICON_THEMES,
    create_icon_image,
    icon_theme_by_key,
    icon_theme_key_from_label,
    icon_theme_label_from_key,
)


class IconThemeTest(unittest.TestCase):
    def test_known_themes_render_enabled_and_disabled_icons(self) -> None:
        for theme in ICON_THEMES:
            with self.subTest(theme=theme.key):
                enabled = create_icon_image(True, theme.key)
                disabled = create_icon_image(False, theme.key)

                self.assertEqual(enabled.size, (64, 64))
                self.assertEqual(disabled.size, (64, 64))

    def test_unknown_theme_falls_back_to_status(self) -> None:
        self.assertEqual(icon_theme_by_key("missing").key, "status")

    def test_label_mapping_roundtrip(self) -> None:
        label = icon_theme_label_from_key("runner_seat")

        self.assertEqual(icon_theme_key_from_label(label), "runner_seat")


if __name__ == "__main__":
    unittest.main()
