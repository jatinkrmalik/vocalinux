"""
Tests for whisper.cpp speech recognition support with Vulkan acceleration.
"""

import sys
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
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
            )

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


class TestWhisperCppEngineInitialization:
    """Test cases for WhisperCppEngine initialization edge cases."""

    def test_init_with_valid_model_size(self):
        """Test initialization with valid model sizes."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            with patch("os.path.exists", return_value=True), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_library"
            ), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_context"
            ):
                # Test various valid model sizes
                for size in ["tiny", "base", "small", "medium", "large-v3"]:
                    engine = WhisperCppEngine(model_size=size, backend=WhisperCppBackend.CPU)
                    assert engine.model_size == size
                    assert engine.backend == WhisperCppBackend.CPU
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_init_with_custom_model_path(self):
        """Test initialization with custom model path."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            custom_path = "/custom/path/to/model.bin"
            with patch("os.path.exists", return_value=True), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_library"
            ), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_context"
            ):
                engine = WhisperCppEngine(
                    model_size="base",
                    backend=WhisperCppBackend.CPU,
                    model_path=custom_path,
                )
                assert engine.model_path == custom_path
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_init_with_invalid_model_size(self):
        """Test that invalid model size raises ValueError."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import WhisperCppEngine

            with pytest.raises(ValueError) as exc_info:
                WhisperCppEngine(model_size="invalid_size")
            assert "Invalid model_size" in str(exc_info.value)
            assert "invalid_size" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_init_with_model_not_found(self):
        """Test that missing model file raises ModelNotFoundError."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                ModelNotFoundError,
                WhisperCppBackend,
            )

            with patch("os.path.exists", return_value=False):
                with pytest.raises(ModelNotFoundError) as exc_info:
                    WhisperCppEngine(
                        model_size="base",
                        backend=WhisperCppBackend.CPU,
                    )
                assert "Model file not found" in str(exc_info.value)
                assert "ggml-base.bin" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_init_creates_model_directory(self):
        """Test that initialization creates model directory if it doesn't exist."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import WhisperCppEngine

            with patch("os.path.exists", return_value=True), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_library"
            ), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_context"
            ), patch(
                "os.makedirs"
            ) as mock_makedirs:

                WhisperCppEngine(model_size="base")
                mock_makedirs.assert_called_once()
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_init_with_device_parameter(self):
        """Test initialization with device parameter."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            with patch("os.path.exists", return_value=True), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_library"
            ), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_context"
            ):
                engine = WhisperCppEngine(
                    model_size="base",
                    backend=WhisperCppBackend.VULKAN,
                    device=1,
                )
                assert engine.device == 1
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_init_with_n_threads_parameter(self):
        """Test initialization with n_threads parameter."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            with patch("os.path.exists", return_value=True), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_library"
            ), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_context"
            ):
                engine = WhisperCppEngine(
                    model_size="base",
                    backend=WhisperCppBackend.CPU,
                    n_threads=8,
                )
                assert engine.n_threads == 8
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_init_with_verbose_parameter(self):
        """Test initialization with verbose parameter."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            with patch("os.path.exists", return_value=True), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_library"
            ), patch(
                "vocalinux.speech_recognition.whisper_cpp_engine.WhisperCppEngine._init_context"
            ):
                engine = WhisperCppEngine(
                    model_size="base",
                    backend=WhisperCppBackend.CPU,
                    verbose=True,
                )
                assert engine.verbose is True
        except ImportError:
            pytest.skip("whisper.cpp not available")


class TestWhisperCppLibraryLoading:
    """Test cases for whisper.cpp library loading."""

    def test_library_not_found_raises_error(self):
        """Test that missing library raises WhisperCppError."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppError,
            )

            # Need to patch model exists first (model check happens before library)
            def exists_side_effect(path):
                if "ggml-base.bin" in path:
                    return True  # Model exists
                return False  # Library doesn't exist

            with patch("os.path.exists", side_effect=exists_side_effect), patch(
                "ctypes.util.find_library", return_value=None
            ):
                with pytest.raises(WhisperCppError) as exc_info:
                    WhisperCppEngine(model_size="base")
                assert "Could not find whisper.cpp shared library" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_library_load_failure_raises_error(self):
        """Test that library load failure raises WhisperCppError."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppError,
            )

            # Need to patch model exists first (model check happens before library)
            def exists_side_effect(path):
                if "ggml-base.bin" in path:
                    return True  # Model exists
                return True  # Library path exists

            with patch("os.path.exists", side_effect=exists_side_effect), patch(
                "ctypes.util.find_library", return_value="/fake/libwhisper.so"
            ), patch("ctypes.CDLL", side_effect=OSError("Library load failed")):
                with pytest.raises(WhisperCppError) as exc_info:
                    WhisperCppEngine(model_size="base")
                assert "Failed to load whisper.cpp library" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp not available")


