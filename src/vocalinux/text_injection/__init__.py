"""
Text injection module for Vocalinux
"""

from . import text_injector  # noqa: F401
from .ibus_engine import (  # noqa: F401
    IBusSetupError,
    IBusTextInjector,
    install_ibus_component,
    is_engine_active,
    is_engine_registered,
    is_ibus_available,
)
