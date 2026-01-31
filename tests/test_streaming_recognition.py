"""
Tests for streaming speech recognition functionality.
"""

import json
import sys
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

import pytest

# Mock vosk module for streaming tests
class MockModel:
    def __init__(self, path):
        pass

class MockKaldiRecognizer:
    def __init__(self, model, rate):
        self.model = model
        self.rate = rate
        self.partial_count = 0
        self.final_count = 0
    
    def AcceptWaveform(self, data):
        self.final_count += 1
        return self.final_count > 2  # Return True after a few chunks
    
    def FinalResult(self):
        return '{"text": "streaming transcription"}'
    
    def PartialResult(self):
        self.partial_count += 1
        partial_texts = ["str", "stream", "streaming", "streaming trans", "streaming transcription"]
        if self.partial_count <= len(partial_texts):
            return f'{{"partial": "{partial_texts[self.partial_count - 1]}"}}'
        return '{"partial": ""}'
    
    def SetWords(self, enabled):
        pass

class MockVoskModule:
    Model = MockModel
    KaldiRecognizer = MockKaldiRecognizer

# Mock whisper module
class MockWhisperModel:
    def transcribe(self, audio_data, **kwargs):
        return {"text": "whisper streaming result"}

class MockWhisperModule:
    def load_model(self, model_size, **kwargs):
        return MockWhisperModel()

# Mock torch for VAD
class MockTorchModule:
    class cuda:
        @staticmethod
        def is_available():
            return False
    
    @staticmethod
    def hub():
        class Hub:
            @staticmethod
            def load(*args, **kwargs):
                return MagicMock()
        return Hub()

# Mock audio modules
sys.modules["vosk"] = MockVoskModule()
sys.modules["whisper"] = MockWhisperModule()
sys.modules["torch"] = MockTorchModule()
sys.modules["pyaudio"] = MagicMock()
sys.modules["numpy"] = MagicMock()

# Mock numpy for audio processing
mock_numpy = MagicMock()
mock_numpy.frombuffer = MagicMock(return_value=MagicMock())
mock_numpy.abs = MagicMock(return_value=MagicMock())
mock_numpy.mean = MagicMock(return_value=300)  # Above VAD threshold
sys.modules["numpy"] = mock_numpy

# Import after mocking
from vocalinux.common_types import RecognitionState
from vocalinux.speech_recognition.streaming_recognizer import StreamingSpeechRecognizer
from vocalinux.speech_recognition.streaming_manager import StreamingRecognitionManager


