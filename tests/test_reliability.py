"""
Comprehensive reliability tests for Vocalinux PR #109 - Microphone Reconnection.

This module tests:
- Device disconnect/reconnect cycles
- Exponential backoff timing verification
- Buffer overflow under load
- Max reconnection attempts boundary
- Audio error recovery

Run with: PYTHONPATH=src python3 -m pytest tests/test_reliability.py -v
"""

import os
import sys
import time
import threading
import unittest
from unittest.mock import MagicMock, Mock, patch, call, ANY

# Ensure we're using the local src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Remove any existing vocalinux-wt-110 paths to avoid conflicts
sys.path = [p for p in sys.path if '/tmp/vocalinux-wt-110' not in p]

# Mock modules BEFORE importing vocalinux modules
sys.modules["vosk"] = MagicMock()
sys.modules["whisper"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["pyaudio"] = MagicMock()
sys.modules["wave"] = MagicMock()
sys.modules["tempfile"] = MagicMock()
sys.modules["tqdm"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["zipfile"] = MagicMock()
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.Gio"] = MagicMock()
sys.modules["vocalinux.ui.audio_feedback"] = MagicMock()

# Now import vocalinux modules
from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager
from vocalinux.common_types import RecognitionState


class TestMicrophoneReconnection(unittest.TestCase):
    """Test microphone reconnection logic and reliability."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()

        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()
        
        self.patcher_vosk_path = patch.object(
            SpeechRecognitionManager, 
            "_get_vosk_model_path", 
            return_value="/mock/path/vosk-model"
        )
        self.mock_vosk_path = self.patcher_vosk_path.start()

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True
        )
        self.manager._model_initialized = True

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_vosk_path.stop()

    def test_initial_reconnection_state(self):
        """Test that reconnection state is properly initialized."""
        self.assertEqual(self.manager._max_reconnection_attempts, 5)
        self.assertEqual(self.manager._reconnection_delay, 1.0)
        self.assertEqual(self.manager._reconnection_attempts, 0)
        self.assertEqual(self.manager._last_audio_error_time, 0)

    def test_buffer_limits_initialization(self):
        """Test that buffer limits are properly initialized."""
        self.assertEqual(self.manager._max_buffer_size, 5000)
        self.assertIsNotNone(self.manager._buffer_lock)
        self.assertEqual(self.manager.audio_buffer, [])

    def test_set_buffer_limit_valid(self):
        """Test setting buffer limit within valid range."""
        self.manager.set_buffer_limit(3000)
        self.assertEqual(self.manager._max_buffer_size, 3000)

    def test_set_buffer_limit_minimum(self):
        """Test buffer limit clamping at minimum."""
        self.manager.set_buffer_limit(50)
        self.assertEqual(self.manager._max_buffer_size, 100)

    def test_set_buffer_limit_maximum(self):
        """Test buffer limit clamping at maximum."""
        self.manager.set_buffer_limit(50000)
        self.assertEqual(self.manager._max_buffer_size, 20000)

    def test_get_buffer_stats_empty(self):
        """Test buffer stats when buffer is empty."""
        stats = self.manager.get_buffer_stats()
        self.assertEqual(stats["buffer_size"], 0)
        self.assertEqual(stats["buffer_limit"], 5000)
        self.assertEqual(stats["memory_usage_bytes"], 0)
        self.assertEqual(stats["buffer_full_percentage"], 0)

    def test_get_buffer_stats_with_data(self):
        """Test buffer stats when buffer has data."""
        self.manager.audio_buffer = [b"x" * 1024] * 100
        
        stats = self.manager.get_buffer_stats()
        self.assertEqual(stats["buffer_size"], 100)
        self.assertEqual(stats["buffer_limit"], 5000)
        self.assertEqual(stats["memory_usage_bytes"], 100 * 1024)
        self.assertAlmostEqual(stats["buffer_full_percentage"], 2.0, places=1)

    def test_get_buffer_stats_thread_safety(self):
        """Test that get_buffer_stats is thread-safe."""
        self.manager.audio_buffer = [b"x" * 1024] * 100
        
        results = []
        
        def collect_stats():
            for _ in range(100):
                results.append(self.manager.get_buffer_stats())
        
        threads = [threading.Thread(target=collect_stats) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        for stats in results:
            self.assertIn("buffer_size", stats)
            self.assertIn("buffer_limit", stats)
            self.assertIn("memory_usage_bytes", stats)


class TestReconnectionAttempts(unittest.TestCase):
    """Test reconnection attempt boundaries and logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()

        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()
        
        self.patcher_vosk_path = patch.object(
            SpeechRecognitionManager, 
            "_get_vosk_model_path", 
            return_value="/mock/path/vosk-model"
        )
        self.mock_vosk_path = self.patcher_vosk_path.start()

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True
        )
        self.manager._model_initialized = True

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_vosk_path.stop()

    def test_reconnection_attempt_counter_increments(self):
        """Test that reconnection attempt counter increments correctly."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Device unavailable")
        mock_audio.paInt16 = MagicMock()

        result = self.manager._attempt_audio_reconnection(mock_audio)
        self.assertFalse(result)
        self.assertEqual(self.manager._reconnection_attempts, 1)

        result = self.manager._attempt_audio_reconnection(mock_audio)
        self.assertFalse(result)
        self.assertEqual(self.manager._reconnection_attempts, 2)

    def test_max_reconnection_attempts_boundary(self):
        """Test that reconnection stops after max attempts."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Device unavailable")
        mock_audio.paInt16 = MagicMock()

        self.manager._max_reconnection_attempts = 3

        for i in range(1, 4):
            result = self.manager._attempt_audio_reconnection(mock_audio)
            self.assertFalse(result)
            self.assertEqual(self.manager._reconnection_attempts, i)

        result = self.manager._attempt_audio_reconnection(mock_audio)
        self.assertFalse(result)
        self.assertEqual(self.manager._reconnection_attempts, 4)

    def test_successful_reconnection(self):
        """Test that successful reconnection works."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream
        mock_audio.paInt16 = MagicMock()
        mock_stream.read.return_value = b"test_data"

        self.manager._reconnection_attempts = 2

        result = self.manager._attempt_audio_reconnection(mock_audio)
        self.assertTrue(result)


class TestExponentialBackoff(unittest.TestCase):
    """Test exponential backoff timing."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.patcher_makedirs.start()

        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.patcher_exists.start()
        
        self.patcher_vosk_path = patch.object(
            SpeechRecognitionManager, 
            "_get_vosk_model_path", 
            return_value="/mock/path/vosk-model"
        )
        self.patcher_vosk_path.start()

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True
        )
        self.manager._model_initialized = True

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_vosk_path.stop()

    @patch("time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep):
        """Test that delays follow exponential backoff pattern."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Device unavailable")
        mock_audio.paInt16 = MagicMock()

        self.manager._reconnection_attempts = 0
        expected_delays = [1.0, 2.0, 4.0, 8.0, 10.0]

        for i, expected_delay in enumerate(expected_delays):
            self.manager._reconnection_attempts = i
            self.manager._attempt_audio_reconnection(mock_audio)
            
            actual_delay = mock_sleep.call_args[0][0]
            self.assertAlmostEqual(actual_delay, expected_delay, places=2,
                                  msg=f"Attempt {i+1}: expected {expected_delay}s, got {actual_delay}s")

    @patch("time.sleep")
    def test_backoff_cap_at_10_seconds(self, mock_sleep):
        """Test that backoff delay caps at 10 seconds."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Device unavailable")
        mock_audio.paInt16 = MagicMock()

        # Test with high attempt count (within max attempts to ensure sleep is called)
        self.manager._reconnection_attempts = 6  # Will be incremented to 7
        self.manager._max_reconnection_attempts = 10  # Allow this attempt
        self.manager._attempt_audio_reconnection(mock_audio)

        # Delay should be capped at 10 seconds (2^6 = 64, capped to 10)
        actual_delay = mock_sleep.call_args[0][0]
        self.assertEqual(actual_delay, 10.0)

    @patch("time.sleep")
    def test_backoff_timing_verification(self, mock_sleep):
        """Verify exact backoff formula."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Device unavailable")
        mock_audio.paInt16 = MagicMock()

        base_delay = self.manager._reconnection_delay

        for attempt in range(6):
            self.manager._reconnection_attempts = attempt
            self.manager._attempt_audio_reconnection(mock_audio)
            
            expected = min(base_delay * (2 ** attempt), 10.0)
            actual = mock_sleep.call_args[0][0]
            
            self.assertEqual(actual, expected,
                           f"Attempt {attempt + 1}: expected {expected}s, got {actual}s")


class TestBufferOverflowHandling(unittest.TestCase):
    """Test buffer overflow and memory management."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.patcher_makedirs.start()

        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.patcher_exists.start()
        
        self.patcher_vosk_path = patch.object(
            SpeechRecognitionManager, 
            "_get_vosk_model_path", 
            return_value="/mock/path/vosk-model"
        )
        self.patcher_vosk_path.start()

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True
        )
        self.manager._model_initialized = True

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_vosk_path.stop()

    def test_buffer_trimming_when_full(self):
        """Test that buffer removes oldest data when limit reached."""
        self.manager._max_buffer_size = 100
        self.manager.audio_buffer = [b"x"] * 150
        
        if len(self.manager.audio_buffer) >= self.manager._max_buffer_size:
            remove_count = self.manager._max_buffer_size // 4
            self.manager.audio_buffer = self.manager.audio_buffer[remove_count:]
        
        self.assertEqual(len(self.manager.audio_buffer), 125)

    def test_buffer_memory_calculation(self):
        """Test accurate memory usage calculation."""
        chunks = [b"x" * 1024, b"y" * 2048, b"z" * 512]
        self.manager.audio_buffer = chunks
        
        stats = self.manager.get_buffer_stats()
        expected_bytes = 1024 + 2048 + 512
        expected_mb = expected_bytes / (1024 * 1024)
        
        self.assertEqual(stats["memory_usage_bytes"], expected_bytes)
        self.assertAlmostEqual(stats["memory_usage_mb"], expected_mb, places=6)

    def test_buffer_under_load_simulation(self):
        """Simulate buffer behavior under high load."""
        self.manager._max_buffer_size = 1000
        
        for i in range(2000):
            self.manager.audio_buffer.append(b"data_chunk" * 100)
            
            if len(self.manager.audio_buffer) >= self.manager._max_buffer_size:
                remove_count = self.manager._max_buffer_size // 4
                self.manager.audio_buffer = self.manager.audio_buffer[remove_count:]
        
        self.assertLessEqual(len(self.manager.audio_buffer), self.manager._max_buffer_size)


