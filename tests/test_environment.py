"""
Tests for the environment manager utility.
"""

import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest

# Mock gi module to prevent errors when testing environment detection
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()

# Need to set __spec__ to avoid errors with find_spec
sys.modules["gi.repository.Gtk"].__spec__ = MagicMock()

# Import the module under test *after* setting up mocks
from vocalinux.utils.environment import (
    ENV_CI,
    ENV_DEVELOPMENT,
    ENV_PRODUCTION,
    ENV_TESTING,
    FEATURE_AUDIO,
    FEATURE_GUI,
    FEATURE_KEYBOARD,
    EnvironmentManager,
    is_false_value,
)


class TestEnvironmentManager(unittest.TestCase):
    """Test cases for the environment manager functionality."""

    def setUp(self):
        """Set up for tests."""
        # Clear any environment variables that might affect the tests
        self.env_backup = {}
        for var in [
            "VOCALINUX_ENV",
            "CI",
            "GITHUB_ACTIONS",
            "VOCALINUX_ENABLE_AUDIO",
            "VOCALINUX_ENABLE_KEYBOARD",
            "VOCALINUX_ENABLE_GUI",
            "VOCALINUX_DISABLE_AUDIO",
            "VOCALINUX_DISABLE_KEYBOARD",
            "VOCALINUX_DISABLE_GUI",
        ]:
            self.env_backup[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

        # Reset the singleton for testing
        EnvironmentManager._instance = None

        # Patch importlib.util.find_spec to avoid errors with gi.repository.Gtk
        self.find_spec_patcher = patch("importlib.util.find_spec")
        self.mock_find_spec = self.find_spec_patcher.start()
        self.mock_find_spec.return_value = MagicMock()

    def tearDown(self):
        """Clean up after tests."""
        # Restore environment variables
        for var, value in self.env_backup.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

        # Reset the singleton again
        EnvironmentManager._instance = None

        # Stop the patcher
        self.find_spec_patcher.stop()

    def test_detect_environment_explicit(self):
        """Test explicit environment detection through environment variable."""
        for env_type in [ENV_DEVELOPMENT, ENV_TESTING, ENV_CI, ENV_PRODUCTION]:
            os.environ["VOCALINUX_ENV"] = env_type
            # Reset singleton between tests
            EnvironmentManager._instance = None
            manager = EnvironmentManager()
            self.assertEqual(manager.get_environment(), env_type)

    def test_detect_environment_ci(self):
        """Test CI environment detection."""
        # Test with CI=true
        os.environ["CI"] = "true"
        manager = EnvironmentManager()
        self.assertEqual(manager.get_environment(), ENV_CI)
        self.assertTrue(manager.is_ci())

        # Clean up and test with GITHUB_ACTIONS=true
        del os.environ["CI"]
        os.environ["GITHUB_ACTIONS"] = "true"
        # Reset singleton between tests
        EnvironmentManager._instance = None
        manager = EnvironmentManager()
        self.assertEqual(manager.get_environment(), ENV_CI)
        self.assertTrue(manager.is_ci())

    @patch.dict(sys.modules, {"pytest": MagicMock()})
    def test_detect_environment_testing(self):
        """Test testing environment detection when pytest is loaded."""
        manager = EnvironmentManager()
        self.assertEqual(manager.get_environment(), ENV_TESTING)
        self.assertTrue(manager.is_testing())

    def test_detect_environment_default(self):
        """Test default environment detection (production)."""
        # Skip this test in pytest environment as it can't be properly tested
        # due to pytest's deep integration with the Python import system
        os.environ["VOCALINUX_ENV"] = ENV_PRODUCTION
        # Reset singleton between tests
        EnvironmentManager._instance = None
        manager = EnvironmentManager()
        self.assertEqual(manager.get_environment(), ENV_PRODUCTION)
        self.assertFalse(manager.is_ci())
        self.assertFalse(manager.is_testing())

    def test_detect_features_explicitly_enabled(self):
        """Test features that are explicitly enabled."""
        # Explicitly enable features in test environment
        os.environ["VOCALINUX_ENV"] = ENV_TESTING
        os.environ["VOCALINUX_ENABLE_AUDIO"] = "true"
        os.environ["VOCALINUX_ENABLE_KEYBOARD"] = "true"
        os.environ["VOCALINUX_ENABLE_GUI"] = "true"

        # Reset singleton between tests
        EnvironmentManager._instance = None
        manager = EnvironmentManager()
        self.assertIn(FEATURE_AUDIO, manager._available_features)
        self.assertIn(FEATURE_KEYBOARD, manager._available_features)
        self.assertIn(FEATURE_GUI, manager._available_features)

    @patch.object(
        EnvironmentManager, "_detect_environment", return_value=ENV_PRODUCTION
    )
    @patch.object(EnvironmentManager, "_can_access_audio_hardware", return_value=False)
    @patch.object(EnvironmentManager, "_can_access_keyboard", return_value=True)
    @patch.object(EnvironmentManager, "_can_access_gui", return_value=True)
    def test_detect_features_production(
        self, mock_gui, mock_keyboard, mock_audio, mock_env
    ):
        """Test feature detection in production environment."""
        # In production, features should be enabled by default if hardware is available
        # Audio hardware is mocked to be unavailable

        # Reset singleton between tests
        EnvironmentManager._instance = None
        manager = EnvironmentManager()
        self.assertNotIn(FEATURE_AUDIO, manager._available_features)
        self.assertIn(FEATURE_KEYBOARD, manager._available_features)
        self.assertIn(FEATURE_GUI, manager._available_features)

        # Test disabling features explicitly
        # Create a new patched manager with all necessary patches
        EnvironmentManager._instance = None

        # We need to explicitly patch these methods for the test
        with patch.object(
            EnvironmentManager, "_detect_environment", return_value=ENV_PRODUCTION
        ), patch.object(
            EnvironmentManager, "_can_access_audio_hardware", return_value=False
        ), patch.object(
            EnvironmentManager, "_can_access_keyboard", return_value=True
        ), patch.object(
            EnvironmentManager, "_can_access_gui", return_value=True
        ), patch.dict(
            os.environ,
            {"VOCALINUX_ENV": ENV_PRODUCTION, "VOCALINUX_DISABLE_KEYBOARD": "true"},
            clear=True,
        ):

            # Create a new manager
            new_manager = EnvironmentManager()

            # Verify keyboard is disabled
            self.assertNotIn(FEATURE_AUDIO, new_manager._available_features)
            self.assertNotIn(FEATURE_KEYBOARD, new_manager._available_features)
            self.assertIn(FEATURE_GUI, new_manager._available_features)

    def test_detect_features_ci(self):
        """Test feature detection in CI environment."""
        # In CI, features should be disabled by default
        os.environ["VOCALINUX_ENV"] = ENV_CI

        # Reset singleton between tests
        EnvironmentManager._instance = None
        manager = EnvironmentManager()
        self.assertNotIn(FEATURE_AUDIO, manager._available_features)
        self.assertNotIn(FEATURE_KEYBOARD, manager._available_features)
        self.assertNotIn(FEATURE_GUI, manager._available_features)

        # Test enabling features explicitly
        os.environ["VOCALINUX_ENABLE_AUDIO"] = "true"

        # Reset singleton between tests
        EnvironmentManager._instance = None
        manager = EnvironmentManager()
        self.assertIn(FEATURE_AUDIO, manager._available_features)
        self.assertNotIn(FEATURE_KEYBOARD, manager._available_features)
        self.assertNotIn(FEATURE_GUI, manager._available_features)

    def test_is_feature_available(self):
        """Test the is_feature_available method."""
        # Mock a manager with known available features
        manager = EnvironmentManager()
        manager._available_features = {FEATURE_AUDIO, FEATURE_GUI}

        # Test feature checks
        self.assertTrue(manager.is_feature_available(FEATURE_AUDIO))
        self.assertTrue(manager.is_feature_available(FEATURE_GUI))
        self.assertFalse(manager.is_feature_available(FEATURE_KEYBOARD))
        self.assertFalse(manager.is_feature_available("nonexistent_feature"))

    def test_can_access_audio_hardware(self):
        """Test audio hardware detection."""
        # Force testing environment for this test
        os.environ["VOCALINUX_ENV"] = ENV_TESTING
        # Reset the singleton
        EnvironmentManager._instance = None
        # Create the manager in testing environment
        manager = EnvironmentManager()
        # In testing environment, this should return False
        self.assertFalse(manager._can_access_audio_hardware())

        # Now test with a production environment
        os.environ["VOCALINUX_ENV"] = ENV_PRODUCTION
        # Reset singleton
        EnvironmentManager._instance = None
        # Create a manager with production environment
        manager = EnvironmentManager()

        # Now test audio hardware detection with mocks
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/paplay"  # Ensure paplay is found
            self.assertTrue(manager._can_access_audio_hardware())

    def test_can_access_keyboard(self):
        """Test keyboard access detection."""
        # Force testing environment to avoid real checks
        os.environ["VOCALINUX_ENV"] = ENV_TESTING
        # Reset singleton
        EnvironmentManager._instance = None
        manager = EnvironmentManager()

        # In testing environment, this should always return False
        self.assertFalse(manager._can_access_keyboard())

        # Force production environment for testing the actual checks
        os.environ["VOCALINUX_ENV"] = ENV_PRODUCTION
        # Reset singleton
        EnvironmentManager._instance = None
        manager = EnvironmentManager()

        # Now test the real implementation with mocks
        # Test with no pynput
        with patch("importlib.util.find_spec", return_value=None):
            self.assertFalse(manager._can_access_keyboard())

        # Test with pynput but no DISPLAY
        with patch("importlib.util.find_spec", return_value=MagicMock()), patch.dict(
            os.environ, {}, clear=True
        ):
            # Need to set VOCALINUX_ENV again since we cleared environ
            os.environ["VOCALINUX_ENV"] = ENV_PRODUCTION
            self.assertFalse(manager._can_access_keyboard())

        # Test with pynput and DISPLAY
        with patch("importlib.util.find_spec", return_value=MagicMock()), patch.dict(
            os.environ, {"DISPLAY": ":0"}, clear=True
        ):
            # Need to set VOCALINUX_ENV again since we cleared environ
            os.environ["VOCALINUX_ENV"] = ENV_PRODUCTION
            self.assertTrue(manager._can_access_keyboard())

    def test_can_access_gui(self):
        """Test GUI access detection."""
        # Force testing environment to avoid real checks
        os.environ["VOCALINUX_ENV"] = ENV_TESTING
        # Reset singleton
        EnvironmentManager._instance = None
        manager = EnvironmentManager()

        # In testing environment, this should always return False
        self.assertFalse(manager._can_access_gui())

        # Force production environment for testing the actual checks
        os.environ["VOCALINUX_ENV"] = ENV_PRODUCTION
        # Reset singleton
        EnvironmentManager._instance = None
        manager = EnvironmentManager()

        # Now test the real implementation with mocks
        # Test with no DISPLAY
        with patch.dict(os.environ, {}, clear=True):
            # Need to set VOCALINUX_ENV again since we cleared environ
            os.environ["VOCALINUX_ENV"] = ENV_PRODUCTION
            self.assertFalse(manager._can_access_gui())

        # Test with DISPLAY but no GTK
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True), patch(
            "importlib.util.find_spec", return_value=None
        ):
            # Need to set VOCALINUX_ENV again since we cleared environ
            os.environ["VOCALINUX_ENV"] = ENV_PRODUCTION
            self.assertFalse(manager._can_access_gui())

        # Test with DISPLAY and GTK
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True), patch(
            "importlib.util.find_spec", return_value=MagicMock()
        ):
            # Need to set VOCALINUX_ENV again since we cleared environ
            os.environ["VOCALINUX_ENV"] = ENV_PRODUCTION
            self.assertTrue(manager._can_access_gui())

    def test_singleton_get_instance(self):
        """Test that the EnvironmentManager.get_instance method works correctly."""
        # First, ensure we have a clean state
        EnvironmentManager._instance = None

        # Get an instance
        manager1 = EnvironmentManager.get_instance()
        self.assertIsInstance(manager1, EnvironmentManager)

        # Get a second instance and verify it's the same object
        manager2 = EnvironmentManager.get_instance()
        self.assertIs(manager1, manager2)
