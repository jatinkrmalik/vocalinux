"""
Tests for lazy model loading functionality in the speech recognition manager.

These tests verify:
1. Models are NOT loaded immediately at initialization (lazy behavior)
2. Models ARE loaded when recognition starts
3. Thread safety under concurrent access
4. Error handling when model load fails
5. Startup time improvement
"""

import sys
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

# Mock modules before importing any modules that might use them
# NOTE: We only mock modules that are directly imported, not modules used internally
# This prevents breaking other tests that rely on these modules
sys.modules["vosk"] = MagicMock()
sys.modules["whisper"] = MagicMock()
sys.modules["pyaudio"] = MagicMock()
sys.modules["wave"] = MagicMock()
sys.modules["numpy"] = MagicMock()

# Import the shared mock from conftest
from conftest import mock_audio_feedback

from vocalinux.common_types import RecognitionState
from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager


class TestLazyInitialization(unittest.TestCase):
    """Test cases for lazy model loading behavior."""

    def setUp(self):
        """Set up for tests."""
        # Create patches for our mocks
        self.mockModel = patch.object(sys.modules["vosk"], "Model")
        self.mockKaldi = patch.object(sys.modules["vosk"], "KaldiRecognizer")
        self.mockMakeDirs = patch("os.makedirs")
        self.mockPath = patch.object(SpeechRecognitionManager, "_get_vosk_model_path")
        self.mockDownload = patch.object(SpeechRecognitionManager, "_download_vosk_model")

        # Start all patches
        self.modelMock = self.mockModel.start()
        self.kaldiMock = self.mockKaldi.start()
        self.makeDirsMock = self.mockMakeDirs.start()
        self.pathMock = self.mockPath.start()
        self.downloadMock = self.mockDownload.start()

        # Set up return values
        self.recognizerMock = MagicMock()
        self.kaldiMock.return_value = self.recognizerMock
        self.pathMock.return_value = "/mock/path/vosk-model"
        self.recognizerMock.FinalResult.return_value = '{"text": "test transcription"}'

        # Reset audio feedback mocks
        mock_audio_feedback.play_start_sound.reset_mock()
        mock_audio_feedback.play_stop_sound.reset_mock()
        mock_audio_feedback.play_error_sound.reset_mock()

    def tearDown(self):
        """Clean up after tests."""
        self.mockModel.stop()
        self.mockKaldi.stop()
        self.mockMakeDirs.stop()
        self.mockPath.stop()
        self.mockDownload.stop()

    def test_model_not_loaded_at_init(self):
        """Test that model is NOT loaded immediately at initialization (lazy loading)."""
        # Create manager - model should NOT be loaded yet
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        # Verify initial state
        self.assertEqual(manager.state, RecognitionState.IDLE)
        self.assertEqual(manager.engine, "vosk")
        self.assertEqual(manager.model_size, "small")

        # CRITICAL: Model should NOT be loaded at initialization
        self.modelMock.assert_not_called()
        self.kaldiMock.assert_not_called()

        # model_ready should be False
        self.assertFalse(manager.model_ready)
        self.assertFalse(manager._model_initialized)
        self.assertIsNone(manager.model)
        self.assertIsNone(manager.recognizer)

    def test_model_loaded_on_demand(self):
        """Test that model IS loaded when _ensure_model_loaded is called."""
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        # Model not loaded yet
        self.assertFalse(manager.model_ready)
        self.modelMock.assert_not_called()

        # Trigger model loading
        result = manager._ensure_model_loaded()

        # Model should now be loaded
        self.assertTrue(result)
        self.assertTrue(manager.model_ready)
        self.assertTrue(manager._model_initialized)
        self.modelMock.assert_called_once()
        self.kaldiMock.assert_called_once()

    def test_model_loaded_only_once(self):
        """Test that model is loaded only once even with multiple calls."""
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        # Trigger model loading multiple times
        manager._ensure_model_loaded()
        manager._ensure_model_loaded()
        manager._ensure_model_loaded()

        # Model should only be loaded once
        self.modelMock.assert_called_once()
        self.kaldiMock.assert_called_once()
        self.assertTrue(manager.model_ready)

    def test_lazy_loading_with_whisper(self):
        """Test lazy loading with Whisper engine."""
        whisper_mock = MagicMock()
        torch_mock = MagicMock()
        whisper_mock.load_model = MagicMock()
        torch_mock.cuda.is_available.return_value = False
        model_mock = MagicMock()
        whisper_mock.load_model.return_value = model_mock

        with patch.dict("sys.modules", {"whisper": whisper_mock, "torch": torch_mock}):
            with patch.object(SpeechRecognitionManager, "_download_whisper_model"):
                # Create manager - model should NOT be loaded
                manager = SpeechRecognitionManager(engine="whisper", model_size="medium")

                self.assertEqual(manager.engine, "whisper")
                self.assertFalse(manager.model_ready)
                whisper_mock.load_model.assert_not_called()

                # Trigger lazy loading
                manager._ensure_model_loaded()

                # Now model should be loaded
                self.assertTrue(manager.model_ready)
                whisper_mock.load_model.assert_called_once()