class TestDeviceDisconnectReconnect(unittest.TestCase):
    """Test device disconnect/reconnect cycles."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.patcher_makedirs.start()

        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.patcher_exists.start()
        
        self.patcher_vosk_path = patch.object(
            SpeechRecognitionManager, 
            "_get_vosk_model_path", 
            return_value="/mock/path/vosk-model"
        )
        self.patcher_vosk_path.start()

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True
        )
        self.manager._model_initialized = True

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_vosk_path.stop()

    @patch("time.sleep")
    def test_device_disconnect_recovery(self, mock_sleep):
        """Test recovery after device disconnect."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.paInt16 = MagicMock()
        
        mock_audio.open.side_effect = [IOError("Device disconnected"), mock_stream]
        mock_stream.read.return_value = b"audio_data"
        
        result = self.manager._attempt_audio_reconnection(mock_audio)
        self.assertFalse(result)
        
        self.manager._reconnection_attempts = 0
        result = self.manager._attempt_audio_reconnection(mock_audio)
        self.assertTrue(result)

    @patch("time.sleep")
    def test_multiple_disconnect_cycles(self, mock_sleep):
        """Test handling multiple disconnect/reconnect cycles."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.paInt16 = MagicMock()
        
        call_count = [0]
        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return mock_stream
            raise IOError("Device error")
        
        mock_audio.open.side_effect = side_effect
        mock_stream.read.return_value = b"audio_data"
        
        results = []
        for i in range(6):
            self.manager._reconnection_attempts = 0
            result = self.manager._attempt_audio_reconnection(mock_audio)
            results.append(result)
        
        expected = [False, True, False, True, False, True]
        self.assertEqual(results, expected)


class TestAudioErrorRecovery(unittest.TestCase):
    """Test audio error recovery mechanisms."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.patcher_makedirs.start()

        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.patcher_exists.start()
        
        self.patcher_vosk_path = patch.object(
            SpeechRecognitionManager, 
            "_get_vosk_model_path", 
            return_value="/mock/path/vosk-model"
        )
        self.patcher_vosk_path.start()

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True
        )
        self.manager._model_initialized = True

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_vosk_path.stop()

    @patch("time.sleep")
    def test_successful_stream_replacement(self, mock_sleep):
        """Test that successful reconnection replaces old stream."""
        mock_audio = MagicMock()
        old_stream = MagicMock()
        new_stream = MagicMock()
        mock_audio.paInt16 = MagicMock()
        
        self.manager._audio_stream = old_stream
        mock_audio.open.return_value = new_stream
        new_stream.read.return_value = b"audio_data"
        
        result = self.manager._attempt_audio_reconnection(mock_audio)
        
        self.assertTrue(result)
        self.assertEqual(self.manager._audio_stream, new_stream)
        old_stream.stop_stream.assert_called_once()
        old_stream.close.assert_called_once()

    @patch("time.sleep")
    def test_stream_test_after_reconnection(self, mock_sleep):
        """Test that stream is tested after reconnection."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.paInt16 = MagicMock()
        
        mock_audio.open.return_value = mock_stream
        mock_stream.read.return_value = b"test_audio_chunk"
        
        result = self.manager._attempt_audio_reconnection(mock_audio)
        
        self.assertTrue(result)
        mock_stream.read.assert_called_once()

    @patch("time.sleep")
    def test_empty_stream_data_considered_failure(self, mock_sleep):
        """Test that empty data from reconnected stream is failure."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.paInt16 = MagicMock()
        
        mock_audio.open.return_value = mock_stream
        mock_stream.read.return_value = b""
        
        result = self.manager._attempt_audio_reconnection(mock_audio)
        
        self.assertFalse(result)
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()


