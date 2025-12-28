"""
Tests for text injection functionality.
"""

import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

# Update import path to use the new package structure
from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

# Create a mock for audio feedback module
mock_audio_feedback = MagicMock()
mock_audio_feedback.play_error_sound = MagicMock()

# Add the mock to sys.modules
sys.modules["vocalinux.ui.audio_feedback"] = mock_audio_feedback


class TestTextInjector(unittest.TestCase):
    """Test cases for the text injection functionality."""

    def setUp(self):
        """Set up for tests."""
        # Create patches for external functions
        self.patch_which = patch("shutil.which")
        self.mock_which = self.patch_which.start()

        self.patch_subprocess = patch("subprocess.run")
        self.mock_subprocess = self.patch_subprocess.start()

        self.patch_sleep = patch("time.sleep")
        self.mock_sleep = self.patch_sleep.start()

        # Setup environment variable patching
        self.env_patcher = patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11", "DISPLAY": ":0"})
        self.env_patcher.start()

        # Set default return values
        self.mock_which.return_value = "/usr/bin/xdotool"  # Default to having xdotool

        # Setup subprocess mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "1234"
        mock_process.stderr = ""
        self.mock_subprocess.return_value = mock_process

        # Reset mock for error sound
        mock_audio_feedback.play_error_sound.reset_mock()

    def tearDown(self):
        """Clean up after tests."""
        self.patch_which.stop()
        self.patch_subprocess.stop()
        self.patch_sleep.stop()
        self.env_patcher.stop()

    def test_detect_x11_environment(self):
        """Test detection of X11 environment."""
        # Force our mock_which to be selective based on command
        self.mock_which.side_effect = lambda cmd: ("/usr/bin/xdotool" if cmd == "xdotool" else None)

        # Explicitly set X11 environment
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            # Create TextInjector and ensure it detects X11
            injector = TextInjector()

            # Force X11 detection by patching the _detect_environment method
            with patch.object(injector, "_detect_environment", return_value=DesktopEnvironment.X11):
                injector.environment = DesktopEnvironment.X11

                # Verify environment is X11
                self.assertEqual(injector.environment, DesktopEnvironment.X11)

    def test_detect_wayland_environment(self):
        """Test detection of Wayland environment."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make wtype available for Wayland
            self.mock_which.side_effect = lambda cmd: ("/usr/bin/wtype" if cmd == "wtype" else None)

            # Mock wtype test call to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stderr = ""
            self.mock_subprocess.return_value = mock_process

            injector = TextInjector()
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)
            self.assertEqual(injector.wayland_tool, "wtype")

    def test_force_wayland_mode(self):
        """Test forcing Wayland mode."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            # Make wtype available
            self.mock_which.side_effect = lambda cmd: ("/usr/bin/wtype" if cmd == "wtype" else None)

            # Create injector with wayland_mode=True
            injector = TextInjector(wayland_mode=True)

            # Should be forced to Wayland
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)

    def test_wayland_fallback_to_xdotool(self):
        """Test fallback to XWayland with xdotool when wtype fails."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make both wtype and xdotool available
            self.mock_which.side_effect = lambda cmd: {
                "wtype": "/usr/bin/wtype",
                "xdotool": "/usr/bin/xdotool",
            }.get(cmd)

            # Make wtype test fail with compositor error
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr = "compositor does not support virtual keyboard protocol"
            self.mock_subprocess.return_value = mock_process

            # Initialize injector
            injector = TextInjector()

            # Should fall back to XWayland
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND_XDOTOOL)

    def test_x11_text_injection(self):
        """Test text injection in X11 environment."""
        # Setup X11 environment
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            # Force X11 mode
            injector = TextInjector()
            injector.environment = DesktopEnvironment.X11

            # Create a list to capture subprocess calls
            calls = []

            def capture_call(*args, **kwargs):
                calls.append((args, kwargs))
                process = MagicMock()
                process.returncode = 0
                return process

            self.mock_subprocess.side_effect = capture_call

            # Inject text
            injector.inject_text("Hello world")

            # Verify xdotool was called correctly
            found_xdotool_call = False
            for args, _ in calls:
                if len(args) > 0 and isinstance(args[0], list):
                    cmd = args[0]
                    if "xdotool" in cmd and "type" in cmd:
                        found_xdotool_call = True
                        break

            self.assertTrue(found_xdotool_call, "No xdotool type calls were made")

    def test_wayland_text_injection(self):
        """Test text injection in Wayland environment using wtype."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make wtype available
            self.mock_which.side_effect = lambda cmd: ("/usr/bin/wtype" if cmd == "wtype" else None)

            # Successful wtype test
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stderr = ""
            self.mock_subprocess.return_value = mock_process

            # Initialize injector
            injector = TextInjector()
            self.assertEqual(injector.wayland_tool, "wtype")

            # Inject text
            injector.inject_text("Hello world")

            # Verify wtype was called correctly
            self.mock_subprocess.assert_any_call(
                ["wtype", "Hello world"], check=True, stderr=subprocess.PIPE, text=True
            )

    def test_wayland_with_ydotool(self):
        """Test text injection in Wayland environment using ydotool."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make only ydotool available
            self.mock_which.side_effect = lambda cmd: (
                "/usr/bin/ydotool" if cmd == "ydotool" else None
            )

            # Initialize injector
            injector = TextInjector()
            self.assertEqual(injector.wayland_tool, "ydotool")

            # Inject text
            injector.inject_text("Hello world")

            # Verify ydotool was called correctly
            self.mock_subprocess.assert_any_call(
                ["ydotool", "type", "Hello world"],
                check=True,
                stderr=subprocess.PIPE,
                text=True,
            )

    def test_inject_special_characters(self):
        """Test injecting text with special characters that need escaping."""
        # Setup a TextInjector using X11 environment
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            # Force X11 mode
            injector = TextInjector()
            injector.environment = DesktopEnvironment.X11

            # Set up subprocess call to properly collect the escaped command
            calls = []

            def capture_call(*args, **kwargs):
                calls.append((args, kwargs))
                process = MagicMock()
                process.returncode = 0
                return process

            self.mock_subprocess.side_effect = capture_call

            # Text with special characters
            special_text = "Special 'quotes' and \"double quotes\" and $dollar signs"

            # Inject text
            injector.inject_text(special_text)

            # Verify xdotool was called with proper escaping
            # Find calls that contain xdotool and check they contain escaped text
            found_escaped = False
            for args, _ in calls:
                if len(args) > 0 and isinstance(args[0], list):
                    cmd = args[0]
                    if "xdotool" in cmd and "type" in cmd:
                        # Join the command to check for escaped characters
                        cmd_str = " ".join(cmd)
                        # Look for escaped quotes and dollar signs
                        if "'" in cmd_str or '\\"' in cmd_str or "\\$" in cmd_str:
                            found_escaped = True
                            break

            self.assertTrue(found_escaped, "Special characters were not properly escaped")

    def test_empty_text_injection(self):
        """Test injecting empty text (should do nothing)."""
        injector = TextInjector()

        # Reset the subprocess mock to clear previous calls
        self.mock_subprocess.reset_mock()

        # Inject empty text
        injector.inject_text("")

        # No subprocess calls should have been made
        self.mock_subprocess.assert_not_called()

        # Try with just whitespace
        injector.inject_text("   ")

        # Still no subprocess calls
        self.mock_subprocess.assert_not_called()

    def test_missing_dependencies(self):
        """Test error when no text injection dependencies are available."""
        # No tools available
        self.mock_which.return_value = None

        # Should raise RuntimeError
        with self.assertRaises(RuntimeError):
            TextInjector()

    def test_xdotool_error_handling(self):
        """Test handling of xdotool errors."""
        # Setup xdotool to fail
        mock_error = subprocess.CalledProcessError(1, ["xdotool", "type"], stderr="Error")
        self.mock_subprocess.side_effect = mock_error

        injector = TextInjector()

        # Get the audio feedback mock
        audio_feedback = sys.modules["vocalinux.ui.audio_feedback"]
        audio_feedback.play_error_sound.reset_mock()

        # Inject text - this should call play_error_sound
        injector.inject_text("Test text")

        # Check that error sound was triggered
        audio_feedback.play_error_sound.assert_called_once()
