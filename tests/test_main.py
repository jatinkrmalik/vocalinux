"""
Tests for the main module functionality.
"""

import argparse
import unittest
from unittest.mock import MagicMock, patch

# Update import to use the new package structure
from vocalinux.main import main, parse_arguments


class TestMainModule(unittest.TestCase):
    """Test cases for the main module."""

    def test_parse_arguments_defaults(self):
        """Test argument parsing with defaults."""
        # Test with no arguments
        with patch("sys.argv", ["vocalinux"]):
            args = parse_arguments()
            self.assertFalse(args.debug)
            self.assertEqual(args.model, "small")
            self.assertEqual(args.engine, "vosk")
            self.assertFalse(args.wayland)

    def test_parse_arguments_custom(self):
        """Test argument parsing with custom values."""
        # Test with custom arguments
        with patch(
            "sys.argv",
            [
                "vocalinux",
                "--debug",
                "--model",
                "large",
                "--engine",
                "whisper",
                "--wayland",
            ],
        ):
            args = parse_arguments()
            self.assertTrue(args.debug)
            self.assertEqual(args.model, "large")
            self.assertEqual(args.engine, "whisper")
            self.assertTrue(args.wayland)

    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.ActionHandler")
    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager")
    @patch("vocalinux.text_injection.text_injector.TextInjector")
    @patch("vocalinux.ui.tray_indicator.TrayIndicator")
    @patch("vocalinux.main.logging")
    @patch("vocalinux.ui.config_manager.ConfigManager")
    def test_main_initializes_components(
        self,
        mock_config_manager,
        mock_logging,
        mock_tray,
        mock_text,
        mock_speech,
        mock_action_handler,
        mock_check_deps,
    ):
        """Test that main initializes all the required components."""
        # Mock dependency check to return True
        mock_check_deps.return_value = True

        # Mock ConfigManager to return empty settings (use command-line defaults)
        mock_config_instance = MagicMock()
        mock_config_instance.get_settings.return_value = {"speech_recognition": {}}
        mock_config_manager.return_value = mock_config_instance

        # Mock objects
        mock_speech_instance = MagicMock()
        mock_text_instance = MagicMock()
        mock_tray_instance = MagicMock()
        mock_action_instance = MagicMock()

        # Setup return values
        mock_speech.return_value = mock_speech_instance
        mock_text.return_value = mock_text_instance
        mock_tray.return_value = mock_tray_instance
        mock_action_handler.return_value = mock_action_instance

        # Mock the arguments
        with patch("vocalinux.main.parse_arguments") as mock_parse:
            mock_args = MagicMock()
            mock_args.debug = False
            mock_args.model = "medium"
            mock_args.engine = "vosk"
            mock_args.wayland = True
            mock_parse.return_value = mock_args

            # Call main function
            main()

            # Verify components were initialized correctly
            mock_speech.assert_called_once_with(
                engine="vosk",
                model_size="medium",
                vad_sensitivity=3,
                silence_timeout=2.0,
                audio_device_index=None,
            )
            mock_text.assert_called_once_with(wayland_mode=True)
            mock_action_handler.assert_called_once_with(mock_text_instance)
            mock_tray.assert_called_once_with(
                speech_engine=mock_speech_instance, text_injector=mock_text_instance
            )

            # Verify callbacks were registered
            mock_speech_instance.register_text_callback.assert_called_once()
            mock_speech_instance.register_action_callback.assert_called_once_with(
                mock_action_instance.handle_action
            )

            # Verify the tray indicator was started
            mock_tray_instance.run.assert_called_once()

    def test_main_with_debug_enabled(self):
        """Test that debug mode enables debug logging."""
        import logging  # Import for DEBUG constant

        # Test with args.debug = True
        with patch("vocalinux.main.parse_arguments") as mock_parse, patch(
            "vocalinux.main.logging"
        ) as mock_logging, patch("vocalinux.main.logging.DEBUG", logging.DEBUG), patch(
            "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager"
        ), patch(
            "vocalinux.text_injection.text_injector.TextInjector"
        ), patch(
            "vocalinux.ui.tray_indicator.TrayIndicator"
        ), patch(
            "vocalinux.main.ActionHandler"
        ), patch(
            "vocalinux.main.check_dependencies"
        ) as mock_check_deps:

            # Mock dependency check to return True
            mock_check_deps.return_value = True

            # Create mock args
            mock_args = MagicMock()
            mock_args.debug = True
            mock_args.model = "small"
            mock_args.engine = "vosk"
            mock_args.wayland = False
            mock_parse.return_value = mock_args

            # Create mock loggers
            root_logger = MagicMock()
            named_logger = MagicMock()
            mock_logging.getLogger.side_effect = [root_logger, named_logger]

            # Call main
            main()

            # Verify root logger had setLevel called with DEBUG
            root_logger.setLevel.assert_called_once_with(logging.DEBUG)
