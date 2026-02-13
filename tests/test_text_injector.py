"""
Tests for text injection functionality.
"""

import os
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

        # Disable IBus for these tests (testing fallback paths)
        self.patch_ibus_available = patch(
            "vocalinux.text_injection.text_injector.is_ibus_available", return_value=False
        )
        self.patch_ibus_available.start()

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
        self.patch_ibus_available.stop()
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

            # Verify xdotool was called with the original text (no escaping needed)
            # Find calls that contain xdotool and check they contain the original text
            found_unescaped = False
            found_escaped = False
            for args, _ in calls:
                if len(args) > 0 and isinstance(args[0], list):
                    cmd = args[0]
                    if "xdotool" in cmd and "type" in cmd:
                        # Join the command to check for characters
                        cmd_str = " ".join(cmd)
                        # Check for unescaped special characters
                        if "'" in cmd_str:
                            found_unescaped = True
                        if "\\'" in cmd_str or '\\"' in cmd_str or "\\$" in cmd_str:
                            # Found escaped characters - this is bad!
                            found_escaped = True
                            break

            # Should find unescaped characters and NOT find escaped ones
            self.assertTrue(
                found_unescaped,
                "Text was not passed correctly to xdotool",
            )
            self.assertFalse(
                found_escaped,
                "Text should not be shell-escaped when passed to xdotool",
            )

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

    def test_detect_environment_unknown(self):
        """Test environment detection when no indicators are present."""
        with patch.dict("os.environ", {}, clear=True):
            # Clear all environment variables
            with patch.object(TextInjector, "_check_dependencies"):
                injector = TextInjector.__new__(TextInjector)
                env = injector._detect_environment()
                # Should default to X11 when unknown
                self.assertEqual(env, DesktopEnvironment.X11)

    def test_detect_environment_wayland_display(self):
        """Test environment detection via WAYLAND_DISPLAY."""
        with patch.dict("os.environ", {"WAYLAND_DISPLAY": "wayland-0"}, clear=True):
            with patch.object(TextInjector, "_check_dependencies"):
                injector = TextInjector.__new__(TextInjector)
                env = injector._detect_environment()
                self.assertEqual(env, DesktopEnvironment.WAYLAND)

    def test_detect_environment_display_only(self):
        """Test environment detection via DISPLAY only."""
        with patch.dict("os.environ", {"DISPLAY": ":0"}, clear=True):
            with patch.object(TextInjector, "_check_dependencies"):
                injector = TextInjector.__new__(TextInjector)
                env = injector._detect_environment()
                self.assertEqual(env, DesktopEnvironment.X11)

    def test_inject_keyboard_shortcut_x11(self):
        """Test keyboard shortcut injection in X11."""
        injector = TextInjector()
        injector.environment = DesktopEnvironment.X11

        mock_process = MagicMock()
        mock_process.returncode = 0
        self.mock_subprocess.return_value = mock_process

        result = injector._inject_keyboard_shortcut("ctrl+z")
        self.assertTrue(result)

    def test_inject_keyboard_shortcut_wayland_xdotool(self):
        """Test keyboard shortcut injection with XWayland fallback."""
        injector = TextInjector()
        injector.environment = DesktopEnvironment.WAYLAND_XDOTOOL

        mock_process = MagicMock()
        mock_process.returncode = 0
        self.mock_subprocess.return_value = mock_process

        result = injector._inject_keyboard_shortcut("ctrl+c")
        self.assertTrue(result)

    def test_inject_keyboard_shortcut_wayland_wtype(self):
        """Test keyboard shortcut injection with wtype (not supported)."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            self.mock_which.side_effect = lambda cmd: ("/usr/bin/wtype" if cmd == "wtype" else None)

            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stderr = ""
            self.mock_subprocess.return_value = mock_process

            injector = TextInjector()
            injector.wayland_tool = "wtype"
            injector.environment = DesktopEnvironment.WAYLAND

            result = injector._inject_shortcut_with_wayland_tool("ctrl+z")
            self.assertFalse(result)  # wtype doesn't support shortcuts

    def test_inject_keyboard_shortcut_wayland_ydotool(self):
        """Test keyboard shortcut injection with ydotool."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            self.mock_which.side_effect = lambda cmd: (
                "/usr/bin/ydotool" if cmd == "ydotool" else None
            )

            injector = TextInjector()
            injector.wayland_tool = "ydotool"
            injector.environment = DesktopEnvironment.WAYLAND

            mock_process = MagicMock()
            mock_process.returncode = 0
            self.mock_subprocess.return_value = mock_process

            result = injector._inject_shortcut_with_wayland_tool("ctrl+z")
            self.assertTrue(result)

    def test_inject_keyboard_shortcut_failure(self):
        """Test keyboard shortcut injection failure handling."""
        injector = TextInjector()
        injector.environment = DesktopEnvironment.X11

        self.mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, ["xdotool", "key"], stderr="Error"
        )

        result = injector._inject_keyboard_shortcut("ctrl+z")
        self.assertFalse(result)

    def test_log_current_window_info_wayland(self):
        """Test window info logging for pure Wayland."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            self.mock_which.side_effect = lambda cmd: ("/usr/bin/wtype" if cmd == "wtype" else None)

            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stderr = ""
            self.mock_subprocess.return_value = mock_process

            injector = TextInjector()
            injector.environment = DesktopEnvironment.WAYLAND

            # Should not raise, just logs debug message
            injector._log_current_window_info()

    def test_inject_text_returns_true_on_success(self):
        """Test that inject_text returns True on success."""
        injector = TextInjector()

        mock_process = MagicMock()
        mock_process.returncode = 0
        self.mock_subprocess.return_value = mock_process

        result = injector.inject_text("Test")
        self.assertTrue(result)

    def test_inject_text_returns_false_on_failure(self):
        """Test that inject_text returns False on failure."""
        injector = TextInjector()

        self.mock_subprocess.side_effect = Exception("Injection failed")

        result = injector.inject_text("Test")
        self.assertFalse(result)

    def test_wayland_tool_fallback_on_injection_failure(self):
        """Test automatic fallback to xdotool when Wayland tool fails during injection."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make both wtype and xdotool available
            self.mock_which.side_effect = lambda cmd: {
                "wtype": "/usr/bin/wtype",
                "xdotool": "/usr/bin/xdotool",
            }.get(cmd)

            # First return success for wtype test, then fail for actual injection
            call_count = [0]

            def mock_subprocess_call(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] <= 1:  # wtype test call
                    mock = MagicMock()
                    mock.returncode = 0
                    mock.stderr = ""
                    return mock
                elif call_count[0] == 2:  # First injection attempt with wtype
                    err = subprocess.CalledProcessError(
                        1, ["wtype"], stderr="compositor does not support"
                    )
                    err.stderr = "compositor does not support"
                    raise err
                else:  # xdotool fallback calls
                    mock = MagicMock()
                    mock.returncode = 0
                    mock.stdout = "12345"
                    return mock

            self.mock_subprocess.side_effect = mock_subprocess_call

            injector = TextInjector()
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)

            # Try injection, should fallback to xdotool
            result = injector.inject_text("Test")

            # After failure, should have switched to WAYLAND_XDOTOOL
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND_XDOTOOL)


