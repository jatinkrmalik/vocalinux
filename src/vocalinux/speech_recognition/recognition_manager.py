"""
Speech recognition manager module for Vocalinux.

This module provides a unified interface to different speech recognition engines,
currently supporting VOSK and Whisper.
"""

import ctypes
import json
import logging
import os
import threading
import time
from typing import Callable, List, Optional

from ..common_types import RecognitionState
from ..ui.audio_feedback import play_error_sound, play_start_sound, play_stop_sound
from .command_processor import CommandProcessor


# ALSA error handler to suppress warnings during PyAudio initialization
def _setup_alsa_error_handler():
    """Set up an error handler to suppress ALSA warnings."""
    try:
        asound = ctypes.CDLL("libasound.so.2")
        # Define error handler type
        ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
            None,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
        )

        # Create a no-op error handler
        def _error_handler(filename, line, function, err, fmt):
            pass

        _alsa_error_handler = ERROR_HANDLER_FUNC(_error_handler)
        asound.snd_lib_error_set_handler(_alsa_error_handler)
        return _alsa_error_handler  # Keep reference to prevent GC
    except (OSError, AttributeError):
        # ALSA not available or different platform
        return None


# Set up ALSA error handler at module load time
_alsa_handler = _setup_alsa_error_handler()


def get_audio_input_devices() -> list:
    """
    Get a list of available audio input devices.

    Returns:
        List of tuples: (device_index, device_name, is_default)
    """
    devices = []
    try:
        import pyaudio

        audio = pyaudio.PyAudio()

        default_input_device = None
        try:
            default_info = audio.get_default_input_device_info()
            default_input_device = default_info.get("index")
        except (IOError, OSError):
            pass  # No default input device

        for i in range(audio.get_device_count()):
            try:
                info = audio.get_device_info_by_index(i)
                # Only include devices that have input channels
                if info.get("maxInputChannels", 0) > 0:
                    name = info.get("name", f"Device {i}")
                    is_default = i == default_input_device
                    devices.append((i, name, is_default))
            except (IOError, OSError):
                continue

        audio.terminate()
    except ImportError:
        logger.error("PyAudio not installed, cannot enumerate audio devices")
    except Exception as e:
        logger.error(f"Error enumerating audio devices: {e}")

    return devices


def test_audio_input(device_index: int = None, duration: float = 1.0) -> dict:
    """
    Test audio input from a device and return diagnostic information.

    Args:
        device_index: The device index to test (None for default)
        duration: How long to record in seconds

    Returns:
        Dictionary with test results including:
        - success: bool
        - device_name: str
        - sample_count: int
        - max_amplitude: float
        - mean_amplitude: float
        - has_signal: bool (amplitude above noise floor)
        - error: str (if failed)
    """
    result = {
        "success": False,
        "device_name": "Unknown",
        "device_index": device_index,
        "sample_count": 0,
        "max_amplitude": 0.0,
        "mean_amplitude": 0.0,
        "has_signal": False,
        "error": None,
    }

    try:
        import numpy as np
        import pyaudio

        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000

        audio = pyaudio.PyAudio()

        # Get device info
        try:
            if device_index is not None:
                info = audio.get_device_info_by_index(device_index)
            else:
                info = audio.get_default_input_device_info()
                device_index = info.get("index")
            result["device_name"] = info.get("name", "Unknown")
            result["device_index"] = device_index
        except (IOError, OSError) as e:
            result["error"] = f"Cannot get device info: {e}"
            audio.terminate()
            return result

        # Open stream
        try:
            stream_kwargs = {
                "format": FORMAT,
                "channels": CHANNELS,
                "rate": RATE,
                "input": True,
                "frames_per_buffer": CHUNK,
            }
            if device_index is not None:
                stream_kwargs["input_device_index"] = device_index

            stream = audio.open(**stream_kwargs)
        except (IOError, OSError) as e:
            result["error"] = f"Cannot open audio stream: {e}"
            audio.terminate()
            return result

        # Record and analyze
        all_amplitudes = []
        frames_to_read = int(RATE * duration / CHUNK)

        for _ in range(frames_to_read):
            try:
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.int16)
                amplitudes = np.abs(audio_data)
                all_amplitudes.extend(amplitudes)
            except Exception as e:
                result["error"] = f"Error reading audio: {e}"
                break

        stream.stop_stream()
        stream.close()
        audio.terminate()

        if all_amplitudes:
            all_amplitudes = np.array(all_amplitudes)
            result["success"] = True
            result["sample_count"] = len(all_amplitudes)
            result["max_amplitude"] = float(np.max(all_amplitudes))
            result["mean_amplitude"] = float(np.mean(all_amplitudes))
            # Signal present if max amplitude is above typical digital noise floor
            # 16-bit audio has max value of 32768, noise floor is typically < 100
            result["has_signal"] = result["max_amplitude"] > 200

    except ImportError as e:
        result["error"] = f"Missing dependency: {e}"
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"

    return result