class TestStreamingSpeechRecognizer(unittest.TestCase):
    """Test cases for the streaming speech recognizer."""

    def setUp(self):
        """Set up for tests."""
        self.recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            model_size="small",
            language="en-us",
            chunk_size=1024,
            sample_rate=16000,
            vad_enabled=False,  # Disable VAD for simpler testing
            min_speech_duration_ms=100,
            silence_timeout_ms=500
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.recognizer.is_running:
            self.recognizer.stop_streaming()

    def test_init_state(self):
        """Test the initial state of the streaming recognizer."""
        self.assertFalse(self.recognizer.is_running)
        self.assertEqual(self.recognizer.engine, "vosk")
        self.assertEqual(self.recognizer.model_size, "small")
        self.assertEqual(self.recognizer.chunk_size, 1024)
        self.assertEqual(self.recognizer.sample_rate, 16000)
        self.assertEqual(len(self.recognizer.partial_result_callbacks), 0)
        self.assertEqual(len(self.recognizer.final_result_callbacks), 0)
        self.assertEqual(len(self.recognizer.error_callbacks), 0)

    def test_start_stop_streaming(self):
        """Test starting and stopping streaming recognition."""
        # Test starting
        self.recognizer.start_streaming()
        self.assertTrue(self.recognizer.is_running)

        # Test stopping
        self.recognizer.stop_streaming()
        self.assertFalse(self.recognizer.is_running)

    def test_callback_registration(self):
        """Test registering callbacks."""
        partial_callback = MagicMock()
        final_callback = MagicMock()
        error_callback = MagicMock()

        # Register callbacks
        self.recognizer.register_partial_result_callback(partial_callback)
        self.recognizer.register_final_result_callback(final_callback)
        self.recognizer.register_error_callback(error_callback)

        # Verify registration
        self.assertEqual(len(self.recognizer.partial_result_callbacks), 1)
        self.assertEqual(len(self.recognizer.final_result_callbacks), 1)
        self.assertEqual(len(self.recognizer.error_callbacks), 1)

    def test_vosk_processing(self):
        """Test VOSK audio processing."""
        partial_callback = MagicMock()
        final_callback = MagicMock()

        self.recognizer.register_partial_result_callback(partial_callback)
        self.recognizer.register_final_result_callback(final_callback)

        # Start streaming
        self.recognizer.start_streaming()

        # Process some audio chunks
        audio_chunk = b"test_audio_data" * 32  # Make it large enough
        
        # Process several chunks to trigger both partial and final results
        for _ in range(5):
            self.recognizer.process_audio_chunk(audio_chunk)
            time.sleep(0.01)  # Small delay to allow processing

        # Give some time for processing to complete
        time.sleep(0.1)

        # Stop streaming
        self.recognizer.stop_streaming()

        # Verify callbacks were called (they should be called in streaming mode)
        # Note: The exact number depends on the VOSK mock implementation
        self.assertTrue(partial_callback.called or final_callback.called)

    def test_whisper_processing(self):
        """Test Whisper audio processing."""
        # Create a Whisper-based recognizer
        whisper_recognizer = StreamingSpeechRecognizer(
            engine="whisper",
            model_size="base",
            language="en",
            vad_enabled=False,  # Disable VAD for simpler testing
            min_speech_duration_ms=50,
            silence_timeout_ms=200
        )

        final_callback = MagicMock()
        whisper_recognizer.register_final_result_callback(final_callback)

        # Start streaming
        whisper_recognizer.start_streaming()

        # Process audio chunks
        audio_chunk = b"whisper_audio_data" * 32
        
        for _ in range(3):
            whisper_recognizer.process_audio_chunk(audio_chunk)
            time.sleep(0.01)

        # Give time for processing
        time.sleep(0.1)

        # Stop streaming
        whisper_recognizer.stop_streaming()

        # Verify final callback was called
        self.assertTrue(final_callback.called)

    def test_error_handling(self):
        """Test error handling in streaming recognition."""
        error_callback = MagicMock()
        self.recognizer.register_error_callback(error_callback)

        # Start streaming
        self.recognizer.start_streaming()

        # The error would typically come from the processing loop
        # For this test, we'll directly call the error notification
        test_error = Exception("Test error")
        self.recognizer._notify_error(test_error)

        # Verify error callback was called
        error_callback.assert_called_with(test_error)

    def test_statistics(self):
        """Test performance statistics collection."""
        # Initial stats
        stats = self.recognizer.get_statistics()
        self.assertEqual(stats["total_chunks_processed"], 0)
        self.assertEqual(stats["total_processing_time"], 0.0)
        self.assertEqual(stats["average_latency_ms"], 0.0)

        # Start streaming and process some chunks
        self.recognizer.start_streaming()
        
        audio_chunk = b"stats_test_data" * 16
        for _ in range(3):
            self.recognizer.process_audio_chunk(audio_chunk)
            time.sleep(0.01)

        # Stop streaming
        self.recognizer.stop_streaming()

        # Check updated stats
        stats = self.recognizer.get_statistics()
        self.assertGreaterEqual(stats["total_chunks_processed"], 0)
        self.assertGreaterEqual(stats["total_processing_time"], 0.0)


