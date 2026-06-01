"""
Common types and type hints for the application.
This module provides type definitions to avoid circular imports.
"""

from enum import Enum, auto
from typing import Callable, Optional, Protocol  # noqa: F401


class RecognitionState(Enum):
    """Enum representing the state of the speech recognition system."""

    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    ERROR = auto()


class SpeechRecognitionManagerProtocol(Protocol):
    """Protocol defining the interface for SpeechRecognitionManager."""

    state: RecognitionState

    def start_recognition(self, mode: str = "toggle") -> None:
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

    def add_streaming_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Register a callback for streaming transcript updates."""
        ...

    def remove_streaming_callback(self, callback: Callable[[str, bool], None]) -> None:
        """Remove a streaming transcript callback."""
        ...


class StreamingCallbackProtocol(Protocol):
    """Protocol for streaming transcript callbacks.

    Called with (text, is_final) where is_final indicates whether the text
    is committed (True, append to document) or partial (False, replace
    previous partial).
    """

    def __call__(self, text: str, is_final: bool) -> None: ...


class TextInjectorProtocol(Protocol):
    """Protocol defining the interface for TextInjector."""

    def inject_text(self, text: str) -> bool:
        """Inject text into the active application."""
        ...
