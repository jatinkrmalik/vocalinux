"""
Command processor for Vocalinux.

This module processes text commands from speech recognition, such as
"new line", "period", etc.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Text commands that attach tightly to the preceding word (strip space before).
_TIGHT_BEFORE = frozenset(
    {
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
)

# Tight punctuation that should not force a space after when the next token is a newline.
_NO_SPACE_AFTER_IF_NEWLINE = frozenset({".", ",", ";", ":", "?", "!", ")", "]", "}"})


class CommandProcessor:
    """
    Processes text commands in speech recognition results.

    This class handles special commands like "new line", "period",
    "delete that", etc.
    """

    def __init__(self):
        """Initialize the command processor."""
        # Map of command phrases to their replacement text
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

        # Active format modifiers (exposed for tests / callers)
        self.active_formats: set = set()

        self._compile_patterns()

    @staticmethod
    def _flex_phrase_pattern(phrase: str) -> str:
        """Build a regex for a command phrase with flexible internal whitespace."""
        return r"\s+".join(re.escape(w) for w in phrase.split())

    def _compile_patterns(self) -> None:
        """Compile regex patterns for command matching."""
        text_cmds = sorted(self.text_commands.keys(), key=len, reverse=True)
        action_cmds = sorted(self.action_commands.keys(), key=len, reverse=True)
        format_cmds = sorted(self.format_commands.keys(), key=len, reverse=True)

        self.text_cmd_regex = re.compile(
            r"\b(" + "|".join(self._flex_phrase_pattern(c) for c in text_cmds) + r")\b",
            re.IGNORECASE,
        )
        self.action_cmd_regex = re.compile(
            r"\b(" + "|".join(self._flex_phrase_pattern(c) for c in action_cmds) + r")\b",
            re.IGNORECASE,
        )
        self.format_cmd_regex = re.compile(
            r"\b(" + "|".join(self._flex_phrase_pattern(c) for c in format_cmds) + r")\b",
            re.IGNORECASE,
        )

        self._text_patterns: List[Tuple[re.Pattern, str, str]] = [
            (
                re.compile(r"\b" + self._flex_phrase_pattern(cmd) + r"\b", re.IGNORECASE),
                cmd,
                repl,
            )
            for cmd, repl in sorted(self.text_commands.items(), key=lambda x: -len(x[0]))
        ]
        self._action_patterns: List[Tuple[re.Pattern, str, str]] = [
            (
                re.compile(r"\b" + self._flex_phrase_pattern(cmd) + r"\b", re.IGNORECASE),
                cmd,
                action,
            )
            for cmd, action in sorted(self.action_commands.items(), key=lambda x: -len(x[0]))
        ]
        self._format_patterns: List[Tuple[re.Pattern, str, str]] = [
            (
                re.compile(r"\b" + self._flex_phrase_pattern(cmd) + r"\b", re.IGNORECASE),
                cmd,
                fmt,
            )
            for cmd, fmt in sorted(self.format_commands.items(), key=lambda x: -len(x[0]))
        ]

    @staticmethod
    def _apply_formats_to_word(word: str, formats: List[str]) -> str:
        """Apply stacked format modifiers to a single word."""
        result = word
        for fmt in formats:
            if fmt == "capitalize_next":
                result = result.capitalize()
            elif fmt == "uppercase_next":
                result = result.upper()
            elif fmt == "lowercase_next":
                result = result.lower()
            # no_spaces_next: reserved (no-op until a multi-word target exists)
        return result

    def process_text(self, text: Optional[str]) -> tuple[str, list[str]]:
        """
        Process text commands in the recognized text.

        Left-to-right scan with longest-match command phrases (flexible internal
        whitespace). Format modifiers stack onto the next word; action phrases are
        stripped and collected; text commands are substituted with spacing rules
        for punctuation and delimiters.

        Args:
            text: The recognized text to process

        Returns:
            Tuple of (processed_text, actions)
        """
        if not text:
            return "", []

        logger.debug(f"Processing commands in text: {text}")
        self.active_formats = set()

        # Tokenize: ws | command (format/action/text, longest) | word | other
        tokens: List[Tuple[str, str, Optional[str]]] = []
        i = 0
        s = text
        n = len(s)

        while i < n:
            if s[i].isspace():
                j = i + 1
                while j < n and s[j].isspace():
                    j += 1
                tokens.append(("ws", s[i:j], None))
                i = j
                continue

            matched = False
            for patterns, kind in (
                (self._format_patterns, "format_cmd"),
                (self._action_patterns, "action_cmd"),
                (self._text_patterns, "text_cmd"),
            ):
                for pattern, phrase, payload in patterns:
                    m = pattern.match(s, i)
                    if m:
                        tokens.append((kind, phrase, payload))
                        i = m.end()
                        matched = True
                        break
                if matched:
                    break
            if matched:
                continue

            m = re.match(r"\w+", s[i:])
            if m:
                tokens.append(("word", m.group(0), None))
                i += m.end()
                continue

            tokens.append(("other", s[i], None))
            i += 1

        actions: List[str] = []
        pending_formats: List[str] = []
        pieces: List[str] = []  # output fragments (no free-floating multi-spaces)

        def strip_trailing_spaces() -> None:
            while pieces and pieces[-1] == " ":
                pieces.pop()

        def emit_space() -> None:
            if not pieces:
                return
            if pieces[-1] in (" ", "\n", "\n\n"):
                return
            if pieces[-1] in _NO_SPACE_AFTER_IF_NEWLINE:
                # space may still be wanted before words; caller decides
                pass
            pieces.append(" ")

        def next_content_kind(start: int) -> Optional[str]:
            for k, v, _ in tokens[start:]:
                if k == "ws":
                    continue
                if k == "format_cmd":
                    continue  # formats don't emit content by themselves
                if k == "action_cmd":
                    continue
                return k
            return None

        def next_emitted_preview(start: int) -> Optional[str]:
            """Preview what the next non-skipped token will emit (approx)."""
            pending = list(pending_formats)
            for k, v, p in tokens[start:]:
                if k == "ws":
                    continue
                if k == "format_cmd":
                    pending.append(str(p))
                    continue
                if k == "action_cmd":
                    continue
                if k == "text_cmd":
                    return str(p)
                if k == "word":
                    return self._apply_formats_to_word(str(v), pending) if pending else str(v)
                if k == "other":
                    return str(v)
            return None

        had_word_or_text = any(k in ("word", "text_cmd", "other") for k, _, _ in tokens)
        only_formats = (
            not had_word_or_text
            and not any(k == "action_cmd" for k, _, _ in tokens)
            and any(k == "format_cmd" for k, _, _ in tokens)
        )

        ti = 0
        while ti < len(tokens):
            kind, value, payload = tokens[ti]

            if kind == "ws":
                # Defer spacing to explicit emit between content tokens
                ti += 1
                continue

            if kind == "action_cmd":
                actions.append(str(payload))
                pending_formats.clear()
                ti += 1
                continue

            if kind == "format_cmd":
                pending_formats.append(str(payload))
                self.active_formats.add(str(payload))
                ti += 1
                continue

            if kind == "text_cmd":
                phrase = str(value)
                replacement = str(payload)

                if phrase in _TIGHT_BEFORE:
                    strip_trailing_spaces()

                # Space before non-tight symbols (dash, quote, open paren, etc.)
                if phrase not in _TIGHT_BEFORE and pieces and pieces[-1] not in (" ", "\n", "\n\n"):
                    # open delimiters / symbols: ensure space before unless start
                    if not pieces[-1].endswith("\n"):
                        emit_space()

                pieces.append(replacement)

                # Spacing after replacement
                nxt = next_emitted_preview(ti + 1)
                if nxt is not None:
                    if replacement in ("\n", "\n\n"):
                        # Keep a single space after newline when more content follows
                        # (e.g. "new line test" -> "\n test")
                        if not nxt.startswith("\n"):
                            pieces.append(" ")
                    elif replacement in _NO_SPACE_AFTER_IF_NEWLINE and nxt.startswith("\n"):
                        pass  # "Name,\n" — no space between comma and newline
                    elif replacement in (".", "?", "!"):
                        # sentence enders: space before following word if any
                        if nxt and nxt[0].isalnum():
                            pieces.append(" ")
                    elif replacement in (",", ";", ":"):
                        if nxt and not nxt.startswith("\n"):
                            pieces.append(" ")
                    elif replacement in ("(", "[", "{"):
                        # open delimiter: one space before content if content is a word
                        if nxt and nxt[0].isalnum():
                            pieces.append(" ")
                    elif replacement in ('"', "'", "-", "_"):
                        if nxt and nxt[0].isalnum():
                            pieces.append(" ")
                    # closers: no forced space

                pending_formats.clear()
                ti += 1
                continue

            if kind == "word":
                word = str(value)
                if pending_formats:
                    word = self._apply_formats_to_word(word, pending_formats)
                    pending_formats.clear()
                    self.active_formats.clear()

                # Space before word unless after open delim without space policy, or start
                if pieces:
                    prev = pieces[-1]
                    if prev not in (" ", "\n", "\n\n", "(", "[", "{"):
                        if prev in (
                            ".",
                            "?",
                            "!",
                            ",",
                            ";",
                            ":",
                            ")",
                            "]",
                            "}",
                            '"',
                            "'",
                            "-",
                            "_",
                        ):
                            # space already handled for most; ensure word separation
                            if prev in (")", "]", "}"):
                                pieces.append(" ")
                            elif prev in ('"', "'", "-", "_") and not prev.endswith(" "):
                                # already may have space from text_cmd handler
                                if pieces[-1] not in (" ",):
                                    # if previous emit didn't add space, add one
                                    pass
                        elif not prev.endswith("\n") and prev != " ":
                            emit_space()
                    # if prev is open delim without trailing space, fixtures want "( content"
                    if prev in ("(", "[", "{"):
                        if pieces[-1] != " ":
                            pieces.append(" ")

                pieces.append(word)
                ti += 1
                continue

            # other characters
            pieces.append(str(value))
            ti += 1

        if only_formats:
            # Bare format command(s) with no target word
            self.active_formats.clear()
            return "", actions

        # Join and light normalize (preserve newlines)
        processed = "".join(pieces)
        # Collapse horizontal whitespace runs, keep newlines intact
        processed = re.sub(r"[^\S\n]+", " ", processed)
        # Remove space before tight closers/punct (safety net)
        processed = re.sub(r" +([,.;:?!)\]}])", r"\1", processed)
        # Remove space after openers if double
        processed = re.sub(r"([(\[{]) +", r"\1 ", processed)
        # No space between punct and following newline
        processed = re.sub(r"([,.;:?!]) +\n", r"\1\n", processed)
        # Trim outer spaces/tabs but keep leading/trailing newlines if whole result is newline(s)
        if processed in ("\n", "\n\n"):
            pass
        else:
            processed = processed.strip(" \t")

        self.active_formats.clear()
        logger.debug(f"Processed result: {processed!r}, actions: {actions}")
        return processed, actions
