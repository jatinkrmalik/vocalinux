"""
Text injection module for Vocalinux.

This module is responsible for injecting recognized text into the active
application, supporting both X11 and Wayland environments.
"""

import logging
import os
import shutil
import subprocess
import time
from enum import Enum
from typing import List, Optional, Tuple  # noqa: F401

from .ibus_engine import (
    IBusTextInjector,
    is_ibus_available,
    is_ibus_daemon_running,
)

logger = logging.getLogger(__name__)


def split_text_by_ascii(text: str) -> List[Tuple[str, bool]]:
    """
    Split text into segments of ASCII and non-ASCII characters.

    This is used to handle Unicode characters that can't be typed with
    the current keyboard layout. Non-ASCII characters need to be typed
    using Unicode input sequences (Ctrl+Shift+U + hex code).

    Args:
        text: The text to split

    Returns:
        A list of tuples (segment, is_ascii) where is_ascii indicates
        whether the segment contains only ASCII characters
    """
    if not text:
        return []

    segments: List[Tuple[str, bool]] = []
    current_segment = []
    current_is_ascii = ord(text[0]) < 128

    for char in text:
        char_is_ascii = ord(char) < 128

        if char_is_ascii == current_is_ascii:
            current_segment.append(char)
        else:
            # Save the current segment and start a new one
            segments.append((''.join(current_segment), current_is_ascii))
            current_segment = [char]
            current_is_ascii = char_is_ascii

    # Don't forget the last segment
    if current_segment:
        segments.append((''.join(current_segment), current_is_ascii))

    return segments


def get_unicode_hex(char: str) -> str:
    """
    Get the Unicode hex code for a character (without U+ prefix).

    Args:
        char: A single Unicode character

    Returns:
        The hex code in lowercase (e.g., '00e4' for 'ä')
    """
    return format(ord(char), '04x')


class DesktopEnvironment(Enum):
    """Enum representing the desktop environment."""

    X11 = "x11"
    X11_IBUS = "x11-ibus"  # X11 with IBus engine (preferred for non-US layouts)
    WAYLAND = "wayland"
    WAYLAND_XDOTOOL = "wayland-xdotool"  # Wayland with XWayland fallback
    WAYLAND_IBUS = "wayland-ibus"  # Wayland with IBus engine (preferred)
    UNKNOWN = "unknown"


