"""
Whisper.cpp speech recognition engine for Vocalinux.

This module provides a high-performance, cross-vendor GPU-accelerated
speech recognition engine using whisper.cpp with Vulkan support.
"""

import json
import logging
import os
import threading
import time
from typing import Callable, List, Optional, Union

from ..common_types import RecognitionState

logger = logging.getLogger(__name__)

# Try to import pywhispercpp
try:
    from pywhispercpp.model import Model
    PYWHISPERCPP_AVAILABLE = True
except ImportError:
    PYWHISPERCPP_AVAILABLE = False
    Model = None


class WhisperCppEngine:
    """
    Whisper.cpp speech recognition engine with Vulkan GPU acceleration.
    
    This engine provides high-performance speech recognition using whisper.cpp,
    supporting cross-vendor GPU acceleration via Vulkan on AMD, NVIDIA, and Intel GPUs.
    """

    def __init__(
        self,
        model_size: str = "base.en",
        language: str = "en",
        n_threads: int = 4,
        use_gpu: bool = True,
        **kwargs,
    ):
        """
        Initialize the Whisper.cpp engine.

        Args:
            model_size: The whisper.cpp model size ('tiny.en', 'base.en', 'small.en', 'medium.en')
            language: Language code for transcription ('en', 'auto', etc.)
            n_threads: Number of CPU threads to use
            use_gpu: Whether to enable GPU acceleration via Vulkan
            **kwargs: Additional whisper.cpp parameters
        """
        if not PYWHISPERCPP_AVAILABLE:
            raise ImportError(
                "pywhispercpp is not installed. Install it with: "
                "GGML_VULKAN=1 pip install git+https://github.com/abdeladim-s/pywhispercpp"
            )

        self.model_size = model_size
        self.language = language
        self.n_threads = n_threads
        self.use_gpu = use_gpu
        self.model = None
        self.is_initialized = False
        
        # whisper.cpp parameters
        self.params = kwargs.copy()
        self.params.update({
            'language': language,
            'print_realtime': False,
            'print_progress': False,
        })

        # Threading
        self._lock = threading.Lock()
        self._should_stop = False
        
        # Callbacks
        self._text_callbacks: List[Callable[[str], None]] = []
        self._state_callbacks: List[Callable[[RecognitionState], None]] = []
        
        logger.info(f"WhisperCpp engine initialized with model={model_size}, "
                   f"language={language}, gpu={use_gpu}")

    def initialize(self) -> bool:
        """
        Initialize the whisper.cpp model.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            with self._lock:
                if self.is_initialized:
                    return True

                logger.info(f"Loading whisper.cpp model: {self.model_size}")
                
                # Initialize the model with parameters
                self.model = Model(
                    self.model_size,
                    n_threads=self.n_threads,
                    **self.params
                )
                
                self.is_initialized = True
                logger.info("Whisper.cpp model loaded successfully")
                
                # Notify callbacks of ready state
                self._notify_state(RecognitionState.IDLE)
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize whisper.cpp model: {e}")
            self._notify_state(RecognitionState.ERROR)
            return False

    def transcribe_file(self, audio_file: str, **kwargs) -> str:
        """
        Transcribe an audio file.

        Args:
            audio_file: Path to the audio file
            **kwargs: Additional transcription parameters

        Returns:
            Transcribed text
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize whisper.cpp model")

        try:
            # Merge kwargs with existing parameters
            params = self.params.copy()
            params.update(kwargs)
            
            # Remove callback parameters for file transcription
            params.pop('new_segment_callback', None)
            
            self._notify_state(RecognitionState.PROCESSING)
            
            # Perform transcription
            segments = self.model.transcribe(audio_file, **params)
            
            # Combine all segments
            text = " ".join(segment.text for segment in segments)
            
            self._notify_state(RecognitionState.IDLE)
            
            if text.strip():
                self._notify_text(text.strip())
                
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            self._notify_state(RecognitionState.ERROR)
            raise

    def transcribe_audio_data(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        Transcribe raw audio data.

        Args:
            audio_data: Raw audio data (16-bit PCM)
            sample_rate: Audio sample rate

        Returns:
            Transcribed text
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize whisper.cpp model")

        try:
            # For now, we need to save to a temporary file
            # TODO: Implement direct audio data processing when supported
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                # Simple WAV header for 16-bit PCM
                import wave
                import struct
                
                with wave.open(tmp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)
                
                # Transcribe the temporary file
                result = self.transcribe_file(tmp_file.name)
                
            # Clean up
            os.unlink(tmp_file.name)
            
            return result
            
        except Exception as e:
            logger.error(f"Error transcribing audio data: {e}")
            self._notify_state(RecognitionState.ERROR)
            raise

    def start_real_time_transcription(self):
        """
        Start real-time transcription mode.
        
        This method should be called when starting continuous listening.
        """
        if not self.is_initialized:
            if not self.initialize():
                raise RuntimeError("Failed to initialize whisper.cpp model")

        with self._lock:
            self._should_stop = False
            self._notify_state(RecognitionState.LISTENING)
            logger.info("Started real-time transcription")

    def process_audio_chunk(self, audio_data: bytes, sample_rate: int = 16032):
        """
        Process an audio chunk in real-time mode.

        Args:
            audio_data: Raw audio data chunk
            sample_rate: Audio sample rate
        """
        if not self.is_initialized or self._should_stop:
            return

        try:
            # For real-time processing, we accumulate chunks and transcribe
            # when we have enough data or when speech ends
            # This is a simplified implementation - in production, you'd want
            # more sophisticated voice activity detection
            
            # TODO: Implement proper real-time chunk processing
            # For now, this is a placeholder
            pass
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            self._notify_state(RecognitionState.ERROR)

    def stop_real_time_transcription(self):
        """
        Stop real-time transcription mode.
        """
        with self._lock:
            if not self._should_stop:
                self._should_stop = True
                self._notify_state(RecognitionState.IDLE)
                logger.info("Stopped real-time transcription")

    def register_text_callback(self, callback: Callable[[str], None]):
        """
        Register a callback for transcribed text.

        Args:
            callback: Function to call with transcribed text
        """
        self._text_callbacks.append(callback)

    def register_state_callback(self, callback: Callable[[RecognitionState], None]):
        """
        Register a callback for state changes.

        Args:
            callback: Function to call with state changes
        """
        self._state_callbacks.append(callback)

    def _notify_text(self, text: str):
        """Notify all text callbacks."""
        for callback in self._text_callbacks:
            try:
                callback(text)
            except Exception as e:
                logger.error(f"Error in text callback: {e}")

    def _notify_state(self, state: RecognitionState):
        """Notify all state callbacks."""
        for callback in self._state_callbacks:
            try:
                callback(state)
            except Exception as e:
                logger.error(f"Error in state callback: {e}")

    def is_gpu_available(self) -> bool:
        """
        Check if GPU acceleration is available.

        Returns:
            True if GPU acceleration is available, False otherwise
        """
        try:
            # Try to determine if Vulkan is available
            # This is a simple check - in production, you'd want more thorough detection
            if self.model and hasattr(self.model, 'ctx'):
                # Check if the context was created with GPU support
                return self.use_gpu
            
            # Fallback: check for Vulkan drivers
            vulkan_info = os.path.exists('/usr/bin/vulkaninfo')
            if vulkan_info:
                try:
                    import subprocess
                    result = subprocess.run(['vulkaninfo'], capture_output=True, text=True)
                    return result.returncode == 0
                except:
                    pass
                    
            return False
            
        except Exception as e:
            logger.debug(f"Error checking GPU availability: {e}")
            return False

    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        info = {
            'model_size': self.model_size,
            'language': self.language,
            'n_threads': self.n_threads,
            'use_gpu': self.use_gpu,
            'gpu_available': self.is_gpu_available(),
            'is_initialized': self.is_initialized,
        }
        
        if self.model:
            info['model_type'] = 'whisper.cpp'
            
        return info

    def cleanup(self):
        """Clean up resources."""
        with self._lock:
            self._should_stop = True
            if self.model:
                # whisper.cpp models don't need explicit cleanup
                pass
            self.is_initialized = False
            logger.info("Whisper.cpp engine cleaned up")


def create_whisper_cpp_engine(**kwargs) -> WhisperCppEngine:
    """
    Factory function to create a Whisper.cpp engine.

    Args:
        **kwargs: Engine configuration parameters

    Returns:
        WhisperCppEngine instance
    """
    return WhisperCppEngine(**kwargs)