"""
Environment detection and configuration module for Vocalinux.

This module provides centralized environment detection and configuration
to allow the application to adapt to different environments (development,
testing, production, CI, etc.)
"""

import logging
import os
import shutil
import subprocess
import sys
from typing import Set

logger = logging.getLogger(__name__)

# Environment types
ENV_DEVELOPMENT = "development"
ENV_TESTING = "testing"
ENV_CI = "ci"
ENV_PRODUCTION = "production"

# Features that can be enabled/disabled based on environment
FEATURE_AUDIO = "audio"
FEATURE_KEYBOARD = "keyboard"
FEATURE_GUI = "gui"


class EnvironmentManager:
    """
    Manages environment detection and feature availability.

    This class centralizes all environment-specific behavior to make
    it easier to handle different execution contexts.
    """

    def __init__(self):
        """Initialize the environment manager and detect current environment."""
        self._environment = self._detect_environment()
        self._available_features = self._detect_available_features()

        logger.info(f"Detected environment: {self._environment}")
        logger.info(f"Available features: {', '.join(self._available_features)}")

    def _detect_environment(self):
        """
        Detect the current execution environment.

        Returns:
            str: The detected environment type
        """
        # Check for explicit environment setting
        if os.environ.get("VOCALINUX_ENV"):
            return os.environ.get("VOCALINUX_ENV")

        # Check for CI environment
        if os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
            return ENV_CI

        # Check for test environment
        if "pytest" in sys.modules:
            return ENV_TESTING

        # Default to production for safety
        return ENV_PRODUCTION

    def _can_access_audio_hardware(self) -> bool:
        """
        Check if the application can access audio hardware.

        Returns:
            bool: True if audio hardware is accessible, False otherwise
        """
        # Check for common audio players
        audio_players = ["paplay", "aplay", "play", "mplayer"]
        for player in audio_players:
            if shutil.which(player):
                logger.debug(f"Found audio player: {player}")
                return True

        # Check if we can access audio devices
        try:
            # Try to check for audio devices without actually opening them
            result = subprocess.run(
                ["arecord", "-l"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1,
            )
            if result.returncode == 0 and b"card" in result.stdout:
                logger.debug("Audio recording devices detected")
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

        logger.debug("No audio hardware detected")
        return False

    def _can_access_keyboard(self) -> bool:
        """
        Check if the application can access keyboard for global shortcuts.

        Returns:
            bool: True if keyboard is accessible for global shortcuts, False otherwise
        """
        # Try to import the keyboard library without side effects
        try:
            import importlib.util

            # Check if pynput is installed
            pynput_spec = importlib.util.find_spec("pynput")
            if pynput_spec is None:
                logger.debug("pynput library not installed")
                return False

            # Check if X11 is available (needed for pynput on Linux)
            if "DISPLAY" not in os.environ:
                logger.debug("X11 DISPLAY environment variable not set")
                return False

            # Check if it's a headless environment
            if os.environ.get("DISPLAY") == ":0":
                logger.debug("Keyboard access likely available")
                return True

            return False
        except ImportError:
            return False

    def _can_access_gui(self) -> bool:
        """
        Check if the application can access GUI libraries/display.

        Returns:
            bool: True if GUI is accessible, False otherwise
        """
        # Check if X11 display is available
        if "DISPLAY" not in os.environ:
            logger.debug("X11 DISPLAY environment variable not set")
            return False

        # Try to check for GTK
        try:
            import importlib.util

            # Check if GTK is installed
            gtk_spec = importlib.util.find_spec("gi.repository.Gtk")
            if gtk_spec is None:
                logger.debug("GTK library not installed")
                return False

            return True
        except ImportError:
            return False

    def _detect_available_features(self) -> Set[str]:
        """
        Detect which features are available in the current environment.

        This uses both environment variables and runtime checks to determine
        which features are available.

        Returns:
            set: Set of available feature names
        """
        available = set()

        # In CI or testing, hardware features must be explicitly enabled
        if self._environment in (ENV_CI, ENV_TESTING):
            # Features can be explicitly enabled even in CI/testing
            if os.environ.get("VOCALINUX_ENABLE_AUDIO") == "true":
                available.add(FEATURE_AUDIO)
            if os.environ.get("VOCALINUX_ENABLE_KEYBOARD") == "true":
                available.add(FEATURE_KEYBOARD)
            if os.environ.get("VOCALINUX_ENABLE_GUI") == "true":
                available.add(FEATURE_GUI)
        else:
            # In development/production, detect hardware features by default
            # unless explicitly disabled

            # Check audio feature
            if os.environ.get("VOCALINUX_DISABLE_AUDIO") != "true":
                if self._can_access_audio_hardware():
                    available.add(FEATURE_AUDIO)

            # Check keyboard feature
            if os.environ.get("VOCALINUX_DISABLE_KEYBOARD") != "true":
                if self._can_access_keyboard():
                    available.add(FEATURE_KEYBOARD)

            # Check GUI feature
            if os.environ.get("VOCALINUX_DISABLE_GUI") != "true":
                if self._can_access_gui():
                    available.add(FEATURE_GUI)

        return available

    def get_environment(self):
        """
        Get the current environment type.

        Returns:
            str: The environment type
        """
        return self._environment

    def is_feature_available(self, feature):
        """
        Check if a specific feature is available.

        Args:
            feature: The feature to check

        Returns:
            bool: True if the feature is available, False otherwise
        """
        return feature in self._available_features

    def is_ci(self):
        """
        Check if running in a CI environment.

        Returns:
            bool: True if in CI environment, False otherwise
        """
        return self._environment == ENV_CI

    def is_testing(self):
        """
        Check if running in a testing environment.

        Returns:
            bool: True if in testing environment, False otherwise
        """
        return self._environment == ENV_TESTING


# Create a singleton instance
environment = EnvironmentManager()
