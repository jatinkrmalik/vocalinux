"""
Transcript buffer for streaming speech recognition.

Implements a Local Agreement (LA-n) policy: text is only committed
when it appears consistently across consecutive recognition passes.
This prevents flickering and duplicate text injection.

"""

import logging
import string
from typing import Optional

logger = logging.getLogger(__name__)


class TranscriptBuffer:
    """Buffers streaming recognition hypotheses and commits confirmed text.

    Uses word-level matching to compare consecutive recognition results.
    Words that match at both passes are confirmed and emitted.
    Remaining unmatched words are kept as pending for the next iteration.
    """

    _MIN_COMMIT_LENGTH = 2

    def __init__(self, confidence_threshold: int = 2):
        self._committed_words: list[str] = []
        self._emitted_count = 0
        self._buffer_words: list[str] = []
        self._new_words: list[str] = []
        self._confidence_threshold = confidence_threshold
        self._insert_count = 0

    def _normalize_word(self, word: str) -> str:
        return word.lower().strip(string.punctuation)

    def _find_tail_head_overlap(self, previous_words: list[str], new_words: list[str]) -> int:
        max_check = min(len(previous_words), len(new_words), 5)
        for count in range(max_check, 0, -1):
            previous_tail = [self._normalize_word(word) for word in previous_words[-count:]]
            new_head = [self._normalize_word(word) for word in new_words[:count]]
            if previous_tail == new_head and any(previous_tail):
                return count
        return 0

    def _strip_terminal_ellipsis(self, words: list[str]) -> list[str]:
        if not words:
            return words

        last_word = words[-1]
        if last_word.endswith("..."):
            stripped = last_word.rstrip(".")
            if stripped:
                words[-1] = stripped
            else:
                words.pop()
        return words

    def insert(self, text: str) -> None:
        if not text or not text.strip():
            return

        new_words = text.strip().split()
        if not new_words:
            return

        self._insert_count += 1

        had_committed_tail_overlap = False
        if self._committed_words and new_words:
            max_check = min(len(self._committed_words), len(new_words), 5)
            for i in range(1, max_check + 1):
                committed_tail = [self._normalize_word(word) for word in self._committed_words[-i:]]
                new_head = [self._normalize_word(word) for word in new_words[:i]]
                if committed_tail == new_head and any(committed_tail):
                    new_words = new_words[i:]
                    had_committed_tail_overlap = True
                    break

        confirmed = []
        if self._buffer_words and new_words:
            max_check = min(len(self._buffer_words), len(new_words))
            for i in range(max_check):
                if self._normalize_word(self._buffer_words[i]) == self._normalize_word(
                    new_words[i]
                ):
                    confirmed.append(new_words[i])
                else:
                    break

        if confirmed:
            self._committed_words.extend(self._strip_terminal_ellipsis(confirmed))
            self._buffer_words = self._buffer_words[len(confirmed) :]
            new_words = new_words[len(confirmed) :]
            logger.debug(f"Committed {len(confirmed)} words: {' '.join(confirmed)}")
        elif self._buffer_words and new_words and not had_committed_tail_overlap:
            # Whisper/whisper.cpp may produce sequential, non-overlapping chunks
            # instead of revised hypotheses for the same window. Once a new
            # unrelated hypothesis arrives, commit the previous pending words so
            # streaming dictation advances instead of waiting until final stop.
            overlap_count = self._find_tail_head_overlap(self._buffer_words, new_words)
            words_to_commit = self._strip_terminal_ellipsis(self._buffer_words.copy())
            self._committed_words.extend(words_to_commit)
            logger.debug(f"Committed stale pending words: {' '.join(self._buffer_words)}")
            self._buffer_words = []
            new_words = new_words[overlap_count:]

        self._buffer_words = new_words
        self._new_words = new_words

    def flush(self) -> Optional[str]:
        if self._emitted_count < len(self._committed_words):
            delta = self._committed_words[self._emitted_count :]
            self._emitted_count = len(self._committed_words)
            return " ".join(delta)
        return None

    def flush_all(self) -> Optional[str]:
        remaining_committed = self._committed_words[self._emitted_count :]
        all_words = remaining_committed + self._buffer_words
        self._committed_words = []
        self._emitted_count = 0
        self._buffer_words = []
        self._new_words = []
        self._insert_count = 0
        if all_words:
            return " ".join(all_words)
        return None

    def reset(self) -> None:
        self._committed_words = []
        self._emitted_count = 0
        self._buffer_words = []
        self._new_words = []
        self._insert_count = 0

    @property
    def committed_text(self) -> str:
        return " ".join(self._committed_words)

    @property
    def pending_text(self) -> str:
        return " ".join(self._buffer_words)

    @property
    def has_pending(self) -> bool:
        return len(self._buffer_words) > 0
