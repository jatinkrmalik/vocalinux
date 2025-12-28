"""
Centralized resource manager for Vocalinux.

This module provides a unified way to locate and access application resources
like icons, sounds, and other assets regardless of how the application is installed.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Centralized manager for application resources.

    This class provides a unified way to locate resources like icons and sounds
    regardless of whether the application is running from source, installed via pip,
    or installed system-wide.
    """

    _instance = None
    _resources_dir = None

    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the resource manager."""
        if self._resources_dir is None:
            self._resources_dir = self._find_resources_dir()

    def _find_resources_dir(self) -> str:
        """
        Find the resources directory regardless of how the application is executed.

        Returns:
            Path to the resources directory
        """
        # Get the directory where this module is located
        module_dir = Path(__file__).parent.absolute()

        # Try several methods to find the resources directory
        candidates = [
            # For direct repository execution (go up from src/vocalinux/utils to root)
            module_dir.parent.parent.parent / "resources",
            # For installed package or virtual environment
            Path(sys.prefix) / "share" / "vocalinux" / "resources",
            # For development in virtual environment
            Path(sys.prefix).parent / "resources",
            # Additional fallbacks
            Path("/usr/local/share/vocalinux/resources"),
            Path("/usr/share/vocalinux/resources"),
        ]

        # Log all candidates for debugging
        for candidate in candidates:
            logger.debug(
                f"Checking resources candidate: {candidate} (exists: {candidate.exists()})"
            )

        # Return the first candidate that exists
        for candidate in candidates:
            if candidate.exists():
                logger.info(f"Found resources directory: {candidate}")
                return str(candidate)

        # If no candidate exists, default to the first one (with warning)
        default_path = str(candidates[0])
        logger.warning(f"Could not find resources directory, defaulting to: {default_path}")
        return default_path

    @property
    def resources_dir(self) -> str:
        """Get the resources directory path."""
        return self._resources_dir

    @property
    def icons_dir(self) -> str:
        """Get the icons directory path."""
        return os.path.join(self._resources_dir, "icons", "scalable")

    @property
    def sounds_dir(self) -> str:
        """Get the sounds directory path."""
        return os.path.join(self._resources_dir, "sounds")

    def get_icon_path(self, icon_name: str) -> str:
        """
        Get the full path to an icon file.

        Args:
            icon_name: Name of the icon (without extension)

        Returns:
            Full path to the icon file
        """
        return os.path.join(self.icons_dir, f"{icon_name}.svg")

    def get_sound_path(self, sound_name: str) -> str:
        """
        Get the full path to a sound file.

        Args:
            sound_name: Name of the sound file (without extension)

        Returns:
            Full path to the sound file
        """
        return os.path.join(self.sounds_dir, f"{sound_name}.wav")

    def ensure_directories_exist(self):
        """Ensure that resource directories exist."""
        os.makedirs(self.icons_dir, exist_ok=True)
        os.makedirs(self.sounds_dir, exist_ok=True)

    def validate_resources(self) -> dict:
        """
        Validate that all expected resources exist.

        Returns:
            Dictionary with validation results
        """
        results = {
            "resources_dir_exists": os.path.exists(self._resources_dir),
            "icons_dir_exists": os.path.exists(self.icons_dir),
            "sounds_dir_exists": os.path.exists(self.sounds_dir),
            "missing_icons": [],
            "missing_sounds": [],
        }

        # Expected icons
        expected_icons = [
            "vocalinux",
            "vocalinux-microphone",
            "vocalinux-microphone-off",
            "vocalinux-microphone-process",
        ]

        for icon in expected_icons:
            icon_path = self.get_icon_path(icon)
            if not os.path.exists(icon_path):
                results["missing_icons"].append(icon)

        # Expected sounds
        expected_sounds = ["start_recording", "stop_recording", "error"]

        for sound in expected_sounds:
            sound_path = self.get_sound_path(sound)
            if not os.path.exists(sound_path):
                results["missing_sounds"].append(sound)

        return results
