"""
Keyboard backend system for Vocalinux.

This package provides a modular backend system for global keyboard shortcuts,
supporting multiple platforms and display servers (X11, Wayland).
"""

import logging
import os
from typing import Optional

from .base import KeyboardBackend

logger = logging.getLogger(__name__)

# Import available backends
try:
    from .evdev_backend import EvdevKeyboardBackend
    EVDEV_AVAILABLE = True
except ImportError:
    EvdevKeyboardBackend = None  # type: ignore
    EVDEV_AVAILABLE = False

try:
    from .pynput_backend import PynputKeyboardBackend
    PYNPUT_AVAILABLE = True
except ImportError:
    PynputKeyboardBackend = None  # type: ignore
    PYNPUT_AVAILABLE = False


class DesktopEnvironment:
    """Desktop environment detection."""

    X11 = "x11"
    WAYLAND = "wayland"
    UNKNOWN = "unknown"

    @staticmethod
    def detect() -> str:
        """
        Detect the current desktop environment.

        Returns:
            'x11', 'wayland', or 'unknown'
        """
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type == "wayland":
            return DesktopEnvironment.WAYLAND
        elif session_type == "x11":
            return DesktopEnvironment.X11

        # Fallback to environment variables
        if "WAYLAND_DISPLAY" in os.environ:
            return DesktopEnvironment.WAYLAND
        elif "DISPLAY" in os.environ:
            return DesktopEnvironment.X11

        logger.warning("Could not detect desktop environment, defaulting to unknown")
        return DesktopEnvironment.UNKNOWN


def create_backend(preferred_backend: Optional[str] = None) -> Optional[KeyboardBackend]:
    """
    Create a keyboard backend based on availability and environment.

    Args:
        preferred_backend: Optional backend name to force ('pynput' or 'evdev')

    Returns:
        A KeyboardBackend instance, or None if no backend is available
    """
    env = DesktopEnvironment.detect()
    logger.info(f"Detected desktop environment: {env}")

    # If a specific backend is requested, try to use it
    if preferred_backend:
        if preferred_backend == "evdev" and EVDEV_AVAILABLE:
            logger.info("Using evdev backend (preferred)")
            return EvdevKeyboardBackend()  # type: ignore
        elif preferred_backend == "pynput" and PYNPUT_AVAILABLE:
            logger.info("Using pynput backend (preferred)")
            return PynputKeyboardBackend()  # type: ignore
        else:
            logger.warning(f"Preferred backend '{preferred_backend}' not available")

    # Auto-select based on environment
    if env == DesktopEnvironment.WAYLAND:
        # On Wayland, prefer evdev (if available) as pynput doesn't work
        if EVDEV_AVAILABLE:
            logger.info("Using evdev backend for Wayland")
            return EvdevKeyboardBackend()  # type: ignore
        else:
            logger.warning(
                "evdev backend not available on Wayland. "
                "Keyboard shortcuts will not work. Install python-evdev and "
                "add your user to the 'input' group."
            )
            return None

    # Default to pynput for X11 or unknown
    if PYNPUT_AVAILABLE:
        logger.info("Using pynput backend")
        return PynputKeyboardBackend()  # type: ignore

    logger.error("No keyboard backend available")
    return None


__all__ = [
    "KeyboardBackend",
    "create_backend",
    "DesktopEnvironment",
    "PynputKeyboardBackend",
    "EvdevKeyboardBackend",
    "EVDEV_AVAILABLE",
    "PYNPUT_AVAILABLE",
]
