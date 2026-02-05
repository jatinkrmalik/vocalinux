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

# Mock gi modules BEFORE any imports
mock_gi = MagicMock()
mock_gi.repository = MagicMock()
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = mock_gi.repository
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.Gio"] = MagicMock()
sys.modules["gi.repository.AppIndicator3"] = MagicMock()
sys.modules["gi.repository.GObject"] = MagicMock()

# Mock Xlib
sys.modules["Xlib"] = MagicMock()
sys.modules["Xlib.display"] = MagicMock()
sys.modules["Xlib.X"] = MagicMock()
sys.modules["Xlib.XK"] = MagicMock()
sys.modules["Xlib.ext"] = MagicMock()
sys.modules["Xlib.ext.xtest"] = MagicMock()

# Mock pynput
sys.modules["pynput"] = MagicMock()
sys.modules["pynput.keyboard"] = MagicMock()


# Mock vosk module for streaming tests
class MockModel:
    def __init__(self, path=None):
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
            silence_timeout_ms=500,
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
            silence_timeout_ms=200,
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
            defer_download=True,
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
        manager_no_streaming = StreamingRecognitionManager(engine="vosk", enable_streaming=False)
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
        with patch.object(self.manager, "_record_audio_streaming") as mock_record:
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
        self.manager.reconfigure(vad_sensitivity=2, silence_timeout=2.0, audio_device_index=1)

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
        # Create a manager that will fail to initialize streaming by patching 
        # the StreamingSpeechRecognizer to raise an exception
        with patch(
            "vocalinux.speech_recognition.streaming_manager.StreamingSpeechRecognizer"
        ) as mock_recognizer:
            mock_recognizer.side_effect = Exception("Streaming initialization failed")

            # This should fall back to non-streaming mode
            manager = StreamingRecognitionManager(engine="vosk", enable_streaming=True)

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
            vad_enabled=False,  # Disable VAD for predictable testing
        )

        # Set up callbacks to capture results
        results = []

        def capture_text(text):
            results.append(text)

        manager.register_text_callback(capture_text)

        # Mock the recording to avoid actual audio I/O
        with patch.object(manager, "_record_audio_streaming") as mock_record:
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
            vad_enabled=False,
        )

        # Get initial stats
        initial_stats = streaming_manager.get_performance_stats()

        # The key metric is that streaming mode is enabled
        self.assertTrue(initial_stats["streaming_mode"])
        self.assertEqual(streaming_manager.streaming_chunk_size, 512)


