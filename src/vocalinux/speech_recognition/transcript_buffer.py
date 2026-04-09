"""
Transcript buffer for streaming speech recognition.

Implements a Local Agreement (LA-n) policy: text is only committed
when it appears consistently across consecutive recognition passes.
This prevents flickering and duplicate text injection.

"""

import logging
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

    def insert(self, text: str) -> None:
        if not text or not text.strip():
            return

        new_words = text.strip().split()
        if not new_words:
            return

        self._insert_count += 1

        if self._committed_words and new_words:
            max_check = min(len(self._committed_words), len(new_words), 5)
            for i in range(1, max_check + 1):
                committed_tail = " ".join(self._committed_words[-i:]).lower()
                new_head = " ".join(new_words[:i]).lower()
                if committed_tail == new_head:
                    new_words = new_words[i:]
                    break

        confirmed = []
        if self._buffer_words and new_words:
            max_check = min(len(self._buffer_words), len(new_words))
            for i in range(max_check):
                if self._buffer_words[i].lower() == new_words[i].lower():
                    confirmed.append(new_words[i])
                else:
                    break

        if confirmed:
            self._committed_words.extend(confirmed)
            self._buffer_words = self._buffer_words[len(confirmed) :]
            new_words = new_words[len(confirmed) :]
            logger.debug(f"Committed {len(confirmed)} words: {' '.join(confirmed)}")

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
