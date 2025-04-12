#!/usr/bin/env python3
"""
Audio feedback module for Vocalinux.

This module provides audio feedback for various events.
"""

import logging
import os
import threading
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Global variable to track if PyAudio is available and working
_audio_available = False
_pyaudio_instance = None

# Try to initialize PyAudio once at module load time
try:
    import pyaudio
    _pyaudio_instance = pyaudio.PyAudio()
    
    # Test if we can open an output stream
    device_index = None
    for i in range(_pyaudio_instance.get_device_count()):
        device_info = _pyaudio_instance.get_device_info_by_index(i)
        if device_info.get('maxOutputChannels', 0) > 0:
            device_index = i
            break
    
    if device_index is not None:
        try:
            # Try to open a test stream
            test_stream = _pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                output_device_index=device_index,
                frames_per_buffer=1024
            )
            test_stream.close()
            _audio_available = True
            logger.info(f"Audio output available using device: {_pyaudio_instance.get_device_info_by_index(device_index)['name']}")
        except Exception as e:
            logger.warning(f"Could not open audio output stream: {e}")
    else:
        logger.warning("No audio output devices found")
        
except ImportError:
    logger.warning("PyAudio not available, audio feedback will be disabled")
except Exception as e:
    logger.warning(f"Error initializing PyAudio: {e}")


def _get_sound_file_path(sound_name: str) -> Optional[str]:
    """
    Get the path to a sound file.
    
    Args:
        sound_name: Name of the sound file without extension
    
    Returns:
        Path to the sound file, or None if not found
    """
    # Try to find the sound file in the resources directory
    possible_paths = [
        # In development environment
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources", "sounds", f"{sound_name}.wav"),
        # In installed package
        os.path.join("/usr/share/vocalinux/sounds", f"{sound_name}.wav"),
        # In user home directory
        os.path.join(os.path.expanduser("~"), ".local", "share", "vocalinux", "sounds", f"{sound_name}.wav"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    logger.warning(f"Sound file '{sound_name}' not found")
    return None


def play_sound(sound_name: str):
    """
    Play a sound file.
    
    Args:
        sound_name: Name of the sound file without extension
    """
    if not _audio_available:
        logger.warning("Audio feedback not available")
        return
    
    sound_path = _get_sound_file_path(sound_name)
    if not sound_path:
        return
    
    try:
        # Create a thread to avoid blocking the main thread
        threading.Thread(
            target=_play_sound_thread,
            args=(sound_path,),
            daemon=True
        ).start()
    except Exception as e:
        logger.error(f"Error playing sound: {e}")


def _play_sound_thread(sound_path: str):
    """
    Play a sound file in a separate thread.
    
    Args:
        sound_path: Path to the sound file
    """
    try:
        import wave
        
        # Open the wave file
        with wave.open(sound_path, 'rb') as wf:
            # Create PyAudio stream for this file
            if _pyaudio_instance is None:
                logger.error("PyAudio not initialized")
                return
            
            # Find a suitable output device
            device_index = None
            for i in range(_pyaudio_instance.get_device_count()):
                device_info = _pyaudio_instance.get_device_info_by_index(i)
                if device_info.get('maxOutputChannels', 0) > 0:
                    device_index = i
                    break
            
            if device_index is None:
                logger.error("No audio output device available")
                return
                
            try:
                stream = _pyaudio_instance.open(
                    format=_pyaudio_instance.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=device_index
                )
                
                # Read and play the sound
                chunk_size = 1024
                data = wf.readframes(chunk_size)
                
                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)
                
                # Clean up
                stream.stop_stream()
                stream.close()
                
            except Exception as e:
                logger.error(f"PyAudio error: {e}")
                
    except Exception as e:
        logger.error(f"Error playing sound: {e}")


def play_start_sound():
    """Play the sound for starting recording."""
    play_sound("start_recording")


def play_stop_sound():
    """Play the sound for stopping recording."""
    play_sound("stop_recording")


def play_error_sound():
    """Play the sound for error."""
    play_sound("error")


class AudioFeedback:
    """
    Audio feedback manager.
    
    This class manages audio feedback for the application.
    """
    
    def __init__(self):
        """Initialize the audio feedback manager."""
        self.enabled = _audio_available
        
        if not self.enabled:
            logger.warning("Audio feedback is disabled due to missing dependencies or device issues")
    
    def play_start(self):
        """Play the start recording sound."""
        play_start_sound()
    
    def play_stop(self):
        """Play the stop recording sound."""
        play_stop_sound()
    
    def play_error(self):
        """Play the error sound."""
        play_error_sound()