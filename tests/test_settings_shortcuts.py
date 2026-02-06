"""
Tests for keyboard shortcuts section in settings dialog.

Uses source code inspection to avoid GTK mocking issues.
"""

import os
import unittest


def _get_source_code():
    """Read the settings dialog source file."""
    source_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "vocalinux",
        "ui",
        "settings_dialog.py",
    )
    with open(source_path, "r") as f:
        return f.read()


class TestSettingsDialogShortcutsSection(unittest.TestCase):
    """Test cases for keyboard shortcuts section in settings dialog."""

    def setUp(self):
        """Set up test fixtures."""
        self.source_code = _get_source_code()

    def test_shortcuts_section_exists(self):
        """Test that shortcuts section build method exists."""
        self.assertIn("def _build_shortcuts_section(self)", self.source_code)

    def test_shortcuts_section_called_in_init(self):
        """Test that shortcuts section is built in __init__."""
        self.assertIn("self._build_shortcuts_section()", self.source_code)

    def test_shortcut_combo_widget_created(self):
        """Test that shortcut combo box widget is created."""
        self.assertIn("self.shortcut_combo = Gtk.ComboBoxText()", self.source_code)

    def test_shortcut_combo_size_request(self):
        """Test that shortcut combo has size request set."""
        self.assertIn("self.shortcut_combo.set_size_request(200, -1)", self.source_code)

    def test_shortcut_combo_tooltip(self):
        """Test that shortcut combo has a tooltip."""
        self.assertIn("self.shortcut_combo.set_tooltip_text(", self.source_code)

    def test_shortcut_options_populated(self):
        """Test that shortcut options are populated from SHORTCUT_DISPLAY_NAMES."""
        self.assertIn(
            "for shortcut_id, display_name in SHORTCUT_DISPLAY_NAMES.items()", self.source_code
        )
        self.assertIn("self.shortcut_combo.append(shortcut_id, display_name)", self.source_code)

    def test_shortcut_config_read(self):
        """Test that shortcut is read from config."""
        self.assertIn('self.config_manager.get("shortcuts", "toggle_recognition"', self.source_code)

    def test_shortcut_changed_handler_exists(self):
        """Test that shortcut changed handler exists."""
        self.assertIn("def _on_shortcut_changed(self, widget)", self.source_code)

    def test_shortcut_change_saved_to_config(self):
        """Test that shortcut change is saved to config."""
        self.assertIn(
            'self.config_manager.set("shortcuts", "toggle_recognition", shortcut_id)',
            self.source_code,
        )

    def test_shortcut_change_triggers_save(self):
        """Test that shortcut change triggers config save."""
        # After setting the shortcut, save_settings should be called
        self.assertIn("self.config_manager.save_settings()", self.source_code)

    def test_shortcut_preference_row_title(self):
        """Test that preference row has correct title."""
        self.assertIn('title="Toggle Recognition"', self.source_code)

    def test_shortcut_preference_row_subtitle(self):
        """Test that preference row has descriptive subtitle."""
        self.assertIn("Press this shortcut twice quickly", self.source_code)

    def test_shortcut_info_label_exists(self):
        """Test that info label exists for user guidance."""
        self.assertIn("self.shortcut_info_label", self.source_code)

    def test_shortcut_info_box_styling(self):
        """Test that info box has proper styling."""
        self.assertIn('get_style_context().add_class("info-box")', self.source_code)

    def test_shortcut_group_title(self):
        """Test that shortcuts group has proper title."""
        self.assertIn('title="Keyboard Shortcuts"', self.source_code)

    def test_imports_shortcut_constants(self):
        """Test that shortcut constants are imported."""
        self.assertIn("from .keyboard_backends import SHORTCUT_DISPLAY_NAMES", self.source_code)
        self.assertIn("SUPPORTED_SHORTCUTS", self.source_code)


class TestKeyboardBackendsBase(unittest.TestCase):
    """Test cases for keyboard backends base module."""

    def test_supported_shortcuts_defined(self):
        """Test that SUPPORTED_SHORTCUTS is defined."""
        from vocalinux.ui.keyboard_backends.base import SUPPORTED_SHORTCUTS

        self.assertIsInstance(SUPPORTED_SHORTCUTS, dict)
        self.assertIn("ctrl+ctrl", SUPPORTED_SHORTCUTS)
        self.assertIn("alt+alt", SUPPORTED_SHORTCUTS)
        self.assertIn("shift+shift", SUPPORTED_SHORTCUTS)
        self.assertIn("super+super", SUPPORTED_SHORTCUTS)

    def test_shortcut_display_names_defined(self):
        """Test that SHORTCUT_DISPLAY_NAMES is defined."""
        from vocalinux.ui.keyboard_backends.base import SHORTCUT_DISPLAY_NAMES

        self.assertIsInstance(SHORTCUT_DISPLAY_NAMES, dict)
        self.assertEqual(
            set(SHORTCUT_DISPLAY_NAMES.keys()),
            {"ctrl+ctrl", "alt+alt", "shift+shift", "super+super"},
        )

    def test_default_shortcut_defined(self):
        """Test that DEFAULT_SHORTCUT is defined."""
        from vocalinux.ui.keyboard_backends.base import DEFAULT_SHORTCUT

        self.assertEqual(DEFAULT_SHORTCUT, "ctrl+ctrl")

    def test_keyboard_backend_shortcut_property(self):
        """Test that KeyboardBackend has shortcut property."""
        from vocalinux.ui.keyboard_backends.base import KeyboardBackend

        # Can't instantiate abstract class, but can check the property exists
        self.assertTrue(hasattr(KeyboardBackend, "shortcut"))
        self.assertTrue(hasattr(KeyboardBackend, "modifier_key"))
        self.assertTrue(hasattr(KeyboardBackend, "set_shortcut"))


class TestConfigManagerShortcuts(unittest.TestCase):
    """Test cases for shortcut configuration in config manager."""

    def test_shortcuts_section_in_default_config(self):
        """Test that shortcuts section exists in DEFAULT_CONFIG."""
        from vocalinux.ui.config_manager import DEFAULT_CONFIG

        self.assertIn("shortcuts", DEFAULT_CONFIG)
        self.assertIn("toggle_recognition", DEFAULT_CONFIG["shortcuts"])
        self.assertEqual(DEFAULT_CONFIG["shortcuts"]["toggle_recognition"], "ctrl+ctrl")

    def test_config_manager_get_shortcut(self):
        """Test getting shortcut from config manager."""
        from unittest.mock import patch

        with patch("vocalinux.ui.config_manager.os.path.exists", return_value=False):
            from vocalinux.ui.config_manager import ConfigManager

            config = ConfigManager()
            shortcut = config.get("shortcuts", "toggle_recognition", "ctrl+ctrl")
            self.assertEqual(shortcut, "ctrl+ctrl")


if __name__ == "__main__":
    unittest.main()
