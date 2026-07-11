"""
Centralized resource manager for Vocalinux.

This module provides a unified way to locate and access application resources
like icons, sounds, and other assets regardless of how the application is installed.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, cast

logger = logging.getLogger(__name__)

_EXPECTED_ICONS = (
    "vocalinux",
    "vocalinux-microphone",
    "vocalinux-microphone-off",
    "vocalinux-microphone-process",
)
_EXPECTED_SOUNDS = ("start_recording", "stop_recording", "error")


class ResourceManager:
    """
    Centralized manager for application resources.

    This class provides a unified way to locate resources like icons and sounds
    regardless of whether the application is running from source, installed via pip,
    or installed system-wide.
    """

    _instance = None
    _resources_dir: Optional[str] = None

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

        Prefers the package-relative path, then common system install locations.

        Returns:
            Path to the resources directory
        """
        # Package-relative path first (src/vocalinux/resources or installed package)
        module_dir = Path(__file__).resolve().parent
        candidates = [
            module_dir.parent / "resources",
            # Direct repository execution (utils -> vocalinux -> src -> root)
            module_dir.parent.parent.parent / "resources",
            # Virtualenv / pip share data
            Path(sys.prefix) / "share" / "vocalinux" / "resources",
            # Standard system install paths
            Path("/usr/local/share/vocalinux/resources"),
            Path("/usr/share/vocalinux/resources"),
        ]

        candidates.extend(
            Path(base) / "vocalinux" / "resources"
            for base in os.environ.get("XDG_DATA_DIRS", "").split(":")
            if base
        )

        for candidate in dict.fromkeys(candidates):
            is_complete = all(
                (candidate / "icons" / "scalable" / f"{icon}.svg").is_file()
                for icon in _EXPECTED_ICONS
            ) and all(
                (candidate / "sounds" / f"{sound}.wav").is_file() for sound in _EXPECTED_SOUNDS
            )
            logger.debug(
                "Checking resources candidate: %s (complete: %s)",
                candidate,
                is_complete,
            )
            if is_complete:
                logger.info("Found resources directory: %s", candidate)
                return str(candidate)

        default_path = str(candidates[0])
        logger.warning("Could not find resources directory, defaulting to: %s", default_path)
        return default_path

    @property
    def resources_dir(self) -> str:
        """Get the resources directory path."""
        return cast(str, self._resources_dir)

    @property
    def icons_dir(self) -> str:
        """Get the icons directory path."""
        return os.path.join(self.resources_dir, "icons", "scalable")

    @property
    def sounds_dir(self) -> str:
        """Get the sounds directory path."""
        return os.path.join(self.resources_dir, "sounds")

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
        resources_dir = self.resources_dir
        results = {
            "resources_dir_exists": os.path.exists(resources_dir),
            "icons_dir_exists": os.path.exists(self.icons_dir),
            "sounds_dir_exists": os.path.exists(self.sounds_dir),
            "missing_icons": [],
            "missing_sounds": [],
        }

        # Expected icons
        for icon in _EXPECTED_ICONS:
            icon_path = self.get_icon_path(icon)
            if not os.path.exists(icon_path):
                results["missing_icons"].append(icon)

        # Expected sounds
        for sound in _EXPECTED_SOUNDS:
            sound_path = self.get_sound_path(sound)
            if not os.path.exists(sound_path):
                results["missing_sounds"].append(sound)

        return results