logger = logging.getLogger(__name__)


def _show_notification(title: str, message: str, icon: str = "dialog-warning"):
    """Show a desktop notification."""
    try:
        import subprocess

        # Use notify-send which is available on most Linux desktops
        subprocess.Popen(
            ["notify-send", "-i", icon, "-a", "Vocalinux", title, message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        logger.debug(f"Could not show notification: {e}")


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

    def __init__(
        self, engine: str = "vosk", model_size: str = "small", defer_download: bool = True, **kwargs
    ):
        """
        Initialize the speech recognition manager.

        Args:
            engine: The speech recognition engine to use ("vosk" or "whisper")
            model_size: The size of the model to use ("small", "medium", "large")
            defer_download: If True, don't download missing models at startup (default: True)
            audio_device_index: Optional audio input device index (None for default)
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

        # Download progress tracking
        self._download_progress_callback: Optional[Callable[[float, float, str], None]] = None
        self._download_cancelled = False
        self._defer_download = defer_download
        self._model_initialized = False

        # Speech detection parameters (load defaults, will be overridden by configure)
        self.vad_sensitivity = kwargs.get("vad_sensitivity", 3)
        self.silence_timeout = kwargs.get("silence_timeout", 2.0)

        # Audio device selection (None means use system default)
        self.audio_device_index = kwargs.get("audio_device_index", None)

        # Audio diagnostics tracking
        self._last_audio_level = 0.0
        self._audio_level_callbacks: List[Callable[[float], None]] = []

        # Recording control flags
        self.should_record = False
        self.audio_buffer = []

        # Create models directory if it doesn't exist
        os.makedirs(MODELS_DIR, exist_ok=True)

        logger.info(f"Initializing speech recognition with {engine} engine and {model_size} model")

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
                if self._defer_download:
                    logger.info(
                        f"VOSK model not found at {self.vosk_model_path}. Will download when needed."
                    )
                    self._model_initialized = False
                    return  # Don't block startup
                else:
                    logger.info(f"VOSK model not found at {self.vosk_model_path}. Downloading...")
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
            self._model_initialized = True
            logger.info("VOSK engine initialized successfully.")

        except ImportError:
            logger.error("Failed to import VOSK. Please install it with 'pip install vosk'")
            self.state = RecognitionState.ERROR
            raise

    def _init_whisper(self):
        """Initialize the Whisper speech recognition engine."""
        import warnings

        try:
            import whisper

            # Suppress CUDA warnings during import
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import torch

            # Validate model size for Whisper
            valid_whisper_models = ["tiny", "base", "small", "medium", "large"]
            if self.model_size not in valid_whisper_models:
                logger.warning(
                    f"Model size '{self.model_size}' not valid for Whisper. "
                    f"Valid options: {valid_whisper_models}. Using 'base' instead."
                )
                self.model_size = "base"

            # Check if model is downloaded
            whisper_cache_dir = os.path.join(MODELS_DIR, "whisper")
            os.makedirs(whisper_cache_dir, exist_ok=True)
            model_file = os.path.join(whisper_cache_dir, f"{self.model_size}.pt")
            default_cache = os.path.expanduser("~/.cache/whisper")
            default_model_file = os.path.join(default_cache, f"{self.model_size}.pt")

            model_exists = os.path.exists(model_file) or os.path.exists(default_model_file)

            if not model_exists and self._defer_download:
                logger.info(
                    f"Whisper model '{self.model_size}' not found. Will download when needed."
                )
                self._model_initialized = False
                return  # Don't block startup

            # If model doesn't exist and we're not deferring, download it with progress
            if not model_exists:
                logger.info(f"Downloading Whisper '{self.model_size}' model...")
                self._download_whisper_model(whisper_cache_dir)

            # Determine device (GPU if available, otherwise CPU)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")

            logger.info(f"Loading Whisper '{self.model_size}' model...")
            # Ensure previous model is released if re-initializing
            self.model = None

            # Load model with device and custom cache directory
            self.model = whisper.load_model(
                self.model_size, device=device, download_root=whisper_cache_dir
            )

            self._model_initialized = True
            logger.info(f"Whisper model loaded on {device.upper()}")
            logger.info("Whisper engine initialized successfully.")

        except ImportError as e:
            logger.error(f"Failed to import required libraries for Whisper: {e}")
            logger.error("Please install with: pip install openai-whisper torch")
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
            audio_buffer: List of audio data chunks (16-bit PCM at 16kHz)

        Returns:
            Transcribed text
        """
        import warnings

        try:
            import numpy as np

            if not audio_buffer:
                return ""

            # Convert audio buffer to numpy array
            audio_data = np.frombuffer(b"".join(audio_buffer), dtype=np.int16)

            # Convert to float32 and normalize to [-1, 1] (Whisper expects this format)
            audio_float = audio_data.astype(np.float32) / 32768.0

            duration = len(audio_float) / 16000.0  # 16kHz sample rate
            logger.debug(f"Transcribing audio: {duration:.2f} seconds")

            # Determine if we should use fp16 (only on CUDA)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import torch
            use_fp16 = self.model.device != torch.device("cpu")

            # Transcribe with Whisper (handles variable length audio automatically)
            result = self.model.transcribe(
                audio_float,
                language="en",
                task="transcribe",
                verbose=False,
                temperature=0.0,  # Greedy decoding for consistency
                no_speech_threshold=0.6,
                fp16=use_fp16,  # Explicitly set to avoid warning on CPU
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

    def set_download_progress_callback(
        self, callback: Optional[Callable[[float, float, str], None]]
    ):
        """
        Set a callback for download progress updates.

        Args:
            callback: Function(progress_fraction, speed_mbps, status_text)
                      or None to clear
        """
        self._download_progress_callback = callback

    def cancel_download(self):
        """Request cancellation of the current download."""
        self._download_cancelled = True
        logger.info("Download cancellation requested")

    def _download_vosk_model(self):
        """Download the VOSK model if it doesn't exist."""
        import zipfile

        import requests

        self._download_cancelled = False

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
            downloaded_size = 0
            start_time = time.time()
            last_update_time = start_time
            chunk_size = 8192  # 8KB chunks for smoother progress

            with open(zip_path, "wb") as f:
                for data in response.iter_content(chunk_size=chunk_size):
                    if self._download_cancelled:
                        logger.info("Download cancelled by user")
                        f.close()
                        if os.path.exists(zip_path):
                            os.remove(zip_path)
                        raise RuntimeError("Download cancelled")

                    f.write(data)
                    downloaded_size += len(data)

                    # Update progress callback
                    current_time = time.time()
                    if (
                        self._download_progress_callback
                        and (current_time - last_update_time) >= 0.1
                    ):
                        elapsed = current_time - start_time
                        if elapsed > 0:
                            speed_mbps = (downloaded_size / (1024 * 1024)) / elapsed
                        else:
                            speed_mbps = 0

                        if total_size > 0:
                            progress = downloaded_size / total_size
                            remaining_mb = (total_size - downloaded_size) / (1024 * 1024)
                            if speed_mbps > 0:
                                eta_seconds = remaining_mb / speed_mbps
                                eta_str = (
                                    f"{int(eta_seconds)}s"
                                    if eta_seconds < 60
                                    else f"{int(eta_seconds / 60)}m {int(eta_seconds % 60)}s"
                                )
                            else:
                                eta_str = "--"
                            status = f"{downloaded_size / (1024 * 1024):.1f} / {total_size / (1024 * 1024):.1f} MB • {speed_mbps:.1f} MB/s • ETA: {eta_str}"
                        else:
                            progress = 0
                            status = (
                                f"{downloaded_size / (1024 * 1024):.1f} MB • {speed_mbps:.1f} MB/s"
                            )

                        self._download_progress_callback(progress, speed_mbps, status)
                        last_update_time = current_time

                        # Also log progress periodically
                        logger.info(f"Download progress: {progress * 100:.1f}% - {status}")

            # Update status for extraction phase
            if self._download_progress_callback:
                self._download_progress_callback(1.0, 0, "Extracting model...")

            # Extract the model
            logger.info(f"Extracting VOSK model to {model_path}")
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(MODELS_DIR)

            # Remove the zip file
            os.remove(zip_path)
            logger.info("VOSK model downloaded and extracted successfully")

            # Final status
            if self._download_progress_callback:
                self._download_progress_callback(1.0, 0, "Complete!")

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
            logger.error(f"An error occurred during VOSK model download/extraction: {e}")
            # Clean up potentially corrupted extraction
            if os.path.exists(zip_path):
                os.remove(zip_path)
            # Consider removing partially extracted model dir if needed
            # if os.path.exists(model_path): shutil.rmtree(model_path)
            raise

    def _download_whisper_model(self, cache_dir: str):
        """Download a Whisper model with progress tracking."""
        import requests

        self._download_cancelled = False

        # Whisper model URLs (from openai-whisper package)
        model_urls = {
            "tiny": "https://openaipublic.azureedge.net/main/whisper/models/"
            "65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/"
            "tiny.pt",
            "base": "https://openaipublic.azureedge.net/main/whisper/models/"
            "ed3a0b6b1c0edf879ad9b11b1af5a0e6ab5db9205f891f668f8b0e6c6326e34e/"
            "base.pt",
            "small": "https://openaipublic.azureedge.net/main/whisper/models/"
            "9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/"
            "small.pt",
            "medium": "https://openaipublic.azureedge.net/main/whisper/models/"
            "345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/"
            "medium.pt",
            "large": "https://openaipublic.azureedge.net/main/whisper/models/"
            "e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/"
            "large-v3.pt",
        }

        url = model_urls.get(self.model_size)
        if not url:
            raise ValueError(f"Unknown Whisper model size: {self.model_size}")

        model_file = os.path.join(cache_dir, f"{self.model_size}.pt")
        temp_file = model_file + ".tmp"

        os.makedirs(cache_dir, exist_ok=True)

        logger.info(f"Downloading Whisper {self.model_size} model to {model_file}")
        logger.info(f"Downloading from {url}")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            start_time = time.time()
            last_update_time = start_time
            chunk_size = 8192  # 8KB chunks

            with open(temp_file, "wb") as f:
                for data in response.iter_content(chunk_size=chunk_size):
                    if self._download_cancelled:
                        logger.info("Download cancelled by user")
                        f.close()
                        if os.path.exists(temp_file):
                            os.remove(temp_file)
                        raise RuntimeError("Download cancelled")

                    f.write(data)
                    downloaded_size += len(data)

                    # Update progress callback
                    current_time = time.time()
                    if (
                        self._download_progress_callback
                        and (current_time - last_update_time) >= 0.1
                    ):
                        elapsed = current_time - start_time
                        if elapsed > 0:
                            speed_mbps = (downloaded_size / (1024 * 1024)) / elapsed
                        else:
                            speed_mbps = 0

                        if total_size > 0:
                            progress = downloaded_size / total_size
                            remaining_mb = (total_size - downloaded_size) / (1024 * 1024)
                            if speed_mbps > 0:
                                eta_seconds = remaining_mb / speed_mbps
                                eta_str = (
                                    f"{int(eta_seconds)}s"
                                    if eta_seconds < 60
                                    else f"{int(eta_seconds / 60)}m {int(eta_seconds % 60)}s"
                                )
                            else:
                                eta_str = "--"
                            status = f"{downloaded_size / (1024 * 1024):.1f} / {total_size / (1024 * 1024):.1f} MB • {speed_mbps:.1f} MB/s • ETA: {eta_str}"
                        else:
                            progress = 0
                            status = (
                                f"{downloaded_size / (1024 * 1024):.1f} MB • {speed_mbps:.1f} MB/s"
                            )

                        self._download_progress_callback(progress, speed_mbps, status)
                        last_update_time = current_time

                        logger.info(f"Download progress: {progress * 100:.1f}% - {status}")

            # Rename temp file to final
            os.rename(temp_file, model_file)
            logger.info("Whisper model downloaded successfully")

            if self._download_progress_callback:
                self._download_progress_callback(1.0, 0, "Complete!")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download Whisper model from {url}: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise RuntimeError(f"Failed to download Whisper model: {e}") from e
        except Exception as e:
            logger.error(f"An error occurred during Whisper model download: {e}")
            if os.path.exists(temp_file):
                os.remove(temp_file)
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

    def get_text_callbacks(self) -> List[Callable[[str], None]]:
        """Get a copy of the current text callbacks list."""
        return list(self.text_callbacks)

    def set_text_callbacks(self, callbacks: List[Callable[[str], None]]):
        """Set the text callbacks list (used for temporarily replacing callbacks)."""
        self.text_callbacks = list(callbacks)

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

    def register_audio_level_callback(self, callback: Callable[[float], None]):
        """
        Register a callback function that will be called with audio level updates.

        Args:
            callback: A function that takes a float argument (0-100 representing audio level %)
        """
        self._audio_level_callbacks.append(callback)

    def unregister_audio_level_callback(self, callback: Callable[[float], None]):
        """
        Unregister an audio level callback function.

        Args:
            callback: The callback function to remove.
        """
        try:
            self._audio_level_callbacks.remove(callback)
        except ValueError:
            pass

    def set_audio_device(self, device_index: Optional[int]):
        """
        Set the audio input device to use.

        Args:
            device_index: The device index to use, or None for system default
        """
        if device_index != self.audio_device_index:
            logger.info(f"Audio device changed from {self.audio_device_index} to {device_index}")
            self.audio_device_index = device_index

    def get_audio_device(self) -> Optional[int]:
        """Get the currently configured audio device index."""
        return self.audio_device_index

    def get_last_audio_level(self) -> float:
        """Get the last recorded audio level (0-100)."""
        return self._last_audio_level

    def _update_state(self, new_state: RecognitionState):
        """
        Update the recognition state and notify callbacks.

        Args:
            new_state: The new recognition state
        """
        self.state = new_state
        for callback in self.state_callbacks:
            callback(new_state)

    @property
    def model_ready(self) -> bool:
        """Check if the model is initialized and ready for recognition."""
        return self._model_initialized and self.model is not None

    def start_recognition(self):
        """Start the speech recognition process."""
        if self.state != RecognitionState.IDLE:
            logger.warning(f"Cannot start recognition in current state: {self.state}")
            return

        # Check if model is ready
        if not self.model_ready:
            logger.warning(
                "Cannot start recognition: model not downloaded. " "Please download via Settings."
            )
            play_error_sound()
            _show_notification(
                "No Speech Model",
                "Please open Settings and download a speech recognition model " "to use dictation.",
                "dialog-warning",
            )
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

        # Process any remaining audio in the buffer before going idle
        if self.audio_buffer:
            logger.debug("Processing remaining audio buffer before stopping")
            self._update_state(RecognitionState.PROCESSING)
            self._process_final_buffer()
            self.audio_buffer = []

        self._update_state(RecognitionState.IDLE)

    def _record_audio(self):
        """Record audio from the microphone."""
        # Lazy import to avoid circular dependency
        from ..ui.audio_feedback import play_error_sound  # noqa: F401

        try:
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

            # Log available devices for debugging
            logger.debug("Available audio input devices:")
            for i in range(audio.get_device_count()):
                try:
                    info = audio.get_device_info_by_index(i)
                    if info.get("maxInputChannels", 0) > 0:
                        logger.debug(
                            f"  [{i}] {info.get('name')} (inputs: {info.get('maxInputChannels')})"
                        )
                except (IOError, OSError):
                    continue

            # Open microphone stream with optional device selection
            stream_kwargs = {
                "format": FORMAT,
                "channels": CHANNELS,
                "rate": RATE,
                "input": True,
                "frames_per_buffer": CHUNK,
            }

            # Use specified device if set, otherwise use system default
            if self.audio_device_index is not None:
                stream_kwargs["input_device_index"] = self.audio_device_index
                try:
                    device_info = audio.get_device_info_by_index(self.audio_device_index)
                    logger.info(
                        f"Using audio device [{self.audio_device_index}]: {device_info.get('name')}"
                    )
                except (IOError, OSError):
                    logger.warning(f"Could not get info for device index {self.audio_device_index}")
            else:
                try:
                    default_device = audio.get_default_input_device_info()
                    logger.info(
                        f"Using default audio device [{default_device.get('index')}]: {default_device.get('name')}"
                    )
                except (IOError, OSError):
                    logger.warning("Could not get default input device info")

            try:
                stream = audio.open(**stream_kwargs)
            except (IOError, OSError) as e:
                logger.error(f"Failed to open audio stream: {e}")
                logger.error("This may indicate a problem with the audio device or permissions.")
                play_error_sound()
                audio.terminate()
                self._update_state(RecognitionState.ERROR)
                return

            logger.info("Audio recording started")

            # Record audio while should_record is True
            silence_counter = 0
            speech_detected_in_session = False
            log_level_interval = 0  # Counter for periodic level logging
            max_level_seen = 0.0

            while self.should_record:
                try:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    self.audio_buffer.append(data)

                    # Simple Voice Activity Detection (VAD)
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    volume = np.abs(audio_data).mean()

                    # Track max level and notify callbacks
                    # Normalize to 0-100 scale (16-bit audio max is ~32768)
                    normalized_level = min(100.0, (volume / 327.68))
                    self._last_audio_level = normalized_level
                    max_level_seen = max(max_level_seen, normalized_level)

                    # Notify audio level callbacks
                    for callback in self._audio_level_callbacks:
                        try:
                            callback(normalized_level)
                        except Exception as e:
                            logger.debug(f"Audio level callback error: {e}")

                    # Log audio levels periodically for debugging
                    log_level_interval += 1
                    if log_level_interval >= 50:  # Every ~3 seconds at 16kHz/1024 chunks
                        logger.debug(
                            f"Audio level: current={normalized_level:.1f}%, max_seen={max_level_seen:.1f}%"
                        )
                        log_level_interval = 0

                    # Threshold based on sensitivity (1-5)
                    # Ensure vad_sensitivity is treated as integer for calculation
                    try:
                        vad_sens = int(self.vad_sensitivity)
                        threshold = 500 / max(1, min(5, vad_sens))  # Use self.vad_sensitivity
                    except ValueError:
                        logger.warning(
                            f"Invalid VAD sensitivity value: {self.vad_sensitivity}. Using default 3."
                        )
                        threshold = 500 / 3

                    if volume < threshold:  # Silence
                        silence_counter += CHUNK / RATE  # Convert chunks to seconds
                        if silence_counter > self.silence_timeout:  # Use self.silence_timeout
                            if len(self.audio_buffer) > 0:
                                logger.debug("Silence detected, processing buffer")
                                self._update_state(RecognitionState.PROCESSING)
                                # Process final buffer
                                self._process_final_buffer()
                                # Reset for next utterance
                                self.audio_buffer = []
                            silence_counter = 0
                            self._update_state(RecognitionState.LISTENING)
                    else:  # Speech
                        if not speech_detected_in_session:
                            logger.debug(
                                f"Speech detected (level={normalized_level:.1f}%, "
                                f"threshold={500 / max(1, min(5, int(self.vad_sensitivity))):.0f})"
                            )
                            speech_detected_in_session = True
                        silence_counter = 0
                except Exception as e:
                    logger.error(f"Error reading audio data: {e}")
                    break

            # Clean up
            stream.stop_stream()
            stream.close()
            audio.terminate()

            # Log summary
            if not speech_detected_in_session and max_level_seen < 5:
                logger.warning(
                    f"No speech detected during session. Max audio level was "
                    f"only {max_level_seen:.1f}%. This may indicate the wrong "
                    "audio device is selected or the microphone is muted."
                )

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
        audio_device_index: Optional[int] = None,
        force_download: bool = True,
        **kwargs,  # Allow for future expansion
    ):
        """
        Reconfigure the speech recognition engine on the fly.

        Args:
            engine: The new speech recognition engine ("vosk" or "whisper").
            model_size: The new model size.
            vad_sensitivity: New VAD sensitivity (for VOSK).
            silence_timeout: New silence timeout (for VOSK).
            audio_device_index: Audio input device index (None for default, -1 to clear).
            force_download: If True, download missing models (default: True for UI-triggered reconfigures).
        """
        logger.info(
            f"Reconfiguring speech engine. New settings: engine={engine}, model_size={model_size}, vad={vad_sensitivity}, silence={silence_timeout}, audio_device={audio_device_index}"
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

        # Handle audio device index (-1 means use default/clear selection)
        if audio_device_index is not None:
            if audio_device_index == -1:
                self.audio_device_index = None
            else:
                self.audio_device_index = audio_device_index

        if restart_needed:
            logger.info("Engine or model changed, re-initializing...")
            # When reconfiguring from UI, allow downloads
            old_defer = self._defer_download
            self._defer_download = not force_download
            # Release old resources explicitly if necessary (Python's GC might handle it)
            self.model = None
            self.recognizer = None
            try:
                if self.engine == "vosk":
                    self._init_vosk()
                elif self.engine == "whisper":
                    self._init_whisper()
                else:
                    raise ValueError(f"Unsupported engine during reconfigure: {self.engine}")
                logger.info("Speech engine re-initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to re-initialize speech engine: {e}", exc_info=True)
                self._update_state(RecognitionState.ERROR)
                # Re-raise or handle appropriately
                raise
            finally:
                self._defer_download = old_defer
        else:
            # If only VOSK params changed, just log it
            logger.info("Applied VAD/silence timeout changes.")
