"""
Streaming speech recognition module for Vocalinux.

This module provides real-time streaming speech recognition with lower latency
by processing audio chunks as they arrive, rather than waiting for complete utterances.
"""

import json
import logging
import threading
import time
import queue
from typing import Callable, List, Optional, Dict, Any
import numpy as np

from ..common_types import RecognitionState
from ..ui.audio_feedback import play_error_sound, play_start_sound, play_stop_sound

logger = logging.getLogger(__name__)


class StreamingSpeechRecognizer:
    """
    Real-time streaming speech recognition engine.

    This class processes audio in chunks and provides both partial and final
    results with minimal latency, suitable for interactive applications.
    """

    def __init__(
        self,
        engine: str = "vosk",
        model_size: str = "small",
        language: str = "en-us",
        chunk_size: int = 1024,
        sample_rate: int = 16000,
        vad_enabled: bool = True,
        vad_threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        silence_timeout_ms: int = 1000,
        **kwargs,
    ):
        """
        Initialize the streaming speech recognizer.

        Args:
            engine: Speech recognition engine ("vosk" or "whisper")
            model_size: Model size ("tiny", "base", "small", "medium", "large")
            language: Language code (e.g., "en-us", "hi")
            chunk_size: Audio chunk size for processing
            sample_rate: Audio sample rate
            vad_enabled: Enable Voice Activity Detection
            vad_threshold: VAD sensitivity threshold (0.0-1.0)
            min_speech_duration_ms: Minimum speech duration to consider valid
            silence_timeout_ms: Silence timeout before finalizing result
        """
        self.engine = engine
        self.model_size = model_size
        self.language = language
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate
        self.vad_enabled = vad_enabled
        self.vad_threshold = vad_threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.silence_timeout_ms = silence_timeout_ms

        # Threading and state management
        self.is_running = False
        self.recognition_thread = None
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()

        # Model and recognizer instances
        self.model = None
        self.recognizer = None

        # Buffer management
        self.audio_buffer = []
        self.speech_buffer = []
        self.last_speech_time = 0
        self.is_speaking = False

        # Callbacks
        self.partial_result_callbacks: List[Callable[[str], None]] = []
        self.final_result_callbacks: List[Callable[[str], None]] = []
        self.error_callbacks: List[Callable[[Exception], None]] = []

        # Statistics
        self.total_chunks_processed = 0
        self.total_processing_time = 0.0
        self.avg_latency_ms = 0.0

        # Initialize the selected engine
        self._init_engine()

    def _init_engine(self):
        """Initialize the speech recognition engine."""
        if self.engine == "vosk":
            self._init_vosk()
        elif self.engine == "whisper":
            self._init_whisper()
        else:
            raise ValueError(f"Unsupported engine: {self.engine}")

    def _init_vosk(self):
        """Initialize VOSK streaming recognizer."""
        try:
            from vosk import Model, KaldiRecognizer

            # Note: In a real implementation, we would load the model path
            # For now, we'll assume the model is available
            self.model = Model()  # This would need actual model path
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

            # Enable partial results
            self.recognizer.SetWords(True)

            logger.info("VOSK streaming recognizer initialized")

        except ImportError:
            logger.error("VOSK not available. Install with: pip install vosk")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize VOSK: {e}")
            raise

    def _init_whisper(self):
        """Initialize Whisper streaming recognizer with chunked processing."""
        try:
            import whisper

            # Load the model
            self.model = whisper.load_model(self.model_size)

            # Initialize VAD if enabled
            if self.vad_enabled:
                self._init_vad()

            logger.info(f"Whisper streaming recognizer initialized with {self.model_size} model")

        except ImportError:
            logger.error("Whisper not available. Install with: pip install openai-whisper")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Whisper: {e}")
            raise

    def _init_vad(self):
        """Initialize Voice Activity Detection."""
        try:
            # Try to import Silero VAD
            import torch

            self.vad_model = torch.hub.load("snakers4/silero-vad", "silero_vad")
            self.vad_enabled = True
            logger.info("Silero VAD initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize VAD: {e}. Disabling VAD.")
            self.vad_enabled = False

    def _detect_speech(self, audio_chunk: bytes) -> bool:
        """
        Detect if audio chunk contains speech using VAD.

        Args:
            audio_chunk: Raw audio data bytes

        Returns:
            True if speech detected, False otherwise
        """
        if not self.vad_enabled or not hasattr(self, "vad_model"):
            # Simple energy-based VAD as fallback
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            energy = np.abs(audio_data).mean()
            return energy > 500  # Simple threshold

        try:
            import torch

            # Convert audio to tensor for Silero VAD
            audio_tensor = torch.frombuffer(audio_chunk, dtype=torch.float32)

            # Reshape if necessary
            if len(audio_tensor.shape) == 1:
                audio_tensor = audio_tensor.unsqueeze(0)

            # Get speech probability
            speech_prob = self.vad_model(audio_tensor, self.sample_rate).item()

            return speech_prob > self.vad_threshold

        except Exception as e:
            logger.debug(f"VAD detection failed: {e}")
            # Fallback to simple energy detection
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            energy = np.abs(audio_data).mean()
            return energy > 500

    def register_partial_result_callback(self, callback: Callable[[str], None]):
        """Register callback for partial results."""
        self.partial_result_callbacks.append(callback)

    def register_final_result_callback(self, callback: Callable[[str], None]):
        """Register callback for final results."""
        self.final_result_callbacks.append(callback)

    def register_error_callback(self, callback: Callable[[Exception], None]):
        """Register callback for errors."""
        self.error_callbacks.append(callback)

    def process_audio_chunk(self, audio_data: bytes):
        """
        Process a single audio chunk.

        Args:
            audio_data: Raw audio data bytes
        """
        if not self.is_running:
            return

        self.audio_queue.put(audio_data)

    def _process_audio_loop(self):
        """Main audio processing loop."""
        logger.info("Starting audio processing loop")

        chunk_start_time = time.time()

        while self.is_running:
            try:
                # Get audio chunk from queue with timeout
                audio_chunk = self.audio_queue.get(timeout=0.1)

                # Process the chunk
                self._process_chunk(audio_chunk)

                # Update statistics
                self.total_chunks_processed += 1
                processing_time = time.time() - chunk_start_time
                self.total_processing_time += processing_time

                # Calculate average latency
                if self.total_chunks_processed > 0:
                    self.avg_latency_ms = (
                        self.total_processing_time / self.total_chunks_processed
                    ) * 1000

                chunk_start_time = time.time()

            except queue.Empty:
                # No audio available, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in audio processing loop: {e}")
                self._notify_error(e)

        logger.info("Audio processing loop stopped")

    def _process_chunk(self, audio_chunk: bytes):
        """Process a single audio chunk."""
        start_time = time.time()

        # Detect speech if VAD is enabled
        if self.vad_enabled:
            is_speech = self._detect_speech(audio_chunk)

            if is_speech:
                if not self.is_speaking:
                    # Speech started
                    self.is_speaking = True
                    self.last_speech_time = time.time()
                    self.speech_buffer = [audio_chunk]
                else:
                    # Continuing speech
                    self.speech_buffer.append(audio_chunk)
                    self.last_speech_time = time.time()
            else:
                # Silence detected
                if self.is_speaking:
                    # Check if silence timeout exceeded
                    silence_duration = (time.time() - self.last_speech_time) * 1000
                    if silence_duration > self.silence_timeout_ms:
                        # End of speech segment
                        self._finalize_speech_segment()
                        self.is_speaking = False
                # Don't add silence to buffer
                return
        else:
            # No VAD, always add to buffer
            self.audio_buffer.append(audio_chunk)
            self.speech_buffer.append(audio_chunk)

        # Process with the selected engine
        if self.engine == "vosk":
            self._process_vosk_chunk(audio_chunk)
        elif self.engine == "whisper":
            self._process_whisper_chunk(audio_chunk)

        processing_time = (time.time() - start_time) * 1000
        logger.debug(f"Processed chunk in {processing_time:.2f}ms")

    def _process_vosk_chunk(self, audio_chunk: bytes):
        """Process audio chunk with VOSK."""
        if self.recognizer is None:
            return

        # Feed chunk to VOSK recognizer
        if self.recognizer.AcceptWaveform(audio_chunk):
            # Final result available
            result = json.loads(self.recognizer.FinalResult())
            text = result.get("text", "").strip()

            if text:
                logger.debug(f"VOSK final result: {text}")
                self._notify_final_result(text)
        else:
            # Partial result available
            partial = json.loads(self.recognizer.PartialResult())
            partial_text = partial.get("partial", "").strip()

            if partial_text:
                logger.debug(f"VOSK partial: {partial_text}")
                self._notify_partial_result(partial_text)

    def _process_whisper_chunk(self, audio_chunk: bytes):
        """Process audio chunk with Whisper."""
        # Whisper processes accumulated speech segments
        # We'll process when we have enough audio or speech ends

        if len(self.speech_buffer) > 0:
            # Calculate accumulated speech duration
            total_samples = sum(
                len(chunk) // 2 for chunk in self.speech_buffer
            )  # 16-bit = 2 bytes per sample
            duration_ms = (total_samples / self.sample_rate) * 1000

            # Process if we have minimum speech duration or if speech just ended
            if duration_ms >= self.min_speech_duration_ms or not self.is_speaking:
                self._transcribe_whisper_segment()

    def _transcribe_whisper_segment(self):
        """Transcribe accumulated speech segment with Whisper."""
        if not self.speech_buffer or self.model is None:
            return

        try:
            # Combine all chunks in speech buffer
            combined_audio = b"".join(self.speech_buffer)

            # Convert to numpy array
            audio_data = np.frombuffer(combined_audio, dtype=np.int16)

            # Convert to float32 and normalize
            audio_float = audio_data.astype(np.float32) / 32768.0

            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_float,
                language=self.language if self.language != "auto" else None,
                task="transcribe",
                verbose=False,
                temperature=0.0,
                no_speech_threshold=0.6,
            )

            text = result.get("text", "").strip()

            if text:
                logger.debug(f"Whisper transcribed: {text}")
                self._notify_final_result(text)

            # Clear the processed buffer
            self.speech_buffer = []

        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            self._notify_error(e)

    def _finalize_speech_segment(self):
        """Finalize current speech segment and process it."""
        if self.engine == "whisper":
            self._transcribe_whisper_segment()
        elif self.engine == "vosk":
            # For VOSK, final result is already handled by AcceptWaveform
            pass

    def _notify_partial_result(self, text: str):
        """Notify all partial result callbacks."""
        for callback in self.partial_result_callbacks:
            try:
                callback(text)
            except Exception as e:
                logger.error(f"Error in partial result callback: {e}")

    def _notify_final_result(self, text: str):
        """Notify all final result callbacks."""
        for callback in self.final_result_callbacks:
            try:
                callback(text)
            except Exception as e:
                logger.error(f"Error in final result callback: {e}")

    def _notify_error(self, error: Exception):
        """Notify all error callbacks."""
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    def start_streaming(self):
        """Start the streaming recognition."""
        if self.is_running:
            logger.warning("Streaming already running")
            return

        self.is_running = True

        # Start the processing thread
        self.recognition_thread = threading.Thread(target=self._process_audio_loop)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()

        logger.info("Streaming recognition started")

    def stop_streaming(self):
        """Stop the streaming recognition."""
        if not self.is_running:
            return

        self.is_running = False

        # Process any remaining audio
        if self.speech_buffer:
            self._finalize_speech_segment()

        # Wait for thread to finish
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=1.0)

        logger.info("Streaming recognition stopped")

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "total_chunks_processed": self.total_chunks_processed,
            "total_processing_time": self.total_processing_time,
            "average_latency_ms": self.avg_latency_ms,
            "is_running": self.is_running,
            "engine": self.engine,
            "model_size": self.model_size,
        }

    def __del__(self):
        """Cleanup when destroyed."""
        self.stop_streaming()
