"""
Base class for keyboard backends.

All keyboard backends must inherit from this class and implement
the required methods.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

# Supported double-tap shortcut keys
SUPPORTED_SHORTCUTS = {
    "ctrl+ctrl": "ctrl",
    "alt+alt": "alt",
    "shift+shift": "shift",
    "super+super": "super",
}

# Human-readable names for shortcuts
SHORTCUT_DISPLAY_NAMES = {
    "ctrl+ctrl": "Double-tap Ctrl",
    "alt+alt": "Double-tap Alt",
    "shift+shift": "Double-tap Shift",
    "super+super": "Double-tap Super (Windows key)",
}

DEFAULT_SHORTCUT = "ctrl+ctrl"


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

    def __init__(self, shortcut: str = DEFAULT_SHORTCUT):
        """
        Initialize the keyboard backend.

        Args:
            shortcut: The shortcut string to listen for (e.g., "ctrl+ctrl")
        """
        self.active = False
        self.double_tap_callback: Optional[Callable] = None
        self._shortcut = shortcut
        self._modifier_key = parse_shortcut(shortcut)

    @property
    def shortcut(self) -> str:
        """Get the current shortcut string."""
        return self._shortcut

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

    def register_toggle_callback(self, callback: Callable) -> None:
        """
        Register a callback for the double-tap shortcut.

        Args:
            callback: Function to call when double-tap is detected
        """
        self.double_tap_callback = callback
