"""Test optional filters for commonly hallucinated text"""

import unittest

from vocalinux.text_injection.hallucination_filter import (
    BackgroundNoiseHallucinationFilter,
    HallucinationFilter,
    SilenceHallucinationFilter,
)


class TestHallucinationFilters(unittest.TestCase):

    def test_silence_filter(self) -> None:
        f: HallucinationFilter = SilenceHallucinationFilter()
        assert f.filter("Thank you.") is None
        assert f.filter("Thank you") == "Thank you"
        assert f.filter(" Hello ") == "Hello"

    def test_background_noise_filter(self) -> None:
        f: HallucinationFilter = BackgroundNoiseHallucinationFilter()
        assert f.filter("(drum beating)") is None
        assert f.filter("(footsteps)") is None
        assert f.filter("(any text)") is None
        assert f.filter(" (any test with spaces) ") is None
        assert f.filter(" drum beating ") == "drum beating"
        assert f.filter("footsteps)") == "footsteps)"
        assert f.filter("(footsteps") == "(footsteps"
