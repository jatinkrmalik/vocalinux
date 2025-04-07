"""
Audio feedback module for Ubuntu Voice Typing.

This module provides audio feedback for various recognition states.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Find the resources directory relative to this module
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(MODULE_DIR)
RESOURCES_DIR = os.path.join(os.path.dirname(PACKAGE_DIR), "resources")
SOUNDS_DIR = os.path.join(RESOURCES_DIR, "sounds")

# Sound file paths
START_SOUND_MP3 = os.path.join(SOUNDS_DIR, "start_recording.mp3")
STOP_SOUND_MP3 = os.path.join(SOUNDS_DIR, "stop_recording.mp3")
ERROR_SOUND_MP3 = os.path.join(SOUNDS_DIR, "error.mp3")

# Fallback WAV files (if MP3 not supported)
START_SOUND_WAV = os.path.join(SOUNDS_DIR, "start_recording.wav")
STOP_SOUND_WAV = os.path.join(SOUNDS_DIR, "stop_recording.wav")
ERROR_SOUND_WAV = os.path.join(SOUNDS_DIR, "error.wav")


def _get_audio_player():
    """
    Determine the best available audio player on the system.
    
    Returns:
        tuple: (player_command, format_supported)
    """
    # Check for PulseAudio paplay (preferred)
    if shutil.which("paplay"):
        return "paplay", ["mp3", "wav"]
    
    # Check for ALSA aplay
    if shutil.which("aplay"):
        return "aplay", ["wav"]
    
    # Check for mpg123 (MP3 player)
    if shutil.which("mpg123"):
        return "mpg123", ["mp3"]
    
    # Check for mplayer
    if shutil.which("mplayer"):
        return "mplayer", ["mp3", "wav"]
    
    # No suitable player found
    logger.warning("No suitable audio player found for sound notifications")
    return None, []


def _play_sound_file(sound_path):
    """
    Play a sound file using the best available player.
    
    Args:
        sound_path: Path to the sound file
    """
    if not os.path.exists(sound_path):
        logger.warning(f"Sound file not found: {sound_path}")
        return False
    
    player, formats = _get_audio_player()
    if not player:
        return False
    
    file_ext = os.path.splitext(sound_path)[1].lower().lstrip('.')
    if file_ext not in formats:
        logger.warning(f"Format {file_ext} not supported by {player}")
        return False
    
    try:
        if player == "paplay":
            subprocess.Popen([player, sound_path], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        elif player == "aplay":
            subprocess.Popen([player, "-q", sound_path], 
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        elif player == "mpg123":
            subprocess.Popen([player, "-q", sound_path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        elif player == "mplayer":
            subprocess.Popen([player, "-really-quiet", sound_path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.error(f"Failed to play sound {sound_path}: {e}")
        return False


def play_start_sound():
    """Play the sound for starting voice recognition."""
    # Try MP3 first, then fall back to WAV if needed
    if os.path.exists(START_SOUND_MP3):
        if _play_sound_file(START_SOUND_MP3):
            return
    
    # Try WAV as fallback
    if os.path.exists(START_SOUND_WAV):
        _play_sound_file(START_SOUND_WAV)


def play_stop_sound():
    """Play the sound for stopping voice recognition."""
    # Try MP3 first, then fall back to WAV if needed
    if os.path.exists(STOP_SOUND_MP3):
        if _play_sound_file(STOP_SOUND_MP3):
            return
    
    # Try WAV as fallback
    if os.path.exists(STOP_SOUND_WAV):
        _play_sound_file(STOP_SOUND_WAV)


def play_error_sound():
    """Play the sound for error notifications."""
    # Try MP3 first, then fall back to WAV if needed
    if os.path.exists(ERROR_SOUND_MP3):
        if _play_sound_file(ERROR_SOUND_MP3):
            return
    
    # Try WAV as fallback
    if os.path.exists(ERROR_SOUND_WAV):
        _play_sound_file(ERROR_SOUND_WAV)