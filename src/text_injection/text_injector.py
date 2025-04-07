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
        if wayland_mode and self.environment != DesktopEnvironment.WAYLAND:
            logger.info("Forcing Wayland compatibility mode")
            self.environment = DesktopEnvironment.WAYLAND
        
        logger.info(f"Using text injection for {self.environment.value} environment")
        
        # Check for required tools
        self._check_dependencies()
    
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
            
            if not wtype_available and not ydotool_available:
                logger.error("Neither wtype nor ydotool found for Wayland support. "
                           "Please install one of them:\n"
                           "For wtype: sudo apt install wtype\n"
                           "For ydotool: sudo apt install ydotool")
                raise RuntimeError("Missing required dependencies for Wayland support")
            
            self.wayland_tool = "wtype" if wtype_available else "ydotool"
            logger.info(f"Using {self.wayland_tool} for Wayland text injection")
    
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
            if self.environment == DesktopEnvironment.X11:
                self._inject_with_xdotool(escaped_text)
            else:
                self._inject_with_wayland_tool(escaped_text)
        except Exception as e:
            logger.error(f"Failed to inject text: {e}")
    
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
        
        subprocess.run(cmd, check=True)
    
    def inject_special_key(self, key: str):
        """
        Inject a special key or key combination.
        
        Args:
            key: The key to inject (e.g., "Return", "BackSpace", etc.)
        """
        logger.debug(f"Injecting special key: {key}")
        
        try:
            if self.environment == DesktopEnvironment.X11:
                subprocess.run(["xdotool", "key", "--clearmodifiers", key], check=True)
            else:
                if self.wayland_tool == "wtype":
                    subprocess.run(["wtype", f"-k {key}"], check=True)
                else:  # ydotool
                    subprocess.run(["ydotool", "key", key], check=True)
        except Exception as e:
            logger.error(f"Failed to inject special key: {e}")