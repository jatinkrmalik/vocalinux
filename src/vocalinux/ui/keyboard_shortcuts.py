"""
Keyboard shortcut manager for Vocalinux.

This module provides global keyboard shortcut functionality to
start/stop speech recognition with a double-tap of the Ctrl key.
"""

import logging
import threading
import time
from typing import Callable

from vocalinux.utils.environment import FEATURE_KEYBOARD, environment

# Only import keyboard libraries if keyboard features are available
if environment.is_feature_available(FEATURE_KEYBOARD):
    try:
        from pynput import keyboard

        KEYBOARD_AVAILABLE = True
    except ImportError:
        KEYBOARD_AVAILABLE = False
        keyboard = None
else:
    KEYBOARD_AVAILABLE = False
    keyboard = None

# Create a dummy keyboard module for testing
if not KEYBOARD_AVAILABLE:

    class DummyKeyboard:
        class Key:
            alt = "Key.alt"
            alt_l = "Key.alt_l"
            alt_r = "Key.alt_r"
            shift = "Key.shift"
            shift_l = "Key.shift_l"
            shift_r = "Key.shift_r"
            ctrl = "Key.ctrl"
            ctrl_l = "Key.ctrl_l"
            ctrl_r = "Key.ctrl_r"
            cmd = "Key.cmd"
            cmd_l = "Key.cmd_l"
            cmd_r = "Key.cmd_r"

        class Listener:
            def __init__(self, on_press=None, on_release=None):
                self.on_press = on_press
                self.on_release = on_release
                self.daemon = False

            def start(self):
                pass

            def stop(self):
                pass

            def join(self, timeout=None):
                pass

            def is_alive(self):
                return True

    keyboard = DummyKeyboard()

logger = logging.getLogger(__name__)


class KeyboardShortcutManager:
    """
    Manages global keyboard shortcuts for the application.

    This class allows registering the double-tap Ctrl shortcut to
    toggle voice typing on and off across the desktop environment.
    """

    def __init__(self):
        """Initialize the keyboard shortcut manager."""
        self.listener = None
        self.active = False
        self.last_trigger_time = 0  # Track last trigger time to prevent double triggers

        # Double-tap tracking variables
        self.last_ctrl_press_time = 0
        self.double_tap_callback = None
        self.double_tap_threshold = 0.3  # seconds between taps to count as double-tap
        self.current_keys = set()

        # Initialize keyboard availability - this can be overridden via setter
        self._keyboard_available = True

        if not self.keyboard_available:
            logger.warning(
                "Keyboard shortcut features not available. Shortcuts will not work."
            )

    @property
    def keyboard_available(self):
        """Check if keyboard shortcuts are available."""
        return (
            self._keyboard_available
            and KEYBOARD_AVAILABLE
            and environment.is_feature_available(FEATURE_KEYBOARD)
        )

    @keyboard_available.setter
    def keyboard_available(self, value):
        """Set keyboard availability (mainly for testing)."""
        self._keyboard_available = value

    def start(self):
        """Start listening for keyboard shortcuts."""
        # Use the property to check availability
        if not self.keyboard_available:
            logger.warning(
                "Cannot start keyboard listener: keyboard features not available"
            )
            return

        if self.active:
            return

        logger.info("Starting keyboard shortcut listener")

        try:
            # Create and start keyboard listener
            self.listener = keyboard.Listener(
                on_press=self._on_press, on_release=self._on_release
            )
            self.listener.daemon = True
            self.listener.start()

            # Verify the listener started successfully
            if self.listener.is_alive():
                logger.info("Keyboard shortcut listener started successfully")
                self.active = True
            else:
                logger.error("Failed to start keyboard listener")
                self.active = False
                self.listener = None
        except Exception as e:
            logger.error(f"Error starting keyboard listener: {e}")
            self.active = False
            self.listener = None

    def stop(self):
        """Stop listening for keyboard shortcuts."""
        if not self.active:
            return

        logger.info("Stopping keyboard shortcut listener")
        self.active = False

        if self.listener:
            try:
                self.listener.stop()
                self.listener.join(timeout=1.0)
            except Exception as e:
                logger.error(f"Error stopping keyboard listener: {e}")
            finally:
                self.listener = None

    def register_toggle_callback(self, callback: Callable):
        """
        Register a callback for the double-tap Ctrl shortcut.

        Args:
            callback: Function to call when the double-tap Ctrl is pressed
        """
        self.double_tap_callback = callback
        logger.info("Registered shortcut: Double-tap Ctrl")

    def _on_press(self, key):
        """
        Handle key press events.

        Args:
            key: The pressed key
        """
        try:
            # Check for double-tap Ctrl
            normalized_key = self._normalize_modifier_key(key)
            if normalized_key == keyboard.Key.ctrl:
                current_time = time.time()
                if current_time - self.last_ctrl_press_time < self.double_tap_threshold:
                    # This is a double-tap Ctrl
                    if (
                        self.double_tap_callback
                        and current_time - self.last_trigger_time > 0.5
                    ):
                        logger.debug("Double-tap Ctrl detected")
                        self.last_trigger_time = current_time
                        # Run callback in a separate thread to avoid blocking
                        threading.Thread(
                            target=self.double_tap_callback, daemon=True
                        ).start()
                self.last_ctrl_press_time = current_time

            # Add to currently pressed modifier keys (only for tracking Ctrl)
            if key in {
                keyboard.Key.ctrl,
                keyboard.Key.ctrl_l,
                keyboard.Key.ctrl_r,
            }:
                # Normalize left/right variants
                normalized_key = self._normalize_modifier_key(key)
                self.current_keys.add(normalized_key)

        except Exception as e:
            logger.error(f"Error in keyboard shortcut handling: {e}")

    def _on_release(self, key):
        """
        Handle key release events.

        Args:
            key: The released key
        """
        try:
            # Normalize the key for left/right variants
            normalized_key = self._normalize_modifier_key(key)
            # Remove from currently pressed keys
            self.current_keys.discard(normalized_key)
        except Exception as e:
            logger.error(f"Error in keyboard release handling: {e}")

    def _normalize_modifier_key(self, key):
        """Normalize left/right variants of modifier keys to their base form."""
        # Map left/right variants to their base key
        if not keyboard or not hasattr(keyboard, "Key"):
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