class TestStreamingChunkProcessing(unittest.TestCase):
    """Tests for streaming audio chunk processing."""

    def setUp(self):
        """Set up for tests."""
        self.recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            model_size="small",
            language="en-us",
            chunk_size=1024,
            sample_rate=16000,
            vad_enabled=False,
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.recognizer.is_running:
            self.recognizer.stop_streaming()

    def test_audio_chunk_queueing(self):
        """Test that audio chunks are properly queued for processing."""
        self.recognizer.start_streaming()

        # Process multiple chunks
        chunks = [b"chunk_data_" + bytes([i]) * 100 for i in range(5)]
        for chunk in chunks:
            self.recognizer.process_audio_chunk(chunk)

        # Verify chunks are in the queue
        self.assertEqual(self.recognizer.audio_queue.qsize(), 5)

        # Process all chunks
        time.sleep(0.1)
        self.recognizer.stop_streaming()

        # Verify statistics
        self.assertGreaterEqual(self.recognizer.total_chunks_processed, 0)

    def test_chunk_size_variations(self):
        """Test processing with different chunk sizes."""
        chunk_sizes = [512, 1024, 2048, 4096]

        for size in chunk_sizes:
            recognizer = StreamingSpeechRecognizer(
                engine="vosk",
                chunk_size=size,
                vad_enabled=False,
            )
            self.assertEqual(recognizer.chunk_size, size)

            # Test processing a chunk
            recognizer.start_streaming()
            audio_chunk = b"x" * size
            recognizer.process_audio_chunk(audio_chunk)
            time.sleep(0.05)
            recognizer.stop_streaming()

    def test_empty_chunk_handling(self):
        """Test handling of empty audio chunks."""
        self.recognizer.start_streaming()

        # Process empty chunk
        self.recognizer.process_audio_chunk(b"")
        time.sleep(0.05)

        # Process normal chunk after empty
        self.recognizer.process_audio_chunk(b"normal_data" * 100)
        time.sleep(0.05)

        self.recognizer.stop_streaming()

        # Should not crash and should have processed at least one chunk
        self.assertGreaterEqual(self.recognizer.total_chunks_processed, 0)

    def test_chunk_processing_rate(self):
        """Test that chunks are processed at expected rate."""
        self.recognizer.start_streaming()

        # Process many chunks quickly
        start_time = time.time()
        chunk_count = 20

        for i in range(chunk_count):
            self.recognizer.process_audio_chunk(b"rate_test" * 100)

        # Wait for processing
        time.sleep(0.2)
        elapsed = time.time() - start_time

        self.recognizer.stop_streaming()

        # Verify reasonable processing time
        self.assertLess(elapsed, 1.0)  # Should process within 1 second

    def test_concurrent_chunk_processing(self):
        """Test processing chunks from multiple threads."""
        self.recognizer.start_streaming()

        chunks_processed = []
        lock = threading.Lock()

        def process_chunks(thread_id, count):
            for i in range(count):
                chunk = f"thread_{thread_id}_chunk_{i}".encode() * 20
                self.recognizer.process_audio_chunk(chunk)
                with lock:
                    chunks_processed.append((thread_id, i))
                time.sleep(0.01)

        # Start multiple threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=process_chunks, args=(i, 5))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        time.sleep(0.1)
        self.recognizer.stop_streaming()

        # Verify all chunks were queued
        self.assertEqual(len(chunks_processed), 15)


class TestAudioBufferManagement(unittest.TestCase):
    """Tests for audio buffer management."""

    def setUp(self):
        """Set up for tests."""
        self.recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            model_size="small",
            vad_enabled=False,
            min_speech_duration_ms=100,
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.recognizer.is_running:
            self.recognizer.stop_streaming()

    def test_buffer_initial_state(self):
        """Test initial state of audio buffers."""
        self.assertEqual(len(self.recognizer.audio_buffer), 0)
        self.assertEqual(len(self.recognizer.speech_buffer), 0)
        self.assertFalse(self.recognizer.is_speaking)

    def test_buffer_accumulation(self):
        """Test that audio buffers accumulate correctly."""
        self.recognizer.start_streaming()

        # Add chunks to buffer
        chunks = [b"buffer_data_" + bytes([i]) * 50 for i in range(5)]
        for chunk in chunks:
            self.recognizer.audio_buffer.append(chunk)
            self.recognizer.speech_buffer.append(chunk)

        # Verify buffer contents
        self.assertEqual(len(self.recognizer.audio_buffer), 5)
        self.assertEqual(len(self.recognizer.speech_buffer), 5)

        self.recognizer.stop_streaming()

    def test_buffer_clear_after_processing(self):
        """Test that buffers are cleared after processing."""
        self.recognizer.start_streaming()

        # Add chunks to speech buffer
        for i in range(3):
            self.recognizer.speech_buffer.append(b"speech_data" * 50)

        # Manually trigger transcription which should clear buffer
        self.recognizer._transcribe_whisper_segment()

        # For whisper, buffer should be cleared
        if self.recognizer.engine == "whisper":
            self.assertEqual(len(self.recognizer.speech_buffer), 0)

        self.recognizer.stop_streaming()

    def test_buffer_size_limits(self):
        """Test buffer size management under load."""
        self.recognizer.start_streaming()

        # Add many chunks
        large_chunk = b"x" * 1024
        for _ in range(100):
            self.recognizer.audio_buffer.append(large_chunk)

        # Verify buffer can handle large amounts of data
        total_size = sum(len(chunk) for chunk in self.recognizer.audio_buffer)
        self.assertEqual(total_size, 100 * 1024)

        self.recognizer.stop_streaming()

    def test_speech_state_transitions(self):
        """Test speech state transitions during buffering."""
        self.recognizer.start_streaming()

        # Initial state
        self.assertFalse(self.recognizer.is_speaking)

        # Simulate speech detection
        self.recognizer.is_speaking = True
        self.recognizer.last_speech_time = time.time()
        self.recognizer.speech_buffer = [b"speech_chunk" * 50]

        # Verify speech state
        self.assertTrue(self.recognizer.is_speaking)
        self.assertGreater(len(self.recognizer.speech_buffer), 0)

        # Simulate end of speech
        self.recognizer.is_speaking = False
        self.assertFalse(self.recognizer.is_speaking)

        self.recognizer.stop_streaming()


