"""
Tests for the SettingsDialog.

Since SettingsDialog inherits from Gtk.Dialog which is mocked during tests,
we can't easily test the actual class methods. Instead, we test the core
logic that the settings dialog is supposed to execute.

UX Design Notes tested:
- Instant-apply pattern: settings apply immediately when changed
- Close-only button (no Apply/Cancel) consistent with GNOME Settings
"""

import sys
import time
import unittest
from unittest.mock import MagicMock, Mock, patch

# Mock GTK before importing anything that might use it
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.Pango"] = MagicMock()

from vocalinux.common_types import RecognitionState  # noqa: E402

# Create mock for speech engine
mock_speech_engine = Mock()
mock_speech_engine.state = RecognitionState.IDLE
mock_speech_engine.reconfigure = Mock()
mock_speech_engine.start_recognition = Mock()
mock_speech_engine.stop_recognition = Mock()
mock_speech_engine.register_text_callback = Mock()
mock_speech_engine.unregister_text_callback = Mock()

# Create mock for config manager
mock_config_manager = Mock()
mock_config_manager.get = Mock(
    return_value={
        "speech_recognition": {
            "engine": "vosk",
            "language": "en-us",
            "model_size": "small",
            "vad_sensitivity": 3,
            "silence_timeout": 2.0,
        }
    }
)
mock_config_manager.update_speech_recognition_settings = Mock()
mock_config_manager.save_settings = Mock()


def apply_settings_internal(dialog, settings: dict) -> bool:
    """
    Simplified version of SettingsDialog._apply_settings_internal for testing.
    This is a test helper that mirrors the real implementation behavior.
    """
    try:
        # 1. Update Config Manager
        dialog.config_manager.update_speech_recognition_settings(settings)
        dialog.config_manager.save_settings()

        # 2. Reconfigure Speech Engine
        # Stop engine before reconfiguring if it's running
        was_running = dialog.speech_engine.state != RecognitionState.IDLE
        if was_running:
            dialog.speech_engine.stop_recognition()
            # Give it a moment to fully stop
            time.sleep(0.01)  # Shortened for tests

        dialog.speech_engine.reconfigure(**settings)
        return True
    except Exception:
        return False


