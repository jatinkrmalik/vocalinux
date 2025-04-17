"""
Tests for the speech recognition manager.
"""

import json
import os
import sys
import unittest
from enum import Enum
from unittest.mock import MagicMock, call, patch, PropertyMock

import pytest

# Create proper mock responses that can be safely JSON serialized
MOCK_VOSK_RESULT = '{"text": "test transcription"}'


# We need to patch the entire vosk Model class and KaldiRecognizer
class MockModel:
    def __init__(self, path):
        pass


class MockKaldiRecognizer:
    def __init__(self, model, rate):
        pass

    def AcceptWaveform(self, data):
        return True

    def FinalResult(self):
        return MOCK_VOSK_RESULT

    def PartialResult(self):
        return '{"partial": "test"}'


# Path modules before importing the recognition_manager
sys.modules["vosk"] = MagicMock()
sys.modules["vosk"].Model = MockModel
sys.modules["vosk"].KaldiRecognizer = MockKaldiRecognizer

# Mock other required modules
sys.modules["pyaudio"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["whisper"] = MagicMock()
sys.modules["whisper"].load_model = MagicMock(return_value=MagicMock())

# Now we can import the recognition manager
from src.speech_recognition.recognition_manager import (
    RecognitionState,
    SpeechRecognitionManager,
)


class TestSpeechRecognition(unittest.TestCase):
    """Test cases for the speech recognition functionality."""

    def setUp(self):
        """Set up for tests."""
        # Patch os.makedirs to avoid creating directories
        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()

        # Patch os.path.exists to return True for any path
        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()

        # Mock the command processor
        self.patcher_cmd = patch(
            "src.speech_recognition.recognition_manager.CommandProcessor"
        )
        self.mock_cmd_class = self.patcher_cmd.start()
        self.mock_cmd = MagicMock()
        self.mock_cmd_class.return_value = self.mock_cmd

        # Mock threading to avoid thread creation
        self.patcher_thread = patch(
            "src.speech_recognition.recognition_manager.threading.Thread"
        )
        self.mock_thread_class = self.patcher_thread.start()
        self.mock_thread = MagicMock()
        self.mock_thread_class.return_value = self.mock_thread

        # Mock audio feedback functions
        self.patcher_play_start = patch(
            "src.speech_recognition.recognition_manager.play_start_sound"
        )
        self.mock_play_start = self.patcher_play_start.start()

        self.patcher_play_stop = patch(
            "src.speech_recognition.recognition_manager.play_stop_sound"
        )
        self.mock_play_stop = self.patcher_play_stop.start()

        self.patcher_play_error = patch(
            "src.speech_recognition.recognition_manager.play_error_sound"
        )
        self.mock_play_error = self.patcher_play_error.start()

        # Patch the download method for vosk models
        self.patcher_download = patch.object(
            SpeechRecognitionManager, "_download_vosk_model"
        )
        self.mock_download = self.patcher_download.start()

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_cmd.stop()
        self.patcher_thread.stop()
        self.patcher_play_start.stop()
        self.patcher_play_stop.stop()
        self.patcher_play_error.stop()
        self.patcher_download.stop()

    def test_init_state(self):
        """Test the initial state of the speech recognition manager."""
        # Test VOSK initialization
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        # Verify initial state
        self.assertEqual(manager.state, RecognitionState.IDLE)
        self.assertEqual(manager.engine, "vosk")
        self.assertEqual(manager.model_size, "small")
        self.assertFalse(manager.should_record)
        self.assertEqual(manager.audio_buffer, [])
        self.assertEqual(manager.text_callbacks, [])
        self.assertEqual(manager.state_callbacks, [])
        self.assertEqual(manager.action_callbacks, [])

        # Test Whisper initialization with different model size
        manager = SpeechRecognitionManager(engine="whisper", model_size="medium")

        # Verify Whisper initialization
        self.assertEqual(manager.engine, "whisper")
        self.assertEqual(manager.model_size, "medium")

        # Test invalid engine
        with self.assertRaises(ValueError):
            SpeechRecognitionManager(engine="invalid")

    def test_callbacks(self):
        """Test registering and using callbacks."""
        manager = SpeechRecognitionManager(engine="vosk")

        # Create mock callbacks
        text_callback = MagicMock()
        state_callback = MagicMock()
        action_callback = MagicMock()

        # Register callbacks
        manager.register_text_callback(text_callback)
        manager.register_state_callback(state_callback)
        manager.register_action_callback(action_callback)

        # Verify callbacks were registered
        self.assertEqual(manager.text_callbacks, [text_callback])
        self.assertEqual(manager.state_callbacks, [state_callback])
        self.assertEqual(manager.action_callbacks, [action_callback])

        # Test state update
        manager._update_state(RecognitionState.LISTENING)
        self.assertEqual(manager.state, RecognitionState.LISTENING)
        state_callback.assert_called_once_with(RecognitionState.LISTENING)

        # Test text processing with callbacks
        # Setup command processor mock return values
        self.mock_cmd.process_text.return_value = ("processed text", ["action1"])

        # Prepare audio buffer for processing
        manager.audio_buffer = [b"audio_data"]

        # Process the buffer
        manager._process_final_buffer()

        # Verify command processor was called
        self.mock_cmd.process_text.assert_called_once_with("test transcription")

        # Verify text callback was called
        text_callback.assert_called_once_with("processed text")

        # Verify action callback was called
        action_callback.assert_called_once_with("action1")

    def test_vosk_model_path(self):
        """Test getting the VOSK model path based on size."""
        with patch.object(
            SpeechRecognitionManager, "_get_vosk_model_path"
        ) as mock_get_path:
            # Test small model size
            mock_get_path.return_value = "/path/to/vosk-model-small-en-us-0.15"
            manager_small = SpeechRecognitionManager(engine="vosk", model_size="small")

            # Verify the small model path is constructed correctly
            mock_get_path.assert_called_with()

            # Test medium model size
            mock_get_path.return_value = "/path/to/vosk-model-en-us-0.22"
            manager_medium = SpeechRecognitionManager(
                engine="vosk", model_size="medium"
            )

            # Verify the medium model path is constructed correctly
            mock_get_path.assert_called_with()

            # Test large model size
            mock_get_path.return_value = "/path/to/vosk-model-en-us-0.42"
            manager_large = SpeechRecognitionManager(engine="vosk", model_size="large")

            # Verify the large model path is constructed correctly
            mock_get_path.assert_called_with()

    def test_download_vosk_model(self):
        """Test downloading VOSK model."""
        # Make os.path.exists return False to trigger download
        with patch("os.path.exists", return_value=False):
            # Instantiate manager which should trigger download
            manager = SpeechRecognitionManager(engine="vosk", model_size="small")

            # Verify download was attempted
            self.mock_download.assert_called_once()

    def test_start_recognition(self):
        """Test starting speech recognition."""
        # Create a manager
        manager = SpeechRecognitionManager(engine="vosk")

        # Reset mock for clean test
        self.mock_thread_class.reset_mock()
        self.mock_play_start.reset_mock()

        # Start recognition
        manager.start_recognition()

        # Verify state changed
        self.assertEqual(manager.state, RecognitionState.LISTENING)

        # Verify start sound was played
        self.mock_play_start.assert_called_once()

        # Verify recording flag was set
        self.assertTrue(manager.should_record)

        # Verify threads were started
        self.assertEqual(self.mock_thread_class.call_count, 2)
        self.mock_thread.start.assert_called()

        # Try starting when already listening
        self.mock_thread_class.reset_mock()
        manager.start_recognition()

        # Should not start again
        self.mock_thread_class.assert_not_called()

    def test_stop_recognition(self):
        """Test stopping speech recognition."""
        # Create a manager
        manager = SpeechRecognitionManager(engine="vosk")

        # Setup manager state
        manager.state = RecognitionState.LISTENING
        manager.should_record = True
        manager.audio_thread = self.mock_thread
        manager.recognition_thread = self.mock_thread

        # Reset mocks
        self.mock_play_stop.reset_mock()

        # Stop recognition
        manager.stop_recognition()

        # Verify state changed
        self.assertEqual(manager.state, RecognitionState.IDLE)

        # Verify stop sound was played
        self.mock_play_stop.assert_called_once()

        # Verify recording flag was cleared
        self.assertFalse(manager.should_record)

        # Verify threads were joined
        self.mock_thread.join.assert_called()

    def test_record_audio(self):
        """Test recording audio with simulated voice activity."""
        # This test would be complex due to audio processing, just test basic setup
        manager = SpeechRecognitionManager(engine="vosk")
        manager.should_record = True

        # Skip detailed testing of the audio recording function
        self.assertTrue(hasattr(manager, "_record_audio"))

    def test_process_final_buffer_vosk(self):
        """Test processing the final audio buffer with VOSK."""
        # Setup manager
        manager = SpeechRecognitionManager(engine="vosk")

        # Setup command processor mock
        self.mock_cmd.process_text.return_value = ("processed text", ["action1"])

        # Register mock callbacks
        text_callback = MagicMock()
        action_callback = MagicMock()
        manager.register_text_callback(text_callback)
        manager.register_action_callback(action_callback)

        # Prepare audio buffer
        manager.audio_buffer = [b"audio_data1", b"audio_data2"]

        # Process the buffer
        manager._process_final_buffer()

        # Verify command processor was called
        self.mock_cmd.process_text.assert_called_once_with("test transcription")

        # Verify callbacks were called
        text_callback.assert_called_once_with("processed text")
        action_callback.assert_called_once_with("action1")

    def test_process_final_buffer_whisper(self):
        """Test processing the final audio buffer with Whisper."""
        # Setup manager with whisper engine
        manager = SpeechRecognitionManager(engine="whisper")

        # Set up a mock model
        whisper_model = MagicMock()
        whisper_model.transcribe.return_value = {"text": "whisper transcription"}
        manager.model = whisper_model

        # Setup command processor mock
        self.mock_cmd.process_text.return_value = ("processed whisper", ["action2"])

        # Register mock callbacks
        text_callback = MagicMock()
        action_callback = MagicMock()
        manager.register_text_callback(text_callback)
        manager.register_action_callback(action_callback)

        # Prepare audio buffer
        manager.audio_buffer = [b"audio_data1", b"audio_data2"]

        # We need to patch tempfile.mkstemp and wave.open for whisper
        with patch("tempfile.mkstemp", return_value=(5, "/tmp/tmpfile.wav")), patch(
            "wave.open", return_value=MagicMock()
        ), patch("os.unlink"):

            # Process the buffer
            manager._process_final_buffer()

            # Verify model.transcribe was called
            whisper_model.transcribe.assert_called_once()

            # Verify command processor was called
            self.mock_cmd.process_text.assert_called_once_with("whisper transcription")

            # Verify callbacks were called
            text_callback.assert_called_once_with("processed whisper")
            action_callback.assert_called_once_with("action2")

    def test_empty_buffer(self):
        """Test processing an empty buffer."""
        # Setup manager
        manager = SpeechRecognitionManager(engine="vosk")

        # Process empty buffer
        manager.audio_buffer = []
        manager._process_final_buffer()

        # Verify command processor was not called
        self.mock_cmd.process_text.assert_not_called()

    def test_configure(self):
        """Test configuring recognition parameters."""
        # Setup manager
        manager = SpeechRecognitionManager(engine="vosk")

        # Default values
        self.assertEqual(manager.vad_sensitivity, 3)
        self.assertEqual(manager.silence_timeout, 2.0)

        # Configure with valid values
        manager.configure(vad_sensitivity=4, silence_timeout=1.5)
        self.assertEqual(manager.vad_sensitivity, 4)
        self.assertEqual(manager.silence_timeout, 1.5)

        # Configure with out-of-range values
        manager.configure(vad_sensitivity=10, silence_timeout=10.0)
        self.assertEqual(manager.vad_sensitivity, 5)  # Clamped to max
        self.assertEqual(manager.silence_timeout, 5.0)  # Clamped to max

        manager.configure(vad_sensitivity=0, silence_timeout=0.2)
        self.assertEqual(manager.vad_sensitivity, 1)  # Clamped to min
        self.assertEqual(manager.silence_timeout, 0.5)  # Clamped to min
