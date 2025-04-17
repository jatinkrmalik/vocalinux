"""
Tests for the ConfigManager component.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.ui.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Test cases for the config manager."""

    def setUp(self):
        """Set up a temporary config directory for testing."""
        # Create temp directory for configs
        self.temp_dir = tempfile.TemporaryDirectory()

        # Patch the CONFIG_DIR constant
        self.patcher = patch("src.ui.config_manager.CONFIG_DIR", self.temp_dir.name)
        self.patcher.start()

        # Patch the CONFIG_FILE constant
        config_file = os.path.join(self.temp_dir.name, "config.json")
        self.file_patcher = patch("src.ui.config_manager.CONFIG_FILE", config_file)
        self.file_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.patcher.stop()
        self.file_patcher.stop()
        self.temp_dir.cleanup()

    def test_config_defaults(self):
        """Test that default configuration values are set correctly."""
        # Create config manager
        config = ConfigManager()

        # Test default values
        assert config.get("recognition", "engine") == "vosk"
        assert config.get("shortcuts", "toggle_recognition") == "alt+shift+v"
        assert config.get("ui", "show_notifications") is True

    def test_set_and_get_config(self):
        """Test setting and getting configuration values."""
        # Create config manager
        config = ConfigManager()

        # Test setting and getting a value
        assert config.set("recognition", "engine", "whisper") is True
        assert config.get("recognition", "engine") == "whisper"

        # Test saving and reloading
        assert config.save_config() is True

        # Create a new instance to load from file
        config2 = ConfigManager()
        assert config2.get("recognition", "engine") == "whisper"
