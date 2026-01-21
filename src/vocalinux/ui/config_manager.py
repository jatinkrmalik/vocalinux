"""
Configuration manager for Vocalinux.

This module handles loading, saving, and accessing user preferences.
"""

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Define constants
CONFIG_DIR = os.path.expanduser("~/.config/vocalinux")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Default configuration
DEFAULT_CONFIG = {
    "speech_recognition": {  # Changed section name
        "engine": "whisper",  # "vosk" or "whisper" - whisper is default for better accuracy
        "model_size": "tiny",  # Current model size (for backward compatibility)
        "vosk_model_size": "small",  # Default model for VOSK engine
        "whisper_model_size": "tiny",  # Default model for Whisper engine
        "vad_sensitivity": 3,  # Voice Activity Detection sensitivity (1-5)
        "silence_timeout": 2.0,  # Seconds of silence before stopping
    },
    "audio": {
        "device_index": None,  # Audio input device index (None for system default)
        "device_name": None,  # Saved device name for display/reference
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
        import copy

        self.config = copy.deepcopy(DEFAULT_CONFIG)
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

            # Check if migration is needed BEFORE merging with defaults
            needs_migration = self._check_needs_migration(user_config)

            # Update the default config with user settings
            self._update_dict_recursive(self.config, user_config)
            logger.info(f"Loaded configuration from {CONFIG_FILE}")

            # Migrate old config format if needed
            if needs_migration:
                self._migrate_config(user_config)

        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def _check_needs_migration(self, user_config: Dict) -> bool:
        """Check if the user config needs migration to add per-engine model sizes."""
        sr_config = user_config.get("speech_recognition", {})
        # Need migration if we have model_size but not the per-engine keys
        return "model_size" in sr_config and (
            "vosk_model_size" not in sr_config or "whisper_model_size" not in sr_config
        )

    def _migrate_config(self, user_config: Dict):
        """Migrate old config formats to the current format."""
        sr_config = self.config.get("speech_recognition", {})
        user_sr_config = user_config.get("speech_recognition", {})

        # Get the current engine and model from the user's original config
        current_engine = user_sr_config.get("engine", "vosk")
        current_model = user_sr_config.get("model_size", "small")

        # Set the per-engine model sizes based on the user's original config
        if "vosk_model_size" not in user_sr_config:
            # If current engine is vosk, use the current model; otherwise use default
            sr_config["vosk_model_size"] = current_model if current_engine == "vosk" else "small"
            logger.info(f"Migrated vosk_model_size to: {sr_config['vosk_model_size']}")

        if "whisper_model_size" not in user_sr_config:
            # If current engine is whisper, use the current model; otherwise use default
            sr_config["whisper_model_size"] = (
                current_model if current_engine == "whisper" else "tiny"
            )
            logger.info(f"Migrated whisper_model_size to: {sr_config['whisper_model_size']}")

        self.save_config()
        logger.info("Config migrated to new per-engine model format")

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

    def save_settings(self):
        """Save the current configuration to the config file."""
        return self.save_config()

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            section: The configuration section
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
            section: The configuration section
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

    def get_model_size_for_engine(self, engine: str) -> str:
        """Get the saved model size for a specific engine.

        Args:
            engine: The engine name ("vosk" or "whisper")

        Returns:
            The model size for the engine, or the default if not found
        """
        sr_config = self.config.get("speech_recognition", {})

        # Try engine-specific model size first
        engine_key = f"{engine.lower()}_model_size"
        if engine_key in sr_config:
            return sr_config[engine_key]

        # Fall back to generic model_size for backward compatibility
        return sr_config.get("model_size", "small" if engine == "vosk" else "tiny")

    def set_model_size_for_engine(self, engine: str, model_size: str):
        """Set the model size for a specific engine.

        Args:
            engine: The engine name ("vosk" or "whisper")
            model_size: The model size to save
        """
        if "speech_recognition" not in self.config:
            self.config["speech_recognition"] = {}

        engine_key = f"{engine.lower()}_model_size"
        self.config["speech_recognition"][engine_key] = model_size
        # Also update the generic model_size for backward compatibility
        self.config["speech_recognition"]["model_size"] = model_size
        logger.info(f"Set {engine} model size to: {model_size}")

    def update_speech_recognition_settings(self, settings: Dict[str, Any]):
        """Update multiple speech recognition settings at once."""
        if "speech_recognition" not in self.config:
            self.config["speech_recognition"] = {}

        # Handle engine-specific model size updates
        if "engine" in settings and "model_size" in settings:
            engine = settings["engine"]
            model_size = settings["model_size"]
            self.set_model_size_for_engine(engine, model_size)

        # Update all other keys present in the provided settings dict
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
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict_recursive(target[key], value)
            else:
                target[key] = value
