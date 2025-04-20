"""
Audio feedback module for Vocalinux.

This module provides audio feedback for various recognition states.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Update paths to find resources directory at the project root
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(MODULE_DIR)
SRC_DIR = os.path.dirname(PACKAGE_DIR)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
RESOURCES_DIR = os.path.join(PROJECT_ROOT, "resources")
SOUNDS_DIR = os.path.join(RESOURCES_DIR, "sounds")

# Sound file paths
START_SOUND = os.path.join(SOUNDS_DIR, "start_recording.wav")
STOP_SOUND = os.path.join(SOUNDS_DIR, "stop_recording.wav")
ERROR_SOUND = os.path.join(SOUNDS_DIR, "error.wav")


def _get_audio_player():
    """
    Determine the best available audio player on the system.

    Returns:
        tuple: (player_command, supported_formats)
    """
    # Check for PulseAudio paplay (preferred)
    if shutil.which("paplay"):
        return "paplay", ["wav"]

    # Check for ALSA aplay
    if shutil.which("aplay"):
        return "aplay", ["wav"]

    # Check for play (from SoX)
    if shutil.which("play"):
        return "play", ["wav"]

    # Check for mplayer
    if shutil.which("mplayer"):
        return "mplayer", ["wav"]

    # No suitable player found
    logger.warning("No suitable audio player found for sound notifications")
    return None, []


def _play_sound_file(sound_path):
    """
    Play a sound file using the best available player.

    Args:
        sound_path: Path to the sound file

    Returns:
        bool: True if sound was played successfully, False otherwise
    """
    if not os.path.exists(sound_path):
        logger.warning(f"Sound file not found: {sound_path}")
        return False

    player, formats = _get_audio_player()
    if not player:
        return False

    try:
        if player == "paplay":
            subprocess.Popen(
                [player, sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif player == "aplay":
            subprocess.Popen(
                [player, "-q", sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif player == "mplayer":
            subprocess.Popen(
                [player, "-really-quiet", sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif player == "play":
            subprocess.Popen(
                [player, "-q", sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return True
    except Exception as e:
        logger.error(f"Failed to play sound {sound_path}: {e}")
        return False


def play_start_sound():
    """
    Play the sound for starting voice recognition.

    Returns:
        bool: True if sound was played successfully, False otherwise
    """
    return _play_sound_file(START_SOUND)


def play_stop_sound():
    """
    Play the sound for stopping voice recognition.

    Returns:
        bool: True if sound was played successfully, False otherwise
    """
    return _play_sound_file(STOP_SOUND)


def play_error_sound():
    """
    Play the sound for error notifications.

    Returns:
        bool: True if sound was played successfully, False otherwise
    """
    return _play_sound_file(ERROR_SOUND)
