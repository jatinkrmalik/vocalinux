"""
Configuration file for pytest.
This file makes sure that the 'src' module can be imported in tests.
"""

import os
import sys

import pytest

# Add the parent directory to sys.path so that 'src' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the environment constants after path is set up
from vocalinux.utils.environment import (
    ENV_TESTING,
    FEATURE_AUDIO,
    FEATURE_GUI,
    FEATURE_KEYBOARD,
)


@pytest.fixture(autouse=True)
def mock_environment(monkeypatch):
    """
    Mock the environment manager for testing.

    This fixture is automatically applied to all tests and ensures that
    hardware-dependent features are properly mocked.
    """

    class MockEnvironmentManager:
        def __init__(self):
            self._environment = ENV_TESTING
            self._features = {FEATURE_AUDIO, FEATURE_KEYBOARD, FEATURE_GUI}

        def get_environment(self):
            """Get the current environment type."""
            return self._environment

        def is_feature_available(self, feature):
            """Check if a specific feature is available."""
            return feature in self._features

        def is_ci(self):
            """Check if running in a CI environment."""
            return False

        def is_testing(self):
            """Check if running in a testing environment."""
            return True

        def _mock_enable_feature(self, feature):
            """Enable a specific feature for testing."""
            self._features.add(feature)

        def _mock_disable_feature(self, feature):
            """Disable a specific feature for testing."""
            self._features.discard(feature)

    # Create an instance of our mock
    mock_env = MockEnvironmentManager()

    # Apply the monkeypatch to replace the real environment manager
    monkeypatch.setattr("vocalinux.utils.environment.environment", mock_env)

    # Return the mock so tests can modify it if needed
    return mock_env


@pytest.fixture
def disable_audio(mock_environment):
    """Fixture to disable audio features during a test."""
    mock_environment._mock_disable_feature(FEATURE_AUDIO)
    yield
    mock_environment._mock_enable_feature(FEATURE_AUDIO)


@pytest.fixture
def disable_keyboard(mock_environment):
    """Fixture to disable keyboard features during a test."""
    mock_environment._mock_disable_feature(FEATURE_KEYBOARD)
    yield
    mock_environment._mock_enable_feature(FEATURE_KEYBOARD)


@pytest.fixture
def disable_gui(mock_environment):
    """Fixture to disable GUI features during a test."""
    mock_environment._mock_disable_feature(FEATURE_GUI)
    yield
    mock_environment._mock_enable_feature(FEATURE_GUI)


# This will help pytest discover all test files correctly
pytest_plugins = []
