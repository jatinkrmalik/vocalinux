#!/usr/bin/env python3
"""
Audio feedback module for Vocalinux.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Determine the sounds directory
PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_SOUNDS_DIR = os.path.join(PACKAGE_DIR, "resources", "sounds")
USER_SOUNDS_DIR = os.path.expanduser("~/.local/share/vocalinux/sounds")

# Sound file paths - first check user directory, then fall back to package directory
def get_sound_path(filename):
    """Get the path to a sound file, preferring user sounds if available."""
    user_path = os.path.join(USER_SOUNDS_DIR, filename)
    default_path = os.path.join(DEFAULT_SOUNDS_DIR, filename)
    
    if os.path.exists(user_path):
        return user_path
    elif os.path.exists(default_path):
        return default_path
    else:
        logger.warning(f"Sound file not found: {filename}")
        return None

# Files for different notification sounds
START_SOUND = "start_recording"
STOP_SOUND = "stop_recording"
ERROR_SOUND = "error"

class AudioFeedback:
    """
    Audio feedback system for application events.
    
    Plays sounds for different application events like
    starting/stopping recording and errors.
    """

    def __init__(self):
        """Initialize the audio feedback system."""
        self.enabled = True
        
        # Create the user sounds directory if it doesn't exist
        os.makedirs(USER_SOUNDS_DIR, exist_ok=True)
        
    def enable(self):
        """Enable audio feedback."""
        self.enabled = True
        
    def disable(self):
        """Disable audio feedback."""
        self.enabled = False
        
    def play_sound(self, sound_name):
        """
        Play a sound.
        
        Args:
            sound_name: The name of the sound to play (without extension)
        """
        if not self.enabled:
            return
            
        # Check for mp3 first, then fall back to wav
        for ext in ["mp3", "wav"]:
            sound_path = get_sound_path(f"{sound_name}.{ext}")
            if sound_path:
                break
        
        if not sound_path:
            logger.error(f"No sound file found for {sound_name}")
            return
            
        try:
            # Use different players depending on platform
            command = None
            
            if sys.platform == "linux":
                # Try paplay (PulseAudio) first, then fall back to aplay (ALSA)
                if os.path.exists("/usr/bin/paplay"):
                    command = ["paplay", sound_path]
                elif os.path.exists("/usr/bin/aplay"):
                    command = ["aplay", "-q", sound_path]
            
            if command:
                # Run the command in the background
                subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.debug(f"Playing sound: {sound_path}")
            else:
                logger.warning("No suitable audio player found")
                
        except Exception as e:
            logger.error(f"Failed to play sound {sound_name}: {str(e)}")
            
    def play_start(self):
        """Play the recording start sound."""
        self.play_sound(START_SOUND)
        
    def play_stop(self):
        """Play the recording stop sound."""
        self.play_sound(STOP_SOUND)
        
    def play_error(self):
        """Play the error sound."""
        self.play_sound(ERROR_SOUND)