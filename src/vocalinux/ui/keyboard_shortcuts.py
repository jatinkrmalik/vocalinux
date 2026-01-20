"""
Keyboard shortcut manager for Vocalinux.

This module provides global keyboard shortcut functionality to
start/stop speech recognition with a double-tap of the Ctrl key.
"""

import logging
import threading
import time
from typing import Callable

# Make keyboard a module-level attribute first, even if it's None
# This will ensure the attribute exists for patching in tests
keyboard = None
KEYBOARD_AVAILABLE = False

# Try to import X11 keyboard libraries
try:
    from pynput import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    # Keep keyboard as None, which we set above
    pass

logger = logging.getLogger(__name__)


class KeyboardShortcutManager:
    """
    Manages global keyboard shortcuts for the application.

    This class allows registering the double-tap Ctrl shortcut to
    toggle voice typing on and off across the desktop environment.
    """

    def __init__(self, shortcut: str = "ctrl+ctrl"):
        """
        Initialize the keyboard shortcut manager.
        
        Args:
            shortcut: The shortcut string configuration ("ctrl+ctrl" or keys like "<ctrl>+<alt>+v")
        """
        self.listener = None
        self.active = False
        self.shortcut = shortcut
        
        # State machine variables for double-tap detection
        self.tap_state = 0  # 0: IDLE, 1: PRESSED_1, 2: RELEASED_1, 3: PRESSED_2
        self.last_event_time = 0
        self.double_tap_callback = None
        
        # Configuration
        self.max_tap_duration = 0.5  # Max duration to hold key (seconds)
        self.max_gap_duration = 0.5  # Max duration between taps (seconds)
        self.min_gap_duration = 0.05 # Min duration to avoid mechanical bounce

        if not KEYBOARD_AVAILABLE:
            logger.error("Keyboard shortcut libraries not available. Shortcuts will not work.")
            return

    def set_shortcut(self, shortcut: str):
        """
        Update the configured shortcut.
        
        Args:
            shortcut: The new shortcut string
        """
        if self.shortcut == shortcut:
            return
            
        logger.info(f"Updating shortcut to: {shortcut}")
        self.shortcut = shortcut
        
        # Restart listener if active
        if self.active:
            self.stop()
            self.start()

    def start(self):
        """Start listening for keyboard shortcuts."""
        if not KEYBOARD_AVAILABLE:
            return

        if self.active:
            return

        logger.info(f"Starting keyboard shortcut listener (mode: {self.shortcut})")
        self.active = True
        
        try:
            if self.shortcut == "ctrl+ctrl":
                # Use double-tap detection strategy
                self._reset_state()
                self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            else:
                # Use standard hotkey strategy
                # We need to wrap the callback because GlobalHotKeys expects a specific dict format
                if not self.double_tap_callback:
                    logger.warning("No callback registered, hotkey will verify but do nothing")
                    
                def on_activate():
                    if self.double_tap_callback:
                        threading.Thread(target=self.double_tap_callback, daemon=True).start()
                
                # Create hotkey dict check
                # Note: This requires the shortcut to be in pynput format e.g. "<ctrl>+<alt>+h"
                hotkeys = {self.shortcut: on_activate}
                self.listener = keyboard.GlobalHotKeys(hotkeys)

            self.listener.daemon = True
            self.listener.start()

            # Verify the listener started successfully
            # Check is_alive if the listener supports it (it should invoke thread start)
            if hasattr(self.listener, "is_alive") and not self.listener.is_alive():
                logger.error("Failed to start keyboard listener")
                self.active = False
            else:
                logger.info("Keyboard shortcut listener started successfully")
        except Exception as e:
            logger.error(f"Error starting keyboard listener: {e}")
            self.active = False

    def stop(self):
        """Stop listening for keyboard shortcuts."""
        if not self.active or not self.listener:
            return

        logger.info("Stopping keyboard shortcut listener")
        self.active = False
        self._reset_state()

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

    def _reset_state(self):
        """Reset the double-tap detection state."""
        self.tap_state = 0
        self.last_event_time = 0

    def _on_press(self, key):
        """
        Handle key press events.

        Args:
            key: The pressed key
        """
        try:
            # Check if it is a Ctrl key
            normalized_key = self._normalize_modifier_key(key)
            is_ctrl = normalized_key == keyboard.Key.ctrl
            
            # Any other key press resets the sequence immediately
            if not is_ctrl:
                if self.tap_state != 0:
                    self._reset_state()
                return

            current_time = time.time()
            
            # State Machine for Double Tap
            if self.tap_state == 0:  # IDLE -> PRESSED_1
                self.tap_state = 1
                self.last_event_time = current_time
                
            elif self.tap_state == 2:  # RELEASED_1 -> PRESSED_2
                time_since_release = current_time - self.last_event_time
                
                if self.min_gap_duration < time_since_release < self.max_gap_duration:
                    self.tap_state = 3
                    self.last_event_time = current_time
                else:
                    # Too slow or too fast - treat as new first tap
                    self.tap_state = 1
                    self.last_event_time = current_time

            elif self.tap_state == 1 or self.tap_state == 3:
                # Already pressed (autorepeat) - ignore
                pass

        except Exception as e:
            logger.error(f"Error in keyboard shortcut handling: {e}")

    def _on_release(self, key):
        """
        Handle key release events.

        Args:
            key: The released key
        """
        try:
            # Check if it is a Ctrl key
            normalized_key = self._normalize_modifier_key(key)
            is_ctrl = normalized_key == keyboard.Key.ctrl
            
            if not is_ctrl:
                # Release of other keys doesn't necessarily reset, but we ignore it
                # Logic: If we were holding 'A', then pressed Ctrl, 'A' press would have reset it.
                # So this is fine.
                return
            
            current_time = time.time()
            
            if self.tap_state == 1:  # PRESSED_1 -> RELEASED_1
                duration = current_time - self.last_event_time
                
                if duration < self.max_tap_duration:
                    self.tap_state = 2
                    self.last_event_time = current_time
                else:
                    # Held too long - reset
                    self._reset_state()
                    
            elif self.tap_state == 3:  # PRESSED_2 -> TRIGGER
                duration = current_time - self.last_event_time
                
                if duration < self.max_tap_duration:
                    # Successful Double Tap!
                    logger.debug("Double-tap Ctrl detected")
                    if self.double_tap_callback:
                        threading.Thread(target=self.double_tap_callback, daemon=True).start()
                    
                    # Reset state
                    self._reset_state()
                else:
                    # Held second too long - reset
                    self._reset_state()

        except Exception as e:
            logger.error(f"Error in keyboard release handling: {e}")

    def _normalize_modifier_key(self, key):
        """Normalize left/right variants of modifier keys to their base form."""
        # Map left/right variants to their base key
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
