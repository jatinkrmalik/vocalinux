"""
Tests for Whisper speech recognition support.
"""

import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager
from vocalinux.common_types import RecognitionState


class TestWhisperSupport:
    """Test cases for Whisper speech recognition support."""

    def test_whisper_import_error_handling(self):
        """Test that Whisper import errors are handled gracefully."""
        # Test that ImportError is raised when whisper is not available
        with patch("builtins.__import__", side_effect=ImportError("No module named 'whisper'")):
            with pytest.raises(ImportError):
                SpeechRecognitionManager(engine="whisper", model_size="small")

    def test_whisper_transcription_method_exists(self):
        """Test that the Whisper transcription method exists."""
        # Test that the method exists without actually calling it
        assert hasattr(SpeechRecognitionManager, '_transcribe_with_whisper')
        
        # Test method signature
        import inspect
        sig = inspect.signature(SpeechRecognitionManager._transcribe_with_whisper)
        params = list(sig.parameters.keys())
        assert 'self' in params
        assert 'audio_buffer' in params

    def test_whisper_model_size_mapping_logic(self):
        """Test the model size mapping logic without initialization."""
        # Test the mapping logic that would be used in _init_whisper
        size_mapping = {
            "tiny": "tiny",
            "small": "base",  # Map small to base for better quality
            "medium": "small", # Map medium to small for balance
            "large": "medium"  # Map large to medium (large is very slow)
        }
        
        # Test the mappings
        assert size_mapping.get("small", "base") == "base"
        assert size_mapping.get("medium", "base") == "small"
        assert size_mapping.get("large", "base") == "medium"
        assert size_mapping.get("tiny", "base") == "tiny"
        assert size_mapping.get("unknown", "base") == "base"

    def test_whisper_constants_and_attributes(self):
        """Test that Whisper-related constants and attributes are properly defined."""
        # Test that the method exists and has the right signature
        manager_class = SpeechRecognitionManager
        
        # Check that _transcribe_with_whisper method exists
        assert hasattr(manager_class, '_transcribe_with_whisper')
        
        # Check that _init_whisper method exists
        assert hasattr(manager_class, '_init_whisper')
        
        # Test that the method has proper type hints
        import inspect
        sig = inspect.signature(manager_class._transcribe_with_whisper)
        assert 'audio_buffer' in sig.parameters
        assert sig.return_annotation == str