"""
Tests for common_types module.
"""

import unittest
from unittest.mock import MagicMock

from vocalinux.common_types import (
    RecognitionState,
    SpeechRecognitionManagerProtocol,
    TextInjectorProtocol,
)


class TestRecognitionState(unittest.TestCase):
    """Tests for RecognitionState enum."""

    def test_enum_values_exist(self):
        """Test that all expected enum values exist."""
        self.assertIsNotNone(RecognitionState.IDLE)
        self.assertIsNotNone(RecognitionState.LISTENING)
        self.assertIsNotNone(RecognitionState.PROCESSING)
        self.assertIsNotNone(RecognitionState.ERROR)

    def test_enum_values_are_distinct(self):
        """Test that enum values are distinct."""
        values = [s.value for s in RecognitionState]
        self.assertEqual(len(values), len(set(values)))

    def test_enum_iteration(self):
        """Test iterating over enum values."""
        states = list(RecognitionState)
        self.assertEqual(len(states), 4)


class TestSpeechRecognitionManagerProtocol(unittest.TestCase):
    """Tests for SpeechRecognitionManagerProtocol."""

    def test_protocol_methods(self):
        """Test that protocol defines expected methods."""
        # Create a mock that satisfies the protocol
        mock_manager = MagicMock(spec=SpeechRecognitionManagerProtocol)
        mock_manager.state = RecognitionState.IDLE

        # Verify protocol methods exist
        mock_manager.start_recognition()
        mock_manager.stop_recognition()
        mock_manager.register_state_callback(lambda x: None)
        mock_manager.register_text_callback(lambda x: None)

        # Verify calls
        mock_manager.start_recognition.assert_called_once()
        mock_manager.stop_recognition.assert_called_once()
        mock_manager.register_state_callback.assert_called_once()
        mock_manager.register_text_callback.assert_called_once()


class TestTextInjectorProtocol(unittest.TestCase):
    """Tests for TextInjectorProtocol."""

    def test_protocol_methods(self):
        """Test that protocol defines expected methods."""
        # Create a mock that satisfies the protocol
        mock_injector = MagicMock(spec=TextInjectorProtocol)

        # Verify protocol method exists
        mock_injector.inject_text("test")
        mock_injector.inject_text.return_value = True

        mock_injector.inject_text.assert_called_with("test")


if __name__ == "__main__":
    unittest.main()
