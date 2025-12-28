"""
Action handler for Vocalinux voice commands.

This module handles special voice commands like "delete that", "undo", etc.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..text_injection.text_injector import TextInjector

logger = logging.getLogger(__name__)


class ActionHandler:
    """
    Handles special voice command actions.

    This class processes action commands from the speech recognition system
    and performs the appropriate actions like deleting text, undoing, etc.
    """

    def __init__(self, text_injector: "TextInjector"):
        """
        Initialize the action handler.

        Args:
            text_injector: The text injector instance for performing actions
        """
        self.text_injector = text_injector
        self.last_injected_text = ""

        # Map actions to handler methods
        self.action_handlers = {
            "delete_last": self._handle_delete_last,
            "undo": self._handle_undo,
            "redo": self._handle_redo,
            "select_all": self._handle_select_all,
            "select_line": self._handle_select_line,
            "select_word": self._handle_select_word,
            "select_paragraph": self._handle_select_paragraph,
            "cut": self._handle_cut,
            "copy": self._handle_copy,
            "paste": self._handle_paste,
        }

    def handle_action(self, action: str) -> bool:
        """
        Handle a voice command action.

        Args:
            action: The action to perform

        Returns:
            True if the action was handled successfully, False otherwise
        """
        logger.debug(f"Handling action: {action}")

        handler = self.action_handlers.get(action)
        if handler:
            try:
                return handler()
            except Exception as e:
                logger.error(f"Error handling action '{action}': {e}")
                return False
        else:
            logger.warning(f"Unknown action: {action}")
            return False

    def set_last_injected_text(self, text: str):
        """
        Set the last injected text for undo/delete operations.

        Args:
            text: The last text that was injected
        """
        self.last_injected_text = text

    def _handle_delete_last(self) -> bool:
        """Handle 'delete that' command by sending backspace keys."""
        if not self.last_injected_text:
            logger.debug("No text to delete")
            return True

        # Send backspace keys for each character in the last injected text
        backspaces = "\b" * len(self.last_injected_text)
        success = self.text_injector.inject_text(backspaces)

        if success:
            logger.debug(f"Deleted {len(self.last_injected_text)} characters")
            self.last_injected_text = ""

        return success

    def _handle_undo(self) -> bool:
        """Handle 'undo' command by sending Ctrl+Z."""
        return self.text_injector._inject_keyboard_shortcut("ctrl+z")

    def _handle_redo(self) -> bool:
        """Handle 'redo' command by sending Ctrl+Y."""
        return self.text_injector._inject_keyboard_shortcut("ctrl+y")

    def _handle_select_all(self) -> bool:
        """Handle 'select all' command by sending Ctrl+A."""
        return self.text_injector._inject_keyboard_shortcut("ctrl+a")

    def _handle_select_line(self) -> bool:
        """Handle 'select line' command by sending Home+Shift+End."""
        return self.text_injector._inject_keyboard_shortcut("Home+shift+End")

    def _handle_select_word(self) -> bool:
        """Handle 'select word' command by sending Ctrl+Shift+Right."""
        return self.text_injector._inject_keyboard_shortcut("ctrl+shift+Right")

    def _handle_select_paragraph(self) -> bool:
        """Handle 'select paragraph' command by sending Ctrl+Shift+Down."""
        return self.text_injector._inject_keyboard_shortcut("ctrl+shift+Down")

    def _handle_cut(self) -> bool:
        """Handle 'cut' command by sending Ctrl+X."""
        return self.text_injector._inject_keyboard_shortcut("ctrl+x")

    def _handle_copy(self) -> bool:
        """Handle 'copy' command by sending Ctrl+C."""
        return self.text_injector._inject_keyboard_shortcut("ctrl+c")

    def _handle_paste(self) -> bool:
        """Handle 'paste' command by sending Ctrl+V."""
        return self.text_injector._inject_keyboard_shortcut("ctrl+v")
