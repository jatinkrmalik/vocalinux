"""
Speech recognition manager module for Vocalinux.

This module provides a unified interface to different speech recognition engines,
currently supporting VOSK and Whisper.
"""

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Callable, List, Optional

from ..common_types import RecognitionState
from ..ui.audio_feedback import play_error_sound, play_start_sound, play_stop_sound
from .command_processor import CommandProcessor

logger = logging.getLogger(__name__)

# Define constants
MODELS_DIR = os.path.expanduser("~/.local/share/vocalinux/models")


class SpeechRecognitionManager:
    """
    Manager class for speech recognition engines.

    This class provides a unified interface for working with different
    speech recognition engines (VOSK and Whisper).
    """

    def __init__(self, engine: str = "vosk", model_size: str = "small"):
        """
        Initialize the speech recognition manager.

        Args:
            engine: The speech recognition engine to use ("vosk" or "whisper")
            model_size: The size of the model to use ("small", "medium", "large")
        """
        self.engine = engine
        self.model_size = model_size
        self.state = RecognitionState.IDLE
        self.audio_thread = None
        self.recognition_thread = None
        self.model = None
        self.command_processor = CommandProcessor()
        self.text_callbacks: List[Callable[[str], None]] = []
        self.state_callbacks: List[Callable[[RecognitionState], None]] = []
        self.action_callbacks: List[Callable[[str], None]] = []

        # Speech detection parameters
        self.vad_sensitivity = 3  # Voice Activity Detection sensitivity (1-5)
        self.silence_timeout = 2.0  # Seconds of silence before stopping recognition

        # Recording control flags
        self.should_record = False
        self.audio_buffer = []

        # Create models directory if it doesn't exist
        os.makedirs(MODELS_DIR, exist_ok=True)

        logger.info(
            f"Initializing speech recognition with {engine} engine and {model_size} model"
        )

        # Initialize the selected speech recognition engine
        if engine == "vosk":
            self._init_vosk()
        elif engine == "whisper":
            self._init_whisper()
        else:
            raise ValueError(f"Unsupported speech recognition engine: {engine}")

    def _init_vosk(self):
        """Initialize the VOSK speech recognition engine."""
        try:
            from vosk import KaldiRecognizer, Model

            self.vosk_model_path = self._get_vosk_model_path()

            if not os.path.exists(self.vosk_model_path):
                logger.info(
                    f"VOSK model not found at {self.vosk_model_path}. Downloading..."
                )
                self._download_vosk_model()

            logger.info(f"Loading VOSK model from {self.vosk_model_path}")
            self.model = Model(self.vosk_model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)

        except ImportError:
            logger.error(
                "Failed to import VOSK. Please install it with 'pip install vosk'"
            )
            self.state = RecognitionState.ERROR
            raise

    def _init_whisper(self):
        """Initialize the Whisper speech recognition engine."""
        try:
            import whisper

            logger.info(f"Loading Whisper {self.model_size} model")
            self.model = whisper.load_model(self.model_size)

        except ImportError:
            logger.error(
                "Failed to import Whisper. Please install it with 'pip install whisper torch'"
            )
            self.state = RecognitionState.ERROR
            raise

    def _get_vosk_model_path(self) -> str:
        """Get the path to the VOSK model based on the selected size."""
        model_map = {
            "small": "vosk-model-small-en-us-0.15",
            "medium": "vosk-model-en-us-0.22",
            "large": "vosk-model-en-us-0.42",
        }

        model_name = model_map.get(self.model_size, model_map["small"])
        return os.path.join(MODELS_DIR, model_name)

    def _download_vosk_model(self):
        """Download the VOSK model if it doesn't exist."""
        import zipfile

        import requests
        import tqdm

        model_urls = {
            "small": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            "medium": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
            "large": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.42.zip",
        }

        url = model_urls.get(self.model_size)
        if not url:
            raise ValueError(f"Unknown model size: {self.model_size}")

        model_name = os.path.basename(url).replace(".zip", "")
        model_path = os.path.join(MODELS_DIR, model_name)
        zip_path = os.path.join(MODELS_DIR, os.path.basename(url))

        # Download the model
        logger.info(f"Downloading VOSK model from {url}")
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get("content-length", 0))

        with open(zip_path, "wb") as f:
            for data in tqdm.tqdm(
                response.iter_content(chunk_size=1024),
                total=total_size // 1024,
                unit="KB",
            ):
                f.write(data)

        # Extract the model
        logger.info(f"Extracting VOSK model to {model_path}")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(MODELS_DIR)

        # Remove the zip file
        os.remove(zip_path)
        logger.info("VOSK model downloaded and extracted successfully")

    def register_text_callback(self, callback: Callable[[str], None]):
        """
        Register a callback function that will be called when text is recognized.

        Args:
            callback: A function that takes a string argument (the recognized text)
        """
        self.text_callbacks.append(callback)

    def register_state_callback(self, callback: Callable[[RecognitionState], None]):
        """
        Register a callback function that will be called when the recognition state changes.

        Args:
            callback: A function that takes a RecognitionState argument
        """
        self.state_callbacks.append(callback)

    def register_action_callback(self, callback: Callable[[str], None]):
        """
        Register a callback function that will be called when a special action is triggered.

        Args:
            callback: A function that takes a string argument (the action)
        """
        self.action_callbacks.append(callback)

    def _update_state(self, new_state: RecognitionState):
        """
        Update the recognition state and notify callbacks.

        Args:
            new_state: The new recognition state
        """
        self.state = new_state
        for callback in self.state_callbacks:
            callback(new_state)

    def start_recognition(self):
        """Start the speech recognition process."""
        if self.state != RecognitionState.IDLE:
            logger.warning(f"Cannot start recognition in current state: {self.state}")
            return

        logger.info("Starting speech recognition")
        self._update_state(RecognitionState.LISTENING)

        # Play the start sound
        play_start_sound()

        # Set recording flag
        self.should_record = True
        self.audio_buffer = []

        # Start the audio recording thread
        self.audio_thread = threading.Thread(target=self._record_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()

        # Start the recognition thread
        self.recognition_thread = threading.Thread(target=self._perform_recognition)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()

    def stop_recognition(self):
        """Stop the speech recognition process."""
        if self.state == RecognitionState.IDLE:
            return

        logger.info("Stopping speech recognition")

        # Play the stop sound
        play_stop_sound()

        # Clear recording flag
        self.should_record = False

        # Wait for threads to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1.0)

        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=1.0)

        self._update_state(RecognitionState.IDLE)

    def _record_audio(self):
        """Record audio from the microphone."""
        try:
            import wave

            import numpy as np
            import pyaudio

            # PyAudio configuration
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000

            # Initialize PyAudio
            audio = pyaudio.PyAudio()

            # Open microphone stream
            stream = audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK,
            )

            logger.info("Audio recording started")

            # Record audio while should_record is True
            silence_counter = 0
            while self.should_record:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    self.audio_buffer.append(data)

                    # Simple Voice Activity Detection (VAD)
                    # TODO: Implement proper VAD using webrtcvad or similar
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = np.abs(audio_data).mean()

                    # Threshold based on sensitivity (1-5)
                    threshold = 500 / self.vad_sensitivity

                    if volume < threshold:  # Silence
                        silence_counter += CHUNK / RATE  # Convert chunks to seconds
                        if silence_counter > self.silence_timeout:
                            logger.debug("Silence detected, stopping recognition")
                            self._update_state(RecognitionState.PROCESSING)
                            # Process final buffer
                            self._process_final_buffer()
                            # Reset for next utterance
                            self.audio_buffer = []
                            silence_counter = 0
                            self._update_state(RecognitionState.LISTENING)
                    else:  # Speech
                        silence_counter = 0
                except Exception as e:
                    logger.error(f"Error reading audio data: {e}")
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

    def _process_final_buffer(self):
        """Process the final audio buffer after silence is detected."""
        if not self.audio_buffer:
            return

        if self.engine == "vosk":
            for data in self.audio_buffer:
                self.recognizer.AcceptWaveform(data)

            result = json.loads(self.recognizer.FinalResult())
            text = result.get("text", "")

        elif self.engine == "whisper":
            # Save buffer to a temporary file
            import tempfile
            import wave

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name

            with wave.open(temp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(16000)
                wf.writeframes(b"".join(self.audio_buffer))

            # Process with Whisper
            result = self.model.transcribe(temp_path)
            text = result.get("text", "")

            # Remove temporary file
            os.unlink(temp_path)

        else:
            logger.error(f"Unknown engine: {self.engine}")
            return

        # Process commands
        if text:
            processed_text, actions = self.command_processor.process_text(text)

            # Call text callbacks with processed text
            if processed_text:
                for callback in self.text_callbacks:
                    callback(processed_text)

            # Call action callbacks for each action
            for action in actions:
                for callback in self.action_callbacks:
                    callback(action)

    def _perform_recognition(self):
        """Perform speech recognition in real-time."""
        while self.should_record:
            # The real work is done in _record_audio and _process_final_buffer
            time.sleep(0.1)

    def configure(self, vad_sensitivity: int = None, silence_timeout: float = None):
        """
        Configure recognition parameters.

        Args:
            vad_sensitivity: Voice Activity Detection sensitivity (1-5)
            silence_timeout: Seconds of silence before stopping recognition
        """
        if vad_sensitivity is not None:
            self.vad_sensitivity = max(1, min(5, vad_sensitivity))

        if silence_timeout is not None:
            self.silence_timeout = max(0.5, min(5.0, silence_timeout))
