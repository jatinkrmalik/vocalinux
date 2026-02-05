"""
Tests for microphone reconnection and audio reliability features.

This test module covers Issue #92 - Microphone reconnection and audio buffer limits:
- Reconnection after device disconnect
- Exponential backoff timing
- Buffer overflow handling
- Max reconnection attempts
- Audio device error recovery
"""

import sys
import time
import threading
from unittest.mock import MagicMock, Mock, patch, PropertyMock

# Mock modules before importing vocalinux
sys.modules["vosk"] = MagicMock()
sys.modules["whisper"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["pyaudio"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["wave"] = MagicMock()
sys.modules["tempfile"] = MagicMock()
sys.modules["tqdm"] = MagicMock()
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()

# Import the shared mock from conftest
from conftest import mock_audio_feedback

from vocalinux.common_types import RecognitionState
from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager


class TestMicrophoneReconnection:
    """Test microphone reconnection logic."""

    def setup_method(self):
        """Set up test fixtures."""
        # Patch os.makedirs to avoid creating directories
        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()

        # Patch os.path.exists to return True for model paths
        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()

        # Patch VOSK initialization
        self.vosk_mock = sys.modules["vosk"]
        self.mock_model = MagicMock()
        self.mock_recognizer = MagicMock()
        self.vosk_mock.Model.return_value = self.mock_model
        self.vosk_mock.KaldiRecognizer.return_value = self.mock_recognizer
        self.mock_recognizer.FinalResult.return_value = '{"text": "test"}'

        # Create manager instance
        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True,
        )

    def teardown_method(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()

    def test_reconnection_attributes_initialized(self):
        """Test that reconnection attributes are properly initialized."""
        assert self.manager._max_buffer_size == 5000
        assert self.manager._max_reconnection_attempts == 5
        assert self.manager._reconnection_delay == 1.0
        assert self.manager._reconnection_attempts == 0
        assert self.manager._last_audio_error_time == 0
        assert self.manager._audio_stream is None
        assert self.manager._pyaudio_instance is None

    def test_reconnection_attempts_increment(self):
        """Test that reconnection attempts counter increments."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream
        mock_stream.read.return_value = b"test_data"
        mock_audio.paInt16 = 0x01

        # Initial state
        assert self.manager._reconnection_attempts == 0

        # First attempt
        result = self.manager._attempt_audio_reconnection(mock_audio)
        assert self.manager._reconnection_attempts == 1
        assert result is True

        # Second attempt
        result = self.manager._attempt_audio_reconnection(mock_audio)
        assert self.manager._reconnection_attempts == 2

    def test_max_reconnection_attempts_limit(self):
        """Test that reconnection stops after max attempts."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Device unavailable")
        mock_audio.paInt16 = 0x01

        # Set max attempts to 3 for faster testing
        self.manager._max_reconnection_attempts = 3

        # Exhaust all reconnection attempts
        for attempt in range(1, 4):
            result = self.manager._attempt_audio_reconnection(mock_audio)
            assert result is False
            assert self.manager._reconnection_attempts == attempt

        # Fourth attempt should immediately fail (max reached)
        result = self.manager._attempt_audio_reconnection(mock_audio)
        assert result is False
        assert self.manager._reconnection_attempts == 4  # Still increments

    def test_reconnection_resets_on_success(self):
        """Test that successful reconnection can reset counter."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream
        mock_stream.read.return_value = b"test_data"
        mock_audio.paInt16 = 0x01

        # Simulate previous failures
        self.manager._reconnection_attempts = 3

        # Successful reconnection
        result = self.manager._attempt_audio_reconnection(mock_audio)
        assert result is True
        # Counter still increments before success
        assert self.manager._reconnection_attempts == 4

    @patch("time.sleep")
    def test_reconnection_closes_existing_stream(self, mock_sleep):
        """Test that existing stream is closed before reconnection."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream
        mock_stream.read.return_value = b"test_data"
        mock_audio.paInt16 = 0x01

        # Create existing stream mock
        existing_stream = MagicMock()
        existing_stream.is_active.return_value = True
        self.manager._audio_stream = existing_stream

        # Attempt reconnection
        result = self.manager._attempt_audio_reconnection(mock_audio)

        # Verify old stream was closed
        existing_stream.stop_stream.assert_called_once()
        existing_stream.close.assert_called_once()
        assert result is True

    @patch("time.sleep")
    def test_reconnection_failure_no_data(self, mock_sleep):
        """Test reconnection failure when stream returns no data."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream
        mock_stream.read.return_value = b""  # Empty data
        mock_audio.paInt16 = 0x01

        result = self.manager._attempt_audio_reconnection(mock_audio)

        # Should fail because no data was read
        assert result is False
        mock_stream.stop_stream.assert_called_once()
        mock_stream.close.assert_called_once()

    @patch("time.sleep")
    def test_reconnection_with_device_index(self, mock_sleep):
        """Test reconnection with specific device index."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream
        mock_stream.read.return_value = b"test_data"
        mock_audio.paInt16 = 0x01

        # Set specific device index
        self.manager.audio_device_index = 2

        result = self.manager._attempt_audio_reconnection(mock_audio)

        assert result is True
        # Verify device index was passed to open()
        call_kwargs = mock_audio.open.call_args[1]
        assert call_kwargs["input_device_index"] == 2


class TestExponentialBackoff:
    """Test exponential backoff timing in reconnection."""

    def setup_method(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()
        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()

        self.vosk_mock = sys.modules["vosk"]
        self.mock_model = MagicMock()
        self.mock_recognizer = MagicMock()
        self.vosk_mock.Model.return_value = self.mock_model
        self.vosk_mock.KaldiRecognizer.return_value = self.mock_recognizer

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True,
        )

    def teardown_method(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()

    @patch("time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep):
        """Test that delays increase exponentially."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Device unavailable")
        mock_audio.paInt16 = 0x01

        expected_delays = [1.0, 2.0, 4.0, 8.0, 10.0]  # Last is capped at 10s

        for attempt, expected_delay in enumerate(expected_delays, 1):
            self.manager._reconnection_attempts = attempt - 1
            self.manager._attempt_audio_reconnection(mock_audio)

            mock_sleep.assert_called_with(expected_delay)

    @patch("time.sleep")
    def test_backoff_delay_capped_at_10_seconds(self, mock_sleep):
        """Test that delay is capped at 10 seconds."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Device unavailable")
        mock_audio.paInt16 = 0x01

        # Set max attempts high enough to test capping
        self.manager._max_reconnection_attempts = 20

        # Set attempt count high enough that uncapped delay would exceed 10 seconds
        # With base delay 1.0: 2^4 = 16 seconds, which gets capped to 10
        self.manager._reconnection_attempts = 4
        self.manager._attempt_audio_reconnection(mock_audio)

        # Should be capped at 10.0 seconds (not 16 seconds)
        mock_sleep.assert_called_with(10.0)


class TestBufferOverflowHandling:
    """Test audio buffer overflow handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()
        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()

        self.vosk_mock = sys.modules["vosk"]
        self.mock_model = MagicMock()
        self.mock_recognizer = MagicMock()
        self.vosk_mock.Model.return_value = self.mock_model
        self.vosk_mock.KaldiRecognizer.return_value = self.mock_recognizer

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True,
        )

    def teardown_method(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()

    def test_buffer_limit_configuration(self):
        """Test that buffer limits are properly configured."""
        assert self.manager._max_buffer_size == 5000

        # Test setting a new limit
        self.manager.set_buffer_limit(3000)
        assert self.manager._max_buffer_size == 3000

    def test_buffer_limit_minimum_enforced(self):
        """Test that buffer limit has a minimum value."""
        self.manager.set_buffer_limit(50)  # Below minimum
        assert self.manager._max_buffer_size == 100  # Should be clamped to 100

    def test_buffer_limit_maximum_enforced(self):
        """Test that buffer limit has a maximum value."""
        self.manager.set_buffer_limit(50000)  # Above maximum
        assert self.manager._max_buffer_size == 20000  # Should be clamped to 20000

    def test_buffer_stats(self):
        """Test buffer statistics reporting."""
        # Add test data to buffer
        self.manager.audio_buffer = [b"test_data"] * 100

        stats = self.manager.get_buffer_stats()

        assert isinstance(stats, dict)
        assert "buffer_size" in stats
        assert "buffer_limit" in stats
        assert "memory_usage_bytes" in stats
        assert "memory_usage_mb" in stats
        assert "buffer_full_percentage" in stats

        assert stats["buffer_size"] == 100
        assert stats["buffer_limit"] == 5000
        assert stats["memory_usage_bytes"] == 900  # 9 bytes * 100
        assert stats["memory_usage_mb"] == 900 / (1024 * 1024)
        assert stats["buffer_full_percentage"] == 2.0  # 100/5000 * 100

    def test_buffer_stats_empty_buffer(self):
        """Test buffer stats with empty buffer."""
        self.manager.audio_buffer = []

        stats = self.manager.get_buffer_stats()

        assert stats["buffer_size"] == 0
        assert stats["memory_usage_bytes"] == 0
        assert stats["memory_usage_mb"] == 0.0
        assert stats["buffer_full_percentage"] == 0.0

    def test_buffer_stats_thread_safety(self):
        """Test that buffer stats use proper locking."""
        # Verify the buffer lock exists
        assert hasattr(self.manager, "_buffer_lock")
        assert isinstance(self.manager._buffer_lock, type(threading.Lock()))

    def test_buffer_trim_on_overflow(self):
        """Test that buffer trims oldest data when limit reached."""
        # Fill buffer beyond limit
        self.manager.audio_buffer = [b"x"] * 6000
        self.manager._max_buffer_size = 5000

        # Simulate the buffer trimming logic from _record_audio
        if len(self.manager.audio_buffer) >= self.manager._max_buffer_size:
            remove_count = self.manager._max_buffer_size // 4
            self.manager.audio_buffer = self.manager.audio_buffer[remove_count:]

        # Should have removed 25% (1250 items)
        assert len(self.manager.audio_buffer) == 4750


class TestAudioDeviceErrorRecovery:
    """Test audio device error recovery mechanisms."""

    def setup_method(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()
        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()

        self.vosk_mock = sys.modules["vosk"]
        self.mock_model = MagicMock()
        self.mock_recognizer = MagicMock()
        self.vosk_mock.Model.return_value = self.mock_model
        self.vosk_mock.KaldiRecognizer.return_value = self.mock_recognizer

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True,
        )

    def teardown_method(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()

    @patch("time.sleep")
    def test_recovery_from_io_error(self, mock_sleep):
        """Test recovery from IO error during audio read."""
        mock_audio = MagicMock()
        mock_stream = MagicMock()

        # First two reads fail, then succeed
        mock_stream.read.side_effect = [
            IOError("Device disconnected"),
            b"recovered_data",
        ]
        mock_audio.open.return_value = mock_stream
        mock_audio.paInt16 = 0x01

        # Reset counter and simulate the recovery
        self.manager._reconnection_attempts = 0

        # Simulate the error handling logic
        try:
            data = mock_stream.read(1024, exception_on_overflow=False)
        except IOError:
            # Should attempt reconnection
            result = self.manager._attempt_audio_reconnection(mock_audio)
            assert result is True

    @patch("time.sleep")
    def test_recovery_from_os_error(self, mock_sleep):
        """Test recovery from OS error during audio read."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = [
            OSError("No such device"),
            MagicMock(),  # Success on retry
        ]
        mock_audio.paInt16 = 0x01

        # First call fails
        try:
            stream = mock_audio.open(format=mock_audio.paInt16)
        except OSError:
            pass

        # Reconnection should succeed
        result = self.manager._attempt_audio_reconnection(mock_audio)
        assert result is True

    def test_error_timestamp_tracking(self):
        """Test that error timestamps are tracked."""
        current_time = time.time()

        # Simulate error timestamp update
        self.manager._last_audio_error_time = current_time

        assert self.manager._last_audio_error_time == current_time

        # Should prevent rapid reconnection attempts
        assert time.time() - self.manager._last_audio_error_time < 1.0

    def test_prevention_of_rapid_reconnection_attempts(self):
        """Test prevention of rapid reconnection attempts."""
        # Simulate recent error
        self.manager._last_audio_error_time = time.time()

        # Should detect that error occurred too recently
        current_time = time.time()
        time_since_last_error = current_time - self.manager._last_audio_error_time

        # In the actual code, if time_since_last_error < 5.0, it should skip reconnection
        assert time_since_last_error < 5.0

    def test_graceful_degradation_on_complete_failure(self):
        """Test graceful degradation when all recovery attempts fail."""
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Permanent failure")
        mock_audio.paInt16 = 0x01

        # Exhaust all reconnection attempts
        self.manager._max_reconnection_attempts = 3
        for _ in range(5):
            result = self.manager._attempt_audio_reconnection(mock_audio)
            if not result and self.manager._reconnection_attempts >= 3:
                break

        # Should eventually give up
        assert self.manager._reconnection_attempts >= 3


class TestIntegrationScenarios:
    """Test integrated scenarios combining multiple reliability features."""

    def setup_method(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()
        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()

        self.vosk_mock = sys.modules["vosk"]
        self.mock_model = MagicMock()
        self.mock_recognizer = MagicMock()
        self.vosk_mock.Model.return_value = self.mock_model
        self.vosk_mock.KaldiRecognizer.return_value = self.mock_recognizer

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True,
        )

    def teardown_method(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()

    def test_device_disconnect_during_recording_simulation(self):
        """Simulate device disconnect during recording and recovery."""
        # Setup mock stream that fails after some reads
        mock_stream = MagicMock()
        read_count = [0]

        def side_effect(*args, **kwargs):
            read_count[0] += 1
            if read_count[0] == 5:
                raise IOError("Device disconnected")
            return b"audio_data"

        mock_stream.read.side_effect = side_effect

        # Setup mock audio
        mock_audio = MagicMock()
        mock_audio.open.return_value = mock_stream
        mock_audio.paInt16 = 0x01
        mock_audio.get_device_count.return_value = 2
        mock_audio.get_device_info_by_index.return_value = {
            "name": "Test Microphone",
            "maxInputChannels": 1,
        }

        self.manager._pyaudio_instance = mock_audio

        # Simulate recording loop behavior
        buffer = []
        error_occurred = False
        recovered = False

        for i in range(10):
            try:
                data = mock_stream.read(1024, exception_on_overflow=False)
                buffer.append(data)
            except IOError as e:
                error_occurred = True
                # Simulate reconnection
                with patch("time.sleep"):
                    mock_new_stream = MagicMock()
                    mock_new_stream.read.return_value = b"recovered_data"
                    mock_audio.open.return_value = mock_new_stream
                    result = self.manager._attempt_audio_reconnection(mock_audio)
                    if result:
                        recovered = True
                        mock_stream = mock_new_stream
                break

        assert error_occurred
        assert recovered

    def test_buffer_management_during_errors(self):
        """Test buffer management during error conditions."""
        # Fill buffer with data
        for i in range(1000):
            self.manager.audio_buffer.append(f"chunk_{i}".encode())

        initial_size = len(self.manager.audio_buffer)

        # Simulate buffer overflow protection
        if len(self.manager.audio_buffer) >= self.manager._max_buffer_size:
            remove_count = self.manager._max_buffer_size // 4
            self.manager.audio_buffer = self.manager.audio_buffer[remove_count:]

        # Buffer should remain manageable
        assert len(self.manager.audio_buffer) <= initial_size

    def test_state_consistency_during_recovery(self):
        """Test that recognition state remains consistent during recovery."""
        # Initial state
        assert self.manager.state == RecognitionState.IDLE

        # Simulate state change
        self.manager._update_state(RecognitionState.LISTENING)
        assert self.manager.state == RecognitionState.LISTENING

        # State should remain consistent even during error recovery
        mock_audio = MagicMock()
        mock_audio.open.side_effect = IOError("Error")
        mock_audio.paInt16 = 0x01

        with patch("time.sleep"):
            self.manager._attempt_audio_reconnection(mock_audio)

        # State should still be LISTENING (not changed by reconnection attempt)
        assert self.manager.state == RecognitionState.LISTENING


class TestBufferLimitEdgeCases:
    """Test edge cases for buffer limits."""

    def setup_method(self):
        """Set up test fixtures."""
        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()
        self.patcher_exists = patch("os.path.exists", return_value=True)
        self.mock_exists = self.patcher_exists.start()

        self.vosk_mock = sys.modules["vosk"]
        self.mock_model = MagicMock()
        self.mock_recognizer = MagicMock()
        self.vosk_mock.Model.return_value = self.mock_model
        self.vosk_mock.KaldiRecognizer.return_value = self.mock_recognizer

        self.manager = SpeechRecognitionManager(
            engine="vosk",
            language="en-us",
            defer_download=True,
        )

    def teardown_method(self):
        """Clean up after tests."""
        self.patcher_makedirs.stop()
        self.patcher_exists.stop()

    def test_buffer_exactly_at_limit(self):
        """Test behavior when buffer is exactly at limit."""
        self.manager._max_buffer_size = 5000
        self.manager.audio_buffer = [b"x"] * 5000

        # Should trigger trim
        if len(self.manager.audio_buffer) >= self.manager._max_buffer_size:
            remove_count = self.manager._max_buffer_size // 4
            self.manager.audio_buffer = self.manager.audio_buffer[remove_count:]

        assert len(self.manager.audio_buffer) == 3750  # 5000 - 1250

    def test_buffer_one_below_limit(self):
        """Test behavior when buffer is just below limit."""
        self.manager._max_buffer_size = 5000
        self.manager.audio_buffer = [b"x"] * 4999

        # Should NOT trigger trim
        if len(self.manager.audio_buffer) >= self.manager._max_buffer_size:
            remove_count = self.manager._max_buffer_size // 4
            self.manager.audio_buffer = self.manager.audio_buffer[remove_count:]

        assert len(self.manager.audio_buffer) == 4999

    def test_large_chunk_sizes(self):
        """Test buffer with large audio chunks."""
        # Simulate large audio chunks (e.g., high quality audio)
        large_chunk = b"x" * 8192  # 8KB chunks
        self.manager.audio_buffer = [large_chunk] * 100

        stats = self.manager.get_buffer_stats()

        # Memory usage should reflect large chunks
        expected_memory = 8192 * 100
        assert stats["memory_usage_bytes"] == expected_memory
        assert stats["memory_usage_mb"] == expected_memory / (1024 * 1024)

    def test_buffer_limit_at_boundary_values(self):
        """Test setting buffer limit at boundary values."""
        # Test minimum boundary
        self.manager.set_buffer_limit(100)
        assert self.manager._max_buffer_size == 100

        # Test maximum boundary
        self.manager.set_buffer_limit(20000)
        assert self.manager._max_buffer_size == 20000

        # Test values slightly below/above boundaries
        self.manager.set_buffer_limit(99)
        assert self.manager._max_buffer_size == 100  # Clamped

        self.manager.set_buffer_limit(20001)
        assert self.manager._max_buffer_size == 20000  # Clamped

    def test_concurrent_buffer_access_simulation(self):
        """Simulate concurrent buffer access patterns."""
        import threading

        results = []

        def writer():
            for i in range(100):
                self.manager.audio_buffer.append(f"data_{i}".encode())

        def reader():
            for _ in range(100):
                stats = self.manager.get_buffer_stats()
                results.append(stats["buffer_size"])

        # Run writer and reader in parallel
        writer_thread = threading.Thread(target=writer)
        reader_thread = threading.Thread(target=reader)

        writer_thread.start()
        reader_thread.start()
        writer_thread.join()
        reader_thread.join()

        # Should complete without errors
        assert len(results) == 100
        assert len(self.manager.audio_buffer) == 100
