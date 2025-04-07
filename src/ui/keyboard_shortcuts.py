"""
Keyboard shortcut manager for Ubuntu Voice Typing.

This module provides global keyboard shortcut functionality to
start/stop speech recognition with a keystroke.
"""

import logging
import threading
import time
from typing import Callable, Dict, Optional, Tuple

# Try to import X11 keyboard libraries first
try:
    from pynput import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

logger = logging.getLogger(__name__)


class KeyboardShortcutManager:
    """
    Manages global keyboard shortcuts for the application.
    
    This class allows registering global keyboard shortcuts that work
    across the desktop environment.
    """
    
    def __init__(self):
        """Initialize the keyboard shortcut manager."""
        self.shortcuts = {}
        self.listener = None
        self.active = False
        self.last_trigger_time = 0  # Track last trigger time to prevent double triggers
        
        if not KEYBOARD_AVAILABLE:
            logger.error("Keyboard shortcut libraries not available. Shortcuts will not work.")
            return
        
        # Default shortcut for toggling voice typing (Alt+Shift+V)
        self.default_shortcut = (
            {keyboard.Key.alt, keyboard.Key.shift},
            keyboard.KeyCode.from_char('v')
        )
    
    def start(self):
        """Start listening for keyboard shortcuts."""
        if not KEYBOARD_AVAILABLE:
            return
        
        if self.active:
            return
        
        logger.info("Starting keyboard shortcut listener")
        self.active = True
        
        # Track currently pressed modifier keys
        self.current_keys = set()
        
        try:
            # Start keyboard listener in a separate thread
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.daemon = True
            self.listener.start()
            
            # Verify the listener started successfully
            if not self.listener.is_alive():
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
        
        if self.listener:
            try:
                self.listener.stop()
                self.listener.join(timeout=1.0)
            except Exception as e:
                logger.error(f"Error stopping keyboard listener: {e}")
            finally:
                self.listener = None
    
    def register_shortcut(self, modifiers: set, key, callback: Callable):
        """
        Register a keyboard shortcut.
        
        Args:
            modifiers: Set of modifier keys (e.g., {keyboard.Key.alt, keyboard.Key.shift})
            key: The main key (e.g., keyboard.KeyCode.from_char('v'))
            callback: Function to call when the shortcut is pressed
        """
        shortcut_key = (frozenset(modifiers), key)
        self.shortcuts[shortcut_key] = callback
        
        # Create readable description of the shortcut for logging
        mod_names = [self._get_key_name(mod) for mod in modifiers]
        key_name = self._get_key_name(key)
        shortcut_desc = "+".join(mod_names + [key_name])
        logger.info(f"Registered shortcut: {shortcut_desc}")
    
    def register_toggle_callback(self, callback: Callable):
        """
        Register a callback for the default toggle shortcut.
        
        Args:
            callback: Function to call when the toggle shortcut is pressed
        """
        modifiers, key = self.default_shortcut
        self.register_shortcut(modifiers, key, callback)
    
    def _get_key_name(self, key):
        """Get a readable name for a key object."""
        if hasattr(key, 'char') and key.char:
            return key.char.upper()
        elif hasattr(key, 'name'):
            return key.name
        else:
            return str(key)
    
    def _on_press(self, key):
        """
        Handle key press events.
        
        Args:
            key: The pressed key
        """
        try:
            # Add to currently pressed keys (only for modifier keys)
            if key in {
                keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
                keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
                keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                keyboard.Key.cmd, keyboard.Key.cmd_l, keyboard.Key.cmd_r
            }:
                # Normalize left/right variants
                normalized_key = self._normalize_modifier_key(key)
                self.current_keys.add(normalized_key)
                
            # Check for shortcuts (only once per 500ms to prevent double triggers)
            current_time = time.time()
            if current_time - self.last_trigger_time > 0.5:  # 500ms debounce
                for (modifiers, trigger_key), callback in self.shortcuts.items():
                    # Normalize the trigger key for character keys
                    if isinstance(trigger_key, keyboard.KeyCode) and hasattr(trigger_key, 'char'):
                        if isinstance(key, keyboard.KeyCode) and hasattr(key, 'char'):
                            key_matches = key.char.lower() == trigger_key.char.lower()
                        else:
                            key_matches = False
                    else:
                        key_matches = key == trigger_key
                        
                    # Check if modifiers match and key matches
                    normalized_modifiers = {self._normalize_modifier_key(m) for m in modifiers}
                    if self.current_keys == normalized_modifiers and key_matches:
                        logger.debug(f"Shortcut triggered: {modifiers} + {trigger_key}")
                        self.last_trigger_time = current_time
                        
                        # Run callback in a separate thread to avoid blocking
                        threading.Thread(target=callback, daemon=True).start()
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
        key_mapping = {
            keyboard.Key.alt_l: keyboard.Key.alt,
            keyboard.Key.alt_r: keyboard.Key.alt,
            keyboard.Key.shift_l: keyboard.Key.shift,
            keyboard.Key.shift_r: keyboard.Key.shift,
            keyboard.Key.ctrl_l: keyboard.Key.ctrl,
            keyboard.Key.ctrl_r: keyboard.Key.ctrl,
            keyboard.Key.cmd_l: keyboard.Key.cmd,
            keyboard.Key.cmd_r: keyboard.Key.cmd
        }
        
        return key_mapping.get(key, key)