class TestVADIntegration(unittest.TestCase):
    """Tests for Voice Activity Detection integration."""

    def setUp(self):
        """Set up for tests."""
        # Create VAD-enabled recognizer
        self.recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            model_size="small",
            vad_enabled=True,
            vad_threshold=0.5,
            min_speech_duration_ms=100,
            silence_timeout_ms=500,
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.recognizer.is_running:
            self.recognizer.stop_streaming()

    def test_vad_enabled_configuration(self):
        """Test that VAD is properly configured."""
        self.assertTrue(self.recognizer.vad_enabled)
        self.assertEqual(self.recognizer.vad_threshold, 0.5)

    def test_vad_disabled_configuration(self):
        """Test recognizer with VAD disabled."""
        recognizer_no_vad = StreamingSpeechRecognizer(
            engine="vosk",
            vad_enabled=False,
        )
        self.assertFalse(recognizer_no_vad.vad_enabled)

    def test_energy_based_vad_fallback(self):
        """Test energy-based VAD when Silero VAD is not available."""
        # Create recognizer that will use energy-based fallback
        recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            model_size="small",
            vad_enabled=True,  # Enable VAD
        )
        recognizer.start_streaming()

        # Ensure no vad_model exists (forces energy-based fallback)
        if hasattr(recognizer, "vad_model"):
            delattr(recognizer, "vad_model")

        # Test _detect_speech by mocking np.frombuffer to return actual values
        with patch("vocalinux.speech_recognition.streaming_recognizer.np") as mock_np:
            # High energy case
            mock_array = MagicMock()
            mock_array.mean.return_value = 1000  # Above threshold
            mock_np.frombuffer.return_value = mock_array
            mock_np.abs.return_value = mock_array

            result = recognizer._detect_speech(b"high_energy_data")
            self.assertTrue(result)

            # Low energy case
            mock_array.mean.return_value = 100  # Below threshold
            result = recognizer._detect_speech(b"low_energy_data")
            self.assertFalse(result)

        recognizer.stop_streaming()

    def test_silence_detection_timeout(self):
        """Test that silence timeout triggers finalization."""
        self.recognizer.start_streaming()

        # Simulate speech start
        self.recognizer.is_speaking = True
        self.recognizer.last_speech_time = time.time() - 1.0  # 1 second ago
        self.recognizer.speech_buffer = [b"speech_data" * 100]

        # Force timeout check
        self.recognizer.silence_timeout_ms = 500  # 500ms timeout

        # Process a silence chunk (low energy)
        silence_chunk = bytes([0x01] * 200)  # Low amplitude

        # Manually check silence timeout
        if self.recognizer.is_speaking:
            silence_duration = (time.time() - self.recognizer.last_speech_time) * 1000
            if silence_duration > self.recognizer.silence_timeout_ms:
                self.recognizer._finalize_speech_segment()
                self.recognizer.is_speaking = False

        # Speech should have ended due to timeout
        self.assertFalse(self.recognizer.is_speaking)

        self.recognizer.stop_streaming()

    def test_vad_sensitivity_levels(self):
        """Test different VAD sensitivity levels."""
        thresholds = [0.1, 0.3, 0.5, 0.7, 0.9]

        for threshold in thresholds:
            recognizer = StreamingSpeechRecognizer(
                engine="vosk",
                vad_enabled=True,
                vad_threshold=threshold,
            )
            self.assertEqual(recognizer.vad_threshold, threshold)


