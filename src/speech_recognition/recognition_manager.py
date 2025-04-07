"""
Speech recognition manager module for Ubuntu Voice Typing.

This module provides a unified interface to different speech recognition engines,
currently supporting VOSK and Whisper.
"""

import json
import logging
import os
import threading
import time
from enum import Enum, auto
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

# Define constants
MODELS_DIR = os.path.expanduser("~/.local/share/ubuntu-voice-typing/models")


class RecognitionState(Enum):
    """Enum representing the state of the speech recognition system."""
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    ERROR = auto()


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
        self.text_callbacks: List[Callable[[str], None]] = []
        self.state_callbacks: List[Callable[[RecognitionState], None]] = []
        
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
            from vosk import Model, KaldiRecognizer
            self.vosk_model_path = self._get_vosk_model_path()
            
            if not os.path.exists(self.vosk_model_path):
                logger.info(f"VOSK model not found at {self.vosk_model_path}. Downloading...")
                self._download_vosk_model()
            
            logger.info(f"Loading VOSK model from {self.vosk_model_path}")
            self.model = Model(self.vosk_model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            
        except ImportError:
            logger.error("Failed to import VOSK. Please install it with 'pip install vosk'")
            self.state = RecognitionState.ERROR
            raise
    
    def _init_whisper(self):
        """Initialize the Whisper speech recognition engine."""
        try:
            import whisper
            
            logger.info(f"Loading Whisper {self.model_size} model")
            self.model = whisper.load_model(self.model_size)
            
        except ImportError:
            logger.error("Failed to import Whisper. Please install it with 'pip install whisper torch'")
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
        import requests
        import tqdm
        import zipfile
        
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
            for data in tqdm.tqdm(response.iter_content(chunk_size=1024), total=total_size//1024, unit="KB"):
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
        self._update_state(RecognitionState.IDLE)
        
        # Stop the audio and recognition threads
        if self.audio_thread and self.audio_thread.is_alive():
            # Signal thread to stop
            self.audio_thread.join(timeout=1.0)
        
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=1.0)
    
    def _record_audio(self):
        """Record audio from the microphone."""
        # TODO: Implement audio recording based on the selected engine
        # This will use PyAudio or similar to record audio and feed it to the recognition engine
        pass
    
    def _perform_recognition(self):
        """Perform speech recognition on the recorded audio."""
        # TODO: Implement speech recognition based on the selected engine
        # This will process the audio and call the registered text callbacks with the results
        pass
    
    def process_commands(self, text: str) -> str:
        """
        Process text commands in the recognized text.
        
        Args:
            text: The recognized text to process
            
        Returns:
            The processed text with commands handled
        """
        # TODO: Implement command processing (e.g., "new line", "delete that", etc.)
        return text