"""
Enhanced speech recognition manager with streaming support for Vocalinux.

This module extends the original recognition manager to include real-time
streaming capabilities with lower latency for both VOSK and Whisper engines.
"""

import json
import logging
import os
import threading
import time
from typing import Callable, List, Optional, Dict, Any

from ..common_types import RecognitionState
from ..ui.audio_feedback import play_error_sound, play_start_sound, play_stop_sound
from ..utils.vosk_model_info import VOSK_MODEL_INFO
from .command_processor import CommandProcessor
from .streaming_recognizer import StreamingSpeechRecognizer

logger = logging.getLogger(__name__)


# Define constants
MODELS_DIR = os.path.expanduser("~/.local/share/vocalinux/models")
# Alternative locations for pre-installed models
SYSTEM_MODELS_DIRS = [
    "/usr/local/share/vocalinux/models",
    "/usr/share/vocalinux/models",
]


class StreamingRecognitionManager:
    """
    Enhanced speech recognition manager with streaming support.

    This manager provides both traditional batch processing and real-time
    streaming capabilities with configurable latency preferences.
    """

    def __init__(
        self,
        engine: str = "vosk",
        model_size: str = "small",
        language: str = "en-us",
        enable_streaming: bool = True,
        streaming_chunk_size: int = 1024,
        vad_enabled: bool = True,
        vad_sensitivity: int = 3,
        silence_timeout: float = 1.0,
        min_speech_duration_ms: int = 250,
        defer_download: bool = True,
        **kwargs,
    ):
        """
        Initialize the streaming recognition manager.

        Args:
            engine: The speech recognition engine ("vosk" or "whisper")
            model_size: The size of the model to use
            language: Language code for recognition
            enable_streaming: Enable real-time streaming mode
            streaming_chunk_size: Audio chunk size for streaming
            vad_enabled: Enable Voice Activity Detection
            vad_sensitivity: VAD sensitivity (1-5)
            silence_timeout: Silence timeout in seconds
            min_speech_duration_ms: Minimum speech duration in ms
            defer_download: Defer model download until needed
        """
        self.engine = engine
        self.model_size = model_size
        self.language = language
        self.enable_streaming = enable_streaming
        self.streaming_chunk_size = streaming_chunk_size
        self.vad_enabled = vad_enabled
        self.vad_sensitivity = vad_sensitivity
        self.silence_timeout = silence_timeout
        self.min_speech_duration_ms = min_speech_duration_ms
        self.defer_download = defer_download

        # State management
        self.state = RecognitionState.IDLE
        self.is_streaming = False

        # Model initialization
        self.model = None
        self._model_initialized = False

        # Callbacks
        self.text_callbacks: List[Callable[[str], None]] = []
        self.state_callbacks: List[Callable[[RecognitionState], None]] = []
        self.action_callbacks: List[Callable[[str], None]] = []

        # Processing components
        self.command_processor = CommandProcessor()
        self.streaming_recognizer = None
        self.audio_thread = None

        # Performance tracking
        self.performance_stats = {
            "total_processing_time": 0.0,
            "total_audio_chunks": 0,
            "average_latency_ms": 0.0,
            "streaming_mode": enable_streaming,
        }

        # Audio device
        self.audio_device_index = kwargs.get("audio_device_index", None)

        # Initialize the streaming recognizer if enabled
        if self.enable_streaming:
            self._init_streaming_recognizer()

        logger.info(
            f"Initialized streaming recognition manager: {engine} engine, "
            f"streaming={enable_streaming}, chunk_size={streaming_chunk_size}"
        )

    def _init_streaming_recognizer(self):
        """Initialize the streaming speech recognizer."""
        try:
            # Convert VAD sensitivity to threshold (0.0-1.0)
            vad_threshold = max(0.1, min(0.9, self.vad_sensitivity / 5.0))

            self.streaming_recognizer = StreamingSpeechRecognizer(
                engine=self.engine,
                model_size=self.model_size,
                language=self.language,
                chunk_size=self.streaming_chunk_size,
                vad_enabled=self.vad_enabled,
                vad_threshold=vad_threshold,
                min_speech_duration_ms=self.min_speech_duration_ms,
                silence_timeout_ms=int(self.silence_timeout * 1000),
            )

            # Register callbacks
            self.streaming_recognizer.register_partial_result_callback(self._on_partial_result)
            self.streaming_recognizer.register_final_result_callback(self._on_final_result)
            self.streaming_recognizer.register_error_callback(self._on_streaming_error)

            logger.info("Streaming recognizer initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize streaming recognizer: {e}")
            # Fall back to non-streaming mode
            self.enable_streaming = False
            if self.streaming_recognizer:
                self.streaming_recognizer = None

    def _on_partial_result(self, text: str):
        """Handle partial streaming results."""
        # For now, we don't process partial text to avoid rapid cursor movements
        # This could be enabled later for real-time preview
        logger.debug(f"Partial result: {text}")

    def _on_final_result(self, text: str):
        """Handle final streaming results."""
        if not text:
            return

        logger.debug(f"Final result: {text}")

        # Process commands in the recognized text
        processed_text, actions = self.command_processor.process_text(text)

        # Call text callbacks with processed text
        if processed_text:
            for callback in self.text_callbacks:
                callback(processed_text)

        # Call action callbacks for each action
        for action in actions:
            for callback in self.action_callbacks:
                callback(action)

    def _on_streaming_error(self, error: Exception):
        """Handle streaming errors."""
        logger.error(f"Streaming error: {error}")
        self._update_state(RecognitionState.ERROR)
        play_error_sound()

    def register_text_callback(self, callback: Callable[[str], None]):
        """Register a callback for recognized text."""
        self.text_callbacks.append(callback)

    def register_state_callback(self, callback: Callable[[RecognitionState], None]):
        """Register a callback for state changes."""
        self.state_callbacks.append(callback)

    def register_action_callback(self, callback: Callable[[str], None]):
        """Register a callback for actions."""
        self.action_callbacks.append(callback)

    def _update_state(self, new_state: RecognitionState):
        """Update recognition state and notify callbacks."""
        self.state = new_state
        for callback in self.state_callbacks:
            callback(new_state)

    def start_recognition(self):
        """Start speech recognition."""
        if self.state != RecognitionState.IDLE:
            logger.warning(f"Cannot start recognition in state: {self.state}")
            return

        logger.info("Starting speech recognition")
        self._update_state(RecognitionState.LISTENING)
        play_start_sound()

        if self.enable_streaming and self.streaming_recognizer:
            # Start streaming recognition
            self.is_streaming = True
            self.streaming_recognizer.start_streaming()

            # Start audio recording thread
            self.audio_thread = threading.Thread(target=self._record_audio_streaming)
            self.audio_thread.daemon = True
            self.audio_thread.start()

            logger.info("Started streaming speech recognition")
        else:
            # Fall back to batch processing
            logger.warning("Streaming not available, falling back to batch processing")
            self._start_batch_recognition()

    def _record_audio_streaming(self):
        """Record audio for streaming processing."""
        try:
            import pyaudio
            import numpy as np
        except ImportError as e:
            logger.error(f"Missing audio dependencies: {e}")
            self._update_state(RecognitionState.ERROR)
            play_error_sound()
            return

        try:
            # Audio configuration
            CHUNK = self.streaming_chunk_size
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000

            # Initialize PyAudio
            audio = pyaudio.PyAudio()

            # Open audio stream
            stream_kwargs = {
                "format": FORMAT,
                "channels": CHANNELS,
                "rate": RATE,
                "input": True,
                "frames_per_buffer": CHUNK,
            }

            if self.audio_device_index is not None:
                stream_kwargs["input_device_index"] = self.audio_device_index

            try:
                stream = audio.open(**stream_kwargs)
            except (IOError, OSError) as e:
                logger.error(f"Failed to open audio stream: {e}")
                play_error_sound()
                audio.terminate()
                self._update_state(RecognitionState.ERROR)
                return

            logger.info("Audio recording started for streaming")

            # Record and stream audio chunks
            while self.is_streaming:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)

                    # Process chunk through streaming recognizer
                    if self.streaming_recognizer:
                        self.streaming_recognizer.process_audio_chunk(data)

                        # Update performance stats
                        self.performance_stats["total_audio_chunks"] += 1

                except Exception as e:
                    logger.error(f"Error reading audio: {e}")
                    break

            # Clean up
            stream.stop_stream()
            stream.close()
            audio.terminate()

            logger.info("Audio recording stopped")

        except Exception as e:
            logger.error(f"Error in audio recording: {e}")
            play_error_sound()
            self._update_state(RecognitionState.ERROR)

    def _start_batch_recognition(self):
        """Start batch processing recognition (fallback)."""
        # Import the original recognition manager for batch processing
        try:
            from .recognition_manager import SpeechRecognitionManager

            # Create batch manager as fallback
            self.batch_manager = SpeechRecognitionManager(
                engine=self.engine,
                model_size=self.model_size,
                language=self.language,
                defer_download=self.defer_download,
                vad_sensitivity=self.vad_sensitivity,
                silence_timeout=self.silence_timeout,
                audio_device_index=self.audio_device_index,
            )

            # Transfer callbacks to batch manager
            for callback in self.text_callbacks:
                self.batch_manager.register_text_callback(callback)
            for callback in self.state_callbacks:
                self.batch_manager.register_state_callback(callback)
            for callback in self.action_callbacks:
                self.batch_manager.register_action_callback(callback)

            # Start batch recognition
            self.batch_manager.start_recognition()

        except Exception as e:
            logger.error(f"Failed to start batch recognition: {e}")
            self._update_state(RecognitionState.ERROR)
            play_error_sound()

    def stop_recognition(self):
        """Stop speech recognition."""
        if self.state == RecognitionState.IDLE:
            return

        logger.info("Stopping speech recognition")
        play_stop_sound()

        if self.is_streaming and self.streaming_recognizer:
            # Stop streaming recognition
            self.is_streaming = False
            self.streaming_recognizer.stop_streaming()

            # Wait for audio thread to finish
            if self.audio_thread and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=1.0)

        elif hasattr(self, "batch_manager") and self.batch_manager:
            # Stop batch recognition
            self.batch_manager.stop_recognition()

        self._update_state(RecognitionState.IDLE)

    def set_audio_device(self, device_index: Optional[int]):
        """Set the audio input device."""
        if device_index != self.audio_device_index:
            logger.info(f"Audio device changed from {self.audio_device_index} to {device_index}")
            self.audio_device_index = device_index

    def get_audio_device(self) -> Optional[int]:
        """Get the current audio device index."""
        return self.audio_device_index

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        base_stats = self.performance_stats.copy()

        if self.streaming_recognizer:
            streaming_stats = self.streaming_recognizer.get_statistics()
            base_stats.update(streaming_stats)

        return base_stats

    def is_streaming_enabled(self) -> bool:
        """Check if streaming mode is enabled and available."""
        return self.enable_streaming and self.streaming_recognizer is not None

    def reconfigure(
        self,
        engine: Optional[str] = None,
        model_size: Optional[str] = None,
        language: Optional[str] = None,
        enable_streaming: Optional[bool] = None,
        vad_sensitivity: Optional[int] = None,
        silence_timeout: Optional[float] = None,
        audio_device_index: Optional[int] = None,
        **kwargs,
    ):
        """
        Reconfigure the recognition manager.

        Args:
            engine: New speech recognition engine
            model_size: New model size
            language: New language
            enable_streaming: Enable/disable streaming mode
            vad_sensitivity: VAD sensitivity
            silence_timeout: Silence timeout
            audio_device_index: Audio device index
        """
        logger.info(f"Reconfiguring recognition manager")

        # Update configuration
        if engine is not None and engine != self.engine:
            self.engine = engine
            self._reinitialize_needed = True

        if model_size is not None and model_size != self.model_size:
            self.model_size = model_size
            self._reinitialize_needed = True

        if language is not None and language != self.language:
            self.language = language
            self._reinitialize_needed = True

        if enable_streaming is not None and enable_streaming != self.enable_streaming:
            self.enable_streaming = enable_streaming
            self._reinitialize_needed = True

        if vad_sensitivity is not None:
            self.vad_sensitivity = max(1, min(5, int(vad_sensitivity)))

        if silence_timeout is not None:
            self.silence_timeout = max(0.5, min(5.0, float(silence_timeout)))

        if audio_device_index is not None:
            if audio_device_index == -1:
                self.audio_device_index = None
            else:
                self.audio_device_index = audio_device_index

        # Reinitialize if needed
        if hasattr(self, "_reinitialize_needed") and self._reinitialize_needed:
            logger.info("Reinitializing recognition manager")

            # Clean up existing components
            if self.streaming_recognizer:
                self.streaming_recognizer.stop_streaming()
                self.streaming_recognizer = None

            # Reinitialize streaming recognizer if enabled
            if self.enable_streaming:
                self._init_streaming_recognizer()

            delattr(self, "_reinitialize_needed")

        logger.info("Recognition manager reconfigured")