class TestSettingsDialog(unittest.TestCase):
    """Test cases for the settings dialog behavior."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset mocks before each test
        mock_speech_engine.reset_mock()
        mock_config_manager.reset_mock()
        mock_speech_engine.state = RecognitionState.IDLE

        # Create a mock dialog object directly
        self.dialog = Mock()

        # Set mock attributes on dialog
        self.dialog.config_manager = mock_config_manager
        self.dialog.speech_engine = mock_speech_engine

        # Default test settings
        self.test_settings = {
            "engine": "vosk",
            "model_size": "small",
            "vad_sensitivity": 3,
            "silence_timeout": 2.0,
        }

    def test_apply_settings_success(self):
        """Test the apply_settings method calls config and engine methods."""
        # Use larger model to test settings actually change
        settings = {
            "engine": "vosk",
            "language": "en-us",
            "model_size": "large",
            "vad_sensitivity": 3,
            "silence_timeout": 2.0,
        }

        # Ensure reconfigure doesn't raise an exception
        mock_speech_engine.reconfigure.side_effect = None

        # Call the method under test
        result = apply_settings_internal(self.dialog, settings)

        # Verify the result
        self.assertTrue(result)

        # Verify mocks were called with the right parameters
        mock_config_manager.update_speech_recognition_settings.assert_called_once_with(settings)
        mock_config_manager.save_settings.assert_called_once()
        mock_speech_engine.reconfigure.assert_called_once_with(**settings)

    def test_apply_settings_stops_engine_if_running(self):
        """Test apply_settings stops the engine if it was running."""
        # Set the engine state to running
        mock_speech_engine.state = RecognitionState.LISTENING

        # Ensure reconfigure doesn't raise an exception
        mock_speech_engine.reconfigure.side_effect = None

        # Call the method under test
        result = apply_settings_internal(self.dialog, self.test_settings)

        # Verify the result
        self.assertTrue(result)

        # Verify engine was stopped before reconfigure
        mock_speech_engine.stop_recognition.assert_called_once()
        mock_speech_engine.reconfigure.assert_called_once()

    def test_apply_settings_failure_reconfigure(self):
        """Test apply_settings handles errors during engine reconfiguration."""
        # Set up the reconfigure method to raise an exception
        mock_speech_engine.reconfigure.side_effect = Exception("Model load failed")

        # Call the method under test
        result = apply_settings_internal(self.dialog, self.test_settings)

        # Verify the result
        self.assertFalse(result)

        # Verify mocks were called
        mock_config_manager.update_speech_recognition_settings.assert_called_once()
        mock_config_manager.save_settings.assert_called_once()
        mock_speech_engine.reconfigure.assert_called_once()


class TestSettingsDialogCSS(unittest.TestCase):
    """Test cases for SettingsDialog CSS styling."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any cached imports
        if "vocalinux.ui.settings_dialog" in sys.modules:
            del sys.modules["vocalinux.ui.settings_dialog"]

    def test_settings_css_exists(self):
        """Test that SETTINGS_CSS constant is defined."""
        from vocalinux.ui.settings_dialog import SETTINGS_CSS

        self.assertIsInstance(SETTINGS_CSS, str)

    def test_settings_css_has_dialog_class(self):
        """Test that CSS includes settings-dialog class."""
        from vocalinux.ui.settings_dialog import SETTINGS_CSS

        self.assertIn(".settings-dialog", SETTINGS_CSS)

    def test_settings_css_has_preferences_group(self):
        """Test that CSS includes preferences-group class."""
        from vocalinux.ui.settings_dialog import SETTINGS_CSS

        self.assertIn(".preferences-group", SETTINGS_CSS)

    def test_settings_css_has_preference_row(self):
        """Test that CSS includes preference-row class."""
        from vocalinux.ui.settings_dialog import SETTINGS_CSS

        self.assertIn(".preference-row", SETTINGS_CSS)

    def test_settings_css_uses_theme_variables(self):
        """Test that CSS uses GTK theme variables."""
        from vocalinux.ui.settings_dialog import SETTINGS_CSS

        # Should use theme variables for proper light/dark mode support
        self.assertIn("@theme_bg_color", SETTINGS_CSS)
        self.assertIn("@theme_base_color", SETTINGS_CSS)

    def test_settings_css_has_status_classes(self):
        """Test that CSS includes status indicator classes."""
        from vocalinux.ui.settings_dialog import SETTINGS_CSS

        self.assertIn(".status-success", SETTINGS_CSS)
        self.assertIn(".status-warning", SETTINGS_CSS)
        self.assertIn(".status-error", SETTINGS_CSS)


class TestSettingsDialogClasses(unittest.TestCase):
    """Test cases for SettingsDialog helper classes."""

    def setUp(self):
        """Set up test fixtures."""
        if "vocalinux.ui.settings_dialog" in sys.modules:
            del sys.modules["vocalinux.ui.settings_dialog"]

    def test_preferences_group_class_exists(self):
        """Test that PreferencesGroup class exists."""
        from vocalinux.ui.settings_dialog import PreferencesGroup

        self.assertTrue(callable(PreferencesGroup))

    def test_preference_row_class_exists(self):
        """Test that PreferenceRow class exists."""
        from vocalinux.ui.settings_dialog import PreferenceRow

        self.assertTrue(callable(PreferenceRow))

    def test_model_download_dialog_class_exists(self):
        """Test that ModelDownloadDialog class exists."""
        from vocalinux.ui.settings_dialog import ModelDownloadDialog

        self.assertTrue(callable(ModelDownloadDialog))


