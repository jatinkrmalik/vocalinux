"""XDG base-directory helpers for Vocalinux.

Vocalinux stores its configuration, speech models and runtime data under the
standard XDG base directories. Honouring ``XDG_CONFIG_HOME`` / ``XDG_DATA_HOME``
instead of hard-coding ``~/.config`` and ``~/.local/share`` is what lets the
application work unchanged inside a Flatpak sandbox, where those variables point
at ``~/.var/app/<app-id>/``.

Outside of a sandbox the behaviour is identical to the previous hard-coded
paths, because the XDG specification mandates the same defaults when the
variables are unset.
"""

import os

#: Sub-directory used for all Vocalinux data under the XDG roots.
APP_DIR_NAME = "vocalinux"


def xdg_config_home() -> str:
    """Return ``$XDG_CONFIG_HOME`` or its spec-mandated default (``~/.config``)."""
    # The spec says a relative or empty value must be ignored, hence ``or``.
    return os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")


def xdg_data_home() -> str:
    """Return ``$XDG_DATA_HOME`` or its spec-mandated default (``~/.local/share``)."""
    return os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")


def config_dir() -> str:
    """Return the Vocalinux configuration directory."""
    return os.path.join(xdg_config_home(), APP_DIR_NAME)


def data_dir() -> str:
    """Return the Vocalinux data directory."""
    return os.path.join(xdg_data_home(), APP_DIR_NAME)


def models_dir() -> str:
    """Return the directory where speech-recognition models are stored."""
    return os.path.join(data_dir(), "models")
