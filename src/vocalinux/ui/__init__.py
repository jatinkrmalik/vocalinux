"""
User interface module for Vocalinux

Note: GTK-dependent modules (tray_indicator) are imported lazily to allow
the package to be imported even when GTK/AppIndicator3 typelibs are not available.
"""

# These modules don't require GTK typelibs at import time
from . import (
    audio_feedback,
    config_manager,
    keyboard_shortcuts,
    logging_manager,
    visual_feedback,
)

# tray_indicator is imported lazily in main.py to handle missing GTK gracefully
