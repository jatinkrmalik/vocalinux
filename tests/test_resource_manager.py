"""
Tests for the resource_manager module.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from vocalinux.utils.resource_manager import ResourceManager


class TestResourceManager(unittest.TestCase):
    """Tests for ResourceManager class."""

    def test_initialization(self):
        """Test ResourceManager initializes properly."""
        manager = ResourceManager()
        self.assertIsNotNone(manager.resources_dir)
        self.assertIsNotNone(manager.icons_dir)
        self.assertIsNotNone(manager.sounds_dir)

    def test_icons_dir_property(self):
        """Test icons_dir returns correct path."""
        manager = ResourceManager()
        self.assertIn("icons", manager.icons_dir)
        self.assertIn("scalable", manager.icons_dir)

    def test_sounds_dir_property(self):
        """Test sounds_dir returns correct path."""
        manager = ResourceManager()
        self.assertIn("sounds", manager.sounds_dir)

    def test_get_icon_path(self):
        """Test get_icon_path returns correct path."""
        manager = ResourceManager()
        path = manager.get_icon_path("test-icon")
        self.assertTrue(path.endswith("test-icon.svg"))

    def test_get_sound_path(self):
        """Test get_sound_path returns correct path."""
        manager = ResourceManager()
        path = manager.get_sound_path("test-sound")
        self.assertTrue(path.endswith("test-sound.wav"))

    def test_ensure_directories_exist(self):
        """Test ensure_directories_exist creates directories."""
        manager = ResourceManager()
        with patch("os.makedirs") as mock_makedirs:
            manager.ensure_directories_exist()
            self.assertEqual(mock_makedirs.call_count, 2)

    def test_validate_resources(self):
        """Test validate_resources returns proper structure."""
        manager = ResourceManager()

        with patch("os.path.exists", return_value=True):
            results = manager.validate_resources()

            self.assertIn("resources_dir_exists", results)
            self.assertIn("icons_dir_exists", results)
            self.assertIn("sounds_dir_exists", results)
            self.assertIn("missing_icons", results)
            self.assertIn("missing_sounds", results)

    def test_validate_resources_missing_icons(self):
        """Test validate_resources detects missing icons."""
        manager = ResourceManager()

        with patch("os.path.exists", return_value=False):
            results = manager.validate_resources()

            self.assertFalse(results["resources_dir_exists"])
            self.assertTrue(len(results["missing_icons"]) > 0)

    def test_validate_resources_missing_sounds(self):
        """Test validate_resources detects missing sounds."""
        manager = ResourceManager()

        with patch("os.path.exists", return_value=False):
            results = manager.validate_resources()

            self.assertTrue(len(results["missing_sounds"]) > 0)

    def test_find_resources_dir_no_candidates_exist(self):
        """Test _find_resources_dir when no candidates exist."""
        # Need to patch at the module level before instantiation
        original_exists = Path.exists

        def mock_exists(self):
            # Return False for all resources paths
            path_str = str(self)
            if "resources" in path_str:
                return False
            return original_exists(self)

        with patch.object(Path, "exists", mock_exists):
            manager = ResourceManager()
            # Should default to first candidate with warning
            self.assertIsNotNone(manager.resources_dir)


if __name__ == "__main__":
    unittest.main()
