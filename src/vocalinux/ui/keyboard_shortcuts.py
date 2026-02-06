"""
Keyboard shortcut manager for Vocalinux.

This module provides global keyboard shortcut functionality to
start/stop speech recognition with configurable double-tap shortcuts.

Supports multiple backends:
- pynput: Works on X11/XWayland
- evdev: Works on both X11 and Wayland (with proper permissions)
"""

import logging
from typing import Callable, Optional

# Import the backend system
from .keyboard_backends import (
    DEFAULT_SHORTCUT,
    EVDEV_AVAILABLE,
    PYNPUT_AVAILABLE,
    SHORTCUT_DISPLAY_NAMES,
    SUPPORTED_SHORTCUTS,
    DesktopEnvironment,
    create_backend,
)

logger = logging.getLogger(__name__)


# Keep legacy module-level attributes for backward compatibility
KEYBOARD_AVAILABLE = PYNPUT_AVAILABLE or EVDEV_AVAILABLE
keyboard = None  # Will be set if pynput is available (for tests)


def _init_legacy_keyboard():
    """Initialize legacy keyboard attribute for backward compatibility."""
    global keyboard
    try:
        from pynput import keyboard as pynput_keyboard

        keyboard = pynput_keyboard
    except ImportError:
        pass


_init_legacy_keyboard()