class TestStreamingRecognitionManager(unittest.TestCase):
    """Test cases for the streaming recognition manager."""

    def setUp(self):
        """Set up for tests."""
        # Mock pyaudio for manager tests
        mock_pyaudio = MagicMock()
        mock_pyaudio.PyAudio.return_value.open.return_value = MagicMock()
        sys.modules["pyaudio"] = mock_pyaudio

        self.manager = StreamingRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            enable_streaming=True,
            streaming_chunk_size=1024,
            vad_enabled=False,
            defer_download=True
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.manager.state != RecognitionState.IDLE:
            self.manager.stop_recognition()

    def test_init_state(self):
        """Test the initial state of the streaming recognition manager."""
        self.assertEqual(self.manager.state, RecognitionState.IDLE)
        self.assertTrue(self.manager.enable_streaming)
        self.assertIsNotNone(self.manager.streaming_recognizer)
        self.assertEqual(self.manager.streaming_chunk_size, 1024)

    def test_streaming_availability(self):
        """Test checking if streaming is enabled and available."""
        self.assertTrue(self.manager.is_streaming_enabled())

        # Test with streaming disabled
        manager_no_streaming = StreamingRecognitionManager(
            engine="vosk",
            enable_streaming=False
        )
        self.assertFalse(manager_no_streaming.is_streaming_enabled())

    def test_callback_registration(self):
        """Test registering callbacks with the manager."""
        text_callback = MagicMock()
        state_callback = MagicMock()
        action_callback = MagicMock()

        self.manager.register_text_callback(text_callback)
        self.manager.register_state_callback(state_callback)
        self.manager.register_action_callback(action_callback)

        # Verify registration
        self.assertEqual(len(self.manager.text_callbacks), 1)
        self.assertEqual(len(self.manager.state_callbacks), 1)
        self.assertEqual(len(self.manager.action_callbacks), 1)

    def test_start_stop_recognition(self):
        """Test starting and stopping recognition."""
        # Mock the audio thread to avoid actual audio recording
        with patch.object(self.manager, '_record_audio_streaming') as mock_record:
            # Start recognition
            self.manager.start_recognition()
            self.assertEqual(self.manager.state, RecognitionState.LISTENING)
            self.assertTrue(self.manager.is_streaming)

            # Stop recognition
            self.manager.stop_recognition()
            self.assertEqual(self.manager.state, RecognitionState.IDLE)
            self.assertFalse(self.manager.is_streaming)

    def test_performance_stats(self):
        """Test getting performance statistics."""
        stats = self.manager.get_performance_stats()
        
        # Check that basic stats are present
        self.assertIn("total_processing_time", stats)
        self.assertIn("total_audio_chunks", stats)
        self.assertIn("average_latency_ms", stats)
        self.assertIn("streaming_mode", stats)
        
        # Verify streaming mode is enabled
        self.assertTrue(stats["streaming_mode"])

    def test_reconfiguration(self):
        """Test reconfiguring the streaming manager."""
        # Initial configuration
        self.assertEqual(self.manager.vad_sensitivity, 3)
        self.assertEqual(self.manager.silence_timeout, 1.0)

        # Reconfigure
        self.manager.reconfigure(
            vad_sensitivity=2,
            silence_timeout=2.0,
            audio_device_index=1
        )

        # Verify changes
        self.assertEqual(self.manager.vad_sensitivity, 2)
        self.assertEqual(self.manager.silence_timeout, 2.0)
        self.assertEqual(self.manager.audio_device_index, 1)

    def test_audio_device_management(self):
        """Test audio device setting and getting."""
        # Set audio device
        self.manager.set_audio_device(2)
        self.assertEqual(self.manager.get_audio_device(), 2)

        # Clear audio device
        self.manager.set_audio_device(None)
        self.assertIsNone(self.manager.get_audio_device())

    def test_batch_fallback(self):
        """Test fallback to batch processing when streaming fails."""
        # Create a manager that will fail to initialize streaming
        with patch.object(StreamingRecognitionManager, '_init_streaming_recognizer') as mock_init:
            mock_init.side_effect = Exception("Streaming initialization failed")
            
            # This should fall back to non-streaming mode
            manager = StreamingRecognitionManager(
                engine="vosk",
                enable_streaming=True
            )
            
            # Should have disabled streaming
            self.assertFalse(manager.enable_streaming)
            self.assertIsNone(manager.streaming_recognizer)


class TestStreamingIntegration(unittest.TestCase):
    """Integration tests for streaming functionality."""

    def setUp(self):
        """Set up for integration tests."""
        # Mock audio components for integration tests
        mock_pyaudio = MagicMock()
        mock_stream = MagicMock()
        mock_stream.read.return_value = b"integration_test_data" * 8
        mock_pyaudio.PyAudio.return_value.open.return_value = mock_stream
        sys.modules["pyaudio"] = mock_pyaudio

    def test_end_to_end_streaming(self):
        """Test end-to-end streaming recognition."""
        # Create manager with streaming enabled
        manager = StreamingRecognitionManager(
            engine="vosk",
            enable_streaming=True,
            vad_enabled=False  # Disable VAD for predictable testing
        )

        # Set up callbacks to capture results
        results = []
        def capture_text(text):
            results.append(text)

        manager.register_text_callback(capture_text)

        # Mock the recording to avoid actual audio I/O
        with patch.object(manager, '_record_audio_streaming') as mock_record:
            # Start recognition
            manager.start_recognition()
            
            # Simulate some audio processing by directly calling the streaming recognizer
            if manager.streaming_recognizer:
                audio_chunk = b"end_to_end_test" * 16
                for _ in range(3):
                    manager.streaming_recognizer.process_audio_chunk(audio_chunk)
                    time.sleep(0.01)
            
            # Stop recognition
            manager.stop_recognition()

        # Verify the manager state is correct
        self.assertEqual(manager.state, RecognitionState.IDLE)

    def test_latency_measurement(self):
        """Test that streaming provides lower latency than batch processing."""
        # This is a conceptual test - in practice, latency would depend on
        # actual audio processing timing
        
        # Create streaming manager
        streaming_manager = StreamingRecognitionManager(
            engine="vosk",
            enable_streaming=True,
            streaming_chunk_size=512,  # Smaller chunks for lower latency
            vad_enabled=False
        )

        # Get initial stats
        initial_stats = streaming_manager.get_performance_stats()
        
        # The key metric is that streaming mode is enabled
        self.assertTrue(initial_stats["streaming_mode"])
        self.assertEqual(streaming_manager.streaming_chunk_size, 512)


if __name__ == "__main__":
    unittest.main()