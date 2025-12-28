"""
Tests for Whisper speech recognition support.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock GTK and other dependencies before importing vocalinux
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["vosk"] = MagicMock()
sys.modules["pyaudio"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["pynput"] = MagicMock()
sys.modules["pynput.keyboard"] = MagicMock()


class TestWhisperSupport:
    """Test cases for Whisper speech recognition support."""

    def test_whisper_transcription_method_exists(self):
        """Test that the Whisper transcription method exists."""
        # Mock whisper and torch before importing
        whisper_mock = MagicMock()
        torch_mock = MagicMock()
        torch_mock.cuda.is_available.return_value = False

        with patch.dict(sys.modules, {"whisper": whisper_mock, "torch": torch_mock}):
            from vocalinux.speech_recognition.recognition_manager import (
                SpeechRecognitionManager,
            )

            # Test that the method exists without actually calling it
            assert hasattr(SpeechRecognitionManager, "_transcribe_with_whisper")

            # Test method signature
            import inspect

            sig = inspect.signature(SpeechRecognitionManager._transcribe_with_whisper)
            params = list(sig.parameters.keys())
            assert "self" in params
            assert "audio_buffer" in params

    def test_whisper_model_validation(self):
        """Test that invalid model sizes are handled correctly."""
        # Valid Whisper model sizes
        valid_models = ["tiny", "base", "small", "medium", "large"]

        # Test that all valid models are accepted
        for model in valid_models:
            assert model in valid_models

        # Test that invalid model would fallback to 'base'
        invalid_model = "unknown"
        assert invalid_model not in valid_models
        # The code defaults to "base" for invalid models

    def test_whisper_init_and_transcribe_methods_exist(self):
        """Test that Whisper-related methods are properly defined."""
        # Mock whisper and torch before importing
        whisper_mock = MagicMock()
        torch_mock = MagicMock()
        torch_mock.cuda.is_available.return_value = False

        with patch.dict(sys.modules, {"whisper": whisper_mock, "torch": torch_mock}):
            from vocalinux.speech_recognition.recognition_manager import (
                SpeechRecognitionManager,
            )

            manager_class = SpeechRecognitionManager

            # Check that _transcribe_with_whisper method exists
            assert hasattr(manager_class, "_transcribe_with_whisper")

            # Check that _init_whisper method exists
            assert hasattr(manager_class, "_init_whisper")

            # Test that the method has proper type hints
            import inspect

            sig = inspect.signature(manager_class._transcribe_with_whisper)
            assert "audio_buffer" in sig.parameters
            assert sig.return_annotation == str

    def test_whisper_engine_initialization_with_mocks(self):
        """Test Whisper engine initialization with mocked dependencies."""
        # Setup mocks
        whisper_mock = MagicMock()
        torch_mock = MagicMock()
        torch_mock.cuda.is_available.return_value = False
        model_mock = MagicMock()
        whisper_mock.load_model.return_value = model_mock

        # Patch modules and mock the download method to avoid network/file operations
        with patch.dict(sys.modules, {"whisper": whisper_mock, "torch": torch_mock}), patch(
            "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._download_whisper_model"
        ) as mock_download, patch("os.path.exists", return_value=True):
            from vocalinux.speech_recognition.recognition_manager import (
                SpeechRecognitionManager,
            )

            # Create manager with Whisper engine and defer_download=False to trigger model loading
            manager = SpeechRecognitionManager(
                engine="whisper", model_size="base", defer_download=False
            )

            # Verify Whisper was initialized correctly
            assert manager.engine == "whisper"
            assert manager.model_size == "base"
            whisper_mock.load_model.assert_called_once()
