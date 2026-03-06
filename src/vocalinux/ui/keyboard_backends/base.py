"""
Base class for keyboard backends.

All keyboard backends must inherit from this class and implement
the required methods.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Optional

Callback = Callable[[], None]

# --- Key name validation sets ---

MODIFIER_KEYS = {"ctrl", "alt", "shift", "super", "meta"}

SPECIAL_KEYS = {
    "escape",
    "tab",
    "space",
    "backspace",
    "delete",
    "enter",
    "return",
    "insert",
    "home",
    "end",
    "pageup",
    "pagedown",
    "up",
    "down",
    "left",
    "right",
    "capslock",
    "numlock",
    "scrolllock",
    "printscreen",
    "pause",
    "menu",
    # Function keys
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
    "f11",
    "f12",
}

# --- Preset shortcuts (backward-compatible) ---

PRESET_SHORTCUTS = {
    "ctrl+ctrl": "ctrl",
    "alt+alt": "alt",
    "shift+shift": "shift",
}

# Backward-compatible alias
SUPPORTED_SHORTCUTS = PRESET_SHORTCUTS

# Human-readable names for preset shortcuts
SHORTCUT_DISPLAY_NAMES = {
    "ctrl+ctrl": "Ctrl",
    "alt+alt": "Alt",
    "shift+shift": "Shift",
}

# Mode-specific display names (format: {shortcut: {mode: display_name}})
SHORTCUT_MODE_DISPLAY_NAMES = {
    "ctrl+ctrl": {
        "toggle": "Double-tap Ctrl",
        "push_to_talk": "Hold Ctrl",
    },
    "alt+alt": {
        "toggle": "Double-tap Alt",
        "push_to_talk": "Hold Alt",
    },
    "shift+shift": {
        "toggle": "Double-tap Shift",
        "push_to_talk": "Hold Shift",
    },
}

DEFAULT_SHORTCUT = "ctrl+ctrl"

# Supported shortcut modes
SHORTCUT_MODES = {
    "toggle": "Toggle (double-tap to start/stop)",
    "push_to_talk": "Push-to-Talk (hold to speak)",
}

DEFAULT_SHORTCUT_MODE = "toggle"


# --- Flexible key parsing functions ---


def is_valid_key_name(key: str) -> bool:
    """
    Check if a string is a valid key name.

    Args:
        key: The key name to validate (lowercase).

    Returns:
        True if the key is a recognized modifier, special key,
        or a single alphanumeric character.
    """
    if key in MODIFIER_KEYS:
        return True
    if key in SPECIAL_KEYS:
        return True
    # Single alphanumeric characters (a-z, 0-9)
    if len(key) == 1 and key.isalnum():
        return True
    return False


def parse_keys(shortcut_string: str) -> List[str]:
    """
    Parse a shortcut string into a list of individual key names.

    Splits on '+', lowercases, strips whitespace, and validates each key.

    Args:
        shortcut_string: The shortcut string (e.g., "ctrl+d", "super+ctrl", "f5")

    Returns:
        A list of lowercase key names (e.g., ["ctrl", "d"])

    Raises:
        ValueError: If the string is empty or contains invalid key names
    """
    if not shortcut_string or not shortcut_string.strip():
        raise ValueError("Shortcut string cannot be empty")

    parts = [part.strip().lower() for part in shortcut_string.split("+")]
    parts = [p for p in parts if p]  # Remove empty parts from e.g. "ctrl+"

    if not parts:
        raise ValueError("Shortcut string cannot be empty")

    for key in parts:
        if not is_valid_key_name(key):
            raise ValueError(
                f"Invalid key name: '{key}'. "
                f"Must be a modifier ({', '.join(sorted(MODIFIER_KEYS))}), "
                f"a special key, or a single alphanumeric character."
            )

    return parts


def is_preset_shortcut(shortcut: str) -> bool:
    """
    Check if a shortcut string is one of the 3 preset double-tap shortcuts.

    Args:
        shortcut: The shortcut string (e.g., "ctrl+ctrl")

    Returns:
        True if the shortcut is a preset (ctrl+ctrl, alt+alt, shift+shift)
    """
    return shortcut.lower().strip() in PRESET_SHORTCUTS


def is_double_tap_shortcut(shortcut: str) -> bool:
    """
    Check if a shortcut string represents a double-tap of the same key.

    Args:
        shortcut: The shortcut string (e.g., "ctrl+ctrl", "alt+alt")

    Returns:
        True if the shortcut is a double-tap (same key repeated with +)
    """
    parts = shortcut.lower().strip().split("+")
    return len(parts) == 2 and parts[0] == parts[1] and parts[0] in MODIFIER_KEYS


def is_combo_shortcut(shortcut: str) -> bool:
    """
    Check if a shortcut is a key combination (not a double-tap preset).

    Args:
        shortcut: The shortcut string

    Returns:
        True if the shortcut is a combo like "ctrl+d" or "super+ctrl"
    """
    return not is_double_tap_shortcut(shortcut)


def format_shortcut_display(shortcut: str) -> str:
    """
    Format a shortcut string for human-readable display.

    Capitalizes each key name and joins with " + ".

    Args:
        shortcut: The shortcut string (e.g., "ctrl+d", "super+ctrl")

    Returns:
        A formatted display string (e.g., "Ctrl + D", "Super + Ctrl")
    """
    parts = shortcut.lower().strip().split("+")
    formatted = []
    for part in parts:
        part = part.strip()
        if part:
            # Capitalize: "ctrl" -> "Ctrl", "f5" -> "F5", "a" -> "A"
            formatted.append(part.capitalize())
    return " + ".join(formatted)


def get_shortcut_display_name(shortcut: str, mode: Optional[str] = None) -> str:
    """
    Get a human-readable display name for a shortcut.

    For preset shortcuts, returns mode-specific names when mode is provided.
    For arbitrary shortcuts, falls back to format_shortcut_display().

    Args:
        shortcut: The shortcut string (e.g., "ctrl+ctrl", "ctrl+d")
        mode: Optional mode string. If provided, returns mode-specific name.

    Returns:
        A human-readable display name for the shortcut
    """
    if mode and shortcut in SHORTCUT_MODE_DISPLAY_NAMES:
        return SHORTCUT_MODE_DISPLAY_NAMES[shortcut].get(
            mode, SHORTCUT_DISPLAY_NAMES.get(shortcut, format_shortcut_display(shortcut))
        )
    if shortcut in SHORTCUT_DISPLAY_NAMES:
        return SHORTCUT_DISPLAY_NAMES[shortcut]
    return format_shortcut_display(shortcut)


def parse_shortcut(shortcut_string: str) -> str:
    """
    Parse a shortcut string and return the modifier key name.

    For preset double-tap shortcuts (e.g., "ctrl+ctrl"), returns the
    modifier key. For arbitrary combos (e.g., "ctrl+d"), returns the
    first key in the combo.

    Args:
        shortcut_string: The shortcut string (e.g., "ctrl+ctrl", "ctrl+d")

    Returns:
        The modifier/primary key name (e.g., "ctrl")

    Raises:
        ValueError: If the shortcut string is not valid
    """
    shortcut_lower = shortcut_string.lower().strip()

    if not shortcut_lower:
        raise ValueError("Shortcut string cannot be empty")

    # Preset double-tap shortcuts
    if shortcut_lower in PRESET_SHORTCUTS:
        return PRESET_SHORTCUTS[shortcut_lower]

    # Arbitrary combos: validate via parse_keys, must have at least 2 keys
    keys = parse_keys(shortcut_lower)
    if len(keys) < 2:
        raise ValueError(
            f"Shortcut must contain at least two keys separated by '+': {shortcut_string}"
        )

    return keys[0]


class KeyboardBackend(ABC):
    """
    Abstract base class for keyboard backends.

    Each backend must implement methods for starting/stopping keyboard
    event listening and registering callbacks for specific shortcuts.
    """

    def __init__(self, shortcut: str = DEFAULT_SHORTCUT, mode: str = DEFAULT_SHORTCUT_MODE):
        """
        Initialize the keyboard backend.

        Args:
            shortcut: The shortcut string to listen for (e.g., "ctrl+ctrl")
            mode: The shortcut mode ("toggle" or "push_to_talk")
        """
        self.active = False
        self.double_tap_callback: Optional[Callback] = None
        self.key_press_callback: Optional[Callback] = None
        self.key_release_callback: Optional[Callback] = None
        self._shortcut = shortcut
        self._mode = mode
        self._modifier_key = parse_shortcut(shortcut)

    @property
    def shortcut(self) -> str:
        """Get the current shortcut string."""
        return self._shortcut

    @property
    def mode(self) -> str:
        """Get the current shortcut mode."""
        return self._mode

    def set_mode(self, mode: str) -> None:
        """
        Update the shortcut mode.

        Args:
            mode: The new mode ("toggle" or "push_to_talk")
        """
        if mode not in SHORTCUT_MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {list(SHORTCUT_MODES.keys())}")
        self._mode = mode

    @property
    def modifier_key(self) -> str:
        """Get the modifier key being watched for double-tap."""
        return self._modifier_key

    def set_shortcut(self, shortcut: str) -> None:
        """
        Update the shortcut to listen for.

        Args:
            shortcut: The new shortcut string (e.g., "ctrl+ctrl", "alt+alt")
        """
        self._modifier_key = parse_shortcut(shortcut)
        self._shortcut = shortcut

    @abstractmethod
    def start(self) -> bool:
        """
        Start listening for keyboard events.

        Returns:
            True if the backend started successfully, False otherwise
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop listening for keyboard events."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this backend is available on the current system.

        Returns:
            True if the backend can be used, False otherwise
        """
        pass

    @abstractmethod
    def get_permission_hint(self) -> Optional[str]:
        """
        Get a hint message if permissions are missing.

        Returns:
            A string explaining how to fix permissions, or None if permissions are OK
        """
        pass

    def register_toggle_callback(self, callback: Optional[Callback]) -> None:
        """
        Register a callback for the double-tap shortcut.

        Args:
            callback: Function to call when double-tap is detected
        """
        self.double_tap_callback = callback

    def register_press_callback(self, callback: Optional[Callback]) -> None:
        """
        Register a callback for key press events (push-to-talk mode).

        Args:
            callback: Function to call when the shortcut key is pressed
        """
        self.key_press_callback = callback

    def register_release_callback(self, callback: Optional[Callback]) -> None:
        """
        Register a callback for key release events (push-to-talk mode).

        Args:
            callback: Function to call when the shortcut key is released
        """
        self.key_release_callback = callback
