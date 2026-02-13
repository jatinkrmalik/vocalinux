"""
Autostart manager for Vocalinux.

This module handles the creation and removal of the XDG autostart desktop entry
for automatically starting Vocalinux on login.
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

AUTOSTART_DIR = Path.home() / ".config" / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "vocalinux.desktop"


def get_executable_path() -> str:
    """Get the path to the current executable."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(sys.argv[0])


def is_autostart_enabled() -> bool:
    """Check if autostart is currently enabled."""
    return AUTOSTART_FILE.exists()


def enable_autostart() -> bool:
    """Enable autostart by creating the desktop entry file."""
    try:
        AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)

        executable_path = get_executable_path()
        logger.info(f"Creating autostart entry with executable: {executable_path}")

        desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Vocalinux
Exec={executable_path} --start-minimized
Icon=vocalinux
Comment=Voice dictation for Linux
X-GNOME-Autostart-enabled=true
"""

        with open(AUTOSTART_FILE, "w") as f:
            f.write(desktop_entry)

        logger.info(f"Autostart enabled: {AUTOSTART_FILE}")
        return True

    except Exception as e:
        logger.error(f"Failed to enable autostart: {e}")
        return False


def disable_autostart() -> bool:
    """Disable autostart by removing the desktop entry file."""
    try:
        if AUTOSTART_FILE.exists():
            AUTOSTART_FILE.unlink()
            logger.info(f"Autostart disabled: {AUTOSTART_FILE}")
        return True

    except Exception as e:
        logger.error(f"Failed to disable autostart: {e}")
        return False


def set_autostart(enabled: bool) -> bool:
    """Set autostart enabled or disabled."""
    if enabled:
        return enable_autostart()
    return disable_autostart()
