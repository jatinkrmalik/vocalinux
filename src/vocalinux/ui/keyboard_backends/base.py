"""
Base class for keyboard backends.

All keyboard backends must inherit from this class and implement
the required methods.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional


class KeyboardBackend(ABC):
    """
    Abstract base class for keyboard backends.

    Each backend must implement methods for starting/stopping keyboard
    event listening and registering callbacks for specific shortcuts.
    """

    def __init__(self):
        """Initialize the keyboard backend."""
        self.active = False
        self.double_tap_callback: Optional[Callable] = None

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
        Register a callback for the double-tap Ctrl shortcut.

        Args:
            callback: Function to call when double-tap Ctrl is detected
        """
        self.double_tap_callback = callback
