"""
Keyboard shortcut manager for Ubuntu Voice Typing.

This module provides global keyboard shortcut functionality to
start/stop speech recognition with a keystroke.
"""

import logging
import threading
from typing import Callable, Dict, Optional, Tuple

# Try to import X11 keyboard libraries first
try:
    from pynput import keyboard
    from Xlib import display
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
        
        # Start keyboard listener in a separate thread
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.daemon = True
        self.listener.start()
    
    def stop(self):
        """Stop listening for keyboard shortcuts."""
        if not self.active or not self.listener:
            return
        
        logger.info("Stopping keyboard shortcut listener")
        self.active = False
        
        if self.listener:
            self.listener.stop()
            self.listener.join(timeout=1.0)
            self.listener = None
    
    def register_shortcut(self, modifiers: set, key, callback: Callable):
        """
        Register a keyboard shortcut.
        
        Args:
            modifiers: Set of modifier keys (e.g., {keyboard.Key.alt, keyboard.Key.shift})
            key: The main key (e.g., keyboard.KeyCode.from_char('v'))
            callback: Function to call when the shortcut is pressed
        """
        self.shortcuts[(frozenset(modifiers), key)] = callback
        logger.debug(f"Registered shortcut: {modifiers} + {key}")
    
    def register_toggle_callback(self, callback: Callable):
        """
        Register a callback for the default toggle shortcut.
        
        Args:
            callback: Function to call when the toggle shortcut is pressed
        """
        modifiers, key = self.default_shortcut
        self.register_shortcut(modifiers, key, callback)
    
    def _on_press(self, key):
        """
        Handle key press events.
        
        Args:
            key: The pressed key
        """
        # Add to currently pressed keys
        if hasattr(key, 'char'):
            # Skip modifier tracking for character keys
            pass
        else:
            self.current_keys.add(key)
        
        # Check for shortcuts
        for (modifiers, trigger_key), callback in self.shortcuts.items():
            if self.current_keys == modifiers and key == trigger_key:
                logger.debug(f"Shortcut triggered: {modifiers} + {trigger_key}")
                callback()
    
    def _on_release(self, key):
        """
        Handle key release events.
        
        Args:
            key: The released key
        """
        # Remove from currently pressed keys
        try:
            self.current_keys.discard(key)
        except KeyError:
            pass  # Key wasn't in the set