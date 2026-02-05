"""
Tests for speech_recognition module __init__.py
"""

import sys
import unittest
from unittest.mock import MagicMock, patch


class TestSpeechRecognitionModule(unittest.TestCase):
    """Tests for the speech_recognition module interface."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the heavy dependencies
        sys.modules["vosk"] = MagicMock()
        sys.modules["pyaudio"] = MagicMock()
        sys.modules["numpy"] = MagicMock()

    def test_get_audio_input_devices(self):
        """Test get_audio_input_devices delegates to recognition_manager."""
        from vocalinux.speech_recognition import recognition_manager

        with patch.object(recognition_manager, "get_audio_input_devices") as mock_get:
            mock_get.return_value = [
                {"index": 0, "name": "Default"},
                {"index": 1, "name": "USB Microphone"},
            ]

            from vocalinux.speech_recognition import get_audio_input_devices

            result = get_audio_input_devices()

            mock_get.assert_called_once()
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Default")

    def test_test_audio_input(self):
        """Test test_audio_input delegates to recognition_manager."""
        from vocalinux.speech_recognition import recognition_manager

        with patch.object(recognition_manager, "test_audio_input") as mock_test:
            mock_test.return_value = {"success": True, "level": 0.5}

            from vocalinux.speech_recognition import test_audio_input

            result = test_audio_input(device_index=1, duration=2.0)

            mock_test.assert_called_once_with(1, 2.0)
            self.assertTrue(result["success"])

    def test_test_audio_input_default_args(self):
        """Test test_audio_input with default arguments."""
        from vocalinux.speech_recognition import recognition_manager

        with patch.object(recognition_manager, "test_audio_input") as mock_test:
            mock_test.return_value = {"success": True}

            from vocalinux.speech_recognition import test_audio_input

            result = test_audio_input()

            mock_test.assert_called_once_with(None, 1.0)


if __name__ == "__main__":
    unittest.main()
