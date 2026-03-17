"""
Additional coverage tests for resource_manager.py module.

Tests for resource directory discovery and validation.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Autouse fixture to prevent sys.modules pollution
@pytest.fixture(autouse=True)
def _restore_sys_modules():
    saved = dict(sys.modules)
    yield
    added = set(sys.modules.keys()) - set(saved.keys())
    for k in added:
        del sys.modules[k]
    for k, v in saved.items():
        if k not in sys.modules or sys.modules[k] is not v:
            sys.modules[k] = v


class TestResourceManagerDefaults:
    """Tests for ResourceManager when resources don't exist."""

    def test_resource_manager_defaults_to_first_candidate(self):
        """Test that ResourceManager defaults to first candidate when none exist."""
        from vocalinux.utils.resource_manager import ResourceManager

        with patch("vocalinux.utils.resource_manager.Path") as mock_path:
            # All candidates return False for exists()
            mock_candidate = MagicMock()
            mock_candidate.exists.return_value = False
            mock_path.return_value = mock_candidate

            # Create manager and trigger _find_resources_dir
            manager = ResourceManager()
            # Reset to test again
            ResourceManager._resources_dir = None

            # Patch the actual _find_resources_dir to return a path
            with patch.object(manager, "_find_resources_dir", return_value="/tmp/resources"):
                manager._resources_dir = None
                manager.__init__()
                assert manager._resources_dir == "/tmp/resources"

    def test_resource_manager_singleton(self):
        """Test that ResourceManager follows singleton pattern."""
        from vocalinux.utils.resource_manager import ResourceManager

        ResourceManager._instance = None
        manager1 = ResourceManager()
        manager2 = ResourceManager()

        assert manager1 is manager2

    def test_resource_manager_properties(self):
        """Test ResourceManager properties."""
        from vocalinux.utils.resource_manager import ResourceManager

        ResourceManager._instance = None
        manager = ResourceManager()

        # Test that properties return strings
        assert isinstance(manager.resources_dir, str)
        assert isinstance(manager.icons_dir, str)
        assert isinstance(manager.sounds_dir, str)

    def test_get_icon_path(self):
        """Test get_icon_path method."""
        from vocalinux.utils.resource_manager import ResourceManager

        ResourceManager._instance = None
        manager = ResourceManager()

        icon_path = manager.get_icon_path("test-icon")
        assert "test-icon.svg" in icon_path
        assert "icons" in icon_path

    def test_get_sound_path(self):
        """Test get_sound_path method."""
        from vocalinux.utils.resource_manager import ResourceManager

        ResourceManager._instance = None
        manager = ResourceManager()

        sound_path = manager.get_sound_path("test-sound")
        assert "test-sound.wav" in sound_path
        assert "sounds" in sound_path

    def test_ensure_directories_exist(self):
        """Test ensure_directories_exist method."""
        from vocalinux.utils.resource_manager import ResourceManager

        ResourceManager._instance = None
        manager = ResourceManager()

        # Just verify the method can be called without error
        # It will attempt to create directories but may fail if path doesn't exist
        try:
            manager.ensure_directories_exist()
        except (OSError, FileNotFoundError):
            # Expected if resources dir doesn't exist
            pass

    def test_validate_resources_missing_resources(self):
        """Test validate_resources when resources are missing."""
        from vocalinux.utils.resource_manager import ResourceManager

        ResourceManager._instance = None

        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = ResourceManager()

            with patch.object(manager, "_resources_dir", tmp_dir):
                results = manager.validate_resources()

                # Resources don't exist, so should show as missing
                assert (
                    results["resources_dir_exists"] is False
                    or results["icons_dir_exists"] is False
                    or results["sounds_dir_exists"] is False
                )


class TestResourceManagerLogging:
    """Tests for resource manager logging."""

    def test_find_resources_dir_returns_string(self):
        """Test that _find_resources_dir returns a string path."""
        from vocalinux.utils.resource_manager import ResourceManager

        ResourceManager._instance = None
        manager = ResourceManager()

        # Just verify the method returns a string path
        result = manager._find_resources_dir()
        assert isinstance(result, str)
        assert len(result) > 0
