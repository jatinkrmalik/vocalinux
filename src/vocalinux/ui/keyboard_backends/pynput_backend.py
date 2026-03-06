"""
Pynput keyboard backend for X11.

This backend uses the pynput library for global keyboard shortcuts.
Works on X11 and XWayland, but NOT on pure Wayland.
"""

import logging
import threading
import time
from typing import Optional, Set

# Try to import pynput
try:
    from pynput import keyboard

    PYNPUT_AVAILABLE = True
except ImportError:
    keyboard = None  # type: ignore
    PYNPUT_AVAILABLE = False

from .base import (
    DEFAULT_SHORTCUT,
    DEFAULT_SHORTCUT_MODE,
    KeyboardBackend,
    is_double_tap_shortcut,
    parse_keys,
)

logger = logging.getLogger(__name__)


# Map modifier key names to pynput Key objects
MODIFIER_KEY_MAP = {
    "ctrl": keyboard.Key.ctrl if PYNPUT_AVAILABLE else None,
    "alt": keyboard.Key.alt if PYNPUT_AVAILABLE else None,
    "shift": keyboard.Key.shift if PYNPUT_AVAILABLE else None,
    "super": keyboard.Key.cmd if PYNPUT_AVAILABLE else None,  # cmd is Super/Windows key
    "meta": keyboard.Key.cmd if PYNPUT_AVAILABLE else None,
}