class TestDesktopEnvironmentEnum(unittest.TestCase):
    """Tests for DesktopEnvironment enum."""

    def test_enum_values(self):
        """Test that enum values are as expected."""
        self.assertEqual(DesktopEnvironment.X11.value, "x11")
        self.assertEqual(DesktopEnvironment.WAYLAND.value, "wayland")
        self.assertEqual(DesktopEnvironment.WAYLAND_XDOTOOL.value, "wayland-xdotool")
        self.assertEqual(DesktopEnvironment.WAYLAND_IBUS.value, "wayland-ibus")
        self.assertEqual(DesktopEnvironment.UNKNOWN.value, "unknown")


class TestTextInjectorEdgeCases(unittest.TestCase):
    """Tests for edge cases in TextInjector."""

    def setUp(self):
        """Set up for tests."""
        self.patch_which = patch("shutil.which")
        self.mock_which = self.patch_which.start()
        self.mock_which.return_value = "/usr/bin/xdotool"

        self.patch_subprocess = patch("subprocess.run")
        self.mock_subprocess = self.patch_subprocess.start()

        self.patch_sleep = patch("time.sleep")
        self.mock_sleep = self.patch_sleep.start()

        # Disable IBus for these tests (testing fallback paths)
        self.patch_ibus_available = patch(
            "vocalinux.text_injection.text_injector.is_ibus_available", return_value=False
        )
        self.patch_ibus_available.start()

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "1234"
        mock_process.stderr = ""
        self.mock_subprocess.return_value = mock_process

    def tearDown(self):
        """Clean up after tests."""
        self.patch_which.stop()
        self.patch_subprocess.stop()
        self.patch_sleep.stop()
        self.patch_ibus_available.stop()

    def test_wtype_test_exception(self):
        """Test wtype test handling exceptions gracefully."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):

            def which_side_effect(cmd):
                if cmd == "wtype":
                    return "/usr/bin/wtype"
                return None

            self.mock_which.side_effect = which_side_effect

            # Make the wtype test raise an exception
            self.mock_subprocess.side_effect = Exception("Test wtype error")

            # Should still create the injector (will log warning)
            injector = TextInjector()
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)

    def test_xwayland_fallback_test_exception(self):
        """Test XWayland fallback test handles exceptions."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make only xdotool available, not wtype
            def which_side_effect(cmd):
                if cmd == "xdotool":
                    return "/usr/bin/xdotool"
                return None

            self.mock_which.side_effect = which_side_effect

            # Make subprocess raise for xdotool test
            self.mock_subprocess.side_effect = Exception("xdotool test failed")

            # Should create injector and log error
            injector = TextInjector()

    def test_check_dependencies_no_xdotool(self):
        """Test _check_dependencies when xdotool is missing on X11."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            self.mock_which.return_value = None  # No tools available

            with self.assertRaises(RuntimeError):
                TextInjector()

    def test_wayland_no_tools_available(self):
        """Test Wayland when no tools are available."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            self.mock_which.return_value = None  # No tools available

            with self.assertRaises(RuntimeError):
                TextInjector()

    def test_detect_environment_unknown(self):
        """Test environment detection when session type is unknown and no display vars set."""
        # Use clear=True to start fresh, then only set XDG_SESSION_TYPE to empty
        # This ensures WAYLAND_DISPLAY and DISPLAY are not in os.environ
        clean_env = {"XDG_SESSION_TYPE": "", "PATH": os.environ.get("PATH", "")}
        with patch.dict("os.environ", clean_env, clear=True):
            injector = TextInjector.__new__(TextInjector)
            # Don't call __init__, just test _detect_environment
            result = injector._detect_environment()
            # Should default to X11 when unknown (no WAYLAND_DISPLAY or DISPLAY)
            self.assertEqual(result, DesktopEnvironment.X11)

    def test_detect_environment_wayland_display(self):
        """Test environment detection via WAYLAND_DISPLAY."""
        # Clear session type but set WAYLAND_DISPLAY
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "", "WAYLAND_DISPLAY": "wayland-0"}):
            injector = TextInjector.__new__(TextInjector)
            result = injector._detect_environment()
            self.assertEqual(result, DesktopEnvironment.WAYLAND)

    def test_detect_environment_display_only(self):
        """Test environment detection via DISPLAY only."""
        # Clear session type and WAYLAND_DISPLAY, set only DISPLAY
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "", "DISPLAY": ":0"}, clear=False):
            # Ensure WAYLAND_DISPLAY is not set
            env_copy = dict(os.environ)
            env_copy.pop("WAYLAND_DISPLAY", None)
            env_copy["XDG_SESSION_TYPE"] = ""
            env_copy["DISPLAY"] = ":0"

            with patch.dict("os.environ", env_copy, clear=True):
                injector = TextInjector.__new__(TextInjector)
                result = injector._detect_environment()
                self.assertEqual(result, DesktopEnvironment.X11)

    def test_wtype_compositor_not_supported(self):
        """Test wtype fallback when compositor doesn't support virtual keyboard."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make both wtype and xdotool available
            def which_side_effect(cmd):
                if cmd in ["wtype", "xdotool"]:
                    return f"/usr/bin/{cmd}"
                return None

            self.mock_which.side_effect = which_side_effect

            # Make wtype test return error about compositor
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr = "compositor does not support virtual keyboard protocol"
            self.mock_subprocess.return_value = mock_process

            injector = TextInjector()
            # Should have fallen back to WAYLAND_XDOTOOL
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND_XDOTOOL)

    def test_wtype_compositor_not_supported_no_fallback(self):
        """Test wtype error when no xdotool fallback available."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make only wtype available
            def which_side_effect(cmd):
                if cmd == "wtype":
                    return "/usr/bin/wtype"
                return None

            self.mock_which.side_effect = which_side_effect

            # Make wtype test return error
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr = "compositor does not support virtual keyboard"
            self.mock_subprocess.return_value = mock_process

            # Should log error but still create injector
            injector = TextInjector()
            # Should stay as WAYLAND since no fallback
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)

    def test_xwayland_fallback_test_exception_with_both_tools(self):
        """Test XWayland fallback when test raises exception with both tools."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make both tools available
            def which_side_effect(cmd):
                if cmd in ["wtype", "xdotool"]:
                    return f"/usr/bin/{cmd}"
                return None

            self.mock_which.side_effect = which_side_effect

            # Make wtype succeed
            mock_wtype = MagicMock()
            mock_wtype.returncode = 0
            mock_wtype.stderr = ""

            # Make xdotool test fail with exception
            def run_side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get("args", [])
                if isinstance(cmd, list) and "xdotool" in cmd:
                    if "getactivewindow" in cmd:
                        raise Exception("XWayland test failed")
                return mock_wtype

            self.mock_subprocess.side_effect = run_side_effect

            # Should still create injector
            injector = TextInjector()
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)

    def test_inject_text_import_error_for_audio(self):
        """Test text injection when audio_feedback import fails."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            self.mock_which.return_value = "/usr/bin/xdotool"

            injector = TextInjector()

            # Make xdotool fail to trigger error path
            self.mock_subprocess.side_effect = Exception("Test error")

            # Mock the audio import to fail
            with patch.dict("sys.modules", {"vocalinux.ui.audio_feedback": None}):
                result = injector.inject_text("test")
                self.assertFalse(result)

    def test_inject_with_xdotool_retry_timeout(self):
        """Test xdotool injection with timeout on retry."""
        import subprocess as real_subprocess

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            self.mock_which.return_value = "/usr/bin/xdotool"

            injector = TextInjector()

            # First call for getactivewindow, then timeouts on type
            call_count = [0]

            def run_side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get("args", [])
                call_count[0] += 1
                if isinstance(cmd, list):
                    if "getactivewindow" in cmd:
                        result = MagicMock()
                        result.returncode = 0
                        result.stdout = "12345"
                        result.stderr = ""
                        return result
                    if "type" in cmd:
                        raise real_subprocess.TimeoutExpired(cmd, 5)
                result = MagicMock()
                result.returncode = 0
                result.stderr = ""
                return result

            self.mock_subprocess.side_effect = run_side_effect

            # Should fail after retries
            with self.assertRaises(real_subprocess.TimeoutExpired):
                injector._inject_with_xdotool("test")

    def test_inject_with_xdotool_xwayland_no_display(self):
        """Test xdotool injection in XWayland mode without DISPLAY set."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}, clear=False):
            # Temporarily remove DISPLAY
            env_backup = os.environ.get("DISPLAY")
            if "DISPLAY" in os.environ:
                del os.environ["DISPLAY"]

            try:

                def which_side_effect(cmd):
                    if cmd in ["xdotool"]:
                        return f"/usr/bin/{cmd}"
                    return None

                self.mock_which.side_effect = which_side_effect

                # Create injector in WAYLAND_XDOTOOL mode
                injector = TextInjector.__new__(TextInjector)
                injector.environment = DesktopEnvironment.WAYLAND_XDOTOOL

                # Mock subprocess.run
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = "12345"
                mock_result.stderr = ""
                self.mock_subprocess.return_value = mock_result

                # Run injection - should set DISPLAY to :0
                injector._inject_with_xdotool("test")

                # Verify DISPLAY was set in the env passed to subprocess
                calls = self.mock_subprocess.call_args_list
                for call in calls:
                    if "env" in call.kwargs:
                        env = call.kwargs["env"]
                        if "type" in str(call):
                            self.assertEqual(env.get("DISPLAY"), ":0")
            finally:
                # Restore DISPLAY
                if env_backup is not None:
                    os.environ["DISPLAY"] = env_backup

    def test_inject_with_wayland_tool_ydotool(self):
        """Test text injection with ydotool."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make only ydotool available
            def which_side_effect(cmd):
                if cmd == "ydotool":
                    return "/usr/bin/ydotool"
                return None

            self.mock_which.side_effect = which_side_effect

            # Create injector
            injector = TextInjector()
            self.assertEqual(injector.wayland_tool, "ydotool")

            # Mock successful injection
            mock_result = MagicMock()
            mock_result.returncode = 0
            self.mock_subprocess.return_value = mock_result

            # Inject text
            injector._inject_with_wayland_tool("test text")

            # Verify ydotool was called correctly
            self.mock_subprocess.assert_called()
            call_args = self.mock_subprocess.call_args
            self.assertIn("ydotool", call_args[0][0])
            self.assertIn("type", call_args[0][0])

    def test_inject_keyboard_shortcut_x11(self):
        """Test keyboard shortcut injection on X11."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            self.mock_which.return_value = "/usr/bin/xdotool"

            injector = TextInjector()

            # Mock subprocess.run for xdotool key command
            mock_result = MagicMock()
            mock_result.returncode = 0
            self.mock_subprocess.return_value = mock_result

            result = injector._inject_keyboard_shortcut("ctrl+c")

            self.assertTrue(result)
            # Verify xdotool key was called
            self.mock_subprocess.assert_called()

    def test_inject_keyboard_shortcut_wayland(self):
        """Test keyboard shortcut injection on Wayland with wtype."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):

            def which_side_effect(cmd):
                if cmd == "wtype":
                    return "/usr/bin/wtype"
                return None

            self.mock_which.side_effect = which_side_effect

            # Make wtype test succeed
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            self.mock_subprocess.return_value = mock_result

            injector = TextInjector()

            result = injector._inject_keyboard_shortcut("ctrl+v")

            # Verify wtype -k was called
            self.mock_subprocess.assert_called()

    def test_inject_keyboard_shortcut_exception(self):
        """Test keyboard shortcut injection handles exceptions."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            self.mock_which.return_value = "/usr/bin/xdotool"

            injector = TextInjector()

            # Make subprocess.run raise an exception
            self.mock_subprocess.side_effect = Exception("Shortcut injection failed")

            result = injector._inject_keyboard_shortcut("ctrl+z")

            self.assertFalse(result)

    def test_inject_shortcut_xdotool_error(self):
        """Test keyboard shortcut injection with xdotool error."""
        import subprocess as real_subprocess

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            self.mock_which.return_value = "/usr/bin/xdotool"

            injector = TextInjector()

            # Make xdotool return error
            error = real_subprocess.CalledProcessError(1, "xdotool")
            error.stderr = "xdotool error message"
            self.mock_subprocess.side_effect = error

            result = injector._inject_shortcut_with_xdotool("ctrl+a")

            self.assertFalse(result)

    def test_inject_shortcut_with_ydotool(self):
        """Test keyboard shortcut injection with ydotool."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make only ydotool available
            def which_side_effect(cmd):
                if cmd == "ydotool":
                    return "/usr/bin/ydotool"
                return None

            self.mock_which.side_effect = which_side_effect

            injector = TextInjector()
            self.assertEqual(injector.wayland_tool, "ydotool")

            # Mock subprocess.run for successful shortcut
            mock_result = MagicMock()
            mock_result.returncode = 0
            self.mock_subprocess.return_value = mock_result

            result = injector._inject_shortcut_with_wayland_tool("ctrl+a")

            self.assertTrue(result)
            # Verify ydotool key was called
            self.mock_subprocess.assert_called()
            call_args = self.mock_subprocess.call_args
            self.assertIn("ydotool", call_args[0][0])
            self.assertIn("key", call_args[0][0])

    def test_inject_shortcut_with_ydotool_error(self):
        """Test keyboard shortcut injection with ydotool error."""
        import subprocess as real_subprocess

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make only ydotool available
            def which_side_effect(cmd):
                if cmd == "ydotool":
                    return "/usr/bin/ydotool"
                return None

            self.mock_which.side_effect = which_side_effect

            injector = TextInjector()

            # Make ydotool return error
            error = real_subprocess.CalledProcessError(1, "ydotool")
            error.stderr = "ydotool error message"
            self.mock_subprocess.side_effect = error

            result = injector._inject_shortcut_with_wayland_tool("ctrl+a")

            self.assertFalse(result)

    def test_inject_shortcut_wayland_unsupported_tool(self):
        """Test keyboard shortcut warning with unsupported wayland tool."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make wtype available
            def which_side_effect(cmd):
                if cmd == "wtype":
                    return "/usr/bin/wtype"
                return None

            self.mock_which.side_effect = which_side_effect

            # Succeed on wtype test
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            self.mock_subprocess.return_value = mock_result

            injector = TextInjector()

            # Force wayland_tool to something unsupported
            injector.wayland_tool = "unsupported_tool"

            result = injector._inject_shortcut_with_wayland_tool("ctrl+a")

            self.assertFalse(result)

    def test_log_current_window_info_exception(self):
        """Test _log_current_window_info handles exceptions gracefully."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            self.mock_which.return_value = "/usr/bin/xdotool"

            injector = TextInjector()

            # Make subprocess.run raise an exception
            self.mock_subprocess.side_effect = Exception("Window info error")

            # Should not raise - just log debug message
            injector._log_current_window_info()

    def test_log_current_window_info_wayland(self):
        """Test _log_current_window_info on pure Wayland."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):

            def which_side_effect(cmd):
                if cmd == "wtype":
                    return "/usr/bin/wtype"
                return None

            self.mock_which.side_effect = which_side_effect

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stderr = ""
            self.mock_subprocess.return_value = mock_result

            injector = TextInjector()

            # Should just log debug message for pure Wayland
            injector._log_current_window_info()

    def test_inject_shortcut_xdotool_wayland_no_display(self):
        """Test shortcut injection in WAYLAND_XDOTOOL mode without DISPLAY."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}, clear=False):
            # Remove DISPLAY for this test
            env_backup = os.environ.get("DISPLAY")
            if "DISPLAY" in os.environ:
                del os.environ["DISPLAY"]

            try:

                def which_side_effect(cmd):
                    if cmd in ["xdotool"]:
                        return f"/usr/bin/{cmd}"
                    return None

                self.mock_which.side_effect = which_side_effect

                # Create injector directly in WAYLAND_XDOTOOL mode
                injector = TextInjector.__new__(TextInjector)
                injector.environment = DesktopEnvironment.WAYLAND_XDOTOOL

                # Mock subprocess.run
                mock_result = MagicMock()
                mock_result.returncode = 0
                self.mock_subprocess.return_value = mock_result

                # Run shortcut injection - should set DISPLAY to :0
                result = injector._inject_shortcut_with_xdotool("ctrl+a")

                self.assertTrue(result)
                # Verify xdotool key was called with env containing DISPLAY
                self.mock_subprocess.assert_called()
                call_args = self.mock_subprocess.call_args
                if "env" in call_args.kwargs:
                    self.assertEqual(call_args.kwargs["env"].get("DISPLAY"), ":0")
            finally:
                # Restore DISPLAY
                if env_backup is not None:
                    os.environ["DISPLAY"] = env_backup

    def test_xwayland_fallback_test_successful(self):
        """Test XWayland fallback test when successful."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland", "DISPLAY": ":0"}):

            def which_side_effect(cmd):
                if cmd == "xdotool":
                    return "/usr/bin/xdotool"
                return None

            self.mock_which.side_effect = which_side_effect

            # Make getactivewindow succeed
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "12345"
            mock_result.stderr = ""
            self.mock_subprocess.return_value = mock_result

            # Create injector - should test XWayland fallback
            injector = TextInjector()

            # Verify it's in WAYLAND_XDOTOOL mode
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND_XDOTOOL)

    def test_xwayland_fallback_test_error_logging(self):
        """Test XWayland fallback logs error when _test_xdotool_fallback raises."""
        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland", "DISPLAY": ":0"}):

            def which_side_effect(cmd):
                if cmd == "xdotool":
                    return "/usr/bin/xdotool"
                return None

            self.mock_which.side_effect = which_side_effect

            # Mock subprocess to not raise during dependency check
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            mock_result.stderr = ""
            self.mock_subprocess.return_value = mock_result

            # Patch _test_xdotool_fallback at the class level before instantiation
            with patch.object(
                TextInjector, "_test_xdotool_fallback", side_effect=Exception("Test error")
            ):
                with patch("time.sleep"):  # Skip the sleep
                    # Should create injector and log error but not crash
                    injector = TextInjector()
                    self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND_XDOTOOL)
