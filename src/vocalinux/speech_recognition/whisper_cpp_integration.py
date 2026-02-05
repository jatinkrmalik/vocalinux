"""
Integration layer for whisper.cpp with Vocalinux.

This module provides the glue code to integrate whisper.cpp
with the existing Vocalinux speech recognition architecture.
"""

import logging
from typing import Optional, List

from .whisper_cpp_engine import (
    WhisperCppEngine,
    WhisperCppBackend,
    WhisperCppError,
    VulkanNotAvailableError,
    ModelNotFoundError,
)

logger = logging.getLogger(__name__)


class WhisperCppIntegration:
    """
    Integration layer for whisper.cpp with Vocalinux.

    This class manages the whisper.cpp engine lifecycle and provides
    a consistent interface compatible with Vocalinux's SpeechRecognitionManager.
    """

    def __init__(
        self,
        model_size: str = "base",
        language: str = "en",
        prefer_gpu: bool = True,
        n_threads: int = 4,
        verbose: bool = False,
        **kwargs,
    ):
        """
        Initialize the whisper.cpp integration.

        Args:
            model_size: Model size (tiny, base, small, medium)
            language: Language code (en, es, auto, etc.)
            prefer_gpu: Whether to prefer GPU acceleration (Vulkan)
            n_threads: Number of CPU threads for CPU fallback
            verbose: Enable verbose logging
            **kwargs: Additional parameters (device index, etc.)
        """
        self.model_size = model_size
        self.language = language
        self.prefer_gpu = prefer_gpu
        self.n_threads = n_threads
        self.verbose = verbose
        self.device = kwargs.get("device", None)

        self._engine: Optional[WhisperCppEngine] = None
        self._backend_used: Optional[WhisperCppBackend] = None

        # Initialize the engine
        self._initialize_engine()

    def _initialize_engine(self):
        """
        Initialize the whisper.cpp engine with appropriate backend.

        This method tries to use the best available backend:
        1. Vulkan (GPU) if available and preferred
        2. CPU fallback
        """
        backends_to_try = []

        if self.prefer_gpu:
            backends_to_try.append(WhisperCppBackend.VULKAN)

        backends_to_try.append(WhisperCppBackend.CPU)

        last_error = None

        for backend in backends_to_try:
            try:
                logger.info(f"Attempting to initialize whisper.cpp with {backend.value} backend...")

                # Check if backend is available
                if not WhisperCppEngine.check_backend_available(backend):
                    logger.info(f"{backend.value} backend not available, trying next...")
                    continue

                # Initialize engine
                self._engine = WhisperCppEngine(
                    model_size=self.model_size,
                    backend=backend,
                    n_threads=self.n_threads,
                    device=self.device,
                    verbose=self.verbose,
                )

                self._backend_used = backend

                backend_info = self._engine.get_backend_info()
                logger.info(
                    f"Successfully initialized whisper.cpp with {backend.value} backend. "
                    f"Model: {self.model_size}"
                )

                if self.verbose:
                    logger.debug(f"Backend info: {backend_info}")

                return

            except ModelNotFoundError as e:
                # This is a user error - model file missing
                logger.error(f"Model file not found: {e}")
                raise
            except VulkanNotAvailableError as e:
                logger.warning(f"Vulkan not available: {e}")
                last_error = e
                continue
            except WhisperCppError as e:
                logger.warning(f"Failed to initialize {backend.value} backend: {e}")
                last_error = e
                continue
            except Exception as e:
                logger.warning(f"Unexpected error initializing {backend.value} backend: {e}")
                last_error = e
                continue

        # All backends failed
        error_msg = (
            f"Failed to initialize whisper.cpp with any available backend. "
            f"Tried: {[b.value for b in backends_to_try]}. "
            f"Last error: {last_error}"
        )
        logger.error(error_msg)
        raise WhisperCppError(error_msg)

    def transcribe(self, audio_buffer: List[bytes]) -> str:
        """
        Transcribe audio buffer using whisper.cpp.

        Args:
            audio_buffer: List of audio data chunks (16-bit PCM at 16kHz)

        Returns:
            Transcribed text

        Raises:
            WhisperCppError: If transcription fails
        """
        if self._engine is None:
            raise WhisperCppError("Whisper.cpp engine is not initialized")

        if not audio_buffer:
            logger.debug("Empty audio buffer, returning empty transcription")
            return ""

        # Combine audio chunks
        audio_data = b"".join(audio_buffer)

        try:
            # Normalize language code for whisper.cpp
            lang = self._normalize_language(self.language)

            # Transcribe
            text = self._engine.transcribe(
                audio_data=audio_data,
                sample_rate=16000,
                language=lang if lang != "auto" else None,
            )

            if text:
                logger.info(f"Whisper.cpp transcribed: '{text}'")
            else:
                logger.debug("Whisper.cpp returned empty transcription")

            return text

        except WhisperCppError as e:
            logger.error(f"Transcription error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            raise WhisperCppError(f"Transcription failed: {e}")

    def _normalize_language(self, language: str) -> str:
        """
        Normalize language codes for whisper.cpp.

        Args:
            language: Language code (e.g., "en-us", "en", "auto")

        Returns:
            Normalized language code
        """
        # Map Vocalinux language codes to whisper.cpp format
        lang_map = {
            "en-us": "en",
            "en-gb": "en",
            "english": "en",
            "auto": "auto",
        }

        # Check if already normalized
        if language in lang_map:
            return lang_map[language]
        elif language == "auto":
            return "auto"
        else:
            # Assume it's already a valid language code
            return language

    def get_backend_info(self) -> dict:
        """
        Get information about the current backend.

        Returns:
            Dictionary with backend information
        """
        if self._engine is None:
            return {"backend": "none", "engine_initialized": False}

        info = self._engine.get_backend_info()
        info["integration_language"] = self.language
        info["prefer_gpu"] = self.prefer_gpu
        info["engine_initialized"] = True

        return info

    def is_gpu_accelerated(self) -> bool:
        """
        Check if GPU acceleration is active.

        Returns:
            True if using GPU backend, False otherwise
        """
        return self._backend_used in [
            WhisperCppBackend.VULKAN,
            WhisperCppBackend.CUDA,
            WhisperCppBackend.ROCM,
        ]

    def cleanup(self):
        """Clean up resources."""
        if self._engine is not None:
            try:
                del self._engine
                self._engine = None
                logger.debug("Whisper.cpp engine cleaned up")
            except Exception as e:
                logger.debug(f"Error during cleanup: {e}")

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()

    @classmethod
    def get_supported_models(cls) -> List[str]:
        """Get list of supported model sizes."""
        return WhisperCppEngine.MODEL_SIZES

    @classmethod
    def check_gpu_available(cls) -> bool:
        """
        Check if any GPU backend is available.

        Returns:
            True if Vulkan or CUDA is available, False otherwise
        """
        return WhisperCppEngine.check_backend_available(
            WhisperCppBackend.VULKAN
        ) or WhisperCppEngine.check_backend_available(WhisperCppBackend.CUDA)


def get_whisper_cpp_integration(
    model_size: str = "base", language: str = "en", prefer_gpu: bool = True, **kwargs
) -> WhisperCppIntegration:
    """
    Factory function to create a WhisperCppIntegration instance.

    This function provides error handling and logging for initialization.

    Args:
        model_size: Model size (tiny, base, small, medium)
        language: Language code
        prefer_gpu: Whether to prefer GPU acceleration
        **kwargs: Additional parameters

    Returns:
        WhisperCppIntegration instance

    Raises:
        WhisperCppError: If initialization fails
    """
    try:
        integration = WhisperCppIntegration(
            model_size=model_size, language=language, prefer_gpu=prefer_gpu, **kwargs
        )
        return integration
    except Exception as e:
        logger.error(f"Failed to create whisper.cpp integration: {e}")
        raise
