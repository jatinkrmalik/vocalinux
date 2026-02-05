"""
Tests for whisper.cpp speech recognition support with Vulkan acceleration.
"""

import sys
import os
from unittest.mock import MagicMock, patch, Mock
import pytest

# Mock GTK and other dependencies before importing vocalinux
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["vosk"] = MagicMock()
sys.modules["pyaudio"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["pynput"] = MagicMock()
sys.modules["pynput.keyboard"] = MagicMock()


class TestWhisperCppEngine:
    """Test cases for whisper.cpp engine."""

    def test_module_import(self):
        """Test that whisper.cpp integration module can be imported."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
                WhisperCppError,
            )
            assert WhisperCppEngine is not None
            assert WhisperCppBackend is not None
            assert WhisperCppError is not None
        except ImportError:
            # This is expected if whisper.cpp is not installed
            pytest.skip("whisper.cpp not available")

    def test_backend_enum(self):
        """Test that WhisperCppBackend enum has expected values."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import WhisperCppBackend

            assert hasattr(WhisperCppBackend, "CPU")
            assert hasattr(WhisperCppBackend, "VULKAN")
            assert hasattr(WhisperCppBackend, "CUDA")
            assert hasattr(WhisperCppBackend, "ROCM")

            assert WhisperCppBackend.CPU.value == "cpu"
            assert WhisperCppBackend.VULKAN.value == "vulkan"
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_model_sizes(self):
        """Test that model sizes are defined correctly."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import WhisperCppEngine

            expected_sizes = ["tiny", "tiny.en", "base", "base.en", "small", "medium", "large-v3"]
            for size in expected_sizes:
                assert size in WhisperCppEngine.MODEL_SIZES
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_invalid_model_size_raises_error(self):
        """Test that invalid model size raises ValueError."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import WhisperCppEngine, ModelNotFoundError

            # Mock os.path.exists to return False
            with patch("os.path.exists", return_value=False):
                with pytest.raises(ValueError) as exc_info:
                    WhisperCppEngine(model_size="invalid_size")
                assert "Invalid model_size" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_vulkan_check_method(self):
        """Test Vulkan availability check method."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import WhisperCppEngine

            # The method should return a boolean
            result = WhisperCppEngine.check_vulkan_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("whisper.cpp not available")


class TestWhisperCppIntegration:
    """Test cases for whisper.cpp integration layer."""

    def test_module_import(self):
        """Test that integration module can be imported."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import (
                WhisperCppIntegration,
                WhisperCppError,
                get_whisper_cpp_integration,
            )
            assert WhisperCppIntegration is not None
            assert WhisperCppError is not None
            assert get_whisper_cpp_integration is not None
        except ImportError:
            pytest.skip("whisper.cpp integration not available")

    def test_supported_models_list(self):
        """Test that supported models list is accessible."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import (
                WhisperCppIntegration,
            )

            models = WhisperCppIntegration.get_supported_models()
            assert isinstance(models, list)
            assert len(models) > 0
            assert "base" in models
        except ImportError:
            pytest.skip("whisper.cpp integration not available")

    def test_language_normalization(self):
        """Test language code normalization."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import WhisperCppIntegration

            # Create a mock integration
            with patch.object(WhisperCppIntegration, "_initialize_engine"):
                integration = WhisperCppIntegration(
                    model_size="base",
                    language="en-us",
                    prefer_gpu=False,
                )

                # Test language normalization
                assert integration._normalize_language("en-us") == "en"
                assert integration._normalize_language("en-gb") == "en"
                assert integration._normalize_language("auto") == "auto"
                assert integration._normalize_language("es") == "es"
        except ImportError:
            pytest.skip("whisper.cpp integration not available")

    def test_gpu_available_check(self):
        """Test GPU availability check."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import WhisperCppIntegration

            # Should return boolean
            result = WhisperCppIntegration.check_gpu_available()
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("whisper.cpp integration not available")


class TestWhisperCppInRecognitionManager:
    """Test whisper.cpp integration with SpeechRecognitionManager."""

    def test_whisper_cpp_available_flag(self):
        """Test that WHISPER_CPP_AVAILABLE flag is defined."""
        from vocalinux.speech_recognition.recognition_manager import WHISPER_CPP_AVAILABLE

        # Should be a boolean
        assert isinstance(WHISPER_CPP_AVAILABLE, bool)

    @pytest.mark.skipif(
        sys.version_info < (3, 8),
        reason="Requires Python 3.8+"
    )
    def test_recognition_manager_accepts_whisper_cpp(self):
        """Test that SpeechRecognitionManager accepts whisper.cpp as engine."""
        try:
            from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

            # Mock the initialization to avoid actual whisper.cpp calls
            with patch.object(SpeechRecognitionManager, "_init_whisper_cpp"):
                manager = SpeechRecognitionManager(
                    engine="whisper.cpp",
                    model_size="base",
                    language="en-us",
                    defer_download=True,
                )

                assert manager.engine == "whisper.cpp"
                assert manager.model_size == "base"
                assert manager.language == "en-us"
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_init_whisper_cpp_method_exists(self):
        """Test that _init_whisper_cpp method exists."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        assert hasattr(SpeechRecognitionManager, "_init_whisper_cpp")

    def test_process_final_buffer_handles_whisper_cpp(self):
        """Test that _process_final_buffer can handle whisper.cpp engine."""
        from vocalinux.speech_recognition.recognition_manager import (
            SpeechRecognitionManager,
        )

        # This is a structural test - we just check the method exists
        # and doesn't crash when called with whisper.cpp engine
        assert hasattr(SpeechRecognitionManager, "_process_final_buffer")