class KeyboardShortcutManager:
    """
    Manages global keyboard shortcuts for the application.

    This class allows registering configurable double-tap shortcuts to
    toggle voice typing on and off across the desktop environment.

    Automatically selects the appropriate backend based on the
    desktop environment (X11, Wayland) and available dependencies.
    """

    def __init__(self, backend: Optional[str] = None, shortcut: str = DEFAULT_SHORTCUT):
        """
        Initialize the keyboard shortcut manager.

        Args:
            backend: Optional backend name to force ('pynput' or 'evdev')
                    If not specified, auto-detects based on environment.
            shortcut: The shortcut to listen for (e.g., "ctrl+ctrl", "alt+alt")
        """
        self.backend_instance = None
        self.active = False
        self._shortcut = shortcut

        # Create the appropriate backend
        self.backend_instance = create_backend(preferred_backend=backend, shortcut=shortcut)

        if self.backend_instance is None:
            logger.error("No keyboard backend available. Shortcuts will not work.")
            self._log_unavailable_hints()

    def _log_unavailable_hints(self):
        """Log helpful hints when no backend is available."""
        env = DesktopEnvironment.detect()

        if env == DesktopEnvironment.WAYLAND:
            logger.warning("=" * 60)
            logger.warning("Keyboard shortcuts not available on Wayland")
            logger.warning("=" * 60)
            logger.warning("To enable keyboard shortcuts on Wayland:")
            logger.warning("1. Install python-evdev:")
            logger.warning("   pip install evdev")
            logger.warning("2. Add your user to the 'input' group:")
            logger.warning("   sudo usermod -a -G input $USER")
            logger.warning("3. Log out and log back in")
            logger.warning("=" * 60)
        else:
            logger.warning("Keyboard shortcuts require pynput or evdev:")
            logger.warning("  pip install pynput evdev")

    @property
    def shortcut(self) -> str:
        """Get the current shortcut string."""
        return self._shortcut

    @property
    def shortcut_display_name(self) -> str:
        """Get the human-readable name for the current shortcut."""
        return SHORTCUT_DISPLAY_NAMES.get(self._shortcut, self._shortcut)

    def set_shortcut(self, shortcut: str) -> bool:
        """
        Update the shortcut to listen for.

        Note: This only updates the internal state. Use restart_with_shortcut()
        to apply changes to an active listener.

        Args:
            shortcut: The new shortcut string (e.g., "ctrl+ctrl", "alt+alt")

        Returns:
            True if successful, False if the shortcut is invalid
        """
        if shortcut not in SUPPORTED_SHORTCUTS:
            logger.error(f"Invalid shortcut: {shortcut}")
            return False

        self._shortcut = shortcut

        if self.backend_instance:
            self.backend_instance.set_shortcut(shortcut)
            logger.info(f"Shortcut updated to: {SHORTCUT_DISPLAY_NAMES.get(shortcut, shortcut)}")

        return True

    def restart_with_shortcut(self, shortcut: str) -> bool:
        """
        Restart the keyboard listener with a new shortcut.

        This stops the current listener, updates the shortcut configuration,
        and starts a new listener with the new shortcut. This enables live
        shortcut switching without requiring an application restart.

        Args:
            shortcut: The new shortcut string (e.g., "ctrl+ctrl", "alt+alt")

        Returns:
            True if the listener was successfully restarted with the new shortcut,
            False if the shortcut is invalid or restart failed
        """
        if shortcut not in SUPPORTED_SHORTCUTS:
            logger.error(f"Invalid shortcut: {shortcut}")
            return False

        if shortcut == self._shortcut:
            logger.debug(f"Shortcut already set to {shortcut}, no restart needed")
            return True

        was_active = self.active
        callback = None

        # Save the current callback before stopping
        if self.backend_instance:
            callback = self.backend_instance.double_tap_callback

        # Stop the current listener
        if was_active:
            logger.info(f"Stopping listener for shortcut change: {self._shortcut} -> {shortcut}")
            self.stop()

        # Update the shortcut
        self._shortcut = shortcut

        # Update backend shortcut
        if self.backend_instance:
            self.backend_instance.set_shortcut(shortcut)

        # Restart if it was active
        if was_active:
            # Re-register the callback
            if callback:
                self.register_toggle_callback(callback)

            success = self.start()
            if success:
                logger.info(
                    f"Listener restarted with new shortcut: "
                    f"{SHORTCUT_DISPLAY_NAMES.get(shortcut, shortcut)}"
                )
            else:
                logger.error(f"Failed to restart listener with shortcut: {shortcut}")
            return success

        logger.info(f"Shortcut updated to: {SHORTCUT_DISPLAY_NAMES.get(shortcut, shortcut)}")
        return True

    def start(self) -> bool:
        """
        Start listening for keyboard shortcuts.

        Returns:
            True if the listener started successfully, False otherwise
        """
        if self.backend_instance is None:
            return False

        if self.active:
            return True

        logger.info(f"Starting keyboard shortcut listener for: {self.shortcut_display_name}")
        self.active = self.backend_instance.start()

        if not self.active:
            hint = self.backend_instance.get_permission_hint()
            if hint:
                logger.warning(f"Permission issue: {hint}")

        return self.active

    def stop(self):
        """Stop listening for keyboard shortcuts."""
        if self.backend_instance is None:
            return

        logger.info("Stopping keyboard shortcut listener")
        self.backend_instance.stop()
        self.active = False

    def register_toggle_callback(self, callback: Callable):
        """
        Register a callback for the double-tap shortcut.

        Args:
            callback: Function to call when the double-tap shortcut is pressed
        """
        if self.backend_instance is None:
            logger.warning("Cannot register callback: no backend available")
            return

        self.backend_instance.register_toggle_callback(callback)
        logger.info(f"Registered shortcut: {self.shortcut_display_name}")

    @property
    def listener(self):
        """
        Legacy property for backward compatibility.

        Returns the underlying backend object if using pynput backend.
        """
        if self.backend_instance and hasattr(self.backend_instance, "listener"):
            return self.backend_instance.listener
        return None


# For backward compatibility with tests
def _normalize_modifier_key(key):
    """
    Legacy function for backward compatibility.

    Normalize left/right variants of modifier keys to their base form.
    """
    if keyboard is None:
        return key

    key_mapping = {
        keyboard.Key.alt_l: keyboard.Key.alt,
        keyboard.Key.alt_r: keyboard.Key.alt,
        keyboard.Key.shift_l: keyboard.Key.shift,
        keyboard.Key.shift_r: keyboard.Key.shift,
        keyboard.Key.ctrl_l: keyboard.Key.ctrl,
        keyboard.Key.ctrl_r: keyboard.Key.ctrl,
        keyboard.Key.cmd_l: keyboard.Key.cmd,
        keyboard.Key.cmd_r: keyboard.Key.cmd,
    }

    return key_mapping.get(key, key)


__all__ = [
    "KeyboardShortcutManager",
    "KEYBOARD_AVAILABLE",
    "DesktopEnvironment",
    "EVDEV_AVAILABLE",
    "PYNPUT_AVAILABLE",
    "SUPPORTED_SHORTCUTS",
    "SHORTCUT_DISPLAY_NAMES",
    "DEFAULT_SHORTCUT",
]
