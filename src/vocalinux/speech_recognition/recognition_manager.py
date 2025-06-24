"""
Speech recognition manager module for Vocalinux.

This module provides a unified interface to different speech recognition engines,
currently supporting VOSK and Whisper.
"""

import json
import logging
import os
import sys
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
# Alternative locations for pre-installed models
SYSTEM_MODELS_DIRS = [
    "/usr/local/share/vocalinux/models",
    "/usr/share/vocalinux/models",
]


class SpeechRecognitionManager:
    """
    Manager class for speech recognition engines.

    This class provides a unified interface for working with different
    speech recognition engines (VOSK and Whisper).
    """

    def __init__(self, engine: str = "vosk", model_size: str = "small", **kwargs):
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
        self.recognizer = None  # Added for VOSK
        self.command_processor = CommandProcessor()
        self.text_callbacks: List[Callable[[str], None]] = []
        self.state_callbacks: List[Callable[[RecognitionState], None]] = []
        self.action_callbacks: List[Callable[[str], None]] = []

        # Speech detection parameters (load defaults, will be overridden by configure)
        self.vad_sensitivity = kwargs.get("vad_sensitivity", 3)
        self.silence_timeout = kwargs.get("silence_timeout", 2.0)

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
                # Update path after download
                self.vosk_model_path = self._get_vosk_model_path()
            else:
                # Check if this is a pre-installed model
                if any(self.vosk_model_path.startswith(sys_dir) for sys_dir in SYSTEM_MODELS_DIRS):
                    logger.info(f"Using pre-installed VOSK model from {self.vosk_model_path}")
                elif os.path.exists(os.path.join(self.vosk_model_path, ".vocalinux_preinstalled")):
                    logger.info(f"Using installer-provided VOSK model from {self.vosk_model_path}")
                else:
                    logger.info(f"Using existing VOSK model from {self.vosk_model_path}")

            logger.info(f"Loading VOSK model from {self.vosk_model_path}")
            # Ensure previous model/recognizer are released if re-initializing
            self.model = None
            self.recognizer = None
            self.model = Model(self.vosk_model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            logger.info("VOSK engine initialized successfully.")

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
            import torch
            
            # Validate model size for Whisper
            valid_whisper_models = ["tiny", "base", "small", "medium", "large"]
            if self.model_size not in valid_whisper_models:
                # Map common size names to Whisper model names
                size_mapping = {
                    "tiny": "tiny",
                    "small": "base",  # Map small to base for better quality
                    "medium": "small", # Map medium to small for balance
                    "large": "medium"  # Map large to medium (large is very slow)
                }
                mapped_size = size_mapping.get(self.model_size, "base")
                logger.warning(f"Model size '{self.model_size}' not valid for Whisper. Using '{mapped_size}' instead.")
                self.whisper_model_size = mapped_size
            else:
                self.whisper_model_size = self.model_size

            # Check for GPU availability
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")
            
            # Download directory for Whisper models
            self.whisper_cache_dir = os.path.join(MODELS_DIR, "whisper")
            os.makedirs(self.whisper_cache_dir, exist_ok=True)
            
            logger.info(f"Loading Whisper '{self.whisper_model_size}' model...")
            # Ensure previous model is released if re-initializing
            self.model = None
            
            # Load model with custom cache directory
            self.model = whisper.load_model(
                self.whisper_model_size, 
                download_root=self.whisper_cache_dir
            )
            
            # Move model to appropriate device
            if self.device == "cuda":
                self.model = self.model.cuda()
                logger.info("Whisper model loaded on GPU")
            else:
                logger.info("Whisper model loaded on CPU")
                
            # Initialize audio preprocessing parameters
            self.whisper_sample_rate = 16000
            self.whisper_chunk_length = 30  # seconds
            
            logger.info("Whisper engine initialized successfully.")
            
        except ImportError as e:
            logger.error(
                f"Failed to import required libraries for Whisper: {e}"
            )
            logger.error(
                "Please install with: pip install openai-whisper torch"
            )
            self.state = RecognitionState.ERROR
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Whisper engine: {e}")
            self.state = RecognitionState.ERROR
            raise

    def _transcribe_with_whisper(self, audio_buffer: List[bytes]) -> str:
        """
        Transcribe audio buffer using Whisper.
        
        Args:
            audio_buffer: List of audio data chunks
            
        Returns:
            Transcribed text
        """
        try:
            import numpy as np
            import torch
            
            if not audio_buffer:
                return ""
            
            # Convert audio buffer to numpy array
            audio_data = np.frombuffer(b"".join(audio_buffer), dtype=np.int16)
            
            # Convert to float32 and normalize to [-1, 1]
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # Ensure audio is the right length (pad or trim)
            target_length = self.whisper_sample_rate * self.whisper_chunk_length
            if len(audio_float) > target_length:
                # Trim to target length
                audio_float = audio_float[:target_length]
            elif len(audio_float) < target_length:
                # Pad with zeros
                audio_float = np.pad(audio_float, (0, target_length - len(audio_float)))
            
            # Convert to torch tensor
            audio_tensor = torch.from_numpy(audio_float)
            
            # Move to appropriate device
            if self.device == "cuda":
                audio_tensor = audio_tensor.cuda()
            
            logger.debug(f"Transcribing audio: {len(audio_float)/self.whisper_sample_rate:.2f} seconds")
            
            # Transcribe with Whisper
            with torch.no_grad():  # Disable gradient computation for inference
                result = self.model.transcribe(
                    audio_tensor,
                    language="en",  # Force English for better performance
                    task="transcribe",
                    verbose=False,  # Reduce logging
                    temperature=0.0,  # Use greedy decoding for consistency
                    compression_ratio_threshold=2.4,
                    logprob_threshold=-1.0,
                    no_speech_threshold=0.6,
                )
            
            text = result.get("text", "").strip()
            
            if text:
                logger.info(f"Whisper transcribed: '{text}'")
            else:
                logger.debug("Whisper returned empty transcription")
            
            return text
            
        except Exception as e:
            logger.error(f"Error in Whisper transcription: {e}", exc_info=True)
            return ""

    def _get_vosk_model_path(self) -> str:
        """Get the path to the VOSK model based on the selected size."""
        model_map = {
            "small": "vosk-model-small-en-us-0.15",
            "medium": "vosk-model-en-us-0.22",
            # Use the standard large model URL, as 0.42 seems unavailable
            "large": "vosk-model-en-us-0.22",
        }

        model_name = model_map.get(self.model_size, model_map["small"])
        
        # First, check user's local models directory
        user_model_path = os.path.join(MODELS_DIR, model_name)
        if os.path.exists(user_model_path):
            logger.debug(f"Found user model at: {user_model_path}")
            return user_model_path
        
        # Then check system-wide installation directories
        for system_dir in SYSTEM_MODELS_DIRS:
            system_model_path = os.path.join(system_dir, model_name)
            if os.path.exists(system_model_path):
                logger.info(f"Found pre-installed model at: {system_model_path}")
                return system_model_path
        
        # If not found anywhere, return the user path (will be created if needed)
        logger.debug(f"No existing model found, will use: {user_model_path}")
        return user_model_path

    def _download_vosk_model(self):
        """Download the VOSK model if it doesn't exist."""
        import zipfile

        import requests
        import tqdm

        model_urls = {
            "small": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            "medium": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
            "large": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",  # Use 0.22 as 0.42 is not available
        }

        url = model_urls.get(self.model_size)
        if not url:
            raise ValueError(f"Unknown model size: {self.model_size}")

        model_name = os.path.basename(url).replace(".zip", "")
        
        # Always download to user's local directory
        model_path = os.path.join(MODELS_DIR, model_name)
        zip_path = os.path.join(MODELS_DIR, os.path.basename(url))
        
        # Create models directory if it doesn't exist
        os.makedirs(MODELS_DIR, exist_ok=True)
        
        logger.info(f"Downloading VOSK {self.model_size} model to user directory: {model_path}")

        # Download the model
        logger.info(f"Downloading VOSK model from {url}")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            total_size = int(response.headers.get("content-length", 0))

            with open(zip_path, "wb") as f:
                for data in tqdm.tqdm(
                    response.iter_content(chunk_size=1024),
                    total=total_size // 1024,
                    unit="KB",
                    desc=f"Downloading {model_name}",  # Add description to progress bar
                ):
                    f.write(data)

            # Extract the model
            logger.info(f"Extracting VOSK model to {model_path}")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(MODELS_DIR)

            # Remove the zip file
            os.remove(zip_path)
            logger.info("VOSK model downloaded and extracted successfully")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download VOSK model from {url}: {e}")
            # Clean up potentially incomplete download
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise RuntimeError(f"Failed to download VOSK model: {e}") from e
        except zipfile.BadZipFile:
            logger.error(f"Downloaded file from {url} is not a valid zip file.")
            # Clean up corrupted download
            if os.path.exists(zip_path):
                os.remove(zip_path)
            raise RuntimeError("Downloaded VOSK model file is corrupted.")
        except Exception as e:
            logger.error(
                f"An error occurred during VOSK model download/extraction: {e}"
            )
            # Clean up potentially corrupted extraction
            if os.path.exists(zip_path):
                os.remove(zip_path)
            # Consider removing partially extracted model dir if needed
            # if os.path.exists(model_path): shutil.rmtree(model_path)
            raise

    def register_text_callback(self, callback: Callable[[str], None]):
        """
        Register a callback function that will be called when text is recognized.

        Args:
            callback: A function that takes a string argument (the recognized text)
        """
        self.text_callbacks.append(callback)

    def unregister_text_callback(self, callback: Callable[[str], None]):
        """
        Unregister a text callback function.

        Args:
            callback: The callback function to remove.
        """
        try:
            self.text_callbacks.remove(callback)
            logger.debug(f"Unregistered text callback: {callback}")
        except ValueError:
            logger.warning(f"Callback {callback} not found in text_callbacks.")

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
        except ImportError as e:
            logger.error(f"Failed to import required audio libraries: {e}")
            logger.error("Please install required dependencies: pip install pyaudio numpy")
            play_error_sound()
            self._update_state(RecognitionState.ERROR)
            return

        try:

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
                    # Ensure vad_sensitivity is treated as integer for calculation
                    try:
                        vad_sens = int(self.vad_sensitivity)
                        threshold = 500 / max(
                            1, min(5, vad_sens)
                        )  # Use self.vad_sensitivity
                    except ValueError:
                        logger.warning(
                            f"Invalid VAD sensitivity value: {self.vad_sensitivity}. Using default 3."
                        )
                        threshold = 500 / 3

                    if volume < threshold:  # Silence
                        silence_counter += CHUNK / RATE  # Convert chunks to seconds
                        if (
                            silence_counter > self.silence_timeout
                        ):  # Use self.silence_timeout
                            logger.debug("Silence detected, processing buffer")
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
            text = self._transcribe_with_whisper(self.audio_buffer)

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

    def reconfigure(
        self,
        engine: Optional[str] = None,
        model_size: Optional[str] = None,
        vad_sensitivity: Optional[int] = None,
        silence_timeout: Optional[float] = None,
        **kwargs,  # Allow for future expansion
    ):
        """
        Reconfigure the speech recognition engine on the fly.

        Args:
            engine: The new speech recognition engine ("vosk" or "whisper").
            model_size: The new model size.
            vad_sensitivity: New VAD sensitivity (for VOSK).
            silence_timeout: New silence timeout (for VOSK).
        """
        logger.info(
            f"Reconfiguring speech engine. New settings: engine={engine}, model_size={model_size}, vad={vad_sensitivity}, silence={silence_timeout}"
        )

        restart_needed = False
        if engine is not None and engine != self.engine:
            self.engine = engine
            restart_needed = True

        if model_size is not None and model_size != self.model_size:
            self.model_size = model_size
            restart_needed = True

        # Update VOSK specific params if provided
        if vad_sensitivity is not None:
            self.vad_sensitivity = max(1, min(5, int(vad_sensitivity)))
        if silence_timeout is not None:
            self.silence_timeout = max(0.5, min(5.0, float(silence_timeout)))

        if restart_needed:
            logger.info("Engine or model changed, re-initializing...")
            # Release old resources explicitly if necessary (Python's GC might handle it)
            self.model = None
            self.recognizer = None
            try:
                if self.engine == "vosk":
                    self._init_vosk()
                elif self.engine == "whisper":
                    self._init_whisper()
                else:
                    raise ValueError(
                        f"Unsupported engine during reconfigure: {self.engine}"
                    )
                logger.info("Speech engine re-initialized successfully.")
            except Exception as e:
                logger.error(
                    f"Failed to re-initialize speech engine: {e}", exc_info=True
                )
                self._update_state(RecognitionState.ERROR)
                # Re-raise or handle appropriately
                raise
        else:
            # If only VOSK params changed, just log it
            logger.info("Applied VAD/silence timeout changes.")
