"""Tests for capitalize_sentences function."""

import unittest

from vocalinux.speech_recognition.command_processor import capitalize_sentences


class TestCapitalizeSentences(unittest.TestCase):
    """Test cases for sentence capitalization."""

    def test_empty_string(self):
        """Empty string returns empty."""
        self.assertEqual(capitalize_sentences(""), "")

    def test_none_input(self):
        """None returns None."""
        self.assertIsNone(capitalize_sentences(None))

    def test_single_word(self):
        """Single lowercase word gets capitalized."""
        self.assertEqual(capitalize_sentences("hello"), "Hello")

    def test_already_capitalized(self):
        """Already capitalized text stays the same."""
        self.assertEqual(capitalize_sentences("Hello world"), "Hello world")

    def test_two_sentences_period(self):
        """Capitalize after period + space."""
        self.assertEqual(
            capitalize_sentences("hello world. goodbye world"),
            "Hello world. Goodbye world",
        )

    def test_multiple_sentences_mixed_punctuation(self):
        """Capitalize after period, question mark, exclamation."""
        self.assertEqual(
            capitalize_sentences("what? really! yes. ok"),
            "What? Really! Yes. Ok",
        )

    def test_url_preserved(self):
        """URLs without trailing space are not mangled."""
        self.assertEqual(
            capitalize_sentences("visit example.com for info"),
            "Visit example.com for info",
        )

    def test_decimal_preserved(self):
        """Decimal numbers are not treated as sentence boundaries."""
        self.assertEqual(
            capitalize_sentences("the value is 3.14 approximately"),
            "The value is 3.14 approximately",
        )

    def test_abbreviation_preserved(self):
        """Abbreviations without trailing space are preserved."""
        self.assertEqual(
            capitalize_sentences("e.g. this is an example"),
            "E.g. This is an example",
        )

    def test_number_after_period(self):
        """Numbers after punctuation are not capitalized (they're not letters)."""
        self.assertEqual(
            capitalize_sentences("42. 100 people showed up"),
            "42. 100 people showed up",
        )

    def test_newlines(self):
        """Newlines are treated as whitespace."""
        self.assertEqual(
            capitalize_sentences("hello.\nworld"),
            "Hello.\nWorld",
        )

    def test_multiple_spaces(self):
        """Multiple spaces after punctuation still trigger capitalization."""
        self.assertEqual(
            capitalize_sentences("hello.  world"),
            "Hello.  World",
        )

    def test_no_space_after_period(self):
        """No space after period means no capitalization (like in URLs)."""
        self.assertEqual(
            capitalize_sentences("test.case"),
            "Test.case",
        )

    def test_all_uppercase(self):
        """All uppercase text stays uppercase."""
        self.assertEqual(
            capitalize_sentences("HELLO WORLD. GOODBYE WORLD"),
            "HELLO WORLD. GOODBYE WORLD",
        )

    def test_mixed_case_after_punctuation(self):
        """Only lowercase letters after punctuation get capitalized."""
        self.assertEqual(
            capitalize_sentences("hello. WORLD. goodbye"),
            "Hello. WORLD. Goodbye",
        )

    def test_single_character(self):
        """Single character gets capitalized."""
        self.assertEqual(capitalize_sentences("a"), "A")

    def test_starts_with_number(self):
        """Text starting with a number is handled correctly."""
        self.assertEqual(
            capitalize_sentences("42 things happened. then more."),
            "42 things happened. Then more.",
        )


if __name__ == "__main__":
    unittest.main()
