"""
Command processor for Vocalinux.

This module processes text commands from speech recognition, such as
"new line", "period", etc.
"""

import logging
import re

logger = logging.getLogger(__name__)


class CommandProcessor:
    """
    Processes text commands in speech recognition results.

    This class handles special commands like "new line", "period",
    "delete that", etc.
    """

    def __init__(self):
        """Initialize the command processor."""
        # Map of command phrases to their actions
        self.text_commands = {
            # Line commands
            "new line": "\n",
            "new paragraph": "\n\n",
            # Punctuation
            "period": ".",
            "full stop": ".",
            "comma": ",",
            "question mark": "?",
            "exclamation mark": "!",
            "exclamation point": "!",
            "semicolon": ";",
            "colon": ":",
            "dash": "-",
            "hyphen": "-",
            "underscore": "_",
            "quote": '"',
            "single quote": "'",
            "open parenthesis": "(",
            "close parenthesis": ")",
            "open bracket": "[",
            "close bracket": "]",
            "open brace": "{",
            "close brace": "}",
        }

        # Special action commands that don't directly map to text
        self.action_commands = {
            "delete that": "delete_last",
            "scratch that": "delete_last",
            "undo": "undo",
            "redo": "redo",
            "select all": "select_all",
            "select line": "select_line",
            "select word": "select_word",
            "select paragraph": "select_paragraph",
            "cut": "cut",
            "copy": "copy",
            "paste": "paste",
        }

        # Formatting commands that modify the next word
        self.format_commands = {
            "capitalize": "capitalize_next",
            "uppercase": "uppercase_next",
            "all caps": "uppercase_next",
            "lowercase": "lowercase_next",
            "no spaces": "no_spaces_next",
        }

        # Active format modifiers
        self.active_formats = set()

        # Compile regex patterns for faster matching
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for command matching."""
        # Create regex pattern for text commands
        text_cmd_pattern = (
            r"\b(" + "|".join(re.escape(cmd) for cmd in self.text_commands.keys()) + r")\b"
        )
        self.text_cmd_regex = re.compile(text_cmd_pattern, re.IGNORECASE)

        # Create regex pattern for action commands
        action_cmd_pattern = (
            r"\b(" + "|".join(re.escape(cmd) for cmd in self.action_commands.keys()) + r")\b"
        )
        self.action_cmd_regex = re.compile(action_cmd_pattern, re.IGNORECASE)

        # Create regex pattern for format commands
        format_cmd_pattern = (
            r"\b(" + "|".join(re.escape(cmd) for cmd in self.format_commands.keys()) + r")\b"
        )
        self.format_cmd_regex = re.compile(format_cmd_pattern, re.IGNORECASE)

    def process_text(self, text: str) -> tuple[str, list[str]]:
        """
        Process text commands in the recognized text.

        Args:
            text: The recognized text to process

        Returns:
            Tuple of (processed_text, actions)
            - processed_text: The text with commands replaced
            - actions: List of special actions to perform
        """
        if not text:
            return "", []

        logger.debug(f"Processing commands in text: {text}")

        processed_text = text.strip()
        actions: list[str] = []

        # Handle action commands
        for cmd, action in self.action_commands.items():
            cmd_pattern = r"\b" + re.escape(cmd) + r"\b"

            if re.search(cmd_pattern, text, re.IGNORECASE):
                actions.append(action)

                # Check if there's text after the command
                match = re.search(r"\b" + re.escape(cmd) + r"\s+(.*)", text, re.IGNORECASE)
                if match:
                    remaining_text = match.group(1).strip()
                    # Only add space if there's text before the command
                    cmd_match = re.search(r"^(.*?)\b" + re.escape(cmd) + r"\b", text, re.IGNORECASE)
                    if cmd_match and cmd_match.group(1).strip():
                        processed_text = " " + remaining_text
                    else:
                        processed_text = remaining_text
                else:
                    processed_text = ""

        # Handle text commands
        for cmd, replacement in self.text_commands.items():
            cmd_pattern = r"\b" + re.escape(cmd) + r"\b"
            if re.search(cmd_pattern, processed_text, re.IGNORECASE):
                if cmd in [
                    "period",
                    "full stop",
                    "comma",
                    "question mark",
                    "exclamation mark",
                    "exclamation point",
                    "semicolon",
                    "colon",
                ]:
                    # For punctuation, replace the command and remove the space before it
                    processed_text = re.sub(
                        r"\s*" + cmd_pattern + r"\s*",
                        replacement,
                        processed_text,
                        flags=re.IGNORECASE,
                    )
                else:
                    processed_text = re.sub(
                        cmd_pattern,
                        replacement,
                        processed_text,
                        flags=re.IGNORECASE,
                    )

        # Handle format commands
        for cmd, format_type in self.format_commands.items():
            cmd_pattern = r"\b" + re.escape(cmd) + r"\b"

            if re.search(cmd_pattern, text, re.IGNORECASE):
                # Handle format command that modifies next word
                match = re.search(r"\b" + re.escape(cmd) + r"\s+(\w+)", text, re.IGNORECASE)
                if match:
                    word = match.group(1)
                    if format_type == "capitalize_next":
                        replacement = word.capitalize()
                    elif format_type == "uppercase_next":
                        replacement = word.upper()
                    elif format_type == "lowercase_next":
                        replacement = word.lower()
                    else:
                        replacement = word

                    # Replace just that word
                    processed_text = re.sub(
                        r"\b" + re.escape(cmd) + r"\s+" + re.escape(word) + r"\b",
                        replacement,
                        text,
                        flags=re.IGNORECASE,
                    )
                else:
                    # Format command with no target word
                    processed_text = ""

        return processed_text, actions
