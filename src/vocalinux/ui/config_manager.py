"""
Configuration manager for Vocalinux.

This module handles loading, saving, and accessing user preferences.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Define constants
CONFIG_DIR = os.path.expanduser("~/.config/vocalinux")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Default configuration
DEFAULT_CONFIG = {
    "speech_recognition": {  # Changed section name
        "engine": "vosk",  # "vosk" or "whisper"
        "model_size": "small",  # "small", "medium", or "large"
        "vad_sensitivity": 3,  # Voice Activity Detection sensitivity (1-5) - Moved here
        "silence_timeout": 2.0,  # Seconds of silence before stopping recognition - Moved here
    },
    "shortcuts": {
        "toggle_recognition": "ctrl+ctrl",  # Double-tap Ctrl
    },
    "ui": {
        "start_minimized": False,
        "show_notifications": True,
    },
    "advanced": {
        "debug_logging": False,
        "wayland_mode": False,
    },
}


class ConfigManager:
    """
    Manager for user configuration settings.

    This class provides methods for loading, saving, and accessing user
    preferences for the application.
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self.config = DEFAULT_CONFIG.copy()
        self._ensure_config_dir()
        self.load_config()

    def _ensure_config_dir(self):
        """Ensure the configuration directory exists."""
        os.makedirs(CONFIG_DIR, exist_ok=True)

    def load_config(self):
        """
        Load configuration from the config file.

        If the config file doesn't exist, the default configuration is used.
        """
        if not os.path.exists(CONFIG_FILE):
            logger.info(f"Config file not found at {CONFIG_FILE}. Using defaults.")
            return

        try:
            with open(CONFIG_FILE, "r") as f:
                user_config = json.load(f)

            # Update the default config with user settings
            self._update_dict_recursive(self.config, user_config)
            logger.info(f"Loaded configuration from {CONFIG_FILE}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def save_config(self):
        """Save the current configuration to the config file."""
        try:
            # Ensure directory exists before writing
            self._ensure_config_dir()
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)

            logger.info(f"Saved configuration to {CONFIG_FILE}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            section: The configuration section (e.g., "speech_recognition", "shortcuts")
            key: The configuration key within the section
            default: The default value to return if the key doesn't exist

        Returns:
            The configuration value
        """
        try:
            return self.config[section][key]
        except KeyError:
            return default

    def set(self, section: str, key: str, value: Any) -> bool:
        """
        Set a configuration value.

        Args:
            section: The configuration section (e.g., "speech_recognition", "shortcuts")
            key: The configuration key within the section
            value: The value to set

        Returns:
            True if successful, False otherwise
        """
        try:
            if section not in self.config:
                self.config[section] = {}

            self.config[section][key] = value
            return True

        except Exception as e:
            logger.error(f"Failed to set config value: {e}")
            return False

    def get_settings(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary."""
        return self.config

    def update_speech_recognition_settings(self, settings: Dict[str, Any]):
        """Update multiple speech recognition settings at once."""
        if "speech_recognition" not in self.config:
            self.config["speech_recognition"] = {}

        # Only update keys present in the provided settings dict
        for key, value in settings.items():
            self.config["speech_recognition"][key] = value
        logger.info(f"Updated speech recognition settings: {settings}")

    def _update_dict_recursive(self, target: Dict, source: Dict):
        """
        Update a dictionary recursively.

        Args:
            target: The target dictionary to update
            source: The source dictionary with updates
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._update_dict_recursive(target[key], value)
            else:
                target[key] = value
