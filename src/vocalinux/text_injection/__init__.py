"""
Text injection module for Vocalinux
"""

from . import text_injector  # noqa: F401
from .ibus_engine import (  # noqa: F401
    IBusSetupError,
    IBusTextInjector,
    is_engine_active,
    is_ibus_active_input_method,
    is_ibus_available,
    start_ibus_daemon,
)
