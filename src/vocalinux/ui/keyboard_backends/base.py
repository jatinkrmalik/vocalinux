"""
Base class for keyboard backends.

All keyboard backends must inherit from this class and implement
the required methods.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

Callback = Callable[[], None]

# Supported double-tap shortcut keys
SUPPORTED_SHORTCUTS = {
    "ctrl+ctrl": "ctrl",
    "alt+alt": "alt",
    "shift+shift": "shift",
}

# Human-readable names for shortcuts (mode-agnostic base names)
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


def get_shortcut_display_name(shortcut: str, mode: Optional[str] = None) -> str:
    """
    Get a human-readable display name for a shortcut.

    Args:
        shortcut: The shortcut string (e.g., "ctrl+ctrl")
        mode: Optional mode string. If provided, returns mode-specific name.

    Returns:
        A human-readable display name for the shortcut
    """
    if mode and shortcut in SHORTCUT_MODE_DISPLAY_NAMES:
        return SHORTCUT_MODE_DISPLAY_NAMES[shortcut].get(
            mode, SHORTCUT_DISPLAY_NAMES.get(shortcut, shortcut)
        )
    return SHORTCUT_DISPLAY_NAMES.get(shortcut, shortcut)


def parse_shortcut(shortcut_string: str) -> str:
    """
    Parse a shortcut string and return the modifier key name.

    Args:
        shortcut_string: The shortcut string (e.g., "ctrl+ctrl", "alt+alt")

    Returns:
        The modifier key name (e.g., "ctrl", "alt")

    Raises:
        ValueError: If the shortcut string is not recognized
    """
    shortcut_lower = shortcut_string.lower().strip()
    if shortcut_lower not in SUPPORTED_SHORTCUTS:
        raise ValueError(
            f"Unsupported shortcut: {shortcut_string}. "
            f"Supported shortcuts: {', '.join(SUPPORTED_SHORTCUTS.keys())}"
        )
    return SUPPORTED_SHORTCUTS[shortcut_lower]


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
