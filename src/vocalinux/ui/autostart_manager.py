"""
Autostart manager for Vocalinux.

This module handles the creation and removal of the XDG autostart desktop entry
for automatically starting Vocalinux on login.
"""

import logging
import os
import shlex
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

DESKTOP_FILENAME = "vocalinux.desktop"


def get_autostart_dir() -> Path:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home).expanduser() / "autostart"
    return Path.home() / ".config" / "autostart"


def get_autostart_file() -> Path:
    return get_autostart_dir() / DESKTOP_FILENAME


def get_exec_command() -> str:
    installed_command = shutil.which("vocalinux")
    if installed_command:
        return f"{shlex.quote(installed_command)} --start-minimized"

    if getattr(sys, "frozen", False):
        return f"{shlex.quote(sys.executable)} --start-minimized"

    return f"{shlex.quote(sys.executable)} -m vocalinux.main --start-minimized"


def is_autostart_enabled() -> bool:
    """Check if autostart is currently enabled."""
    return get_autostart_file().exists()


def enable_autostart() -> bool:
    """Enable autostart by creating the desktop entry file."""
    try:
        autostart_dir = get_autostart_dir()
        autostart_file = get_autostart_file()
        autostart_dir.mkdir(parents=True, exist_ok=True)

        exec_command = get_exec_command()
        logger.info(f"Creating autostart entry with command: {exec_command}")

        desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Vocalinux
Exec={exec_command}
Icon=vocalinux
Comment=Voice dictation for Linux
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""

        with open(autostart_file, "w", encoding="utf-8") as f:
            f.write(desktop_entry)

        logger.info(f"Autostart enabled: {autostart_file}")
        return True

    except Exception as e:
        logger.error(f"Failed to enable autostart: {e}")
        return False


def disable_autostart() -> bool:
    """Disable autostart by removing the desktop entry file."""
    try:
        autostart_file = get_autostart_file()
        if autostart_file.exists():
            autostart_file.unlink()
            logger.info(f"Autostart disabled: {autostart_file}")
        return True

    except Exception as e:
        logger.error(f"Failed to disable autostart: {e}")
        return False


def set_autostart(enabled: bool) -> bool:
    """Set autostart enabled or disabled."""
    if enabled:
        return enable_autostart()
    return disable_autostart()