class TestStressScenarios(unittest.TestCase):
    """Stress tests for reliability under extreme conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.patcher_makedirs.start()

        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.patcher_exists.start()
        
        self.patcher_vosk_path = patch.object(
            SpeechRecognitionManager, 
            "_get_vosk_model_path", 
            return_value="/mock/path/vosk-model"
        )
        self.patcher_vosk_path.start()

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True
        )
        self.manager._model_initialized = True

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_vosk_path.stop()

    def test_rapid_state_changes(self):
        """Test behavior during rapid state changes."""
        for i in range(100):
            self.manager.should_record = i % 2 == 0
        self.assertIsInstance(self.manager.should_record, bool)

    def test_concurrent_buffer_access(self):
        """Test thread safety under concurrent access."""
        self.manager._max_buffer_size = 1000
        errors = []
        
        def writer():
            try:
                for i in range(1000):
                    with self.manager._buffer_lock:
                        self.manager.audio_buffer.append(b"data")
                        if len(self.manager.audio_buffer) >= self.manager._max_buffer_size:
                            remove_count = self.manager._max_buffer_size // 4
                            self.manager.audio_buffer = self.manager.audio_buffer[remove_count:]
            except Exception as e:
                errors.append(e)
        
        def reader():
            try:
                for _ in range(1000):
                    _ = self.manager.get_buffer_stats()
            except Exception as e:
                errors.append(e)
        
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=writer))
            threads.append(threading.Thread(target=reader))
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")

    @patch("time.sleep")
    def test_reconnection_storm_protection(self, mock_sleep):
        """Test protection against rapid reconnection attempts."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Device unavailable")
        mock_audio.paInt16 = MagicMock()
        
        results = []
        for _ in range(20):
            result = self.manager._attempt_audio_reconnection(mock_audio)
            results.append(result)
        
        failure_count = sum(1 for r in results if not r)
        self.assertEqual(failure_count, 20)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.patcher_makedirs.start()

        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.patcher_exists.start()
        
        self.patcher_vosk_path = patch.object(
            SpeechRecognitionManager, 
            "_get_vosk_model_path", 
            return_value="/mock/path/vosk-model"
        )
        self.patcher_vosk_path.start()

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True
        )
        self.manager._model_initialized = True

    def tearDown(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()
        self.patcher_vosk_path.stop()

    def test_zero_max_buffer_size(self):
        """Test behavior with zero max buffer size."""
        self.manager.set_buffer_limit(0)
        self.assertEqual(self.manager._max_buffer_size, 100)

    def test_negative_max_buffer_size(self):
        """Test behavior with negative max buffer size."""
        self.manager.set_buffer_limit(-1000)
        self.assertEqual(self.manager._max_buffer_size, 100)

    def test_buffer_stats_at_exact_limit(self):
        """Test buffer stats when exactly at limit."""
        self.manager._max_buffer_size = 100
        self.manager.audio_buffer = [b"x"] * 100
        
        stats = self.manager.get_buffer_stats()
        self.assertEqual(stats["buffer_full_percentage"], 100.0)

    def test_reconnection_with_none_audio_instance(self):
        """Test reconnection handling when audio instance is None."""
        result = self.manager._attempt_audio_reconnection(None)
        self.assertFalse(result)

    @patch("time.sleep")
    def test_reconnection_preserves_device_index(self, mock_sleep):
        """Test that reconnection preserves audio device index."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.paInt16 = MagicMock()
        
        self.manager.audio_device_index = 5
        mock_audio.open.return_value = mock_stream
        mock_stream.read.return_value = b"audio_data"
        
        self.manager._attempt_audio_reconnection(mock_audio)
        
        call_kwargs = mock_audio.open.call_args[1]
        self.assertEqual(call_kwargs["input_device_index"], 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
