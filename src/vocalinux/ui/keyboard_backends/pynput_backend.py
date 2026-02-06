"""
Pynput keyboard backend for X11.

This backend uses the pynput library for global keyboard shortcuts.
Works on X11 and XWayland, but NOT on pure Wayland.
"""

import logging
import threading
import time
from typing import Optional

# Try to import pynput
try:
    from pynput import keyboard

    PYNPUT_AVAILABLE = True
except ImportError:
    keyboard = None  # type: ignore
    PYNPUT_AVAILABLE = False

from .base import DEFAULT_SHORTCUT, KeyboardBackend

logger = logging.getLogger(__name__)


# Map modifier key names to pynput Key objects
MODIFIER_KEY_MAP = {
    "ctrl": keyboard.Key.ctrl if PYNPUT_AVAILABLE else None,
    "alt": keyboard.Key.alt if PYNPUT_AVAILABLE else None,
    "shift": keyboard.Key.shift if PYNPUT_AVAILABLE else None,
    "super": keyboard.Key.cmd if PYNPUT_AVAILABLE else None,  # cmd is Super/Windows key
}

# Map for normalizing left/right variants
MODIFIER_NORMALIZE_MAP = {}
if PYNPUT_AVAILABLE:
    MODIFIER_NORMALIZE_MAP = {
        keyboard.Key.ctrl_l: keyboard.Key.ctrl,
        keyboard.Key.ctrl_r: keyboard.Key.ctrl,
        keyboard.Key.alt_l: keyboard.Key.alt,
        keyboard.Key.alt_r: keyboard.Key.alt,
        keyboard.Key.shift_l: keyboard.Key.shift,
        keyboard.Key.shift_r: keyboard.Key.shift,
        keyboard.Key.cmd_l: keyboard.Key.cmd,
        keyboard.Key.cmd_r: keyboard.Key.cmd,
    }


class PynputKeyboardBackend(KeyboardBackend):
    """
    Keyboard backend using pynput library.

    This backend works on X11 and XWayland but NOT on pure Wayland
    due to Wayland's security restrictions.
    """

    def __init__(self, shortcut: str = DEFAULT_SHORTCUT):
        """
        Initialize the pynput keyboard backend.

        Args:
            shortcut: The shortcut string to listen for (e.g., "ctrl+ctrl")
        """
        super().__init__(shortcut)
        self.listener = None
        self.last_trigger_time = 0
        self.last_key_press_time = 0
        self.double_tap_threshold = 0.3  # seconds
        self.current_keys = set()

        if not PYNPUT_AVAILABLE:
            logger.error("pynput library not available")

    def _get_target_key(self):
        """Get the pynput Key object for the configured modifier."""
        return MODIFIER_KEY_MAP.get(self._modifier_key)

    def is_available(self) -> bool:
        """Check if pynput is available."""
        return PYNPUT_AVAILABLE

    def get_permission_hint(self) -> Optional[str]:
        """
        Get permission hint for pynput backend.

        Returns:
            None for pynput (permissions are typically OK on X11)
        """
        return None

    def start(self) -> bool:
        """
        Start the pynput keyboard listener.

        Returns:
            True if started successfully, False otherwise
        """
        if not PYNPUT_AVAILABLE:
            logger.error("Cannot start: pynput not available")
            return False

        if self.active:
            return True

        logger.info(f"Starting pynput keyboard listener for shortcut: {self._shortcut}")
        self.current_keys = set()

        try:
            self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self.listener.daemon = True
            self.listener.start()

            if not self.listener.is_alive():
                logger.error("Failed to start pynput listener")
                return False

            logger.info("Pynput keyboard listener started successfully")
            self.active = True
            return True

        except Exception as e:
            logger.error(f"Error starting pynput listener: {e}")
            return False

    def stop(self) -> None:
        """Stop the pynput keyboard listener."""
        if not self.active or not self.listener:
            return

        logger.info("Stopping pynput keyboard listener")
        self.active = False

        if self.listener:
            try:
                self.listener.stop()
                self.listener.join(timeout=1.0)
            except Exception as e:
                logger.error(f"Error stopping pynput listener: {e}")
            finally:
                self.listener = None

    def _on_press(self, key) -> None:
        """Handle key press events."""
        try:
            normalized_key = self._normalize_modifier_key(key)
            target_key = self._get_target_key()

            if normalized_key == target_key:
                current_time = time.time()
                if (
                    current_time - self.last_key_press_time < self.double_tap_threshold
                    and self.double_tap_callback is not None
                    and current_time - self.last_trigger_time > 0.5
                ):
                    logger.debug(f"Double-tap {self._modifier_key} detected (pynput)")
                    self.last_trigger_time = current_time
                    threading.Thread(target=self.double_tap_callback, daemon=True).start()
                self.last_key_press_time = current_time

            # Track current keys (using target key for reference)
            if target_key and key in self._get_key_variants(self._modifier_key):
                self.current_keys.add(normalized_key)

        except Exception as e:
            logger.error(f"Error in pynput key press handling: {e}")

    def _on_release(self, key) -> None:
        """Handle key release events."""
        try:
            normalized_key = self._normalize_modifier_key(key)
            self.current_keys.discard(normalized_key)
        except Exception as e:
            logger.error(f"Error in pynput key release handling: {e}")

    def _normalize_modifier_key(self, key):
        """Normalize left/right variants of modifier keys."""
        return MODIFIER_NORMALIZE_MAP.get(key, key)

    def _get_key_variants(self, modifier_name: str):
        """Get all key variants for a modifier name."""
        if not PYNPUT_AVAILABLE:
            return set()

        variants = {
            "ctrl": {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
            "alt": {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r},
            "shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
            "super": {keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r},
        }
        return variants.get(modifier_name, set())


# Export availability
__all__ = ["PynputKeyboardBackend", "PYNPUT_AVAILABLE"]
