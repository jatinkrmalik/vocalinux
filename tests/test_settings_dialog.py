"""
Tests for the SettingsDialog.
"""

import os
import time
import unittest
from unittest.mock import MagicMock, patch, ANY

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

# Mock necessary modules before importing the classes under test
# Mock SpeechRecognitionManager methods that might involve hardware/downloads
mock_speech_engine = MagicMock()
mock_speech_engine.state = "IDLE"  # Use string representation for simplicity in mock
mock_speech_engine.reconfigure = MagicMock()
mock_speech_engine.start_recognition = MagicMock()
mock_speech_engine.stop_recognition = MagicMock()
mock_speech_engine.register_text_callback = MagicMock()
mock_speech_engine.unregister_text_callback = MagicMock()

# Mock ConfigManager
mock_config_manager = MagicMock()
mock_config_manager.get_settings = MagicMock(
    return_value={
        "speech_recognition": {
            "engine": "vosk",
            "model_size": "small",
            "vad_sensitivity": 3,
            "silence_timeout": 2.0,
        }
    }
)
mock_config_manager.update_speech_recognition_settings = MagicMock()
mock_config_manager.save_settings = MagicMock()

# Apply mocks using patch context managers or decorators if preferred
# For simplicity here, we assume they are globally mocked or passed directly

# Now import the class under test
from vocalinux.ui.settings_dialog import SettingsDialog, ENGINE_MODELS
from vocalinux.common_types import RecognitionState


# Helper function to process GTK events
def process_gtk_events():
    while Gtk.events_pending():
        Gtk.main_iteration()
    # Add a small sleep to allow async operations/callbacks to potentially trigger
    time.sleep(0.1)