class TestThreadSafety(unittest.TestCase):
    """Test cases for thread safety of lazy loading."""

    def setUp(self):
        """Set up for tests."""
        self.mockModel = patch.object(sys.modules["vosk"], "Model")
        self.mockKaldi = patch.object(sys.modules["vosk"], "KaldiRecognizer")
        self.mockMakeDirs = patch("os.makedirs")
        self.mockPath = patch.object(SpeechRecognitionManager, "_get_vosk_model_path")
        self.mockDownload = patch.object(SpeechRecognitionManager, "_download_vosk_model")

        self.modelMock = self.mockModel.start()
        self.kaldiMock = self.mockKaldi.start()
        self.makeDirsMock = self.mockMakeDirs.start()
        self.pathMock = self.mockPath.start()
        self.downloadMock = self.mockDownload.start()

        self.recognizerMock = MagicMock()
        self.kaldiMock.return_value = self.recognizerMock
        self.pathMock.return_value = "/mock/path/vosk-model"

        # Add a small delay to simulate model loading time
        def slow_model_init(*args, **kwargs):
            time.sleep(0.01)  # 10ms delay
            return MagicMock()

        self.modelMock.side_effect = slow_model_init

    def tearDown(self):
        """Clean up after tests."""
        self.mockModel.stop()
        self.mockKaldi.stop()
        self.mockMakeDirs.stop()
        self.mockPath.stop()
        self.mockDownload.stop()

    def test_concurrent_model_loading(self):
        """Test that concurrent access safely loads model only once."""
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        results = []
        errors = []

        def try_load():
            try:
                result = manager._ensure_model_loaded()
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads that all try to load the model
        threads = [threading.Thread(target=try_load) for _ in range(10)]

        # Start all threads simultaneously
        for t in threads:
            t.start()

        # Wait for all to complete
        for t in threads:
            t.join()

        # All threads should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))
        self.assertEqual(len(errors), 0)

        # Model should only be loaded once
        self.modelMock.assert_called_once()
        self.assertTrue(manager.model_ready)


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling during model loading."""

    def setUp(self):
        """Set up for tests."""
        self.mockModel = patch.object(sys.modules["vosk"], "Model")
        self.mockKaldi = patch.object(sys.modules["vosk"], "KaldiRecognizer")
        self.mockMakeDirs = patch("os.makedirs")
        self.mockPath = patch.object(SpeechRecognitionManager, "_get_vosk_model_path")
        self.mockDownload = patch.object(SpeechRecognitionManager, "_download_vosk_model")
        self.mockLogger = patch("vocalinux.speech_recognition.recognition_manager.logger")

        self.modelMock = self.mockModel.start()
        self.kaldiMock = self.mockKaldi.start()
        self.makeDirsMock = self.mockMakeDirs.start()
        self.pathMock = self.mockPath.start()
        self.downloadMock = self.mockDownload.start()
        self.loggerMock = self.mockLogger.start()

        self.pathMock.return_value = "/mock/path/vosk-model"

    def tearDown(self):
        """Clean up after tests."""
        self.mockModel.stop()
        self.mockKaldi.stop()
        self.mockMakeDirs.stop()
        self.mockPath.stop()
        self.mockDownload.stop()
        self.mockLogger.stop()

    def test_model_load_failure_handling(self):
        """Test that model loading failures are properly handled."""
        # Make model loading fail
        self.modelMock.side_effect = RuntimeError("Failed to load model")

        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        # Attempt to load should raise exception
        with self.assertRaises(RuntimeError) as context:
            manager._ensure_model_loaded()

        self.assertIn("Failed to load model", str(context.exception))

        # Manager should be in error state
        self.assertEqual(manager.state, RecognitionState.ERROR)
        self.assertFalse(manager.model_ready)

        # Error should be logged
        self.loggerMock.error.assert_called()

    def test_model_load_failure_recovery(self):
        """Test that manager can recover from failed model load."""
        self.modelMock.side_effect = RuntimeError("First attempt failed")

        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        # First attempt fails
        with self.assertRaises(RuntimeError):
            manager._ensure_model_loaded()

        self.assertFalse(manager.model_ready)

        # Fix the model loading
        self.modelMock.side_effect = None
        self.modelMock.return_value = MagicMock()

        # Reset state manually (this would normally be done by user retry)
        manager.state = RecognitionState.IDLE
        manager._model_initialized = False
        manager.model = None

        # Second attempt should succeed
        result = manager._ensure_model_loaded()
        self.assertTrue(result)
        self.assertTrue(manager.model_ready)

    def test_import_error_handling(self):
        """Test handling of import errors for speech recognition backends."""
        # Simulate vosk not being available
        with patch.dict("sys.modules", {"vosk": None}):
            manager = SpeechRecognitionManager(engine="vosk", model_size="small")

            # Import should fail when trying to load model
            with self.assertRaises((ImportError, TypeError)):
                manager._ensure_model_loaded()


class TestStartupTime(unittest.TestCase):
    """Test cases for startup time improvement with lazy loading."""

    def setUp(self):
        """Set up for tests."""
        self.mockModel = patch.object(sys.modules["vosk"], "Model")
        self.mockKaldi = patch.object(sys.modules["vosk"], "KaldiRecognizer")
        self.mockMakeDirs = patch("os.makedirs")
        self.mockPath = patch.object(SpeechRecognitionManager, "_get_vosk_model_path")

        self.modelMock = self.mockModel.start()
        self.kaldiMock = self.mockKaldi.start()
        self.makeDirsMock = self.mockMakeDirs.start()
        self.pathMock = self.mockPath.start()

        # Simulate slow model loading (500ms)
        def slow_model_init(*args, **kwargs):
            time.sleep(0.5)
            return MagicMock()

        self.modelMock.side_effect = slow_model_init
        self.pathMock.return_value = "/mock/path/vosk-model"

    def tearDown(self):
        """Clean up after tests."""
        self.mockModel.stop()
        self.kaldiMock.stop()
        self.mockMakeDirs.stop()
        self.mockPath.stop()

    def test_fast_startup_time(self):
        """Test that initialization is fast (model not loaded immediately)."""
        start_time = time.time()

        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        init_time = time.time() - start_time

        # Initialization should be fast (< 100ms) since model is not loaded
        self.assertLess(init_time, 0.1, f"Initialization took {init_time:.3f}s, expected < 0.1s")

        # Model should not be ready yet
        self.assertFalse(manager.model_ready)

    def test_model_loading_takes_time(self):
        """Test that actual model loading takes expected time."""
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        start_time = time.time()
        manager._ensure_model_loaded()
        load_time = time.time() - start_time

        # Model loading should take the expected time (> 400ms due to our mock)
        self.assertGreater(load_time, 0.4, f"Model loading took {load_time:.3f}s, expected > 0.4s")

        # Model should now be ready
        self.assertTrue(manager.model_ready)

    def test_lazy_vs_eager_startup_comparison(self):
        """Compare lazy vs eager loading startup times."""

        # Simulate eager loading (model loaded at init)
        def eager_loading():
            start = time.time()
            mgr = SpeechRecognitionManager(engine="vosk", model_size="small")
            # Simulate eager loading by calling _ensure_model_loaded
            mgr._ensure_model_loaded()
            return time.time() - start

        # Measure lazy loading
        lazy_start = time.time()
        lazy_manager = SpeechRecognitionManager(engine="vosk", model_size="small")
        lazy_init_time = time.time() - lazy_start

        # Lazy initialization should be much faster than model loading
        self.assertLess(
            lazy_init_time, 0.1, f"Lazy init took {lazy_init_time:.3f}s, expected < 0.1s"
        )


class TestLazyLoadingIntegration(unittest.TestCase):
    """Integration tests for lazy loading with recognition workflow."""

    def setUp(self):
        """Set up for tests."""
        self.mockModel = patch.object(sys.modules["vosk"], "Model")
        self.mockKaldi = patch.object(sys.modules["vosk"], "KaldiRecognizer")
        self.mockMakeDirs = patch("os.makedirs")
        self.mockPath = patch.object(SpeechRecognitionManager, "_get_vosk_model_path")
        self.mockDownload = patch.object(SpeechRecognitionManager, "_download_vosk_model")
        self.mockThread = patch("threading.Thread")

        self.modelMock = self.mockModel.start()
        self.kaldiMock = self.mockKaldi.start()
        self.makeDirsMock = self.mockMakeDirs.start()
        self.pathMock = self.mockPath.start()
        self.downloadMock = self.mockDownload.start()
        self.threadMock = self.mockThread.start()

        self.recognizerMock = MagicMock()
        self.kaldiMock.return_value = self.recognizerMock
        self.pathMock.return_value = "/mock/path/vosk-model"
        self.recognizerMock.FinalResult.return_value = '{"text": "hello world"}'

        self.threadInstance = MagicMock()
        self.threadMock.return_value = self.threadInstance

    def tearDown(self):
        """Clean up after tests."""
        self.mockModel.stop()
        self.kaldiMock.stop()
        self.mockMakeDirs.stop()
        self.mockPath.stop()
        self.mockDownload.stop()
        self.mockThread.stop()

    def test_model_loaded_when_recognition_starts(self):
        """Test that model is loaded when start_recognition is called."""
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        # Model not loaded yet
        self.assertFalse(manager.model_ready)
        self.modelMock.assert_not_called()

        # Start recognition
        manager.start_recognition()

        # Model should now be loaded (or at least attempted)
        self.modelMock.assert_called_once()
        self.assertTrue(manager.model_ready)
        self.assertEqual(manager.state, RecognitionState.LISTENING)

    def test_reconfigure_resets_lazy_loading(self):
        """Test that reconfigure resets lazy loading state."""
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")

        # Load the model
        manager._ensure_model_loaded()
        self.assertTrue(manager.model_ready)
        self.modelMock.assert_called_once()

        # Reconfigure with different model
        manager.reconfigure(model_size="medium")

        # Model should be unloaded
        self.assertFalse(manager.model_ready)
        self.assertIsNone(manager.model)
        self.assertIsNone(manager.recognizer)

        # Loading again should use new configuration
        # (in real scenario, it would load the medium model)


if __name__ == "__main__":
    unittest.main()
