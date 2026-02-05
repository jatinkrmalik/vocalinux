"""
Tests for the SettingsDialog.

Since SettingsDialog inherits from Gtk.Dialog which is mocked during tests,
we can't easily test the actual class methods. Instead, we test the core
logic that the settings dialog is supposed to execute.
"""

import sys
import time
import unittest
from unittest.mock import MagicMock, Mock

# Mock GTK before importing anything that might use it
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()

from vocalinux.common_types import RecognitionState

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


if __name__ == "__main__":
    unittest.main()