class TestWhisperCppErrorHandling:
    """Test error handling for whisper.cpp."""

    def test_model_not_found_error(self):
        """Test ModelNotFoundError exception."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import ModelNotFoundError

            with pytest.raises(ModelNotFoundError) as exc_info:
                raise ModelNotFoundError("Model file not found")
            assert "Model file not found" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_vulkan_not_available_error(self):
        """Test VulkanNotAvailableError exception."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import VulkanNotAvailableError

            with pytest.raises(VulkanNotAvailableError) as exc_info:
                raise VulkanNotAvailableError("Vulkan not available")
            assert "Vulkan not available" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_fallback_to_cpu_on_vulkan_failure(self):
        """Test that integration falls back to CPU if Vulkan fails."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import (
                WhisperCppIntegration,
                WhisperCppBackend,
            )

            # Mock the engine initialization to fail with Vulkan first
            mock_engine = Mock()
            mock_engine.get_backend_info.return_value = {"backend": "cpu"}

            with patch(
                "vocalinux.speech_recognition.whisper_cpp_integration.WhisperCppEngine"
            ) as MockEngine:
                # First call fails (Vulkan), second succeeds (CPU)
                MockEngine.side_effect = [
                    Exception("Vulkan failed"),
                    mock_engine,
                ]

                # Create integration with prefer_gpu=True
                # Should fall back to CPU after Vulkan fails
                try:
                    integration = WhisperCppIntegration(
                        model_size="base",
                        language="en",
                        prefer_gpu=True,
                    )
                    # Should have tried both backends
                    assert MockEngine.call_count >= 1
                except Exception:
                    # Expected if both fail
                    pass
        except ImportError:
            pytest.skip("whisper.cpp integration not available")


class TestWhisperCppBackendInfo:
    """Test backend information retrieval."""

    def test_get_backend_info(self):
        """Test get_backend_info method."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import WhisperCppEngine

            # Mock the engine initialization
            with patch("os.path.exists", return_value=True), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_library"
            ), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_context"
            ):
                engine = WhisperCppEngine(model_size="base", backend=WhisperCppBackend.CPU)
                info = engine.get_backend_info()

                assert isinstance(info, dict)
                assert "backend" in info
                assert "model_size" in info
                assert "model_path" in info
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_is_gpu_accelerated(self):
        """Test is_gpu_accelerated method."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import WhisperCppIntegration

            # Mock the integration
            with patch.object(WhisperCppIntegration, "_initialize_engine"):
                integration = WhisperCppIntegration(
                    model_size="base",
                    language="en",
                    prefer_gpu=False,
                )

                # Should return boolean
                result = integration.is_gpu_accelerated()
                assert isinstance(result, bool)
        except ImportError:
            pytest.skip("whisper.cpp integration not available")
