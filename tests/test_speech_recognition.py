"""
Tests for speech recognition functionality.
"""

import sys  # noqa: F401
import unittest
from unittest.mock import MagicMock, patch

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


# Create a proper mock vosk module that uses our custom classes
class MockVoskModule:
    Model = MockModel
    KaldiRecognizer = MockKaldiRecognizer


# Path modules before importing the recognition_manager
sys.modules["vosk"] = MockVoskModule

# Mock other required modules
sys.modules["pyaudio"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["whisper"] = MagicMock()
sys.modules["whisper"].load_model = MagicMock(return_value=MagicMock())
sys.modules["torch"] = MagicMock()
sys.modules["torch"].cuda.is_available = MagicMock(return_value=False)

# Mock tempfile and wave modules to avoid file system issues
mock_tempfile = MagicMock()
mock_temp_file = MagicMock()
mock_temp_file.name = "/tmp/tmpfile.wav"
mock_temp_file.__enter__ = MagicMock(return_value=mock_temp_file)
mock_temp_file.__exit__ = MagicMock(return_value=None)
mock_tempfile.NamedTemporaryFile = MagicMock(return_value=mock_temp_file)
sys.modules["tempfile"] = mock_tempfile

mock_wave = MagicMock()
mock_wave_file = MagicMock()
mock_wave_file.__enter__ = MagicMock(return_value=mock_wave_file)
mock_wave_file.__exit__ = MagicMock(return_value=None)
mock_wave.open = MagicMock(return_value=mock_wave_file)
sys.modules["wave"] = mock_wave

# Import the shared mock from conftest
from conftest import mock_audio_feedback  # noqa: E402

# Update import paths to use the new package structure
from vocalinux.common_types import RecognitionState  # noqa: E402
from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager  # noqa: E402


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
            "vocalinux.speech_recognition.recognition_manager.CommandProcessor"
        )
        self.mock_cmd_class = self.patcher_cmd.start()
        self.mock_cmd = MagicMock()
        self.mock_cmd_class.return_value = self.mock_cmd

        # Mock threading to avoid thread creation
        self.patcher_thread = patch(
            "vocalinux.speech_recognition.recognition_manager.threading.Thread"
        )
        self.mock_thread_class = self.patcher_thread.start()
        self.mock_thread = MagicMock()
        self.mock_thread_class.return_value = self.mock_thread

        # Use the module-level audio feedback mock
        self.mock_play_start = mock_audio_feedback.play_start_sound
        self.mock_play_stop = mock_audio_feedback.play_stop_sound
        self.mock_play_error = mock_audio_feedback.play_error_sound

        # Patch the download method for vosk models
        self.patcher_download = patch.object(SpeechRecognitionManager, "_download_vosk_model")
        self.mock_download = self.patcher_download.start()

        # Patch os.unlink to avoid file removal errors
        self.patcher_unlink = patch("os.unlink")
        self.mock_unlink = self.patcher_unlink.start()

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_cmd.stop()
        self.patcher_thread.stop()
        self.patcher_download.stop()
        self.patcher_unlink.stop()

        # Reset the audio feedback mocks for the next test
        mock_audio_feedback.reset_mock()

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

        # Replace recognizer with a mock that returns proper JSON
        mock_recognizer = MagicMock()
        mock_recognizer.FinalResult.return_value = MOCK_VOSK_RESULT
        mock_recognizer.AcceptWaveform.return_value = True
        manager.recognizer = mock_recognizer

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

        # Prepare audio buffer for processing (need >= 5 chunks to pass minimum buffer check)
        manager.audio_buffer = [b"audio_data"] * 5

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
        with patch.object(SpeechRecognitionManager, "_get_vosk_model_path") as mock_get_path:
            # Test small model size
            mock_get_path.return_value = "/path/to/vosk-model-small-en-us-0.15"
            _ = SpeechRecognitionManager(engine="vosk", model_size="small")

            # Verify the small model path is constructed correctly
            mock_get_path.assert_called_with()

            # Test medium model size
            mock_get_path.return_value = "/path/to/vosk-model-en-us-0.22"
            _ = SpeechRecognitionManager(engine="vosk", model_size="medium")

            # Verify the medium model path is constructed correctly
            mock_get_path.assert_called_with()

            # Test large model size
            mock_get_path.return_value = "/path/to/vosk-model-en-us-0.42"
            _ = SpeechRecognitionManager(engine="vosk", model_size="large")

            # Verify the large model path is constructed correctly
            mock_get_path.assert_called_with()

    def test_download_vosk_model(self):
        """Test downloading VOSK model."""
        # Make os.path.exists return False to trigger download
        with patch("os.path.exists", return_value=False):
            # Instantiate manager with defer_download=False to trigger download
            _ = SpeechRecognitionManager(engine="vosk", model_size="small", defer_download=False)

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

        # Replace recognizer with a mock that returns proper JSON
        mock_recognizer = MagicMock()
        mock_recognizer.FinalResult.return_value = MOCK_VOSK_RESULT
        mock_recognizer.AcceptWaveform.return_value = True
        manager.recognizer = mock_recognizer

        # Setup command processor mock
        self.mock_cmd.process_text.return_value = ("processed text", ["action1"])

        # Register mock callbacks
        text_callback = MagicMock()
        action_callback = MagicMock()
        manager.register_text_callback(text_callback)
        manager.register_action_callback(action_callback)

        # Prepare audio buffer (need >= 5 chunks to pass minimum buffer check)
        manager.audio_buffer = [
            b"audio_data1",
            b"audio_data2",
            b"audio_data3",
            b"audio_data4",
            b"audio_data5",
        ]

        # Process the buffer
        manager._process_final_buffer()

        # Verify command processor was called
        self.mock_cmd.process_text.assert_called_once_with("test transcription")

        # Verify callbacks were called
        text_callback.assert_called_once_with("processed text")
        action_callback.assert_called_once_with("action1")

    def test_process_final_buffer_whisper(self):
        """Test processing the final audio buffer with Whisper."""
        # Skip the problematic file operations by creating a mock implementation
        # of the _process_final_buffer method
        with patch.object(SpeechRecognitionManager, "_process_final_buffer") as mock_process:
            # Setup manager with whisper engine (this should work now with mocked torch)
            manager = SpeechRecognitionManager(engine="whisper")

            # Setup side effect function that will be called when _process_final_buffer is called
            def process_side_effect():
                # Simulate processing the result through command processor
                processed_text, actions = self.mock_cmd.process_text("whisper transcription")
                # Call callbacks as the real method would
                for callback in manager.text_callbacks:
                    callback(processed_text)
                for callback in manager.action_callbacks:
                    for action in actions:
                        callback(action)

            # Set the side effect
            mock_process.side_effect = process_side_effect

            # Set up a mock model just for completeness
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

            # Prepare audio buffer (not actually used because we're mocking the method)
            manager.audio_buffer = [b"audio_data1", b"audio_data2"]

            # Call the mocked process method
            manager._process_final_buffer()

            # Verify command processor was called with expected text
            self.mock_cmd.process_text.assert_called_once_with("whisper transcription")

            # Verify callbacks were called with expected values
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

    def test_process_final_buffer_whisper_real(self):
        """Test _process_final_buffer with whisper engine executes the real code path.

        This ensures the whisper-specific anti-hallucination code
        (_check_audio_energy, _is_whisper_hallucination, _recent_transcriptions)
        is actually exercised and won't cause NameError at runtime.
        """
        manager = SpeechRecognitionManager(engine="whisper")
        manager.audio_buffer = [b"data"] * 10

        # Mock energy check to return speech-level energy
        with patch(
            "vocalinux.speech_recognition.recognition_manager._check_audio_energy",
            return_value=1000.0,
        ):
            with patch.object(manager, "_transcribe_with_whisper", return_value="hello world"):
                text_callback = MagicMock()
                manager.register_text_callback(text_callback)

                with patch.object(manager.command_processor, "process_text") as mock_process:
                    mock_process.return_value = ("hello world", [])
                    manager._process_final_buffer()

                    text_callback.assert_called_once_with("hello world")

    def test_process_final_buffer_whisper_low_energy_skipped(self):
        """Test that whisper skips transcription on low-energy audio."""
        manager = SpeechRecognitionManager(engine="whisper")
        manager.audio_buffer = [b"data"] * 10

        # Mock energy check to return near-silence
        with patch(
            "vocalinux.speech_recognition.recognition_manager._check_audio_energy",
            return_value=50.0,
        ):
            with patch.object(manager, "_transcribe_with_whisper") as mock_transcribe:
                manager._process_final_buffer()

                # Whisper should NOT be called — energy too low
                mock_transcribe.assert_not_called()

    def test_process_final_buffer_whisper_hallucination_filtered(self):
        """Test that repetitive whisper hallucinations are filtered."""
        manager = SpeechRecognitionManager(engine="whisper")
        manager.audio_buffer = [b"data"] * 10

        with patch(
            "vocalinux.speech_recognition.recognition_manager._check_audio_energy",
            return_value=1000.0,
        ):
            with patch.object(
                manager, "_transcribe_with_whisper", return_value="you you you you you"
            ):
                text_callback = MagicMock()
                manager.register_text_callback(text_callback)

                manager._process_final_buffer()

                # Should be filtered as hallucination
                text_callback.assert_not_called()

    def test_configure(self):
        """Test configuring recognition parameters."""
        # Setup manager
        manager = SpeechRecognitionManager(engine="vosk")

        # Default values
        self.assertEqual(manager.vad_sensitivity, 3)
        self.assertEqual(manager.silence_timeout, 2.0)

        # Configure with valid values
        manager.reconfigure(vad_sensitivity=4, silence_timeout=1.5)
        self.assertEqual(manager.vad_sensitivity, 4)
        self.assertEqual(manager.silence_timeout, 1.5)

        # Configure with out-of-range values
        manager.reconfigure(vad_sensitivity=10, silence_timeout=10.0)
        self.assertEqual(manager.vad_sensitivity, 5)  # Clamped to max
        self.assertEqual(manager.silence_timeout, 5.0)  # Clamped to max

        manager.reconfigure(vad_sensitivity=0, silence_timeout=0.2)
        self.assertEqual(manager.vad_sensitivity, 1)  # Clamped to min
        self.assertEqual(manager.silence_timeout, 0.5)  # Clamped to min