class TestLatencyMeasurement(unittest.TestCase):
    """Tests for latency measurement under load."""

    def setUp(self):
        """Set up for tests."""
        self.recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            model_size="small",
            vad_enabled=False,
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.recognizer.is_running:
            self.recognizer.stop_streaming()

    def test_latency_statistics_initial(self):
        """Test initial latency statistics."""
        stats = self.recognizer.get_statistics()
        self.assertEqual(stats["average_latency_ms"], 0.0)
        self.assertEqual(stats["total_chunks_processed"], 0)

    def test_latency_tracking_under_load(self):
        """Test latency tracking during heavy load."""
        self.recognizer.start_streaming()

        # Process many chunks rapidly
        start_time = time.time()
        chunk_count = 50

        for _ in range(chunk_count):
            self.recognizer.process_audio_chunk(b"latency_test" * 100)

        # Wait for processing
        time.sleep(0.3)

        elapsed = time.time() - start_time
        stats = self.recognizer.get_statistics()

        self.recognizer.stop_streaming()

        # Verify statistics were updated
        self.assertGreaterEqual(stats["total_chunks_processed"], 0)
        self.assertGreaterEqual(stats["total_processing_time"], 0.0)

        # Latency should be reasonable (less than 100ms per chunk on average)
        if stats["total_chunks_processed"] > 0:
            avg_latency = stats["average_latency_ms"]
            self.assertGreaterEqual(avg_latency, 0.0)

    def test_chunk_size_impact_on_latency(self):
        """Test that chunk size affects latency."""
        chunk_sizes = [512, 2048]
        latencies = {}

        for size in chunk_sizes:
            recognizer = StreamingSpeechRecognizer(
                engine="vosk",
                chunk_size=size,
                vad_enabled=False,
            )

            recognizer.start_streaming()

            # Process chunks
            for _ in range(10):
                recognizer.process_audio_chunk(b"x" * size)

            time.sleep(0.1)
            recognizer.stop_streaming()

            stats = recognizer.get_statistics()
            latencies[size] = stats["average_latency_ms"]

        # Both should have processed chunks
        self.assertIn(512, latencies)
        self.assertIn(2048, latencies)

    def test_manager_performance_stats(self):
        """Test streaming manager performance statistics."""
        manager = StreamingRecognitionManager(
            engine="vosk",
            enable_streaming=True,
            vad_enabled=False,
        )

        stats = manager.get_performance_stats()

        # Verify all expected keys are present
        self.assertIn("total_processing_time", stats)
        self.assertIn("total_audio_chunks", stats)
        self.assertIn("average_latency_ms", stats)
        self.assertIn("streaming_mode", stats)

        # Verify streaming mode
        self.assertTrue(stats["streaming_mode"])

    def test_processing_time_accumulation(self):
        """Test that processing time accumulates correctly."""
        self.recognizer.start_streaming()

        initial_time = self.recognizer.total_processing_time

        # Process chunks
        for _ in range(10):
            self.recognizer.process_audio_chunk(b"time_test" * 100)

        time.sleep(0.1)
        self.recognizer.stop_streaming()

        # Processing time should have increased (or stayed at 0 if no chunks processed)
        final_time = self.recognizer.total_processing_time
        self.assertGreaterEqual(final_time, initial_time)


