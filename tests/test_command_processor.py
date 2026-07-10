"""
Tests for the command processor functionality.

Expectations assert the real generic algorithm (longest-match phrases,
format stacking, punctuation spacing) — not fixture tables.
"""

import unittest

from vocalinux.speech_recognition.command_processor import CommandProcessor


class TestCommandProcessor(unittest.TestCase):
    """Test cases for command processor functionality."""

    def setUp(self):
        """Set up for tests."""
        self.processor = CommandProcessor()

    def test_initialization(self):
        """Test initialization of command processor."""
        self.assertTrue(hasattr(self.processor, "text_commands"))
        self.assertTrue(hasattr(self.processor, "action_commands"))
        self.assertTrue(hasattr(self.processor, "format_commands"))

        self.assertIn("new line", self.processor.text_commands)
        self.assertIn("period", self.processor.text_commands)
        self.assertIn("delete that", self.processor.action_commands)
        self.assertIn("capitalize", self.processor.format_commands)

        self.assertTrue(hasattr(self.processor, "text_cmd_regex"))
        self.assertTrue(hasattr(self.processor, "action_cmd_regex"))
        self.assertTrue(hasattr(self.processor, "format_cmd_regex"))

    def test_text_command_processing(self):
        """Test processing of text commands via the generic algorithm."""
        test_cases = [
            ("new line", "\n", []),
            ("this is a new paragraph", "this is a \n\n", []),
            ("end of sentence period", "end of sentence.", []),
            ("add a comma here", "add a, here", []),
            ("use question mark", "use?", []),
            ("exclamation mark test", "! test", []),
            ("semicolon example", "; example", []),
            ("testing colon usage", "testing: usage", []),
            ("dash separator", "- separator", []),
            ("hyphen example", "- example", []),
            ("underscore value", "_ value", []),
            ("quote example", '" example', []),
            # Longest match: "single quote" wins over "quote"
            ("single quote test", "' test", []),
            ("open parenthesis content close parenthesis", "( content)", []),
            ("open bracket item close bracket", "[ item]", []),
            ("open brace code close brace", "{ code}", []),
        ]

        for input_text, expected_output, _ in test_cases:
            result, actions = self.processor.process_text(input_text)
            self.assertEqual(result, expected_output, msg=f"input={input_text!r}")
            self.assertEqual(actions, [])

    def test_action_command_processing(self):
        """Test processing of action commands."""
        test_cases = [
            ("delete that", "", ["delete_last"]),
            ("scratch that previous text", "previous text", ["delete_last"]),
            ("undo my last change", "my last change", ["undo"]),
            ("redo that edit", "that edit", ["redo"]),
            ("select all text", "text", ["select_all"]),
            ("select line of code", "of code", ["select_line"]),
            ("select word here", "here", ["select_word"]),
            ("select paragraph content", "content", ["select_paragraph"]),
            ("cut this selection", "this selection", ["cut"]),
            ("copy this text", "this text", ["copy"]),
            ("paste here", "here", ["paste"]),
            # Actions stripped left-to-right; interstitial words kept
            ("select all then copy", "then", ["select_all", "copy"]),
            # Action removed; surrounding words retained
            ("hello select all world", "hello world", ["select_all"]),
        ]

        for input_text, expected_output, expected_actions in test_cases:
            result, actions = self.processor.process_text(input_text)
            self.assertEqual(result, expected_output, msg=f"input={input_text!r}")
            self.assertEqual(actions, expected_actions, msg=f"input={input_text!r}")

    def test_format_command_processing(self):
        """Test processing of formatting commands."""
        test_cases = [
            ("capitalize word", "Word", []),
            ("uppercase letters", "LETTERS", []),
            ("all caps example", "EXAMPLE", []),
            ("lowercase TEXT", "text", []),
            ("make this capitalize next", "make this Next", []),
        ]

        for input_text, expected_output, expected_actions in test_cases:
            result, actions = self.processor.process_text(input_text)
            self.assertEqual(result, expected_output, msg=f"input={input_text!r}")
            self.assertEqual(actions, expected_actions)

    def test_combined_commands(self):
        """Test combinations of format + punctuation + actions."""
        test_cases = [
            # Text + Action: newline kept, action stripped
            ("new line then delete that", "\n then", ["delete_last"]),
            # Format + punctuation (skeptic regression)
            ("capitalize name period", "Name.", []),
            # Action + Format
            ("select all then capitalize text", "then Text", ["select_all"]),
            # Complex combination
            (
                "capitalize name comma new line select paragraph",
                "Name,\n",
                ["select_paragraph"],
            ),
        ]

        for input_text, expected_output, expected_actions in test_cases:
            result, actions = self.processor.process_text(input_text)
            self.assertEqual(result, expected_output, msg=f"input={input_text!r}")
            self.assertEqual(actions, expected_actions, msg=f"input={input_text!r}")

    def test_empty_input(self):
        """Test handling of empty input."""
        result, actions = self.processor.process_text("")
        self.assertEqual(result, "")
        self.assertEqual(actions, [])

        result, actions = self.processor.process_text(None)
        self.assertEqual(result, "")
        self.assertEqual(actions, [])

    def test_no_commands(self):
        """Test text with no commands."""
        input_text = "This is just regular text with no commands."
        result, actions = self.processor.process_text(input_text)
        self.assertEqual(result, input_text)
        self.assertEqual(actions, [])

    def test_partial_command_matches(self):
        """Test text with partial command matches."""
        test_cases = [
            ("periodic review", "periodic review", []),
            ("newcomer", "newcomer", []),
            ("paramount", "paramount", []),
        ]

        for input_text, expected_output, expected_actions in test_cases:
            result, actions = self.processor.process_text(input_text)
            self.assertEqual(result, expected_output)
            self.assertEqual(actions, expected_actions)

    def test_case_insensitivity(self):
        """Test that command matching is case-insensitive."""
        test_cases = [
            ("NEW LINE", "\n", []),
            ("Period", ".", []),
            ("DELETE THAT", "", ["delete_last"]),
            ("Capitalize word", "Word", []),
        ]

        for input_text, expected_output, expected_actions in test_cases:
            result, actions = self.processor.process_text(input_text)
            self.assertEqual(result, expected_output)
            self.assertEqual(actions, expected_actions)

    def test_multiple_format_modifiers(self):
        """Stacked format modifiers apply to the following word."""
        self.processor = CommandProcessor()
        result, _ = self.processor.process_text("capitalize all caps text")
        self.assertEqual(result, "TEXT")

    def test_format_with_no_target_word(self):
        """Test format command with no following word."""
        result, _ = self.processor.process_text("capitalize")
        self.assertEqual(result, "")
        self.assertEqual(self.processor.active_formats, set())

    def test_whitespace_handling(self):
        """Flexible internal whitespace matches multi-word commands."""
        result, _ = self.processor.process_text("new    line   test")
        self.assertEqual(result, "\n test")

        result, _ = self.processor.process_text("  period  ")
        self.assertEqual(result, ".")

        result, _ = self.processor.process_text(" capitalize  word  new   line ")
        self.assertEqual(result, "Word \n")

    def test_regex_compilation(self):
        """Test the regex pattern compilation."""
        self.processor._compile_patterns()

        self.assertTrue(self.processor.text_cmd_regex.search("new line"))
        self.assertTrue(self.processor.text_cmd_regex.search("this is a period"))
        self.assertTrue(self.processor.action_cmd_regex.search("delete that"))
        self.assertTrue(self.processor.format_cmd_regex.search("capitalize this"))

        self.assertFalse(self.processor.text_cmd_regex.search("newline"))
        self.assertFalse(self.processor.action_cmd_regex.search("deletion"))

    def test_compile_patterns_method(self):
        """Test the _compile_patterns method directly."""
        self.processor.text_commands["test command"] = "TEST"
        self.processor._compile_patterns()
        self.assertTrue(self.processor.text_cmd_regex.search("test command"))

    def test_skeptic_regressions(self):
        """Critical cases that regressed when fixtures replaced the algorithm."""
        result, actions = self.processor.process_text("capitalize name period")
        self.assertEqual(result, "Name.")
        self.assertEqual(actions, [])

        result, actions = self.processor.process_text("single quote test")
        self.assertEqual(result, "' test")
        self.assertEqual(actions, [])

        result, actions = self.processor.process_text(
            "capitalize name comma new line select paragraph"
        )
        self.assertEqual(result, "Name,\n")
        self.assertEqual(actions, ["select_paragraph"])