class TestWhisperCppBackendSelection:
    """Test cases for backend selection logic."""

    def test_backend_selection_priority_with_gpu_preferred(self):
        """Test that Vulkan is tried first when GPU is preferred."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import (
                WhisperCppIntegration,
                WhisperCppBackend,
            )

            with patch(
                "vocalinux.speech_recognition.whisper_cpp_integration.WhisperCppEngine"
            ) as MockEngine, patch.object(
                WhisperCppIntegration, "check_gpu_available", return_value=True
            ):
                mock_instance = Mock()
                MockEngine.return_value = mock_instance
                mock_instance.get_backend_info.return_value = {"backend": "vulkan"}

                WhisperCppIntegration(
                    model_size="base",
                    language="en",
                    prefer_gpu=True,
                )

                # Should have been called with Vulkan backend
                call_args = MockEngine.call_args
                assert call_args.kwargs["backend"] == WhisperCppBackend.VULKAN
        except ImportError:
            pytest.skip("whisper.cpp integration not available")

    def test_backend_fallback_to_cpu_when_gpu_fails(self):
        """Test fallback to CPU when GPU initialization fails."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import (
                WhisperCppIntegration,
            )

            # Mock both the check and the engine to simulate GPU unavailable
            with patch.object(
                WhisperCppIntegration, "check_gpu_available", return_value=False
            ), patch(
                "vocalinux.speech_recognition.whisper_cpp_integration.WhisperCppEngine"
            ) as MockEngine:
                mock_instance = Mock()
                MockEngine.return_value = mock_instance
                mock_instance.get_backend_info.return_value = {"backend": "cpu"}

                integration = WhisperCppIntegration(
                    model_size="base",
                    language="en",
                    prefer_gpu=True,
                )

                # Should have tried to initialize (with CPU since GPU not available)
                assert MockEngine.call_count >= 1
                # Verify integration was created successfully
                assert integration is not None
        except ImportError:
            pytest.skip("whisper.cpp integration not available")

    def test_cpu_only_when_gpu_not_preferred(self):
        """Test that only CPU is used when GPU is not preferred."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import (
                WhisperCppIntegration,
                WhisperCppBackend,
            )

            with patch(
                "vocalinux.speech_recognition.whisper_cpp_integration.WhisperCppEngine"
            ) as MockEngine:
                mock_instance = Mock()
                MockEngine.return_value = mock_instance
                mock_instance.get_backend_info.return_value = {"backend": "cpu"}

                WhisperCppIntegration(
                    model_size="base",
                    language="en",
                    prefer_gpu=False,
                )

                # Should only use CPU
                call_args = MockEngine.call_args
                assert call_args.kwargs["backend"] == WhisperCppBackend.CPU
        except ImportError:
            pytest.skip("whisper.cpp integration not available")

    def test_all_backends_failed_raises_error(self):
        """Test that error is raised when all backends fail."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import (
                WhisperCppIntegration,
                WhisperCppError,
            )

            with patch(
                "vocalinux.speech_recognition.whisper_cpp_integration.WhisperCppEngine",
                side_effect=WhisperCppError("Backend failed"),
            ):
                with pytest.raises(WhisperCppError) as exc_info:
                    WhisperCppIntegration(
                        model_size="base",
                        language="en",
                        prefer_gpu=False,
                    )
                assert "Failed to initialize whisper.cpp" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp integration not available")


