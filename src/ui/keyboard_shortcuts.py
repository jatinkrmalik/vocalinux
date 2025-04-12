#!/usr/bin/env python3
"""
Keyboard shortcut manager for Vocalinux.
"""

import logging
import threading
from typing import Callable, Dict

# Try to import keyboard library, which requires root on Linux
# We'll try xlib/pynput as alternatives if not available
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    
# Alternative keyboard libraries for different platforms
if not KEYBOARD_AVAILABLE:
    try:
        from pynput import keyboard as pynput_keyboard
        PYNPUT_AVAILABLE = True
    except ImportError:
        PYNPUT_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class KeyboardShortcuts:
    """
    Keyboard shortcut manager for the application.
    
    Handles registration and triggering of keyboard shortcuts.
    """

    def __init__(self, default_shortcut=None):
        """
        Initialize the keyboard shortcut manager.
        
        Args:
            default_shortcut: Optional default shortcut to register
        """
        self.shortcuts = {}
        self.pynput_listener = None
        self.lock = threading.Lock()
        self.default_callback = None
        
        # Check for available libraries
        if not (KEYBOARD_AVAILABLE or PYNPUT_AVAILABLE):
            logger.warning("No keyboard libraries available. Shortcuts will not work.")
            
    def register_shortcut(self, key_combination, callback):
        """
        Register a keyboard shortcut.
        
        Args:
            key_combination: The key combination as a string (e.g., "ctrl+shift+a")
            callback: The function to call when the shortcut is triggered
        """
        with self.lock:
            if not key_combination:
                logger.warning("Empty key combination provided")
                return False
                
            # Store the callback
            self.shortcuts[self._normalize_key_combination(key_combination)] = callback
            
            # Register with the appropriate library
            if KEYBOARD_AVAILABLE:
                try:
                    keyboard.add_hotkey(key_combination, callback, suppress=True)
                    logger.info(f"Registered shortcut {key_combination}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to register shortcut {key_combination}: {e}")
                    return False
            elif PYNPUT_AVAILABLE:
                # For pynput, we need to set up a listener if not already done
                if not self.pynput_listener:
                    self._setup_pynput_listener()
                logger.info(f"Registered shortcut {key_combination} with pynput")
                return True
            else:
                logger.warning("Cannot register shortcuts without keyboard libraries")
                return False
                
    def unregister_shortcut(self, key_combination):
        """
        Unregister a keyboard shortcut.
        
        Args:
            key_combination: The key combination to unregister
        """
        with self.lock:
            normalized = self._normalize_key_combination(key_combination)
            if normalized in self.shortcuts:
                del self.shortcuts[normalized]
                
                if KEYBOARD_AVAILABLE:
                    try:
                        keyboard.remove_hotkey(key_combination)
                        logger.info(f"Unregistered shortcut {key_combination}")
                    except Exception as e:
                        logger.error(f"Failed to unregister shortcut {key_combination}: {e}")
                        
                # For pynput, we just remove from our dict; the listener will check it
                
    def unregister_all(self):
        """Unregister all shortcuts."""
        with self.lock:
            self.shortcuts.clear()
            
            if KEYBOARD_AVAILABLE:
                keyboard.unhook_all()
                
            if PYNPUT_AVAILABLE and self.pynput_listener:
                self.pynput_listener.stop()
                self.pynput_listener = None
                
    def _normalize_key_combination(self, combo):
        """
        Normalize a key combination string.
        
        Handles different formats and ordering of modifier keys.
        
        Args:
            combo: The key combination string
            
        Returns:
            A normalized key combination string
        """
        if not combo:
            return ""
            
        parts = combo.lower().split("+")
        
        # Sort modifiers for consistent ordering
        modifiers = []
        key = None
        
        for part in parts:
            if part in ["ctrl", "control", "alt", "option", "shift", "super", "win", "meta", "command"]:
                # Normalize modifier names
                if part in ["control", "ctrl"]:
                    modifiers.append("ctrl")
                elif part in ["option", "alt"]:
                    modifiers.append("alt")
                elif part in ["super", "win", "meta", "command"]:
                    modifiers.append("super")
                else:
                    modifiers.append(part)
            else:
                # The last non-modifier is the key
                key = part
                
        modifiers.sort()
        
        if key:
            return "+".join(modifiers + [key])
        else:
            # If no key was found, use the last part as the key
            if parts:
                return "+".join(modifiers + [parts[-1]])
            return ""
            
    def _setup_pynput_listener(self):
        """Set up a pynput keyboard listener for shortcuts."""
        if not PYNPUT_AVAILABLE:
            return
            
        # Track currently pressed keys
        self.pressed_keys = set()
        
        def on_press(key):
            try:
                # Convert key to string
                if hasattr(key, "char") and key.char:
                    key_str = key.char.lower()
                else:
                    key_str = key.name.lower() if hasattr(key, "name") else str(key).lower()
                    
                # Add to pressed keys
                self.pressed_keys.add(key_str)
                
                # Check if any registered combination is pressed
                current_combo = "+".join(sorted(self.pressed_keys))
                for combo, callback in self.shortcuts.items():
                    if current_combo == combo:
                        callback()
                        
            except Exception as e:
                logger.error(f"Error in keyboard listener: {e}")
                
        def on_release(key):
            try:
                # Convert key to string
                if hasattr(key, "char") and key.char:
                    key_str = key.char.lower()
                else:
                    key_str = key.name.lower() if hasattr(key, "name") else str(key).lower()
                    
                # Remove from pressed keys
                if key_str in self.pressed_keys:
                    self.pressed_keys.remove(key_str)
                    
            except Exception as e:
                logger.error(f"Error in keyboard listener: {e}")
                
        # Create and start the listener
        self.pynput_listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
        self.pynput_listener.start()
        logger.info("Started pynput keyboard listener")
        
    def register_callback(self, callback):
        """
        Register a callback for the default shortcut.
        
        Args:
            callback: The function to call when the shortcut is triggered
            
        Returns:
            True if registration was successful, False otherwise
        """
        self.default_callback = callback
        return True
    
    def stop_listener(self):
        """Stop the keyboard listener."""
        self.unregister_all()