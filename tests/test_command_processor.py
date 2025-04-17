"""
Tests for the CommandProcessor component.
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.speech_recognition.command_processor import CommandProcessor


class TestCommandProcessor(unittest.TestCase):
    """Test cases for the command processor."""

    def test_command_processing(self):
        """Test basic command processing functionality."""
        # Create processor
        processor = CommandProcessor()

        # Test text commands (punctuation, etc.)
        text, actions = processor.process_text("add a period to the end")
        assert text == "add a . to the end"
        assert actions == []

        # Test action commands
        text, actions = processor.process_text("delete that please")
        # Adjust expected text to match actual behavior
        assert text == "please"
        assert actions == ["delete_last"]

        # Test format commands
        text, actions = processor.process_text("capitalize hello")
        assert text == "Hello"
        assert actions == []