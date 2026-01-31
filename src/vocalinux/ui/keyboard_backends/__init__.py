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
        # Primary detection: XDG_SESSION_TYPE
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type == "wayland":
            return DesktopEnvironment.WAYLAND
        elif session_type == "x11":
            return DesktopEnvironment.X11

        # Secondary detection: Direct environment variables
        if "WAYLAND_DISPLAY" in os.environ:
            # Check if we're actually running under Wayland
            wayland_display = os.environ.get("WAYLAND_DISPLAY", "")
            if wayland_display:  # Not empty
                return DesktopEnvironment.WAYLAND
        
        if "DISPLAY" in os.environ:
            display = os.environ.get("DISPLAY", "")
            if display:  # Not empty
                # If we have DISPLAY but no WAYLAND_DISPLAY, assume X11
                if "WAYLAND_DISPLAY" not in os.environ:
                    return DesktopEnvironment.X11

        # Tertiary detection: Check for XWayland (Wayland with X11 compatibility)
        if "XDG_SESSION_TYPE" not in os.environ and "DISPLAY" in os.environ:
            # This could be XWayland - check for common Wayland indicators
            if any(env in os.environ for env in ["WAYLAND_DISPLAY", "_JAVA_AWT_WM_NONREPARENTING"]):
                logger.info("Detected potential XWayland session")
                return DesktopEnvironment.WAYLAND

        # Final fallback
        logger.warning("Could not detect desktop environment, defaulting to unknown")
        logger.info("Set WAYLAND_DISPLAY or DISPLAY environment variable to force detection")
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
        if preferred_backend == "evdev":
            if EVDEV_AVAILABLE:
                logger.info("Using evdev backend (preferred)")
                backend = EvdevKeyboardBackend()  # type: ignore
                # Test if the backend is actually usable
                if backend.is_available():
                    return backend
                else:
                    hint = backend.get_permission_hint()
                    if hint:
                        logger.warning(f"Evdev backend not usable: {hint}")
                    logger.warning("Evdev backend preferred but not available, falling back")
            else:
                logger.warning("Evdev backend not available (python-evdev not installed)")
        
        elif preferred_backend == "pynput":
            if PYNPUT_AVAILABLE:
                logger.info("Using pynput backend (preferred)")
                return PynputKeyboardBackend()  # type: ignore
            else:
                logger.warning("Pynput backend not available")
        else:
            logger.warning(f"Unknown preferred backend: '{preferred_backend}'")

    # Auto-select based on environment with fallback logic
    if env == DesktopEnvironment.WAYLAND:
        # On Wayland, prefer evdev (if available) as pynput doesn't work
        if EVDEV_AVAILABLE:
            logger.info("Using evdev backend for Wayland")
            backend = EvdevKeyboardBackend()  # type: ignore
            if backend.is_available():
                return backend
            else:
                hint = backend.get_permission_hint()
                if hint:
                    logger.warning(f"Evdev backend not usable on Wayland: {hint}")
                logger.warning("Keyboard shortcuts will not work on Wayland without evdev access")
                return None
        else:
            logger.warning(
                "evdev backend not available on Wayland. "
                "Keyboard shortcuts will not work. Install python-evdev and "
                "add your user to the 'input' group."
            )
            return None

    # For X11 or unknown, try pynput first (more secure, no special permissions needed)
    if PYNPUT_AVAILABLE:
        logger.info("Using pynput backend")
        return PynputKeyboardBackend()  # type: ignore

    # Fallback to evdev if pynput is not available (less secure but better than nothing)
    if EVDEV_AVAILABLE:
        logger.warning("Pynput not available, falling back to evdev backend")
        backend = EvdevKeyboardBackend()  # type: ignore
        if backend.is_available():
            return backend
        else:
            hint = backend.get_permission_hint()
            if hint:
                logger.warning(f"Evdev backend not usable: {hint}")
            return None

    logger.error("No keyboard backend available")
    logger.info("To enable keyboard shortcuts, install either python-evdev or pynput")
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