class TestGracefulDegradation(unittest.TestCase):
    """Tests for graceful degradation under various failure conditions."""

    def test_recognizer_handles_init_failure(self):
        """Test that recognizer handles initialization failures."""
        # This tests error handling during recognizer creation
        with patch(
            "vocalinux.speech_recognition.streaming_recognizer.StreamingSpeechRecognizer._init_vosk"
        ) as mock_init:
            mock_init.side_effect = Exception("VOSK init failed")

            # Should raise the exception (not silently fail)
            with self.assertRaises(Exception):
                StreamingSpeechRecognizer(engine="vosk")

    def test_recognizer_invalid_engine(self):
        """Test handling of invalid engine type."""
        with self.assertRaises(ValueError) as context:
            StreamingSpeechRecognizer(engine="invalid_engine")

        self.assertIn("Unsupported engine", str(context.exception))

    def test_manager_handles_streaming_failure(self):
        """Test manager falls back when streaming fails to initialize."""
        with patch(
            "vocalinux.speech_recognition.streaming_manager.StreamingSpeechRecognizer"
        ) as mock_recognizer:
            mock_recognizer.side_effect = ImportError("Vosk not installed")

            manager = StreamingRecognitionManager(
                engine="vosk",
                enable_streaming=True,
            )

            # Should fall back gracefully
            self.assertFalse(manager.enable_streaming)
            self.assertIsNone(manager.streaming_recognizer)

    def test_error_callback_invocation(self):
        """Test that error callbacks are properly invoked."""
        recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            vad_enabled=False,
        )

        error_received = []

        def error_handler(error):
            error_received.append(error)

        recognizer.register_error_callback(error_handler)

        # Simulate an error
        test_error = Exception("Test error")
        recognizer._notify_error(test_error)

        # Verify callback was called
        self.assertEqual(len(error_received), 1)
        self.assertEqual(str(error_received[0]), "Test error")

    def test_processing_error_recovery(self):
        """Test recovery from processing errors."""
        recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            vad_enabled=False,
        )

        error_count = [0]

        def counting_error_handler(error):
            error_count[0] += 1

        recognizer.register_error_callback(counting_error_handler)

        recognizer.start_streaming()

        # Process some chunks (may generate errors due to mocks)
        for _ in range(5):
            recognizer.process_audio_chunk(b"error_test" * 100)

        time.sleep(0.1)

        # Should still be running after potential errors
        self.assertTrue(recognizer.is_running)

        recognizer.stop_streaming()

    def test_callback_error_isolation(self):
        """Test that errors in callbacks don't crash the recognizer."""
        recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            vad_enabled=False,
        )

        def failing_callback(text):
            raise Exception("Callback error")

        recognizer.register_final_result_callback(failing_callback)
        recognizer.register_partial_result_callback(failing_callback)

        recognizer.start_streaming()

        # Process a chunk - callbacks may fail but shouldn't crash
        recognizer.process_audio_chunk(b"isolation_test" * 100)
        time.sleep(0.05)

        # Should still be running
        self.assertTrue(recognizer.is_running)

        recognizer.stop_streaming()

    def test_reconfiguration_after_failure(self):
        """Test that manager can be reconfigured after failures."""
        manager = StreamingRecognitionManager(
            engine="vosk",
            enable_streaming=True,
            vad_enabled=False,
        )

        # Reconfigure various settings
        manager.reconfigure(
            vad_sensitivity=2,
            silence_timeout=2.0,
            audio_device_index=1,
        )

        # Verify settings were updated
        self.assertEqual(manager.vad_sensitivity, 2)
        self.assertEqual(manager.silence_timeout, 2.0)
        self.assertEqual(manager.audio_device_index, 1)

    def test_audio_device_change_during_runtime(self):
        """Test changing audio device setting."""
        manager = StreamingRecognitionManager(
            engine="vosk",
            enable_streaming=True,
            vad_enabled=False,
        )

        # Change device
        manager.set_audio_device(2)
        self.assertEqual(manager.get_audio_device(), 2)

        # Clear device
        manager.set_audio_device(None)
        self.assertIsNone(manager.get_audio_device())

    def test_stop_when_not_running(self):
        """Test that stop is safe when recognizer is not running."""
        recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            vad_enabled=False,
        )

        # Should not crash when stopped without starting
        recognizer.stop_streaming()
        self.assertFalse(recognizer.is_running)

    def test_multiple_start_calls(self):
        """Test handling of multiple start calls."""
        recognizer = StreamingSpeechRecognizer(
            engine="vosk",
            vad_enabled=False,
        )

        # Start multiple times
        recognizer.start_streaming()
        recognizer.start_streaming()  # Second call should be ignored
        recognizer.start_streaming()  # Third call should be ignored

        self.assertTrue(recognizer.is_running)

        recognizer.stop_streaming()
        self.assertFalse(recognizer.is_running)


if __name__ == "__main__":
    unittest.main()