class TextInjector:
    """
    Class for injecting text into the active application.

    This class handles the injection of text into the currently focused
    application window, supporting both X11 and Wayland environments.
    """

    def __init__(self, wayland_mode: bool = False):
        """
        Initialize the text injector.

        Args:
            wayland_mode: Force Wayland compatibility mode
        """
        self._ibus_injector: Optional[IBusTextInjector] = None
        self.environment = self._detect_environment()

        # Force Wayland mode if requested
        if wayland_mode and self.environment == DesktopEnvironment.X11:
            logger.info("Forcing Wayland compatibility mode")
            self.environment = DesktopEnvironment.WAYLAND

        logger.info(f"Using text injection for {self.environment.value} environment")

        # Check for required tools
        self._check_dependencies()

        # Test if wtype actually works in this environment
        if (
            self.environment == DesktopEnvironment.WAYLAND
            and hasattr(self, "wayland_tool")
            and self.wayland_tool == "wtype"
        ):
            try:
                # Try a test with wtype
                result = subprocess.run(
                    ["wtype", "test"], stderr=subprocess.PIPE, text=True, check=False
                )
                error_output = result.stderr.lower()
                if "compositor does not support" in error_output or result.returncode != 0:
                    logger.warning(
                        "Wayland compositor does not support virtual "
                        f"keyboard protocol: {error_output}"
                    )
                    if shutil.which("xdotool"):
                        logger.info("Automatically switching to XWayland fallback with xdotool")
                        self.environment = DesktopEnvironment.WAYLAND_XDOTOOL
                    else:
                        logger.error("No fallback text injection method available")
            except Exception as e:
                logger.warning(f"Error testing wtype: {e}, will try to use it anyway")

        # Verify XWayland fallback works - perform a test injection
        if self.environment == DesktopEnvironment.WAYLAND_XDOTOOL:
            logger.info("Testing XWayland text injection fallback")
            try:
                # Wait a moment to ensure any error messages are displayed before test
                time.sleep(0.5)
                # Try xdotool in more verbose mode for better diagnostics
                self._test_xdotool_fallback()
            except Exception as e:
                logger.error(f"XWayland fallback test failed: {e}")

    def stop(self) -> None:
        """
        Clean up resources and restore previous state.

        Call this when shutting down Vocalinux.
        """
        if self._ibus_injector:
            logger.info("Stopping IBus text injector")
            self._ibus_injector.stop()
            self._ibus_injector = None

    def _detect_environment(self) -> DesktopEnvironment:
        """
        Detect the current desktop environment (X11 or Wayland).

        Returns:
            The detected desktop environment
        """
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type == "wayland":
            return DesktopEnvironment.WAYLAND
        elif session_type == "x11":
            return DesktopEnvironment.X11
        else:
            # Try to detect based on other methods
            if "WAYLAND_DISPLAY" in os.environ:
                return DesktopEnvironment.WAYLAND
            elif "DISPLAY" in os.environ:
                return DesktopEnvironment.X11
            else:
                logger.warning("Could not detect desktop environment, defaulting to X11")
                return DesktopEnvironment.X11

    def _check_dependencies(self):
        """Check for the required tools for text injection."""
        # Prefer IBus on both X11 and Wayland - it sends Unicode directly,
        # bypassing keyboard layout issues entirely
        if is_ibus_available():
            # Check if ibus-daemon is running before attempting setup
            if not is_ibus_daemon_running():
                logger.info(
                    "IBus daemon not running. This is normal on some desktop environments "
                    "(e.g., KDE Plasma). Using alternative text injection method. "
                    "For IBus setup, see: https://github.com/jatinkrmalik/vocalinux/wiki/IBus-Setup"
                )
            else:
                try:
                    self._ibus_injector = IBusTextInjector(auto_activate=True)
                    if self.environment == DesktopEnvironment.X11:
                        self.environment = DesktopEnvironment.X11_IBUS
                    else:
                        self.environment = DesktopEnvironment.WAYLAND_IBUS
                    logger.info(
                        f"Using IBus for {self.environment.value} text injection (best compatibility)"
                    )
                    return
                except Exception as e:
                    logger.warning(f"IBus initialization failed: {e}, trying alternatives")

        if self.environment == DesktopEnvironment.X11:
            # Check for xdotool
            if not shutil.which("xdotool"):
                logger.error("xdotool not found. Please install it with: sudo apt install xdotool")
                raise RuntimeError("Missing required dependency: xdotool")
        else:
            # Fallback: Check for wtype or ydotool for Wayland
            wtype_available = shutil.which("wtype") is not None
            ydotool_available = shutil.which("ydotool") is not None
            xdotool_available = shutil.which("xdotool") is not None

            if ydotool_available:
                # Verify ydotoold daemon is running before selecting ydotool
                try:
                    subprocess.run(
                        ["ydotool", "type", ""],
                        check=True,
                        stderr=subprocess.PIPE,
                        timeout=2,
                    )
                    self.wayland_tool = "ydotool"
                    logger.info(f"Using {self.wayland_tool} for Wayland text injection")
                except (
                    subprocess.CalledProcessError,
                    subprocess.TimeoutExpired,
                    FileNotFoundError,
                ):
                    if wtype_available:
                        self.wayland_tool = "wtype"
                        logger.info(
                            f"Using {self.wayland_tool} for Wayland text injection (ydotoold not running)"
                        )
                    else:
                        logger.warning("ydotool found but ydotoold daemon not running")
            elif wtype_available:
                self.wayland_tool = "wtype"
                logger.info(f"Using {self.wayland_tool} for Wayland text injection")
            elif xdotool_available:
                # Fallback to xdotool with XWayland
                self.environment = DesktopEnvironment.WAYLAND_XDOTOOL
                logger.info(
                    "No native Wayland tools found. Using xdotool with XWayland as fallback"
                )
            else:
                logger.error(
                    "No text injection tools found. Please install one of:\n"
                    "- IBus (recommended, usually pre-installed)\n"
                    "- wtype: sudo apt install wtype\n"
                    "- ydotool: sudo apt install ydotool\n"
                    "- xdotool: sudo apt install xdotool"
                )
                raise RuntimeError("Missing required dependencies for text injection")

    def _test_xdotool_fallback(self):
        """Test if xdotool is working correctly with XWayland."""
        try:
            # Get the DISPLAY environment variable for XWayland
            xwayland_display = os.environ.get("DISPLAY", ":0")
            logger.debug(f"Using DISPLAY={xwayland_display} for XWayland")

            # Try using xdotool with explicit DISPLAY setting
            test_env = os.environ.copy()
            test_env["DISPLAY"] = xwayland_display

            # Check if we can get active window (less intrusive test)
            window_id = subprocess.run(
                ["xdotool", "getwindowfocus"],
                env=test_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            if window_id.returncode != 0 or "failed" in window_id.stderr.lower():
                logger.warning(f"XWayland detection test failed: {window_id.stderr}")
                # Try to force XWayland environment more explicitly
                test_env["GDK_BACKEND"] = "x11"
            else:
                logger.debug("XWayland test successful")
        except Exception as e:
            logger.error(f"Failed to test XWayland fallback: {e}")

    def inject_text(self, text: str) -> bool:
        """
        Inject text into the currently focused application.

        Args:
            text: The text to inject

        Returns:
            True if injection was successful, False otherwise
        """
        if not text or not text.strip():
            logger.debug("Empty text provided, skipping injection")
            return True

        logger.info(f"Starting text injection: '{text}' (length: {len(text)})")
        logger.debug(f"Environment: {self.environment}")

        # Get information about the current window/application
        self._log_current_window_info()

        # Note: No shell escaping needed - subprocess is called with list arguments,
        # which passes text directly without shell interpretation
        logger.debug(f"Text to inject: '{text}'")

        try:
            if (
                self.environment == DesktopEnvironment.WAYLAND_IBUS
                or self.environment == DesktopEnvironment.X11_IBUS
            ):
                if self._ibus_injector is not None:
                    return self._ibus_injector.inject_text(text)
                else:
                    logger.error("IBus injector not initialized")
                    return False
            elif (
                self.environment == DesktopEnvironment.X11
                or self.environment == DesktopEnvironment.WAYLAND_XDOTOOL
            ):
                self._inject_with_xdotool(text)
            else:
                try:
                    self._inject_with_wayland_tool(text)
                except subprocess.CalledProcessError as e:
                    stderr_msg = e.stderr.strip() if e.stderr else "No stderr output"
                    logger.warning(
                        f"Wayland tool failed: {e}. stderr: {stderr_msg}. Falling back to xdotool"
                    )
                    if "compositor does not support" in str(
                        e
                    ).lower() + " " + stderr_msg.lower() and shutil.which("xdotool"):
                        logger.info("Automatically switching to XWayland fallback permanently")
                        self.environment = DesktopEnvironment.WAYLAND_XDOTOOL
                        self._inject_with_xdotool(text)
                    else:
                        raise
            logger.info("Text injection completed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to inject text: {e}", exc_info=True)
            try:
                from ..ui.audio_feedback import play_error_sound

                play_error_sound()  # Play error sound when text injection fails
            except ImportError:
                logger.warning("Could not import audio feedback module")
            return False

    def _inject_with_xdotool(self, text: str):
        """
        Inject text using xdotool for X11 environments.

        This method handles both ASCII and Unicode characters. For Unicode
        characters (like German umlauts), it uses the Ctrl+Shift+U Unicode
        input sequence to type characters not available on the current
        keyboard layout.

        Args:
            text: The text to inject
        """
        # Create environment with explicit X11 settings for Wayland compatibility
        env = os.environ.copy()

        if self.environment == DesktopEnvironment.WAYLAND_XDOTOOL:
            # Force X11 backend for XWayland
            env["GDK_BACKEND"] = "x11"
            env["QT_QPA_PLATFORM"] = "xcb"
            # Ensure DISPLAY is set correctly for XWayland
            if "DISPLAY" not in env or not env["DISPLAY"]:
                env["DISPLAY"] = ":0"

            logger.debug(f"Using XWayland with DISPLAY={env['DISPLAY']}")

            # Add a small delay to ensure text is injected properly
            time.sleep(0.3)  # Increased delay for better reliability

            # Try to ensure the window has focus using more robust approach
            try:
                # Get current active window
                active_window = subprocess.run(
                    ["xdotool", "getactivewindow"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                )

                if active_window.returncode == 0 and active_window.stdout.strip():
                    window_id = active_window.stdout.strip()
                    # Focus explicitly on that window
                    subprocess.run(
                        ["xdotool", "windowactivate", "--sync", window_id],
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                    # Wait a moment for the focus to take effect
                    time.sleep(0.2)
            except Exception as e:
                logger.debug(f"Window focus command failed: {e}")

        # Inject text using xdotool
        try:
            max_retries = 2
            logger.debug(f"Starting xdotool injection with {max_retries} max retries")

            for retry in range(max_retries + 1):
                try:
                    # Split text into ASCII and non-ASCII segments for proper Unicode handling
                    segments = split_text_by_ascii(text)
                    logger.debug(f"Text split into {len(segments)} segments")

                    for segment_idx, (segment, is_ascii) in enumerate(segments):
                        if is_ascii:
                            # ASCII text can be typed directly
                            self._inject_ascii_with_xdotool(segment, env, segment_idx, len(segments))
                        else:
                            # Non-ASCII text needs Unicode input sequence
                            self._inject_unicode_with_xdotool(segment, env, segment_idx, len(segments))

                    logger.info(
                        f"Text injected using xdotool: '{text[:20]}...' ({len(text)} chars)"
                    )
                    break  # Successfully injected
                except subprocess.CalledProcessError as chunk_error:
                    if retry < max_retries:
                        logger.warning(
                            f"Retrying text injection (attempt {retry + 1}/{max_retries}): "
                            f"{chunk_error.stderr}"
                        )
                        time.sleep(0.5)  # Wait before retry
                    else:
                        logger.error(f"Final attempt failed: {chunk_error.stderr}")
                        raise  # Re-raise on final attempt
                except subprocess.TimeoutExpired:
                    if retry < max_retries:
                        logger.warning(
                            f"Text injection timeout, retrying (attempt {retry + 1}/{max_retries})"
                        )
                        time.sleep(0.5)
                    else:
                        logger.error("Text injection timed out on final attempt")
                        raise

            # Try to reset any stuck modifiers
            try:
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "Escape"],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except Exception:
                pass  # Ignore any errors from this command
        except subprocess.CalledProcessError as e:
            logger.error(f"xdotool error: {e.stderr}")
            raise

    def _inject_ascii_with_xdotool(self, text: str, env: dict, segment_idx: int, total_segments: int):
        """
        Inject ASCII text using xdotool type command.

        Args:
            text: ASCII text to inject
            env: Environment variables for subprocess
            segment_idx: Current segment index (for logging)
            total_segments: Total number of segments (for logging)
        """
        # Inject in smaller chunks to avoid issues with very long text
        chunk_size = 20  # Reduced chunk size for better reliability
        total_chunks = (len(text) + chunk_size - 1) // chunk_size
        logger.debug(
            f"Injecting ASCII segment {segment_idx + 1}/{total_segments} "
            f"in {total_chunks} chunks"
        )

        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            chunk_num = (i // chunk_size) + 1

            cmd = ["xdotool", "type", "--clearmodifiers", chunk]
            logger.debug(f"Injecting ASCII chunk {chunk_num}/{total_chunks}: '{chunk}'")

            subprocess.run(
                cmd,
                env=env,
                check=True,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
            )

            # Add a small delay between chunks
            if i + chunk_size < len(text):
                time.sleep(0.05)

    def _inject_unicode_with_xdotool(self, text: str, env: dict, segment_idx: int, total_segments: int):
        """
        Inject Unicode text using xdotool with Ctrl+Shift+U Unicode input sequence.

        This method types Unicode characters by using the Linux Unicode input
        sequence: Ctrl+Shift+U followed by the hex code, then Space.

        Args:
            text: Unicode text to inject (non-ASCII characters)
            env: Environment variables for subprocess
            segment_idx: Current segment index (for logging)
            total_segments: Total number of segments (for logging)
        """
        logger.debug(
            f"Injecting Unicode segment {segment_idx + 1}/{total_segments}: "
            f"{len(text)} characters"
        )

        for char in text:
            hex_code = get_unicode_hex(char)
            logger.debug(f"Typing Unicode char '{char}' as U+{hex_code}")

            # Use xdotool to type the Unicode sequence:
            # 1. Press and hold Ctrl+Shift
            # 2. Press and release U
            # 3. Release Ctrl+Shift
            # 4. Type the hex code
            # 5. Press Space to commit the character
            try:
                # Type the Unicode sequence using keydown/keyup for modifiers
                # Ctrl+Shift+U, then hex code, then space
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers",
                     "Ctrl+Shift+u", "space"],  # Some systems need space after U
                    env=env,
                    check=True,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=2,
                )

                # Small delay to ensure the Unicode input mode is ready
                time.sleep(0.02)

                # Type the hex code
                subprocess.run(
                    ["xdotool", "type", "--clearmodifiers", hex_code],
                    env=env,
                    check=True,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=2,
                )

                # Press space to commit the character
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "space"],
                    env=env,
                    check=True,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=2,
                )

                # Small delay between characters for reliability
                time.sleep(0.02)

            except subprocess.CalledProcessError as e:
                logger.warning(f"Failed to type Unicode char '{char}': {e.stderr}")
                raise

    def _inject_with_wayland_tool(self, text: str):
        """
        Inject text using a Wayland-compatible tool (wtype or ydotool).

        For wtype: Unicode is supported natively - text is passed directly.
        For ydotool: Non-ASCII characters require Unicode input sequences
        (Ctrl+Shift+U + hex code) since ydotool simulates keypresses based
        on the current keyboard layout.

        Args:
            text: The text to inject

        Raises:
            subprocess.CalledProcessError: If the tool fails, with stderr captured
        """
        if self.wayland_tool == "wtype":
            # wtype supports Unicode natively - just pass the text
            cmd = ["wtype", text]
            try:
                subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
            except subprocess.CalledProcessError as e:
                raise subprocess.CalledProcessError(
                    e.returncode, e.cmd, output=e.output, stderr=e.stderr
                ) from e

            logger.info(
                f"Text injected using wtype: '{text[:20]}...' ({len(text)} chars)"
            )
        else:  # ydotool
            # ydotool needs special handling for Unicode characters
            self._inject_with_ydotool(text)

    def _inject_with_ydotool(self, text: str):
        """
        Inject text using ydotool with proper Unicode handling.

        For ASCII characters, uses ydotool type directly.
        For non-ASCII characters (like German umlauts), uses Unicode input
        sequence: Ctrl+Shift+U + hex code + Space.

        Args:
            text: The text to inject

        Raises:
            subprocess.CalledProcessError: If the tool fails
        """
        # Split text into ASCII and non-ASCII segments
        segments = split_text_by_ascii(text)
        logger.debug(f"ydotool: Text split into {len(segments)} segments")

        for segment_idx, (segment, is_ascii) in enumerate(segments):
            if is_ascii:
                # ASCII text can be typed directly with ydotool
                cmd = ["ydotool", "type", segment]
                logger.debug(f"ydotool typing ASCII segment {segment_idx + 1}: '{segment}'")
                try:
                    subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
                except subprocess.CalledProcessError as e:
                    raise subprocess.CalledProcessError(
                        e.returncode, e.cmd, output=e.output, stderr=e.stderr
                    ) from e
            else:
                # Non-ASCII text needs Unicode input sequence
                logger.debug(
                    f"ydotool typing Unicode segment {segment_idx + 1}: "
                    f"{len(segment)} characters"
                )
                for char in segment:
                    self._inject_unicode_with_ydotool(char)

        logger.info(
            f"Text injected using ydotool: '{text[:20]}...' ({len(text)} chars)"
        )

    def _inject_unicode_with_ydotool(self, char: str):
        """
        Inject a single Unicode character using ydotool with Unicode input sequence.

        Uses the Linux Unicode input sequence: Ctrl+Shift+U + hex code + Space.

        Args:
            char: A single Unicode character to inject

        Raises:
            subprocess.CalledProcessError: If the tool fails
        """
        hex_code = get_unicode_hex(char)
        logger.debug(f"ydotool typing Unicode char '{char}' as U+{hex_code}")

        try:
            # Press Ctrl+Shift+U to initiate Unicode input
            # ydotool uses key codes: 29=Ctrl, 42=Shift, 22=U
            # Format: key_code:1 (press), key_code:0 (release)
            subprocess.run(
                ["ydotool", "key", "29:1", "42:1", "22:1", "22:0", "42:0", "29:0"],
                check=True,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
            )

            # Small delay to ensure Unicode input mode is ready
            time.sleep(0.02)

            # Type the hex code
            subprocess.run(
                ["ydotool", "type", hex_code],
                check=True,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
            )

            # Press Space to commit the character
            # Space key code is 57
            subprocess.run(
                ["ydotool", "key", "57:1", "57:0"],
                check=True,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
            )

            # Small delay between characters for reliability
            time.sleep(0.02)

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to type Unicode char '{char}' with ydotool: {e.stderr}")
            raise

    def _inject_keyboard_shortcut(self, shortcut: str) -> bool:
        """
        Inject a keyboard shortcut.

        Args:
            shortcut: The keyboard shortcut to inject (e.g., "ctrl+z", "ctrl+a")

        Returns:
            True if injection was successful, False otherwise
        """
        logger.debug(f"Injecting keyboard shortcut: {shortcut}")

        try:
            if (
                self.environment == DesktopEnvironment.X11
                or self.environment == DesktopEnvironment.WAYLAND_XDOTOOL
            ):
                return self._inject_shortcut_with_xdotool(shortcut)
            else:
                return self._inject_shortcut_with_wayland_tool(shortcut)
        except Exception as e:
            logger.error(f"Failed to inject keyboard shortcut '{shortcut}': {e}")
            return False

    def _inject_shortcut_with_xdotool(self, shortcut: str) -> bool:
        """
        Inject a keyboard shortcut using xdotool.

        Args:
            shortcut: The keyboard shortcut to inject

        Returns:
            True if successful, False otherwise
        """
        # Create environment with explicit X11 settings for Wayland compatibility
        env = os.environ.copy()

        if self.environment == DesktopEnvironment.WAYLAND_XDOTOOL:
            env["GDK_BACKEND"] = "x11"
            env["QT_QPA_PLATFORM"] = "xcb"
            if "DISPLAY" not in env or not env["DISPLAY"]:
                env["DISPLAY"] = ":0"

        try:
            cmd = ["xdotool", "key", "--clearmodifiers", shortcut]
            subprocess.run(cmd, env=env, check=True, stderr=subprocess.PIPE, text=True)
            logger.debug(f"Keyboard shortcut '{shortcut}' injected successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"xdotool shortcut error: {e.stderr}")
            return False

    def _inject_shortcut_with_wayland_tool(self, shortcut: str) -> bool:
        """
        Inject a keyboard shortcut using a Wayland-compatible tool.

        Args:
            shortcut: The keyboard shortcut to inject

        Returns:
            True if successful, False otherwise
        """
        if self.wayland_tool == "wtype":
            # wtype doesn't support key combinations directly, so we can't implement this easily
            logger.warning("Keyboard shortcuts not supported with wtype")
            return False
        elif self.wayland_tool == "ydotool":
            try:
                cmd = ["ydotool", "key", shortcut]
                subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
                logger.debug(f"Keyboard shortcut '{shortcut}' injected successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"ydotool shortcut error: {e.stderr}")
                return False
        else:
            logger.warning(f"Keyboard shortcuts not supported with {self.wayland_tool}")
            return False

    def _log_current_window_info(self):
        """Log information about the current window/application for debugging."""
        try:
            if (
                self.environment == DesktopEnvironment.X11
                or self.environment == DesktopEnvironment.WAYLAND_XDOTOOL
            ):
                self._log_x11_window_info()
            else:
                logger.debug("Window info logging not available for pure Wayland")
        except Exception as e:
            logger.debug(f"Could not get window info: {e}")

    def _log_x11_window_info(self):
        """Log X11 window information."""
        env = os.environ.copy()

        if self.environment == DesktopEnvironment.WAYLAND_XDOTOOL:
            env["GDK_BACKEND"] = "x11"
            env["QT_QPA_PLATFORM"] = "xcb"
            if "DISPLAY" not in env or not env["DISPLAY"]:
                env["DISPLAY"] = ":0"

        try:
            # Get active window ID
            result = subprocess.run(
                ["xdotool", "getactivewindow"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=2,
            )
            window_id = result.stdout.strip()
            logger.debug(f"Active window ID: {window_id}")

            # Get window name
            result = subprocess.run(
                ["xdotool", "getwindowname", window_id],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=2,
            )
            window_name = result.stdout.strip()
            logger.info(f"Target window: '{window_name}' (ID: {window_id})")

            # Get window class
            result = subprocess.run(
                ["xdotool", "getwindowclassname", window_id],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=2,
            )
            window_class = result.stdout.strip()
            logger.debug(f"Window class: {window_class}")

            # Get window PID
            result = subprocess.run(
                ["xdotool", "getwindowpid", window_id],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=2,
            )
            window_pid = result.stdout.strip()
            logger.debug(f"Window PID: {window_pid}")

            # Try to get process name
            try:
                with open(f"/proc/{window_pid}/comm", "r") as f:
                    process_name = f.read().strip()
                logger.info(f"Target process: {process_name} (PID: {window_pid})")
            except Exception:
                pass

        except subprocess.TimeoutExpired:
            logger.warning("Timeout getting window information")
        except subprocess.CalledProcessError as e:
            logger.debug(f"xdotool command failed: {e.stderr}")
        except Exception as e:
            logger.debug(f"Error getting window info: {e}")