class TestSettingsDialogInstantApply(unittest.TestCase):
    """Test cases for instant-apply behavior (Close-only button pattern)."""

    def setUp(self):
        """Set up test fixtures."""
        if "vocalinux.ui.settings_dialog" in sys.modules:
            del sys.modules["vocalinux.ui.settings_dialog"]

    def test_settings_dialog_has_auto_apply_method(self):
        """Test that SettingsDialog has _auto_apply_settings method in source."""
        import os

        source_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "src",
            "vocalinux",
            "ui",
            "settings_dialog.py",
        )
        with open(source_path, "r") as f:
            source_code = f.read()

        self.assertIn("def _auto_apply_settings(self", source_code)

    def test_settings_dialog_close_only_pattern(self):
        """Test that SettingsDialog uses Close-only button pattern (no Apply/Cancel)."""
        import os

        source_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "src",
            "vocalinux",
            "ui",
            "settings_dialog.py",
        )
        with open(source_path, "r") as f:
            source_code = f.read()

        # Check for Close button
        self.assertIn("_Close", source_code)
        # Should NOT have Apply or Cancel buttons (instant-apply pattern)
        self.assertNotIn("_Apply", source_code)
        self.assertNotIn("ResponseType.APPLY", source_code)

    def test_settings_dialog_no_revert_settings(self):
        """Test that SettingsDialog does NOT have _revert_settings (removed)."""
        from vocalinux.ui.settings_dialog import SettingsDialog

        # _revert_settings was removed as part of Close-only button pattern
        self.assertFalse(hasattr(SettingsDialog, "_revert_settings"))

    def test_settings_dialog_no_show_applied_message(self):
        """Test that SettingsDialog does NOT have _show_settings_applied_message (removed)."""
        from vocalinux.ui.settings_dialog import SettingsDialog

        # _show_settings_applied_message was removed as part of instant-apply pattern
        self.assertFalse(hasattr(SettingsDialog, "_show_settings_applied_message"))


class TestSettingsDialogHelperFunctions(unittest.TestCase):
    """Test cases for settings dialog helper functions."""

    def setUp(self):
        """Set up test fixtures."""
        if "vocalinux.ui.settings_dialog" in sys.modules:
            del sys.modules["vocalinux.ui.settings_dialog"]

    def test_format_size_function_exists(self):
        """Test that _format_size function exists."""
        from vocalinux.ui.settings_dialog import _format_size

        self.assertTrue(callable(_format_size))

    def test_format_size_mb(self):
        """Test _format_size with MB values."""
        from vocalinux.ui.settings_dialog import _format_size

        self.assertEqual(_format_size(100), "100 MB")
        self.assertEqual(_format_size(500), "500 MB")

    def test_format_size_gb(self):
        """Test _format_size with GB values."""
        from vocalinux.ui.settings_dialog import _format_size

        self.assertEqual(_format_size(1000), "1.0 GB")
        self.assertEqual(_format_size(2500), "2.5 GB")

    def test_is_whisper_model_downloaded_function_exists(self):
        """Test that _is_whisper_model_downloaded function exists."""
        from vocalinux.ui.settings_dialog import _is_whisper_model_downloaded

        self.assertTrue(callable(_is_whisper_model_downloaded))

    def test_is_vosk_model_downloaded_function_exists(self):
        """Test that _is_vosk_model_downloaded function exists."""
        from vocalinux.ui.settings_dialog import _is_vosk_model_downloaded

        self.assertTrue(callable(_is_vosk_model_downloaded))

    def test_get_recommended_whisper_model_function_exists(self):
        """Test that _get_recommended_whisper_model function exists."""
        from vocalinux.ui.settings_dialog import _get_recommended_whisper_model

        self.assertTrue(callable(_get_recommended_whisper_model))

    def test_get_recommended_vosk_model_function_exists(self):
        """Test that _get_recommended_vosk_model function exists."""
        from vocalinux.ui.settings_dialog import _get_recommended_vosk_model

        self.assertTrue(callable(_get_recommended_vosk_model))


if __name__ == "__main__":
    unittest.main()
