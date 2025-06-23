"""
Vocalinux - A seamless voice dictation system for Linux
"""

__version__ = "0.1.0"

# Import common types first to avoid circular imports
from .common_types import RecognitionState

# Make key modules accessible from the top-level package
# Note: We're careful about import order to avoid circular imports
from .speech_recognition import recognition_manager
from .text_injection import text_injector
from .ui import tray_indicator
from .utils import ResourceManager
