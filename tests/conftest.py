"""
Configuration file for pytest.
This file makes sure that the 'src' module can be imported in tests.
"""

import os
import sys
from unittest.mock import MagicMock

import pytest

# Add the parent directory to sys.path so that 'src' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create and export the mock_audio_feedback module for tests that need it
# This mock is used by test_recognition_manager.py and test_speech_recognition.py
mock_audio_feedback = MagicMock()
mock_audio_feedback.play_start_sound = MagicMock()
mock_audio_feedback.play_stop_sound = MagicMock()
mock_audio_feedback.play_error_sound = MagicMock()

# Inject the mock into sys.modules so imports resolve correctly
sys.modules["vocalinux.ui.audio_feedback"] = mock_audio_feedback


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
