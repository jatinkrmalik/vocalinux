"""
Tests for the TextInjector component.
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.text_injection.text_injector import DesktopEnvironment, TextInjector


class TestTextInjector(unittest.TestCase):
    """Test cases for the text injector."""

    @patch("src.text_injection.text_injector.shutil.which")
    @patch("src.text_injection.text_injector.TextInjector._detect_environment")
    def test_init_x11(self, mock_detect, mock_which):
        """Test initialization in X11 environment."""
        mock_detect.return_value = DesktopEnvironment.X11
        mock_which.return_value = "/usr/bin/xdotool"  # Simulate xdotool exists

        injector = TextInjector()
        assert injector.environment == DesktopEnvironment.X11

    @patch("src.text_injection.text_injector.subprocess.run")
    @patch("src.text_injection.text_injector.shutil.which")
    @patch("src.text_injection.text_injector.TextInjector._detect_environment")
    def test_inject_text_x11(self, mock_detect, mock_which, mock_run):
        """Test text injection in X11 environment."""
        mock_detect.return_value = DesktopEnvironment.X11
        mock_which.return_value = "/usr/bin/xdotool"

        injector = TextInjector()
        injector.inject_text("Hello, world!")

        # The TextInjector makes two subprocess calls:
        # 1. To type the text
        # 2. To press Escape to exit insertion mode
        assert mock_run.call_count == 2
        first_call_args = mock_run.call_args_list[0][0][0]
        second_call_args = mock_run.call_args_list[1][0][0]

        # Verify first call types the text
        assert first_call_args[0] == "xdotool"
        assert first_call_args[2] == "--clearmodifiers"
        assert first_call_args[3] == "Hello, world!"

        # Verify second call presses Escape
        assert second_call_args[0] == "xdotool"
        assert second_call_args[2] == "--clearmodifiers"
        assert second_call_args[3] == "Escape"

    @patch("shutil.which")
    @patch("os.environ.get")
    def test_environment_detection_x11(self, mock_environ_get, mock_which):
        """Test environment detection for X11."""
        # Mock environment variables for X11
        mock_environ_get.return_value = "x11"
        mock_which.return_value = "/usr/bin/xdotool"

        # Create injector with mocked environment
        injector = TextInjector()

        # Check environment detection
        assert injector.environment == DesktopEnvironment.X11

    @patch("shutil.which")
    @patch("os.environ.get")
    def test_environment_detection_wayland(self, mock_environ_get, mock_which):
        """Test environment detection for Wayland."""
        # Mock environment variables for Wayland
        mock_environ_get.return_value = "wayland"
        mock_which.return_value = "/usr/bin/wtype"

        # Create injector with mocked environment
        injector = TextInjector()

        # Check environment detection
        assert injector.environment == DesktopEnvironment.WAYLAND