# Map special key names to pynput Key objects
SPECIAL_KEY_MAP = {}
if PYNPUT_AVAILABLE:
    SPECIAL_KEY_MAP = {
        "space": keyboard.Key.space,
        "tab": keyboard.Key.tab,
        "enter": keyboard.Key.enter,
        "return": keyboard.Key.enter,
        "escape": keyboard.Key.esc,
        "backspace": keyboard.Key.backspace,
        "delete": keyboard.Key.delete,
        "insert": keyboard.Key.insert,
        "home": keyboard.Key.home,
        "end": keyboard.Key.end,
        "pageup": keyboard.Key.page_up,
        "pagedown": keyboard.Key.page_down,
        "up": keyboard.Key.up,
        "down": keyboard.Key.down,
        "left": keyboard.Key.left,
        "right": keyboard.Key.right,
        "capslock": keyboard.Key.caps_lock,
        "numlock": keyboard.Key.num_lock,
        "scrolllock": keyboard.Key.scroll_lock,
        "pause": keyboard.Key.pause,
        "printscreen": keyboard.Key.print_screen,
        "menu": keyboard.Key.menu,
        "f1": keyboard.Key.f1,
        "f2": keyboard.Key.f2,
        "f3": keyboard.Key.f3,
        "f4": keyboard.Key.f4,
        "f5": keyboard.Key.f5,
        "f6": keyboard.Key.f6,
        "f7": keyboard.Key.f7,
        "f8": keyboard.Key.f8,
        "f9": keyboard.Key.f9,
        "f10": keyboard.Key.f10,
        "f11": keyboard.Key.f11,
        "f12": keyboard.Key.f12,
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


def _resolve_pynput_key(key_name: str):
    """
    Map a key name string to its pynput Key or KeyCode representation.

    Args:
        key_name: Lowercase key name (e.g., "ctrl", "d", "f5", "space")

    Returns:
        A pynput Key enum value or KeyCode instance
    """
    if not PYNPUT_AVAILABLE:
        return None

    # Check modifiers first
    if key_name in MODIFIER_KEY_MAP:
        return MODIFIER_KEY_MAP[key_name]

    # Check special keys
    if key_name in SPECIAL_KEY_MAP:
        return SPECIAL_KEY_MAP[key_name]

    # Single character -> KeyCode
    if len(key_name) == 1:
        return keyboard.KeyCode.from_char(key_name)

    return None


def _normalize_key(key):
    """
    Normalize a pynput key by mapping left/right modifier variants
    to their generic form and lowercasing KeyCode chars.

    Args:
        key: A pynput Key or KeyCode

    Returns:
        The normalized key
    """
    if not PYNPUT_AVAILABLE:
        return key

    # Normalize left/right modifier variants
    normalized = MODIFIER_NORMALIZE_MAP.get(key, key)

    # Lowercase KeyCode chars
    if hasattr(normalized, "char") and normalized.char is not None:
        return keyboard.KeyCode.from_char(normalized.char.lower())

    return normalized


class PynputKeyboardBackend(KeyboardBackend):
    """
    Keyboard backend using pynput library.

    This backend works on X11 and XWayland but NOT on pure Wayland
    due to Wayland's security restrictions.
    """

    def __init__(self, shortcut: str = DEFAULT_SHORTCUT, mode: str = DEFAULT_SHORTCUT_MODE):
        """
        Initialize the pynput keyboard backend.

        Args:
            shortcut: The shortcut string to listen for (e.g., "ctrl+ctrl", "ctrl+d")
            mode: The shortcut mode ("toggle" or "push_to_talk")
        """
        super().__init__(shortcut, mode)
        self.listener = None
        self.last_trigger_time = 0
        self.last_key_press_time = 0
        self.double_tap_threshold = 0.3  # seconds
        self.current_keys: Set = set()

        # Combo tracking
        self._pressed_keys: Set = set()
        self._combo_active: bool = False
        self._target_keys: Set = set()
        self._update_target_keys()

        if not PYNPUT_AVAILABLE:
            logger.error("pynput library not available")

    def _update_target_keys(self) -> None:
        """Update the set of target pynput keys from the current shortcut."""
        if self._is_double_tap():
            # For double-tap shortcuts like ctrl+ctrl, target is just the single modifier
            key_name = self._shortcut.lower().strip().split("+")[0]
            resolved = _resolve_pynput_key(key_name)
            self._target_keys = {resolved} if resolved else set()
        else:
            # For combo shortcuts, resolve all keys
            try:
                keys = parse_keys(self._shortcut)
                self._target_keys = set()
                for k in keys:
                    resolved = _resolve_pynput_key(k)
                    if resolved is not None:
                        self._target_keys.add(resolved)
            except ValueError:
                self._target_keys = set()

    def set_shortcut(self, shortcut: str) -> None:
        """
        Update the shortcut to listen for.

        Args:
            shortcut: The new shortcut string (e.g., "ctrl+ctrl", "ctrl+d")
        """
        super().set_shortcut(shortcut)
        self._update_target_keys()
        # Reset combo state
        self._pressed_keys = set()
        self._combo_active = False

    def _is_double_tap(self) -> bool:
        """Check if the current shortcut is a double-tap shortcut."""
        return is_double_tap_shortcut(self._shortcut)

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

        logger.info(
            f"Starting pynput keyboard listener for shortcut: "
            f"{self._shortcut} (mode: {self._mode})"
        )
        self.current_keys = set()
        self._pressed_keys = set()
        self._combo_active = False

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
            normalized_key = _normalize_key(key)

            if normalized_key not in self._target_keys:
                return

            if self._is_double_tap():
                # Double-tap logic
                current_time = time.time()

                if self._mode == "toggle":
                    if (
                        current_time - self.last_key_press_time < self.double_tap_threshold
                        and self.double_tap_callback is not None
                        and current_time - self.last_trigger_time > 0.5
                    ):
                        logger.debug(f"Double-tap {self._modifier_key} detected (pynput)")
                        self.last_trigger_time = current_time
                        threading.Thread(target=self.double_tap_callback, daemon=True).start()
                elif self._mode == "push_to_talk":
                    if self.key_press_callback is not None:
                        logger.debug(f"Key press {self._modifier_key} detected (pynput)")
                        threading.Thread(target=self.key_press_callback, daemon=True).start()

                self.last_key_press_time = current_time
            else:
                # Combo logic: track pressed keys
                self._pressed_keys.add(normalized_key)

                if self._pressed_keys >= self._target_keys and not self._combo_active:
                    self._combo_active = True
                    if self._mode == "toggle":
                        if self.double_tap_callback is not None:
                            logger.debug(f"Combo {self._shortcut} activated (pynput)")
                            threading.Thread(target=self.double_tap_callback, daemon=True).start()
                    elif self._mode == "push_to_talk":
                        if self.key_press_callback is not None:
                            logger.debug(f"Combo press {self._shortcut} detected (pynput)")
                            threading.Thread(target=self.key_press_callback, daemon=True).start()

        except Exception as e:
            logger.error(f"Error in pynput key press handling: {e}")

    def _on_release(self, key) -> None:
        """Handle key release events."""
        try:
            normalized_key = _normalize_key(key)

            if self._is_double_tap():
                # Double-tap push-to-talk release
                if self._mode == "push_to_talk" and normalized_key in self._target_keys:
                    if self.key_release_callback is not None:
                        logger.debug(f"Key release {self._modifier_key} detected (pynput)")
                        threading.Thread(target=self.key_release_callback, daemon=True).start()
            else:
                # Combo release logic
                self._pressed_keys.discard(normalized_key)

                if self._combo_active and not (self._pressed_keys >= self._target_keys):
                    self._combo_active = False
                    if self._mode == "push_to_talk":
                        if self.key_release_callback is not None:
                            logger.debug(f"Combo release {self._shortcut} detected (pynput)")
                            threading.Thread(target=self.key_release_callback, daemon=True).start()

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
