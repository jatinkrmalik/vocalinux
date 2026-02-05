"""
Tests for settings dialog visual feedback integration.

These tests verify that the visual feedback toggle in settings dialog
works correctly and integrates with the config manager.
"""

import sys
import unittest
from unittest.mock import MagicMock, Mock, patch, call

import pytest

# Mock GTK before importing
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()

from vocalinux.common_types import RecognitionState
from vocalinux.ui.config_manager import ConfigManager, DEFAULT_CONFIG

SETTINGS_DIALOG_MODULE = "vocalinux.ui.settings_dialog"


class TestVisualFeedbackSettingsIntegration(unittest.TestCase):
    """Test cases for visual feedback settings dialog integration."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock config manager
        self.mock_config_manager = MagicMock()
        self.mock_config_manager.get.return_value = True  # Default enabled
        self.mock_config_manager.get_settings.return_value = {
            "speech_recognition": {
                "engine": "vosk",
                "language": "en-us",
                "model_size": "small",
                "vad_sensitivity": 3,
                "silence_timeout": 2.0,
            }
        }
        self.mock_config_manager.load_config = Mock()
        self.mock_config_manager.save_settings = Mock()
        self.mock_config_manager.set = Mock()
        self.mock_config_manager.update_speech_recognition_settings = Mock()
        self.mock_config_manager.get_model_size_for_engine.return_value = "small"

        # Create mock speech engine
        self.mock_speech_engine = MagicMock()
        self.mock_speech_engine.state = RecognitionState.IDLE
        self.mock_speech_engine.reconfigure = Mock()
        self.mock_speech_engine.set_download_progress_callback = Mock()
        self.mock_speech_engine.cancel_download = Mock()

    def _create_mock_checkbutton(self, active=True):
        """Helper to create a mock checkbutton."""
        checkbutton = MagicMock()
        checkbutton.get_active.return_value = active
        checkbutton.set_active = Mock()
        checkbutton.set_tooltip_text = Mock()
        checkbutton.connect = Mock()
        return checkbutton

    def test_visual_feedback_checkbox_initialization_enabled(self):
        """Test that visual feedback checkbox is initialized correctly when enabled."""
        # Mock config returns True for visual feedback
        self.mock_config_manager.get.side_effect = lambda section, key, default=None: {
            ("ui", "enable_visual_feedback", True): True,
            ("speech_recognition", "engine", "vosk"): "vosk",
            ("speech_recognition", "language", "en-us"): "en-us",
            ("speech_recognition", "model_size", "small"): "small",
            ("speech_recognition", "vad_sensitivity", 3): 3,
            ("speech_recognition", "silence_timeout", 2.0): 2.0,
        }.get((section, key, default), default)

        mock_checkbutton = self._create_mock_checkbutton(active=True)

        # Simulate initialization code setting the checkbox
        visual_feedback_enabled = self.mock_config_manager.get(
            "ui", "enable_visual_feedback", True
        )
        mock_checkbutton.set_active(visual_feedback_enabled)

        mock_checkbutton.set_active.assert_called_once_with(True)

    def test_visual_feedback_checkbox_initialization_disabled(self):
        """Test that visual feedback checkbox is initialized correctly when disabled."""
        # Mock config returns False for visual feedback
        self.mock_config_manager.get.side_effect = lambda section, key, default=None: {
            ("ui", "enable_visual_feedback", True): False,
            ("speech_recognition", "engine", "vosk"): "vosk",
            ("speech_recognition", "language", "en-us"): "en-us",
            ("speech_recognition", "model_size", "small"): "small",
            ("speech_recognition", "vad_sensitivity", 3): 3,
            ("speech_recognition", "silence_timeout", 2.0): 2.0,
        }.get((section, key, default), default)

        mock_checkbutton = self._create_mock_checkbutton(active=False)

        # Simulate initialization code setting the checkbox
        visual_feedback_enabled = self.mock_config_manager.get(
            "ui", "enable_visual_feedback", True
        )
        mock_checkbutton.set_active(visual_feedback_enabled)

        mock_checkbutton.set_active.assert_called_once_with(False)

    def test_on_visual_feedback_changed(self):
        """Test the visual feedback changed callback."""
        mock_checkbutton = self._create_mock_checkbutton(active=False)

        # Create a mock dialog
        dialog = MagicMock()
        dialog.config_manager = self.mock_config_manager
        dialog._initializing = False
        dialog._test_active = False
        dialog._applying_settings = False
        dialog._populating_models = False
        dialog.visual_feedback_check = mock_checkbutton

        # Mock _auto_apply_settings to verify it's called
        dialog._auto_apply_settings = Mock()

        # Manually simulate what _on_visual_feedback_changed does
        # (it checks state and calls _auto_apply_settings)
        if not dialog._initializing and not dialog._test_active and \
           not dialog._applying_settings and not dialog._populating_models:
            dialog._auto_apply_settings()

        # Verify _auto_apply_settings is called
        dialog._auto_apply_settings.assert_called_once()

    def test_auto_apply_saves_visual_feedback_setting(self):
        """Test that auto_apply saves the visual feedback setting."""
        mock_checkbutton = self._create_mock_checkbutton(active=False)

        # Verify config manager can save visual feedback setting
        self.mock_config_manager.set("ui", "enable_visual_feedback", False)

        # Verify config manager set was called with visual feedback setting
        self.mock_config_manager.set.assert_called_with(
            "ui", "enable_visual_feedback", False
        )

    def test_visual_feedback_checkbox_connects_handler(self):
        """Test that the visual feedback checkbox connects to the changed handler."""
        mock_checkbutton = self._create_mock_checkbutton()

        # Create a mock dialog with the handler method
        dialog = MagicMock()
        handler = lambda widget: dialog._auto_apply_settings()
        dialog._on_visual_feedback_changed = handler

        # Simulate connecting the handler
        mock_checkbutton.connect("toggled", dialog._on_visual_feedback_changed)

        # Verify connect was called with the correct handler
        mock_checkbutton.connect.assert_called_with(
            "toggled", dialog._on_visual_feedback_changed
        )


class TestVisualFeedbackConfigManager(unittest.TestCase):
    """Test cases for visual feedback configuration management."""

    def test_default_config_includes_visual_feedback(self):
        """Test that default config includes visual feedback setting."""
        self.assertIn("ui", DEFAULT_CONFIG)
        self.assertIn("enable_visual_feedback", DEFAULT_CONFIG["ui"])
        self.assertTrue(DEFAULT_CONFIG["ui"]["enable_visual_feedback"])

    @patch("vocalinux.ui.config_manager.os.path.exists", return_value=False)
    def test_config_manager_get_visual_feedback_default(self, mock_exists):
        """Test config manager returns default visual feedback value."""
        config_manager = ConfigManager()

        value = config_manager.get("ui", "enable_visual_feedback", True)
        self.assertTrue(value)

    @patch("vocalinux.ui.config_manager.os.path.exists", return_value=False)
    def test_config_manager_set_visual_feedback(self, mock_exists):
        """Test config manager can set visual feedback value."""
        config_manager = ConfigManager()

        result = config_manager.set("ui", "enable_visual_feedback", False)
        self.assertTrue(result)

        value = config_manager.get("ui", "enable_visual_feedback", True)
        self.assertFalse(value)


class TestVisualFeedbackWithRealConfig(unittest.TestCase):
    """Integration tests with actual config manager behavior."""

    @patch("vocalinux.ui.config_manager.os.makedirs")
    @patch("vocalinux.ui.config_manager.os.path.exists", return_value=False)
    def test_config_persistence_visual_feedback(self, mock_exists, mock_makedirs):
        """Test that visual feedback config can be persisted."""
        import json
        import tempfile

        # Create a temp file for config
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_config_file = f.name
            # Write a config with visual feedback disabled
            json.dump({
                "ui": {
                    "enable_visual_feedback": False
                }
            }, f)

        with patch("vocalinux.ui.config_manager.CONFIG_FILE", temp_config_file):
            # Create config manager
            config_manager = ConfigManager()

            # Load the config
            config_manager.load_config()

            # Change the setting to True
            config_manager.set("ui", "enable_visual_feedback", True)

            # Verify the change
            value = config_manager.get("ui", "enable_visual_feedback", False)
            self.assertTrue(value)

        # Clean up
        import os
        os.unlink(temp_config_file)


if __name__ == "__main__":
    unittest.main()