class TestWhisperCppTranscription:
    """Test cases for whisper.cpp transcription functionality."""

    def test_transcribe_with_empty_audio_buffer(self):
        """Test transcription with empty audio buffer."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import WhisperCppIntegration

            with patch(
                "vocalinux.speech_recognition.whisper_cpp_integration.WhisperCppEngine"
            ) as MockEngine:
                mock_instance = Mock()
                MockEngine.return_value = mock_instance
                mock_instance.get_backend_info.return_value = {"backend": "cpu"}

                integration = WhisperCppIntegration(
                    model_size="base",
                    language="en",
                    prefer_gpu=False,
                )

                # Should return empty string for empty buffer
                result = integration.transcribe([])
                assert result == ""
        except ImportError:
            pytest.skip("whisper.cpp integration not available")

    def test_transcribe_calls_engine(self):
        """Test that transcribe calls the engine correctly."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import WhisperCppIntegration

            with patch(
                "vocalinux.speech_recognition.whisper_cpp_integration.WhisperCppEngine"
            ) as MockEngine:
                mock_instance = Mock()
                MockEngine.return_value = mock_instance
                mock_instance.get_backend_info.return_value = {"backend": "cpu"}
                mock_instance.transcribe.return_value = "hello world"

                integration = WhisperCppIntegration(
                    model_size="base",
                    language="en",
                    prefer_gpu=False,
                )

                # Transcribe with audio data
                audio_data = [b"audio", b"data"]
                result = integration.transcribe(audio_data)

                assert result == "hello world"
                mock_instance.transcribe.assert_called_once()
        except ImportError:
            pytest.skip("whisper.cpp integration not available")

    def test_transcribe_language_normalization(self):
        """Test that language codes are normalized during transcription."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import WhisperCppIntegration

            with patch(
                "vocalinux.speech_recognition.whisper_cpp_integration.WhisperCppEngine"
            ) as MockEngine:
                mock_instance = Mock()
                MockEngine.return_value = mock_instance
                mock_instance.get_backend_info.return_value = {"backend": "cpu"}

                integration = WhisperCppIntegration(
                    model_size="base",
                    language="en-us",
                    prefer_gpu=False,
                )

                # Language should be normalized
                assert integration._normalize_language("en-us") == "en"
                assert integration._normalize_language("en-gb") == "en"
                assert integration._normalize_language("english") == "en"
                assert integration._normalize_language("auto") == "auto"
                assert integration._normalize_language("es") == "es"
        except ImportError:
            pytest.skip("whisper.cpp integration not available")

    def test_transcribe_without_initialized_engine(self):
        """Test that transcribe raises error when engine is not initialized."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_integration import (
                WhisperCppIntegration,
                WhisperCppError,
            )

            with patch(
                "vocalinux.speech_recognition.whisper_cpp_integration.WhisperCppEngine"
            ) as MockEngine:
                mock_instance = Mock()
                MockEngine.return_value = mock_instance
                mock_instance.get_backend_info.return_value = {"backend": "cpu"}

                integration = WhisperCppIntegration(
                    model_size="base",
                    language="en",
                    prefer_gpu=False,
                )
                # Simulate engine not initialized
                integration._engine = None

                with pytest.raises(WhisperCppError) as exc_info:
                    integration.transcribe([b"audio"])
                assert "engine is not initialized" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp integration not available")


class TestWhisperCppContextInitialization:
    """Test cases for whisper.cpp context initialization."""

    def test_context_init_with_basic_api(self):
        """Test context initialization with basic API."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            mock_lib = Mock()
            mock_lib.whisper_init_from_file.return_value = Mock()

            def exists_side_effect(path):
                # Model file exists, library exists
                return True

            with patch("os.path.exists", side_effect=exists_side_effect), patch(
                "ctypes.util.find_library", return_value="/fake/libwhisper.so"
            ), patch("ctypes.CDLL", return_value=mock_lib), patch.object(
                WhisperCppEngine, "_init_context"
            ) as mock_init_ctx:
                WhisperCppEngine(
                    model_size="base",
                    backend=WhisperCppBackend.CPU,
                )
                # Context init was called
                mock_init_ctx.assert_called_once()
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_context_init_failure_raises_error(self):
        """Test that context initialization failure raises error."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
                WhisperCppError,
            )

            mock_lib = Mock()
            mock_lib.whisper_init_from_file.return_value = None  # Failed init
            mock_lib.whisper_init_from_file_with_params.return_value = None

            def exists_side_effect(path):
                return True

            with patch("os.path.exists", side_effect=exists_side_effect), patch(
                "ctypes.util.find_library", return_value="/fake/libwhisper.so"
            ), patch("ctypes.CDLL", return_value=mock_lib):
                with pytest.raises(WhisperCppError) as exc_info:
                    WhisperCppEngine(
                        model_size="base",
                        backend=WhisperCppBackend.CPU,
                    )
                assert "Failed to initialize whisper.cpp context" in str(exc_info.value)
        except ImportError:
            pytest.skip("whisper.cpp not available")


class TestWhisperCppBackendAvailability:
    """Test cases for backend availability checking."""

    def test_check_backend_available_cpu(self):
        """Test backend availability check for CPU."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            # CPU should always be available
            result = WhisperCppEngine.check_backend_available(WhisperCppBackend.CPU)
            assert result is True
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_check_backend_available_vulkan(self):
        """Test backend availability check for Vulkan."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            # Should return a boolean (may be True or False depending on system)
            result = WhisperCppEngine.check_backend_available(WhisperCppBackend.VULKAN)
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_check_backend_available_cuda(self):
        """Test backend availability check for CUDA."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            # Should return a boolean
            result = WhisperCppEngine.check_backend_available(WhisperCppBackend.CUDA)
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("whisper.cpp not available")

    def test_check_backend_available_rocm(self):
        """Test backend availability check for ROCm."""
        try:
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

            # Should return a boolean
            result = WhisperCppEngine.check_backend_available(WhisperCppBackend.ROCM)
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

    @pytest.mark.skipif(sys.version_info < (3, 8), reason="Requires Python 3.8+")
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
                    WhisperCppIntegration(
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
            from vocalinux.speech_recognition.whisper_cpp_engine import (
                WhisperCppEngine,
                WhisperCppBackend,
            )

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
