import logging
import re
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class HallucinationFilter(ABC):

    @abstractmethod
    def filter(self, input_str: Optional[str]) -> Optional[str]:
        pass


class BackgroundNoiseHallucinationFilter(HallucinationFilter):
    """Ignore transcripts of background noise (indicated by parenthesis)"""

    IGNORE_PATTERN = re.compile(r"^\(.*\)$")

    def filter(self, input_str: Optional[str]) -> Optional[str]:
        if input_str is None or input_str.strip() is None:
            return None

        input_str = input_str.strip()
        if self.IGNORE_PATTERN.fullmatch(input_str.strip()) is not None:
            logger.info(f"Ignoring: {input_str}")

            return None
        return input_str


class SilenceHallucinationFilter(HallucinationFilter):
    """Ignore phrases commonly hallucinated when there is silence."""

    ignore_list = {
        "Thank you.",
        "Thank you for watching.",
        "See you later!",
    }

    def filter(self, input_str: Optional[str]) -> Optional[str]:
        if input_str is None or input_str.strip() is None:
            return None

        input_str = input_str.strip()

        if input_str in self.ignore_list:
            logger.info(f"Ignoring: {input_str}")
            return None
        return input_str
