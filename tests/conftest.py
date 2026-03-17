"""
Configuration file for pytest.
This file makes sure that the 'src' module can be imported in tests.
"""

import os
import socket
import sys
from unittest.mock import MagicMock

import pytest

# Set PYTEST_RUNNING early so audio_feedback module can detect it
os.environ["PYTEST_RUNNING"] = "1"

# Set a short global default socket timeout to prevent tests from blocking
# indefinitely on socket operations (e.g. accept(), connect(), recv()).
# This is critical on CI where ibus_engine tests create real Unix sockets
# with daemon threads that block on accept() and can never be interrupted
# by pytest-timeout's signal- or thread-based mechanisms.
# Use a very short timeout (0.1s) to avoid slowing down the test suite.
socket.setdefaulttimeout(0.1)

# Add the parent directory to sys.path so that 'src' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Always mock GI/GTK modules before any test files are collected.
# On CI, real gi (PyGObject) is installed via "pip install PyGObject" and
# module-level imports in vocalinux source files (ibus_engine, tray_indicator,
# settings_dialog, etc.) will trigger GTK initialization or IBus daemon
# connections that hang indefinitely in headless environments.
# pytest-timeout cannot interrupt these C-level blocking calls.
#
# We unconditionally replace gi with a mock — even if the real package is
# already imported — because the real gi causes hangs on headless CI runners.
# The previous "if 'gi' not in sys.modules" guard was ineffective on CI
# precisely because PyGObject was installed and already loaded.
_mock_gi = MagicMock()
_mock_gi_repository = MagicMock()
sys.modules["gi"] = _mock_gi
sys.modules["gi.repository"] = _mock_gi_repository

# Create and export the mock_audio_feedback module for tests that need it
# This mock is used by test_recognition_manager.py and test_speech_recognition.py
mock_audio_feedback = MagicMock()
mock_audio_feedback.play_start_sound = MagicMock()
mock_audio_feedback.play_stop_sound = MagicMock()
mock_audio_feedback.play_error_sound = MagicMock()

# Inject the mock into sys.modules so imports resolve correctly
sys.modules["vocalinux.ui.audio_feedback"] = mock_audio_feedback


@pytest.fixture(autouse=True)
def _cleanup_ibus_server():
    """Stop any leftover IBus socket server threads after each test.

    Some tests trigger VocalinuxEngine._start_socket_server() which spawns
    a daemon thread blocking on socket.accept().  If the test doesn't call
    stop_socket_server(), the thread keeps running and eventually causes
    pytest-timeout to kill the whole process.
    """
    yield

    try:
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        if getattr(VocalinuxEngine, "_server_running", False):
            VocalinuxEngine._server_running = False
        sock = getattr(VocalinuxEngine, "_server_socket", None)
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
            VocalinuxEngine._server_socket = None
    except Exception:
        pass


def pytest_addoption(parser):
    """Add custom command line options for pytest."""
    parser.addoption(
        "--run-tray-tests",
        action="store_true",
        default=False,
        help="Run tray indicator tests (may hang in headless environments)",
    )
    parser.addoption(
        "--run-audio-tests",
        action="store_true",
        default=False,
        help="Run audio feedback tests (may fail in CI environments without audio)",
    )


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "tray: marks tests as tray indicator tests")
    config.addinivalue_line("markers", "audio: marks tests as audio feedback tests")


@pytest.fixture
def mock_gi():
    """Fixture to mock GTK/GI modules for tests that need it."""
    mock_gtk = MagicMock()
    mock_glib = MagicMock()
    mock_gobject = MagicMock()
    mock_gdkpixbuf = MagicMock()
    mock_appindicator = MagicMock()

    # Make idle_add execute the function directly
    mock_glib.idle_add.side_effect = lambda func, *args: func(*args) or False

    return {
        "Gtk": mock_gtk,
        "GLib": mock_glib,
        "GObject": mock_gobject,
        "GdkPixbuf": mock_gdkpixbuf,
        "AppIndicator3": mock_appindicator,
    }


@pytest.fixture
def mock_audio_player():
    """Fixture to mock audio player detection."""
    return MagicMock()


# This will help pytest discover all test files correctly
pytest_plugins = []
