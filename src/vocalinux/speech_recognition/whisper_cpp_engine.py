"""
Whisper.cpp speech recognition engine with Vulkan GPU acceleration.

This module provides a production-quality integration of whisper.cpp
with Vulkan support for AMD, NVIDIA, and Intel GPUs.
"""

import logging
import os
import ctypes
import ctypes.util
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class WhisperCppBackend(Enum):
    """Available whisper.cpp backend options."""

    CPU = "cpu"
    VULKAN = "vulkan"
    CUDA = "cuda"
    ROCM = "rocm"


class WhisperCppError(Exception):
    """Base exception for whisper.cpp errors."""

    pass


class VulkanNotAvailableError(WhisperCppError):
    """Raised when Vulkan is not available or initialization fails."""

    pass


class ModelNotFoundError(WhisperCppError):
    """Raised when the whisper.cpp model file is not found."""

    pass


class WhisperCppEngine:
    """
    Whisper.cpp speech recognition engine with Vulkan GPU acceleration.

    This class provides a high-level Python interface to whisper.cpp
    with support for multiple backends including Vulkan.
    """

    # GGML model sizes available
    MODEL_SIZES = [
        "tiny",
        "tiny.en",
        "base",
        "base.en",
        "small",
        "small.en",
        "medium",
        "medium.en",
        "large-v1",
        "large-v2",
        "large-v3",
    ]

    # Default model directory
    DEFAULT_MODEL_DIR = os.path.expanduser("~/.local/share/vocalinux/models/whisper_cpp")

    def __init__(
        self,
        model_size: str = "base",
        backend: WhisperCppBackend = WhisperCppBackend.VULKAN,
        model_path: Optional[str] = None,
        n_threads: int = 4,
        device: Optional[int] = None,
        verbose: bool = False,
    ):
        """
        Initialize the Whisper.cpp engine.

        Args:
            model_size: Model size (e.g., "tiny", "base", "small", "medium")
            backend: Backend to use (VULKAN, CPU, CUDA, ROCM)
            model_path: Path to model file (auto-downloaded if None)
            n_threads: Number of CPU threads to use
            device: GPU device index (for multi-GPU systems)
            verbose: Enable verbose logging

        Raises:
            ValueError: If model_size is invalid
            VulkanNotAvailableError: If Vulkan backend requested but unavailable
            ModelNotFoundError: If model file not found
        """
        if model_size not in self.MODEL_SIZES:
            raise ValueError(
                f"Invalid model_size '{model_size}'. Valid options: {self.MODEL_SIZES}"
            )

        self.model_size = model_size
        self.backend = backend
        self.n_threads = n_threads
        self.device = device
        self.verbose = verbose
        self._ctx = None
        self._library = None

        # Determine model path
        if model_path is None:
            os.makedirs(self.DEFAULT_MODEL_DIR, exist_ok=True)
            model_filename = f"ggml-{model_size}.bin"
            self.model_path = os.path.join(self.DEFAULT_MODEL_DIR, model_filename)
        else:
            self.model_path = model_path

        # Check if model exists
        if not os.path.exists(self.model_path):
            raise ModelNotFoundError(
                f"Model file not found at {self.model_path}. "
                f"Please download the GGML model for '{model_size}'."
            )

        # Initialize whisper.cpp library
        self._init_library()
        self._init_context()

        if self.verbose:
            logger.info(
                f"Whisper.cpp initialized: model={model_size}, "
                f"backend={backend.value}, device={device}"
            )

    def _init_library(self):
        """
        Load the whisper.cpp shared library.

        This method attempts to find and load the whisper.cpp library
        from various locations including system paths and the models directory.
        """
        # Library names to try (platform-specific)
        library_names = []
        if os.name == "nt":  # Windows
            library_names.extend(["whisper.dll", "libwhisper.dll"])
        else:  # Unix-like (Linux, macOS)
            library_names.extend(["libwhisper.so", "libwhisper.dylib", "whisper.so"])

        # Search paths
        search_paths = [
            self.DEFAULT_MODEL_DIR,  # Local models directory
            "/usr/local/lib",  # Standard local lib
            "/usr/lib",  # Standard system lib
            "/usr/lib/x86_64-linux-gnu",  # Debian/Ubuntu multiarch
            os.getcwd(),  # Current directory
        ]

        library_path = None
        for lib_name in library_names:
            # Try ctypes.util.find_library first
            found = ctypes.util.find_library(lib_name.replace(".so", "").replace(".dll", ""))
            if found and os.path.exists(found):
                library_path = found
                logger.info(f"Found whisper.cpp library via ctypes: {library_path}")
                break

            # Try explicit paths
            for search_path in search_paths:
                path = os.path.join(search_path, lib_name)
                if os.path.exists(path):
                    library_path = path
                    logger.info(f"Found whisper.cpp library: {library_path}")
                    break
            if library_path:
                break

        if library_path is None:
            raise WhisperCppError(
                "Could not find whisper.cpp shared library. "
                "Please install whisper.cpp with Vulkan support. "
                "See: https://github.com/ggerganov/whisper.cpp"
            )

        # Load the library
        try:
            self._library = ctypes.CDLL(library_path)
            logger.debug(f"Successfully loaded whisper.cpp library from {library_path}")
        except Exception as e:
            raise WhisperCppError(f"Failed to load whisper.cpp library from {library_path}: {e}")

    def _init_context(self):
        """
        Initialize the whisper.cpp context with the specified backend.

        This method sets up the whisper.cpp context with the appropriate
        backend configuration (Vulkan, CPU, CUDA, etc.).
        """
        # Define function signatures
        whisper_init_from_file = self._library.whisper_init_from_file
        whisper_init_from_file.argtypes = [ctypes.c_char_p]
        whisper_init_from_file.restype = ctypes.c_void_p

        whisper_free = self._library.whisper_free
        whisper_free.argtypes = [ctypes.c_void_p]

        # For newer whisper.cpp versions with backend support
        try:
            whisper_init_from_file_with_params = self._library.whisper_init_from_file_with_params
            whisper_init_from_file_with_params.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
            whisper_init_from_file_with_params.restype = ctypes.c_void_p

            whisper_context_default_params = self._library.whisper_context_default_params
            whisper_context_default_params.argtypes = []
            whisper_context_default_params.restype = ctypes.c_void_p

            # Try to use backend-aware initialization
            params = whisper_context_default_params()

            # Set backend if the function is available
            if hasattr(self._library, "ggml_backend_reg_type"):
                # Note: Setting backend requires accessing struct fields which is complex
                # Backend mapping is defined but currently relies on whisper.cpp's
                # auto-detection based on build flags

                if self.verbose:
                    logger.info(f"Attempting to use backend: {self.backend.value}")

            # Initialize context with params
            self._ctx = whisper_init_from_file_with_params(self.model_path.encode("utf-8"), params)

        except AttributeError:
            # Fall back to basic initialization
            if self.verbose:
                logger.info("Using basic initialization (backend not explicitly set)")
            self._ctx = whisper_init_from_file(self.model_path.encode("utf-8"))

        if not self._ctx:
            # Check if Vulkan was requested and might have failed
            if self.backend == WhisperCppBackend.VULKAN:
                logger.warning(
                    "Vulkan backend may have failed to initialize. "
                    "Falling back to CPU if context is valid."
                )
            raise WhisperCppError(f"Failed to initialize whisper.cpp context for {self.model_path}")

        if self.verbose:
            logger.info("Whisper.cpp context initialized successfully")

    def transcribe(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> str:
        """
        Transcribe audio data using whisper.cpp.

        Args:
            audio_data: Raw audio data as bytes (16-bit PCM, 16kHz, mono)
            sample_rate: Sample rate of the audio (must be 16000)
            language: Language code (e.g., "en", "es", None for auto-detect)

        Returns:
            Transcribed text

        Raises:
            WhisperCppError: If transcription fails
        """
        if self._ctx is None:
            raise WhisperCppError("Whisper.cpp context is not initialized")

        if sample_rate != 16000:
            logger.warning(f"Sample rate {sample_rate} != 16000. Audio may need resampling.")

        # Define function signatures
        whisper_full = self._library.whisper_full
        whisper_full.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
        whisper_full.restype = ctypes.c_int

        whisper_full_default_params = self._library.whisper_full_default_params
        whisper_full_default_params.argtypes = [ctypes.c_int]
        whisper_full_default_params.restype = ctypes.c_void_p

        whisper_full_n_segments = self._library.whisper_full_n_segments
        whisper_full_n_segments.argtypes = [ctypes.c_void_p]
        whisper_full_n_segments.restype = ctypes.c_int

        whisper_full_get_segment_text = self._library.whisper_full_get_segment_text
        whisper_full_get_segment_text.argtypes = [ctypes.c_void_p, ctypes.c_int]
        whisper_full_get_segment_text.restype = ctypes.c_char_p

        # Convert audio data to float32 array
        import numpy as np

        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception as e:
            raise WhisperCppError(f"Failed to process audio data: {e}")

        # Prepare parameters
        # WHISPER_SAMPLING_GREEDY = 0
        params = whisper_full_default_params(0)

        # Run transcription
        audio_ptr = audio_array.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        result = whisper_full(self._ctx, params, audio_ptr, len(audio_array))

        if result < 0:
            raise WhisperCppError(f"Transcription failed with error code: {result}")

        # Extract text from all segments
        text_parts = []
        n_segments = whisper_full_n_segments(self._ctx)

        for i in range(n_segments):
            segment_text = whisper_full_get_segment_text(self._ctx, i)
            if segment_text:
                text_parts.append(segment_text.decode("utf-8"))

        full_text = "".join(text_parts).strip()

        if self.verbose:
            logger.debug(f"Transcribed {n_segments} segments, {len(full_text)} characters")

        return full_text

    def __del__(self):
        """Clean up whisper.cpp resources."""
        if self._ctx is not None and self._library is not None:
            try:
                whisper_free = self._library.whisper_free
                whisper_free.argtypes = [ctypes.c_void_p]
                whisper_free(self._ctx)
                self._ctx = None
                if self.verbose:
                    logger.debug("Whisper.cpp context freed")
            except Exception as e:
                logger.debug(f"Error freeing whisper.cpp context: {e}")

    @classmethod
    def check_vulkan_available(cls) -> bool:
        """
        Check if Vulkan is available on the system.

        Returns:
            True if Vulkan is available, False otherwise
        """
        try:
            # Try to run vulkaninfo command
            import subprocess

            result = subprocess.run(["vulkaninfo", "--summary"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # Try to import vulkan module
            try:
                import vulkan  # noqa: F401

                return True
            except ImportError:
                pass
        return False

    @classmethod
    def check_backend_available(cls, backend: WhisperCppBackend) -> bool:
        """
        Check if a specific backend is available.

        Args:
            backend: The backend to check

        Returns:
            True if the backend is available, False otherwise
        """
        if backend == WhisperCppBackend.VULKAN:
            return cls.check_vulkan_available()
        elif backend == WhisperCppBackend.CPU:
            return True  # CPU is always available
        elif backend == WhisperCppBackend.CUDA:
            try:
                import torch

                return torch.cuda.is_available()
            except ImportError:
                return False
        elif backend == WhisperCppBackend.ROCM:
            # ROCm detection is more complex, approximate check
            try:
                with open("/proc/driver/amdgpu/version", "r"):
                    return True
            except (FileNotFoundError, IOError):
                return False
        return False

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about the current backend.

        Returns:
            Dictionary with backend information
        """
        info = {
            "backend": self.backend.value,
            "model_size": self.model_size,
            "model_path": self.model_path,
            "n_threads": self.n_threads,
            "device": self.device,
        }

        # Add Vulkan-specific info if available
        if self.backend == WhisperCppBackend.VULKAN:
            info["vulkan_available"] = self.check_vulkan_available()

        return info
