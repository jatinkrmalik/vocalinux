"""
Text injection module for Ubuntu Voice Typing.

This module is responsible for injecting recognized text into the active
application, supporting both X11 and Wayland environments.
"""

import logging
import os
import shutil
import subprocess
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
        cmd = ["xdotool", "type", "--clearmodifiers", text]
        subprocess.run(cmd, check=True)
        logger.info(f"Text injected using xdotool: '{text[:20]}...' ({len(text)} chars)")
    
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
        
        try:
            result = subprocess.run(cmd, check=True, stderr=subprocess.PIPE, text=True)
            logger.info(f"Text injected using {self.wayland_tool}: '{text[:20]}...' ({len(text)} chars)")
        except subprocess.CalledProcessError as e:
            if "compositor does not support" in e.stderr.lower():
                logger.warning("Wayland compositor does not support virtual keyboard protocol")
            raise
    
    def inject_special_key(self, key: str):
        """
        Inject a special key or key combination.
        
        Args:
            key: The key to inject (e.g., "Return", "BackSpace", etc.)
        """
        logger.debug(f"Injecting special key: {key}")
        
        try:
            if self.environment == DesktopEnvironment.X11 or self.environment == DesktopEnvironment.WAYLAND_XDOTOOL:
                subprocess.run(["xdotool", "key", "--clearmodifiers", key], check=True)
                logger.info(f"Special key {key} injected using xdotool")
            else:
                try:
                    if self.wayland_tool == "wtype":
                        subprocess.run(["wtype", f"-k {key}"], check=True, stderr=subprocess.PIPE, text=True)
                    else:  # ydotool
                        subprocess.run(["ydotool", "key", key], check=True)
                    logger.info(f"Special key {key} injected using {self.wayland_tool}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Wayland tool failed for special key: {e}. Falling back to xdotool")
                    if "compositor does not support" in str(e).lower() and shutil.which("xdotool"):
                        self.environment = DesktopEnvironment.WAYLAND_XDOTOOL
                        subprocess.run(["xdotool", "key", "--clearmodifiers", key], check=True)
                    else:
                        raise
        except Exception as e:
            logger.error(f"Failed to inject special key: {e}")
            from ..ui.audio_feedback import play_error_sound
            play_error_sound()  # Play error sound when key injection fails