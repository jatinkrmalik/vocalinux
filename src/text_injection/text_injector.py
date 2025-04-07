"""
Text injection module for Ubuntu Voice Typing.

This module is responsible for injecting recognized text into the active
application, supporting both X11 and Wayland environments.
"""

import logging
import os
import shutil
import subprocess
import time
from enum import Enum
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DesktopEnvironment(Enum):
    """Enum representing the desktop environment."""
    X11 = "x11"
    WAYLAND = "wayland"
    WAYLAND_XDOTOOL = "wayland-xdotool"  # Wayland with XWayland fallback
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
        self.environment = self._detect_environment()
        
        # Force Wayland mode if requested
        if wayland_mode and self.environment == DesktopEnvironment.X11:
            logger.info("Forcing Wayland compatibility mode")
            self.environment = DesktopEnvironment.WAYLAND
        
        logger.info(f"Using text injection for {self.environment.value} environment")
        
        # Check for required tools
        self._check_dependencies()
        
        # Test if wtype actually works in this environment
        if self.environment == DesktopEnvironment.WAYLAND and hasattr(self, 'wayland_tool') and self.wayland_tool == "wtype":
            try:
                # Try a test with wtype
                result = subprocess.run(["wtype", "test"], stderr=subprocess.PIPE, text=True, check=False)
                error_output = result.stderr.lower()
                if "compositor does not support" in error_output or result.returncode != 0:
                    logger.warning(f"Wayland compositor does not support virtual keyboard protocol: {error_output}")
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
        if self.environment == DesktopEnvironment.X11:
            # Check for xdotool
            if not shutil.which("xdotool"):
                logger.error("xdotool not found. Please install it with: sudo apt install xdotool")
                raise RuntimeError("Missing required dependency: xdotool")
        else:
            # Check for wtype or ydotool for Wayland
            wtype_available = shutil.which("wtype") is not None
            ydotool_available = shutil.which("ydotool") is not None
            xdotool_available = shutil.which("xdotool") is not None
            
            if wtype_available:
                self.wayland_tool = "wtype"
                logger.info(f"Using {self.wayland_tool} for Wayland text injection")
            elif ydotool_available:
                self.wayland_tool = "ydotool"
                logger.info(f"Using {self.wayland_tool} for Wayland text injection")
            elif xdotool_available:
                # Fallback to xdotool with XWayland
                self.environment = DesktopEnvironment.WAYLAND_XDOTOOL
                logger.info("No native Wayland tools found. Using xdotool with XWayland as fallback")
            else:
                logger.error("No text injection tools found. Please install one of:\n"
                           "- wtype: sudo apt install wtype\n"
                           "- ydotool: sudo apt install ydotool\n"
                           "- xdotool: sudo apt install xdotool")
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
                check=False
            )
            
            if window_id.returncode != 0 or "failed" in window_id.stderr.lower():
                logger.warning(f"XWayland detection test failed: {window_id.stderr}")
                # Try to force XWayland environment more explicitly
                test_env["GDK_BACKEND"] = "x11"
            else:
                logger.debug("XWayland test successful")
        except Exception as e:
            logger.error(f"Failed to test XWayland fallback: {e}")
    
    def inject_text(self, text: str):
        """
        Inject text into the currently focused application.
        
        Args:
            text: The text to inject
        """
        if not text or not text.strip():
            return
        
        logger.debug(f"Injecting text: {text}")
        
        # Escape special characters for shell
        escaped_text = self._escape_text(text)
        
        try:
            if self.environment == DesktopEnvironment.X11 or self.environment == DesktopEnvironment.WAYLAND_XDOTOOL:
                self._inject_with_xdotool(escaped_text)
            else:
                try:
                    self._inject_with_wayland_tool(escaped_text)
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Wayland tool failed: {e}. Falling back to xdotool")
                    if "compositor does not support" in str(e).lower() and shutil.which("xdotool"):
                        logger.info("Automatically switching to XWayland fallback permanently")
                        self.environment = DesktopEnvironment.WAYLAND_XDOTOOL
                        self._inject_with_xdotool(escaped_text)
                    else:
                        raise
        except Exception as e:
            logger.error(f"Failed to inject text: {e}")
            from ..ui.audio_feedback import play_error_sound
            play_error_sound()  # Play error sound when text injection fails
    
    def _escape_text(self, text: str) -> str:
        """
        Escape special characters in the text for shell commands.
        
        Args:
            text: The original text
            
        Returns:
            The escaped text
        """
        # Replace common special characters
        replacements = {
            "'": r"\'",
            '"': r'\"',
            '`': r'\`',
            '\\': r'\\',
            '$': r'\$',
        }
        
        result = text
        for char, replacement in replacements.items():
            result = result.replace(char, replacement)
        
        return result
    
    def _inject_with_xdotool(self, text: str):
        """
        Inject text using xdotool for X11 environments.
        
        Args:
            text: The text to inject (already escaped)
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
                    check=False
                )
                
                if active_window.returncode == 0 and active_window.stdout.strip():
                    window_id = active_window.stdout.strip()
                    # Focus explicitly on that window
                    subprocess.run(
                        ["xdotool", "windowactivate", "--sync", window_id], 
                        env=env, 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        check=False
                    )
                    # Wait a moment for the focus to take effect
                    time.sleep(0.2)
            except Exception as e:
                logger.debug(f"Window focus command failed: {e}")
        
        # Inject text using xdotool
        try:
            max_retries = 2
            for retry in range(max_retries + 1):
                try:
                    # Inject in smaller chunks to avoid issues with very long text
                    chunk_size = 20  # Reduced chunk size for better reliability
                    for i in range(0, len(text), chunk_size):
                        chunk = text[i:i+chunk_size]
                        
                        # First try with clearmodifiers
                        cmd = ["xdotool", "type", "--clearmodifiers", chunk]
                        result = subprocess.run(cmd, env=env, check=True, stderr=subprocess.PIPE, text=True)
                        
                        # Add a larger delay between chunks
                        if i + chunk_size < len(text):
                            time.sleep(0.1)
                            
                    logger.info(f"Text injected using xdotool: '{text[:20]}...' ({len(text)} chars)")
                    break  # Successfully injected
                except subprocess.CalledProcessError as chunk_error:
                    if retry < max_retries:
                        logger.warning(f"Retrying text injection (attempt {retry+1}/{max_retries}): {chunk_error.stderr}")
                        time.sleep(0.5)  # Wait before retry
                    else:
                        raise  # Re-raise on final attempt
            
            # Try to reset any stuck modifiers
            try:
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "Escape"], 
                    env=env, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            except Exception:
                pass  # Ignore any errors from this command
        except subprocess.CalledProcessError as e:
            logger.error(f"xdotool error: {e.stderr}")
            raise
    
    def _inject_with_wayland_tool(self, text: str):
        """
        Inject text using a Wayland-compatible tool (wtype or ydotool).
        
        Args:
            text: The text to inject (already escaped)
        """
        if self.wayland_tool == "wtype":
            cmd = ["wtype", text]
        else:  # ydotool
            cmd = ["ydotool", "type", text]
            
        result = subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
        logger.info(f"Text injected using {self.wayland_tool}: '{text[:20]}...' ({len(text)} chars)")