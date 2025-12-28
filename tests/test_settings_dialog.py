"""
Tests for the SettingsDialog.
"""

import os

# Mock GTK before importing anything that might use it
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()

from vocalinux.common_types import RecognitionState

# Now import the class under test with GTK already mocked
from vocalinux.ui.settings_dialog import ENGINE_MODELS, SettingsDialog

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
            "model_size": "small",
            "vad_sensitivity": 3,
            "silence_timeout": 2.0,
        }
    }
)
mock_config_manager.update_speech_recognition_settings = Mock()
mock_config_manager.save_settings = Mock()


class TestSettingsDialog(unittest.TestCase):
    """Test cases for the settings dialog."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset mocks before each test
        mock_speech_engine.reset_mock()
        mock_config_manager.reset_mock()

        # Create mock for dialog components
        self.engine_combo = Mock()
        self.engine_combo.get_active_text.return_value = "Vosk"
        self.engine_combo.get_active_id.return_value = "Vosk"

        self.model_combo = Mock()
        self.model_combo.get_active_text.return_value = "Small"
        self.model_combo.get_active_id.return_value = "Small"

        self.vad_spin = Mock()
        self.vad_spin.get_value.return_value = 3

        self.silence_spin = Mock()
        self.silence_spin.get_value.return_value = 2.0

        self.vosk_settings_box = Mock()
        self.vosk_settings_box.is_visible.return_value = True

        self.test_button = Mock()

        self.test_textview = Mock()
        buffer_mock = Mock()
        buffer_mock.get_start_iter.return_value = Mock()
        buffer_mock.get_end_iter.return_value = Mock()
        buffer_mock.get_text.return_value = ""
        self.test_textview.get_buffer.return_value = buffer_mock

        # Mock SettingsDialog to avoid actually creating GTK objects
        with patch("vocalinux.ui.settings_dialog.SettingsDialog.__init__", return_value=None):
            self.dialog = SettingsDialog(
                parent=None,
                config_manager=mock_config_manager,
                speech_engine=mock_speech_engine,
            )
            # Set mock attributes on dialog
            self.dialog.engine_combo = self.engine_combo
            self.dialog.model_combo = self.model_combo
            self.dialog.vad_spin = self.vad_spin
            self.dialog.silence_spin = self.silence_spin
            self.dialog.vosk_settings_box = self.vosk_settings_box
            self.dialog.test_button = self.test_button
            self.dialog.test_textview = self.test_textview
            self.dialog.config_manager = mock_config_manager
            self.dialog.speech_engine = mock_speech_engine

            # Mock methods that interact with UI
            self.dialog.get_selected_settings = Mock(
                return_value={
                    "engine": "vosk",
                    "model_size": "small",
                    "vad_sensitivity": 3,
                    "silence_timeout": 2.0,
                }
            )

            # Create a real method for apply_settings to test
            self.dialog.apply_settings = SettingsDialog.apply_settings.__get__(
                self.dialog, SettingsDialog
            )
            self.dialog._test_text_callback = Mock()
            self.dialog._stop_test_after_delay = Mock()
            self.dialog.destroy = Mock()
            # Add missing attributes for apply_settings
            self.dialog.current_model_size = "small"
            self.dialog.current_engine = "vosk"
            self.dialog._populate_model_options = Mock()

    def test_apply_settings_success(self):
        """Test the apply_settings method calls config and engine methods."""
        # Change the returned settings for this test
        self.dialog.get_selected_settings.return_value = {
            "engine": "vosk",
            "model_size": "large",
            "vad_sensitivity": 3,
            "silence_timeout": 2.0,
        }

        # Ensure reconfigure doesn't raise an exception
        mock_speech_engine.reconfigure.side_effect = None

        # Mock the Gtk module for this test
        with patch("vocalinux.ui.settings_dialog.Gtk") as mock_gtk, patch(
            "vocalinux.ui.settings_dialog.GLib"
        ) as mock_glib, patch("vocalinux.ui.settings_dialog.threading") as mock_threading, patch(
            "vocalinux.ui.settings_dialog.time"
        ) as mock_time, patch(
            "vocalinux.ui.settings_dialog.logging"
        ) as mock_logging, patch(
            "vocalinux.ui.settings_dialog._is_vosk_model_downloaded", return_value=True
        ) as mock_vosk_check, patch(
            "vocalinux.ui.settings_dialog._is_whisper_model_downloaded", return_value=True
        ) as mock_whisper_check:
            # Call the method under test
            result = self.dialog.apply_settings()

            # Verify the result
            self.assertTrue(result)

            # Verify mocks were called with the right parameters
            mock_config_manager.update_speech_recognition_settings.assert_called_once()
            mock_config_manager.save_settings.assert_called_once()
            mock_speech_engine.reconfigure.assert_called_once()

    def test_apply_settings_stops_engine_if_running(self):
        """Test apply_settings stops the engine if it was running."""
        # Set the engine state to running
        mock_speech_engine.state = RecognitionState.LISTENING

        # Ensure reconfigure doesn't raise an exception
        mock_speech_engine.reconfigure.side_effect = None

        # Mock the Gtk module for this test
        with patch("vocalinux.ui.settings_dialog.Gtk") as mock_gtk, patch(
            "vocalinux.ui.settings_dialog.GLib"
        ) as mock_glib, patch("vocalinux.ui.settings_dialog.threading") as mock_threading, patch(
            "vocalinux.ui.settings_dialog.time"
        ) as mock_time, patch(
            "vocalinux.ui.settings_dialog.logging"
        ) as mock_logging, patch(
            "vocalinux.ui.settings_dialog._is_vosk_model_downloaded", return_value=True
        ) as mock_vosk_check, patch(
            "vocalinux.ui.settings_dialog._is_whisper_model_downloaded", return_value=True
        ) as mock_whisper_check:
            # Call the method under test
            result = self.dialog.apply_settings()

            # Verify the result
            self.assertTrue(result)

            # Verify engine was stopped before reconfigure
            mock_speech_engine.stop_recognition.assert_called_once()
            mock_speech_engine.reconfigure.assert_called_once()

    def test_apply_settings_failure_reconfigure(self):
        """Test apply_settings handles errors during engine reconfiguration."""
        # Set up the reconfigure method to raise an exception
        mock_speech_engine.reconfigure.side_effect = Exception("Model load failed")

        # Mock the Gtk module for this test
        with patch("vocalinux.ui.settings_dialog.Gtk") as mock_gtk, patch(
            "vocalinux.ui.settings_dialog.GLib"
        ) as mock_glib, patch("vocalinux.ui.settings_dialog.threading") as mock_threading, patch(
            "vocalinux.ui.settings_dialog.time"
        ) as mock_time, patch(
            "vocalinux.ui.settings_dialog.logging"
        ) as mock_logging, patch(
            "vocalinux.ui.settings_dialog._is_vosk_model_downloaded", return_value=True
        ) as mock_vosk_check, patch(
            "vocalinux.ui.settings_dialog._is_whisper_model_downloaded", return_value=True
        ) as mock_whisper_check:
            # Mock the message dialog
            mock_dialog = MagicMock()
            mock_gtk.MessageDialog.return_value = mock_dialog

            # Call the method under test
            result = self.dialog.apply_settings()

            # Verify the result
            self.assertFalse(result)

            # Verify mocks were called
            mock_config_manager.update_speech_recognition_settings.assert_called_once()
            mock_config_manager.save_settings.assert_called_once()
            mock_speech_engine.reconfigure.assert_called_once()

            # Verify error dialog was handled properly
            mock_gtk.MessageDialog.assert_called_once()
            mock_dialog.run.assert_called_once()
            mock_dialog.destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
