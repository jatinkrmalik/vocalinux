"""
Tests for the speech recognition manager.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock modules before importing any modules that might use them
sys.modules['vosk'] = MagicMock()
sys.modules['whisper'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['pyaudio'] = MagicMock()
sys.modules['wave'] = MagicMock()
sys.modules['tempfile'] = MagicMock()
sys.modules['tqdm'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['zipfile'] = MagicMock()

# Need to create a mock for audio_feedback module before importing the recognition_manager
mock_audio_feedback = MagicMock()
mock_audio_feedback.play_start_sound = MagicMock()
mock_audio_feedback.play_stop_sound = MagicMock() 
mock_audio_feedback.play_error_sound = MagicMock()
sys.modules['src.ui.audio_feedback'] = mock_audio_feedback

# Now we can import our module
from src.speech_recognition.recognition_manager import (
    RecognitionState,
    SpeechRecognitionManager,
    MODELS_DIR,
)
from src.speech_recognition.command_processor import CommandProcessor


class TestSpeechRecognition(unittest.TestCase):
    """Test cases for the speech recognition functionality."""

    def setUp(self):
        """Set up for tests."""
        # Create patches for our mocks
        self.mockKaldi = patch.object(sys.modules['vosk'], 'KaldiRecognizer')
        self.mockModel = patch.object(sys.modules['vosk'], 'Model')
        self.mockMakeDirs = patch('os.makedirs')
        self.mockThread = patch('threading.Thread')
        self.mockPath = patch.object(SpeechRecognitionManager, '_get_vosk_model_path')
        self.mockDownload = patch.object(SpeechRecognitionManager, '_download_vosk_model')
        self.mockCmdProcessor = patch.object(CommandProcessor, 'process_text')
        
        # Start all patches
        self.kaldiMock = self.mockKaldi.start()
        self.modelMock = self.mockModel.start()
        self.makeDirsMock = self.mockMakeDirs.start()
        self.threadMock = self.mockThread.start()
        self.pathMock = self.mockPath.start()
        self.downloadMock = self.mockDownload.start()
        self.cmdProcessorMock = self.mockCmdProcessor.start()
        
        # Set up return values
        self.recognizerMock = MagicMock()
        self.kaldiMock.return_value = self.recognizerMock
        self.pathMock.return_value = "/mock/path/vosk-model"
        self.threadInstance = MagicMock()
        self.threadMock.return_value = self.threadInstance
        self.cmdProcessorMock.return_value = ("processed text", ["action1"])
        
        # Critical: Set FinalResult to return valid JSON string
        self.recognizerMock.FinalResult.return_value = '{"text": "test transcription"}'
        
        # Reset audio feedback mocks before each test
        mock_audio_feedback.play_start_sound.reset_mock()
        mock_audio_feedback.play_stop_sound.reset_mock()
        mock_audio_feedback.play_error_sound.reset_mock()
    
    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        self.mockKaldi.stop()
        self.mockModel.stop()
        self.mockMakeDirs.stop()
        self.mockThread.stop()
        self.mockPath.stop()
        self.mockDownload.stop()
        self.mockCmdProcessor.stop()
    
    def test_init(self):
        """Test initialization with different engines."""
        # Test VOSK initialization
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")
        
        # Verify initial state
        self.assertEqual(manager.state, RecognitionState.IDLE)
        self.assertEqual(manager.engine, "vosk")
        self.assertEqual(manager.model_size, "small")
        self.assertFalse(manager.should_record)
        self.assertEqual(manager.audio_buffer, [])
        
        # Verify VOSK model was initialized
        self.modelMock.assert_called_once()
        self.kaldiMock.assert_called_once()
        
        # Test invalid engine
        with self.assertRaises(ValueError):
            SpeechRecognitionManager(engine="invalid")
    
    def test_register_callbacks(self):
        """Test callback registration."""
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
    
    def test_process_buffer(self):
        """Test processing audio buffer."""
        # Setup for test
        manager = SpeechRecognitionManager(engine="vosk")
        
        # Register callbacks
        text_callback = MagicMock()
        action_callback = MagicMock()
        manager.register_text_callback(text_callback)
        manager.register_action_callback(action_callback)
        
        # Setup audio buffer
        manager.audio_buffer = [b'data1', b'data2']
        
        # Process buffer
        manager._process_final_buffer()
        
        # Verify Vosk methods were called
        self.recognizerMock.AcceptWaveform.assert_any_call(b'data1')
        self.recognizerMock.AcceptWaveform.assert_any_call(b'data2')
        self.recognizerMock.FinalResult.assert_called_once()
        
        # Verify command processor was called
        self.cmdProcessorMock.assert_called_once_with("test transcription")
        
        # Verify callbacks were called
        text_callback.assert_called_once_with("processed text")
        action_callback.assert_called_once_with("action1")
    
    def test_start_stop_recognition(self):
        """Test starting and stopping recognition."""
        manager = SpeechRecognitionManager(engine="vosk")
        
        # Start recognition
        manager.start_recognition()
        
        # Verify state and calls
        self.assertEqual(manager.state, RecognitionState.LISTENING)
        self.assertTrue(manager.should_record)
        mock_audio_feedback.play_start_sound.assert_called_once()
        self.assertEqual(self.threadMock.call_count, 2)
        self.threadInstance.start.assert_called()
        
        # Reset mocks
        self.threadMock.reset_mock()
        self.threadInstance.reset_mock()
        
        # Already listening, should not start again
        manager.start_recognition()
        self.threadMock.assert_not_called()
        
        # Stop recognition
        manager.audio_thread = self.threadInstance
        manager.recognition_thread = self.threadInstance
        manager.stop_recognition()
        
        # Verify stopped state
        self.assertEqual(manager.state, RecognitionState.IDLE)
        self.assertFalse(manager.should_record)
        mock_audio_feedback.play_stop_sound.assert_called_once()
        self.threadInstance.join.assert_called()
    
    def test_whisper_engine(self):
        """Test initialization and usage with Whisper engine."""
        # Setup Whisper mock
        whisper_mock = sys.modules['whisper']
        whisper_mock.load_model = MagicMock()
        model_mock = MagicMock()
        whisper_mock.load_model.return_value = model_mock
        
        # Create manager with Whisper engine
        manager = SpeechRecognitionManager(engine="whisper", model_size="medium")
        
        # Verify Whisper was initialized
        self.assertEqual(manager.engine, "whisper")
        self.assertEqual(manager.model_size, "medium")
        whisper_mock.load_model.assert_called_once_with("medium")
        
        # Test processing with Whisper engine
        # Setup for testing whisper processing
        temp_mock = sys.modules['tempfile']
        wave_mock = sys.modules['wave']
        
        # Create tempfile mock
        temp_file_mock = MagicMock()
        temp_file_mock.name = "/tmp/test.wav"
        temp_context_mock = MagicMock()
        temp_context_mock.__enter__ = MagicMock(return_value=temp_file_mock)
        temp_context_mock.__exit__ = MagicMock(return_value=None)
        temp_mock.NamedTemporaryFile = MagicMock(return_value=temp_context_mock)
        
        # Create wave file mock
        wave_file_mock = MagicMock()
        wave_context_mock = MagicMock()
        wave_context_mock.__enter__ = MagicMock(return_value=wave_file_mock)
        wave_context_mock.__exit__ = MagicMock(return_value=None)
        wave_mock.open = MagicMock(return_value=wave_context_mock)
        
        # Setup model transcribe return value
        model_mock.transcribe = MagicMock(return_value={"text": "whisper test"})
        
        # Prepare manager for test
        manager.model = model_mock
        manager.audio_buffer = [b'whisper_data']
        
        # Register callbacks
        text_callback = MagicMock()
        manager.register_text_callback(text_callback)
        
        # Mock command processor
        self.cmdProcessorMock.return_value = ("processed whisper", [])
        
        # Process with unlink mocked
        with patch('os.unlink') as unlink_mock:
            manager._process_final_buffer()
            
            # Verify wave file operations
            wave_mock.open.assert_called_once_with("/tmp/test.wav", "wb")
            wave_file_mock.setnchannels.assert_called_once_with(1)
            wave_file_mock.setsampwidth.assert_called_once_with(2)
            wave_file_mock.setframerate.assert_called_once_with(16000)
            
            # Verify transcription
            model_mock.transcribe.assert_called_once_with("/tmp/test.wav")
            
            # Verify command processor
            self.cmdProcessorMock.assert_called_once_with("whisper test")
            
            # Verify callback
            text_callback.assert_called_once_with("processed whisper")
            
            # Verify cleanup
            unlink_mock.assert_called_once_with("/tmp/test.wav")
    
    def test_vosk_model_path(self):
        """Test model path generation."""
        # Disable our path mock to test actual implementation
        self.mockPath.stop()
        
        # Test with different model sizes
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")
        path = manager._get_vosk_model_path()
        self.assertIn("small", path)
        
        manager = SpeechRecognitionManager(engine="vosk", model_size="medium")
        path = manager._get_vosk_model_path()
        self.assertIn("0.22", path)
        
        manager = SpeechRecognitionManager(engine="vosk", model_size="large")
        path = manager._get_vosk_model_path()
        self.assertIn("0.42", path)
        
        # Restart our mock
        self.pathMock = self.mockPath.start()
        self.pathMock.return_value = "/mock/path/vosk-model"
    
    def test_configure(self):
        """Test configuration method."""
        manager = SpeechRecognitionManager(engine="vosk")
        
        # Default values
        self.assertEqual(manager.vad_sensitivity, 3)
        self.assertEqual(manager.silence_timeout, 2.0)
        
        # Configure with valid values
        manager.configure(vad_sensitivity=4, silence_timeout=1.5)
        self.assertEqual(manager.vad_sensitivity, 4)
        self.assertEqual(manager.silence_timeout, 1.5)
        
        # Test bounds checking
        manager.configure(vad_sensitivity=10, silence_timeout=10.0)
        self.assertEqual(manager.vad_sensitivity, 5)  # Max is 5
        self.assertEqual(manager.silence_timeout, 5.0)  # Max is 5.0
        
        manager.configure(vad_sensitivity=0, silence_timeout=0.0)
        self.assertEqual(manager.vad_sensitivity, 1)  # Min is 1
        self.assertEqual(manager.silence_timeout, 0.5)  # Min is 0.5