class TestSettingsDialog(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Ensure GTK is initialized (though usually handled by running the app)
        pass

    def setUp(self):
        # Reset mocks before each test
        mock_speech_engine.reset_mock()
        mock_config_manager.reset_mock()
        # Reset config mock return value for consistency
        mock_config_manager.get_settings.return_value = {
            "speech_recognition": {
                "engine": "vosk",
                "model_size": "small",
                "vad_sensitivity": 3,
                "silence_timeout": 2.0,
            }
        }
        mock_speech_engine.state = RecognitionState.IDLE  # Use actual Enum

        # Create dialog instance for testing
        self.dialog = SettingsDialog(
            parent=None,
            config_manager=mock_config_manager,
            speech_engine=mock_speech_engine,
        )
        # Process events to ensure UI is constructed
        process_gtk_events()

    def tearDown(self):
        # Destroy the dialog window after each test
        if self.dialog:
            self.dialog.destroy()
        process_gtk_events()  # Process destroy events

    def test_dialog_initialization(self):
        """Test if the dialog initializes and loads settings correctly."""
        self.assertIsNotNone(self.dialog)
        self.assertEqual(self.dialog.engine_combo.get_active_text(), "Vosk")
        self.assertEqual(self.dialog.model_combo.get_active_text(), "Small")
        self.assertEqual(self.dialog.vad_spin.get_value(), 3)
        self.assertAlmostEqual(self.dialog.silence_spin.get_value(), 2.0, places=1)
        self.assertTrue(self.dialog.vosk_settings_box.is_visible())

    def test_engine_change_updates_models(self):
        """Test if changing the engine updates the model dropdown."""
        # Simulate changing engine to Whisper
        self.dialog.engine_combo.set_active_id("Whisper")
        process_gtk_events()

        self.assertEqual(self.dialog.engine_combo.get_active_text(), "Whisper")
        # Check if model combo is updated
        model_items = [
            self.dialog.model_combo.get_model()[i][0]
            for i in range(len(self.dialog.model_combo.get_model()))
        ]
        expected_models = [m.capitalize() for m in ENGINE_MODELS["whisper"]]
        self.assertListEqual(model_items, expected_models)
        # Check if VOSK settings are hidden
        self.assertFalse(self.dialog.vosk_settings_box.is_visible())

        # Simulate changing back to Vosk
        self.dialog.engine_combo.set_active_id("Vosk")
        process_gtk_events()
        self.assertEqual(self.dialog.engine_combo.get_active_text(), "Vosk")
        model_items = [
            self.dialog.model_combo.get_model()[i][0]
            for i in range(len(self.dialog.model_combo.get_model()))
        ]
        expected_models = [m.capitalize() for m in ENGINE_MODELS["vosk"]]
        self.assertListEqual(model_items, expected_models)
        self.assertTrue(self.dialog.vosk_settings_box.is_visible())

    def test_get_selected_settings_vosk(self):
        """Test retrieving selected settings when VOSK is chosen."""
        # Set some values
        self.dialog.engine_combo.set_active_id("Vosk")
        self.dialog.model_combo.set_active_id("Medium")
        self.dialog.vad_spin.set_value(4)
        self.dialog.silence_spin.set_value(1.5)
        process_gtk_events()

        settings = self.dialog.get_selected_settings()
        expected = {
            "engine": "vosk",
            "model_size": "medium",
            "vad_sensitivity": 4,
            "silence_timeout": 1.5,
        }
        self.assertDictEqual(settings, expected)

    def test_get_selected_settings_whisper(self):
        """Test retrieving selected settings when Whisper is chosen."""
        # Set some values
        self.dialog.engine_combo.set_active_id("Whisper")
        process_gtk_events()  # Allow model combo to update
        self.dialog.model_combo.set_active_id("Base")
        process_gtk_events()

        settings = self.dialog.get_selected_settings()
        expected = {
            "engine": "whisper",
            "model_size": "base",
            # VOSK specific settings should not be included
        }
        self.assertDictEqual(settings, expected)

    def test_apply_settings_success(self):
        """Test the apply_settings method calls config and engine methods."""
        # Change a setting
        self.dialog.model_combo.set_active_id("Large")
        process_gtk_events()

        expected_settings = {
            "engine": "vosk",
            "model_size": "large",
            "vad_sensitivity": 3,
            "silence_timeout": 2.0,
        }

        result = self.dialog.apply_settings()
        self.assertTrue(result)

        # Verify mocks were called
        mock_config_manager.update_speech_recognition_settings.assert_called_once_with(
            expected_settings
        )
        mock_config_manager.save_settings.assert_called_once()
        mock_speech_engine.reconfigure.assert_called_once_with(**expected_settings)
        # Check if engine was stopped/restarted (assuming it was IDLE initially)
        mock_speech_engine.stop_recognition.assert_not_called()  # Was IDLE

    def test_apply_settings_stops_engine_if_running(self):
        """Test apply_settings stops the engine if it was running."""
        mock_speech_engine.state = (
            RecognitionState.LISTENING
        )  # Set engine state to running

        result = self.dialog.apply_settings()
        self.assertTrue(result)

        # Verify engine was stopped before reconfigure
        mock_speech_engine.stop_recognition.assert_called_once()
        mock_speech_engine.reconfigure.assert_called_once()

    @patch("vocalinux.ui.settings_dialog.Gtk.MessageDialog")
    def test_apply_settings_failure_reconfigure(self, mock_message_dialog):
        """Test apply_settings handles errors during engine reconfiguration."""
        mock_speech_engine.reconfigure.side_effect = Exception("Model load failed")

        result = self.dialog.apply_settings()
        self.assertFalse(result)

        # Verify mocks
        mock_config_manager.update_speech_recognition_settings.assert_called_once()
        mock_config_manager.save_settings.assert_called_once()  # Config saved even if reconfigure fails
        mock_speech_engine.reconfigure.assert_called_once()
        # Verify error dialog was shown
        mock_message_dialog.assert_called_once()
        instance = mock_message_dialog.return_value
        instance.run.assert_called_once()
        instance.destroy.assert_called_once()

    def test_test_button_requires_apply(self):
        """Test that the test button shows a message if settings haven't been applied."""
        # Change a setting without applying
        self.dialog.model_combo.set_active_id("Medium")
        process_gtk_events()

        # Click test button
        self.dialog.test_button.emit("clicked")
        process_gtk_events()

        # Check text view content
        buffer = self.dialog.test_textview.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        self.assertEqual(text, "Please Apply settings before testing.")
        mock_speech_engine.start_recognition.assert_not_called()

    @patch("vocalinux.ui.settings_dialog.threading.Thread")  # Mock the thread
    @patch("vocalinux.ui.settings_dialog.GLib.idle_add")  # Mock idle_add
    def test_test_button_starts_recognition(self, mock_idle_add, mock_thread):
        """Test the test button starts recognition if settings are applied."""
        # Apply settings first (to match current config)
        self.dialog.apply_settings()
        mock_config_manager.reset_mock()  # Reset mocks after apply
        mock_speech_engine.reset_mock()

        # Click test button
        self.dialog.test_button.emit("clicked")
        process_gtk_events()

        # Check UI state
        self.assertFalse(self.dialog.test_button.get_sensitive())
        self.assertEqual(self.dialog.test_button.get_label(), "Testing... Speak Now!")
        buffer = self.dialog.test_textview.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        self.assertEqual(text, "")  # Text view cleared

        # Verify mocks
        mock_speech_engine.register_text_callback.assert_called_once_with(
            self.dialog._test_text_callback
        )
        mock_speech_engine.start_recognition.assert_called_once()
        # Verify thread was started to stop the test
        mock_thread.assert_called_once_with(
            target=self.dialog._stop_test_after_delay, args=(3,)
        )
        mock_thread.return_value.start.assert_called_once()

    # Need more involved tests for the callback and finalization, potentially using GLib timeouts
    # or more intricate mocking of GLib.idle_add behavior.


if __name__ == "__main__":
    unittest.main()
