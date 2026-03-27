"""
Vocalinux - A seamless voice dictation system for Linux

Note: GTK-dependent modules are imported lazily in main.py to allow
the package to be imported even when system GTK typelibs are not available.
This is important for pip/pipx installations where PyGObject is installed
but system typelibs (AppIndicator3, etc.) may not be accessible.
"""

__version__ = "0.1.0"

# Import common types first to avoid circular imports
from .common_types import RecognitionState  # noqa: F401

# Import non-GTK modules that are safe to import at package level
from .utils import ResourceManager

# Note: speech_recognition, text_injection, and ui.tray_indicator
# are imported lazily in main.py to handle missing GTK gracefully
