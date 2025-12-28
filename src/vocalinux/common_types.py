"""
Common types and type hints for the application.
This module provides type definitions to avoid circular imports.
"""

from enum import Enum, auto
from typing import Callable, List, Optional, Protocol


class RecognitionState(Enum):
    """Enum representing the state of the speech recognition system."""

    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    ERROR = auto()


class SpeechRecognitionManagerProtocol(Protocol):
    """Protocol defining the interface for SpeechRecognitionManager."""

    state: RecognitionState

    def start_recognition(self) -> None:
        """Start the speech recognition process."""
        ...

    def stop_recognition(self) -> None:
        """Stop the speech recognition process."""
        ...

    def register_state_callback(self, callback: Callable[[RecognitionState], None]) -> None:
        """Register a callback for state changes."""
        ...

    def register_text_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback for recognized text."""
        ...


class TextInjectorProtocol(Protocol):
    """Protocol defining the interface for TextInjector."""

    def inject_text(self, text: str) -> bool:
        """Inject text into the active application."""
        ...
