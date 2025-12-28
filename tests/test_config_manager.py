"""
Tests for the config manager functionality.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Update import path to use the new package structure
from vocalinux.ui.config_manager import (
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_CONFIG,
    ConfigManager,
)


class TestConfigManager(unittest.TestCase):
    """Test cases for the configuration manager."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for configuration
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_config_dir = os.path.join(self.temp_dir.name, ".config/vocalinux")
        os.makedirs(self.temp_config_dir, exist_ok=True)
        self.temp_config_file = os.path.join(self.temp_config_dir, "config.json")

        # Patch the config paths to use our temporary directory
        self.config_dir_patcher = patch(
            "vocalinux.ui.config_manager.CONFIG_DIR", self.temp_config_dir
        )
        self.config_file_patcher = patch(
            "vocalinux.ui.config_manager.CONFIG_FILE", self.temp_config_file
        )

        self.config_dir_patcher.start()
        self.config_file_patcher.start()

        # Patch logging to avoid actual logging
        self.logger_patcher = patch("vocalinux.ui.config_manager.logger")
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        """Clean up after tests."""
        self.config_dir_patcher.stop()
        self.config_file_patcher.stop()
        self.logger_patcher.stop()
        self.temp_dir.cleanup()

    def test_init_default_config(self):
        """Test initialization with default configuration."""
        config_manager = ConfigManager()
        self.assertEqual(config_manager.config, DEFAULT_CONFIG)
        self.mock_logger.info.assert_called_with(
            f"Config file not found at {self.temp_config_file}. Using defaults."
        )
        self.assertTrue(os.path.exists(self.temp_config_dir))

    def test_ensure_config_dir(self):
        """Test that _ensure_config_dir creates the directory."""
        # Delete the config directory to test creation
        os.rmdir(self.temp_config_dir)
        self.assertFalse(os.path.exists(self.temp_config_dir))

        # Create config manager, which should create the directory
        config_manager = ConfigManager()
        self.assertTrue(os.path.exists(self.temp_config_dir))

    def test_load_config(self):
        """Test loading configuration from file."""
        # Create a test config file
        test_config = {
            "speech_recognition": {
                "engine": "whisper",
                "model_size": "large",
            },
            "ui": {
                "start_minimized": True,
            },
        }

        with open(self.temp_config_file, "w") as f:
            json.dump(test_config, f)

        # Load the config
        config_manager = ConfigManager()

        # Verify it merged with defaults correctly
        self.assertEqual(config_manager.config["speech_recognition"]["engine"], "whisper")
        self.assertEqual(config_manager.config["speech_recognition"]["model_size"], "large")
        self.assertEqual(
            config_manager.config["speech_recognition"]["vad_sensitivity"], 3
        )  # From defaults
        self.assertEqual(config_manager.config["ui"]["start_minimized"], True)
        self.assertEqual(config_manager.config["ui"]["show_notifications"], True)  # From defaults

    def test_load_config_file_error(self):
        """Test handling of errors when loading config file."""
        # Create a broken config file
        with open(self.temp_config_file, "w") as f:
            f.write("{broken json")

        # Load the config, should use defaults
        config_manager = ConfigManager()
        self.assertEqual(config_manager.config, DEFAULT_CONFIG)
        self.mock_logger.error.assert_called()

    def test_save_config(self):
        """Test saving configuration to file."""
        config_manager = ConfigManager()

        # Modify config
        config_manager.config["speech_recognition"]["engine"] = "whisper"
        config_manager.config["ui"]["start_minimized"] = True

        # Save config
        result = config_manager.save_config()
        self.assertTrue(result)

        # Verify file was created with correct content
        self.assertTrue(os.path.exists(self.temp_config_file))
        with open(self.temp_config_file, "r") as f:
            saved_config = json.load(f)

        self.assertEqual(saved_config["speech_recognition"]["engine"], "whisper")
        self.assertEqual(saved_config["ui"]["start_minimized"], True)

    def test_save_config_error(self):
        """Test handling of errors when saving config file."""
        config_manager = ConfigManager()

        # Mock open to raise an exception
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = config_manager.save_config()
            self.assertFalse(result)
            self.mock_logger.error.assert_called()

    def test_get_existing_value(self):
        """Test getting an existing configuration value."""
        config_manager = ConfigManager()
        value = config_manager.get("speech_recognition", "engine")
        self.assertEqual(value, "vosk")

    def test_get_nonexistent_value(self):
        """Test getting a nonexistent configuration value."""
        config_manager = ConfigManager()
        value = config_manager.get("nonexistent", "key", "default_value")
        self.assertEqual(value, "default_value")

    def test_set_existing_section(self):
        """Test setting a value in an existing section."""
        config_manager = ConfigManager()
        result = config_manager.set("speech_recognition", "engine", "whisper")
        self.assertTrue(result)
        self.assertEqual(config_manager.config["speech_recognition"]["engine"], "whisper")

    def test_set_new_section(self):
        """Test setting a value in a new section."""
        config_manager = ConfigManager()
        result = config_manager.set("new_section", "key", "value")
        self.assertTrue(result)
        self.assertEqual(config_manager.config["new_section"]["key"], "value")

    def test_set_error(self):
        """Test handling of errors when setting a value."""
        config_manager = ConfigManager()
        config_manager.config = 1  # Not a dict, will cause error
        result = config_manager.set("section", "key", "value")
        self.assertFalse(result)
        self.mock_logger.error.assert_called()

    def test_update_dict_recursive(self):
        """Test recursive dictionary update."""
        target = {"a": {"b": 1, "c": 2}, "d": 3}

        source = {"a": {"b": 10, "e": 20}, "f": 30}

        config_manager = ConfigManager()
        config_manager._update_dict_recursive(target, source)

        # Check that values were updated correctly
        self.assertEqual(target["a"]["b"], 10)  # Updated
        self.assertEqual(target["a"]["c"], 2)  # Unchanged
        self.assertEqual(target["a"]["e"], 20)  # Added
        self.assertEqual(target["d"], 3)  # Unchanged
        self.assertEqual(target["f"], 30)  # Added
