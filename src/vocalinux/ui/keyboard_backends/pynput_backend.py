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

from .base import KeyboardBackend

logger = logging.getLogger(__name__)


class PynputKeyboardBackend(KeyboardBackend):
    """
    Keyboard backend using pynput library.

    This backend works on X11 and XWayland but NOT on pure Wayland
    due to Wayland's security restrictions.
    """

    def __init__(self):
        """Initialize the pynput keyboard backend."""
        super().__init__()
        self.listener = None
        self.last_trigger_time = 0
        self.last_ctrl_press_time = 0
        self.double_tap_threshold = 0.3  # seconds
        self.current_keys = set()

        if not PYNPUT_AVAILABLE:
            logger.error("pynput library not available")

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

        logger.info("Starting pynput keyboard listener")
        self.current_keys = set()

        try:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
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
            if normalized_key == keyboard.Key.ctrl:
                current_time = time.time()
                if (current_time - self.last_ctrl_press_time < self.double_tap_threshold and
                        self.double_tap_callback is not None and
                        current_time - self.last_trigger_time > 0.5):
                    logger.debug("Double-tap Ctrl detected (pynput)")
                    self.last_trigger_time = current_time
                    threading.Thread(
                        target=self.double_tap_callback,
                        daemon=True
                    ).start()
                self.last_ctrl_press_time = current_time

            if key in {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}:
                normalized_key = self._normalize_modifier_key(key)
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


# Export availability
__all__ = ["PynputKeyboardBackend", "PYNPUT_AVAILABLE"]
