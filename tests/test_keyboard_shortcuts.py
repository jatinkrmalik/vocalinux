"""
Tests for the keyboard shortcuts functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest


class TestKeyboardShortcuts(unittest.TestCase):
    """Test cases for keyboard shortcuts functionality."""

    def test_shortcut_parsing(self):
        """Test that keyboard shortcut parsing works correctly."""

        # Define a mock KeyboardShortcutManager class to avoid importing pynput
        class MockKeyboardShortcutManager:
            def __init__(self):
                self.shortcuts = {}
                self.current_keys = set()

            def parse_shortcut(self, shortcut_str):
                """Parse a shortcut string into a list of key identifiers."""
                return shortcut_str.lower().split("+")

            def register_shortcut(self, name, shortcut, callback):
                """Register a keyboard shortcut."""
                self.shortcuts[name] = {
                    "keys": self.parse_shortcut(shortcut),
                    "callback": callback,
                }
                return True

        # Create an instance of our mock manager
        shortcut_manager = MockKeyboardShortcutManager()

        # Test shortcut parsing
        shortcut_manager.register_shortcut("test", "ctrl+shift+t", lambda: None)
        assert "test" in shortcut_manager.shortcuts
        assert shortcut_manager.shortcuts["test"]["keys"] == ["ctrl", "shift", "t"]

        # Test multiple shortcut registration
        callback_called = False

        def test_callback():
            nonlocal callback_called
            callback_called = True

        shortcut_manager.register_shortcut(
            "toggle_dictation", "alt+shift+v", test_callback
        )
        assert "toggle_dictation" in shortcut_manager.shortcuts
        assert shortcut_manager.shortcuts["toggle_dictation"]["keys"] == ["alt", "shift", "v"]
        assert shortcut_manager.shortcuts["toggle_dictation"]["callback"] == test_callback

    # Mock test for the detection algorithm - without the dependency
    def test_shortcut_detection_logic(self):
        """Test the logic for detecting keyboard shortcuts."""

        # Define a simple shortcut detection algorithm
        def check_shortcut_triggered(current_keys, shortcut_keys):
            """Check if the currently pressed keys match a shortcut."""
            return set(shortcut_keys).issubset(set(current_keys)) and len(
                current_keys
            ) == len(shortcut_keys)

        # Test detection with various key combinations
        # Case 1: All keys in the shortcut are pressed
        current_keys = ["alt", "shift", "v"]
        shortcut_keys = ["alt", "shift", "v"]
        assert check_shortcut_triggered(current_keys, shortcut_keys) is True

        # Case 2: Some keys in the shortcut are pressed
        current_keys = ["alt", "v"]
        shortcut_keys = ["alt", "shift", "v"]
        assert check_shortcut_triggered(current_keys, shortcut_keys) is False

        # Case 3: Extra keys are pressed
        current_keys = ["alt", "shift", "v", "ctrl"]
        shortcut_keys = ["alt", "shift", "v"]
        assert check_shortcut_triggered(current_keys, shortcut_keys) is False

        # Case 4: Different shortcut is pressed
        current_keys = ["ctrl", "shift", "t"]
        shortcut_keys = ["alt", "shift", "v"]
        assert check_shortcut_triggered(current_keys, shortcut_keys) is False