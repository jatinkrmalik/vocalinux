"""Process spoken text, formatting, and action commands."""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

_TIGHT_BEFORE = {
    "period",
    "full stop",
    "comma",
    "question mark",
    "exclamation mark",
    "exclamation point",
    "semicolon",
    "colon",
    "close parenthesis",
    "close bracket",
    "close brace",
}


class CommandProcessor:
    """Replace spoken commands and return any requested editor actions."""

    def __init__(self):
        """Initialize the command tables and regexes."""
        self.text_commands = {
            "new line": "\n",
            "new paragraph": "\n\n",
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
        self.format_commands = {
            "capitalize": "capitalize_next",
            "uppercase": "uppercase_next",
            "all caps": "uppercase_next",
            "lowercase": "lowercase_next",
            "no spaces": "no_spaces_next",
        }
        self.active_formats = set()
        self._compile_patterns()

    @staticmethod
    def _phrase_pattern(phrase: str) -> str:
        """Allow flexible whitespace inside a multi-word command."""
        return r"\s+".join(re.escape(word) for word in phrase.split())

    def _command_pattern(self, commands: dict[str, str]) -> re.Pattern:
        phrases = sorted(commands, key=len, reverse=True)
        return re.compile(
            r"\b(" + "|".join(self._phrase_pattern(phrase) for phrase in phrases) + r")\b",
            re.IGNORECASE,
        )

    def _compile_patterns(self) -> None:
        """Compile public command regexes and the combined processing regex."""
        self.text_cmd_regex = self._command_pattern(self.text_commands)
        self.action_cmd_regex = self._command_pattern(self.action_commands)
        self.format_cmd_regex = self._command_pattern(self.format_commands)
        self._command_regex = self._command_pattern(
            {**self.text_commands, **self.action_commands, **self.format_commands}
        )

    @staticmethod
    def _apply_formats(word: str, formats: list[str]) -> str:
        for format_name in formats:
            if format_name == "capitalize_next":
                word = word.capitalize()
            elif format_name == "uppercase_next":
                word = word.upper()
            elif format_name == "lowercase_next":
                word = word.lower()
            # no_spaces_next remains a no-op until it has a multi-word target.
        return word

    def process_text(self, text: Optional[str]) -> tuple[str, list[str]]:
        """Replace commands in *text* and return ``(processed_text, actions)``."""
        if not text:
            return "", []

        matches = list(self._command_regex.finditer(text))
        if not matches:
            return text.strip(), []

        actions: list[str] = []
        pending_formats: list[str] = []
        pieces: list[str] = []
        cursor = 0

        def append_text(fragment: str) -> None:
            if pending_formats:
                word_match = re.search(r"\w+", fragment)
                if word_match:
                    word = self._apply_formats(word_match.group(), pending_formats)
                    fragment = fragment[: word_match.start()] + word + fragment[word_match.end() :]
                    pending_formats.clear()
                    self.active_formats.clear()
            pieces.append(fragment)

        def strip_trailing_space() -> None:
            while pieces:
                pieces[-1] = pieces[-1].rstrip(" \t")
                if pieces[-1]:
                    break
                pieces.pop()

        for match in matches:
            append_text(text[cursor : match.start()])
            phrase = re.sub(r"\s+", " ", match.group().lower())

            if phrase in self.format_commands:
                format_name = self.format_commands[phrase]
                pending_formats.append(format_name)
                self.active_formats.add(format_name)
            elif phrase in self.action_commands:
                actions.append(self.action_commands[phrase])
                pending_formats.clear()
                self.active_formats.clear()
            else:
                if phrase in _TIGHT_BEFORE:
                    strip_trailing_space()
                pieces.append(self.text_commands[phrase])
                pending_formats.clear()
                self.active_formats.clear()

            cursor = match.end()

        append_text(text[cursor:])
        self.active_formats.clear()

        processed = re.sub(r"[^\S\n]+", " ", "".join(pieces))
        processed = re.sub(r"([,.;:?!]) +\n", r"\1\n", processed)
        processed = processed.strip(" \t")
        logger.debug("Processed result: %r, actions: %s", processed, actions)
        return processed, actions
