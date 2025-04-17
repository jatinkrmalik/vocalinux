"""
Tests for the SpeechRecognitionManager component.
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.speech_recognition.recognition_manager import (
    RecognitionState,
    SpeechRecognitionManager,
)


class TestSpeechRecognition(unittest.TestCase):
    """Test cases for the speech recognition manager."""

    @patch("src.speech_recognition.recognition_manager.os.path.exists")
    @patch("src.speech_recognition.recognition_manager.os.makedirs")
    @patch(
        "src.speech_recognition.recognition_manager.SpeechRecognitionManager._initialize_model"
    )
    def test_init_state(self, mock_init_model, mock_makedirs, mock_exists):
        """Test the initial state of the speech recognition manager."""
        # Mock the file existence check
        mock_exists.return_value = True

        manager = SpeechRecognitionManager(engine="vosk", model_size="small")
        assert manager.state == RecognitionState.IDLE
        assert manager.engine == "vosk"
        assert manager.model_size == "small"

    @patch("src.speech_recognition.recognition_manager.os.path.exists")
    @patch("src.speech_recognition.recognition_manager.os.makedirs")
    @patch(
        "src.speech_recognition.recognition_manager.SpeechRecognitionManager._initialize_model"
    )
    def test_callbacks(self, mock_init_model, mock_makedirs, mock_exists):
        """Test callback registration and invocation."""
        # Mock the file existence check
        mock_exists.return_value = True

        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        # Mock callbacks
        text_callback = MagicMock()
        state_callback = MagicMock()

        # Register callbacks
        manager.register_text_callback(text_callback)
        manager.register_state_callback(state_callback)

        # Verify callbacks were registered
        assert text_callback in manager.text_callbacks
        assert state_callback in manager.state_callbacks

        # Test state update
        manager._update_state(RecognitionState.LISTENING)
        state_callback.assert_called_once_with(RecognitionState.LISTENING)
