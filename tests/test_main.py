"""
Tests for the main module functionality.
"""

import argparse
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock GTK modules before importing vocalinux.main
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()

# Update import to use the new package structure
from vocalinux.main import check_dependencies, main, parse_arguments


class TestMainModule(unittest.TestCase):
    """Test cases for the main module."""

    def test_parse_arguments_defaults(self):
        """Test argument parsing with defaults."""
        # Test with no arguments (model/engine/language will be None without defaults)
        with patch("sys.argv", ["vocalinux"]):
            args = parse_arguments()
            self.assertFalse(args.debug)
            self.assertIsNone(args.model)  # No default set, loaded from config instead
            self.assertIsNone(args.engine)
            self.assertIsNone(args.language)
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
                "--language",
                "fr",
                "--wayland",
            ],
        ):
            args = parse_arguments()
            self.assertTrue(args.debug)
            self.assertEqual(args.model, "large")
            self.assertEqual(args.engine, "whisper")
            self.assertEqual(args.language, "fr")
            self.assertTrue(args.wayland)

    def test_parse_arguments_model_choices(self):
        """Test that model only accepts valid choices."""
        with patch("sys.argv", ["vocalinux", "--model", "small"]):
            args = parse_arguments()
            self.assertEqual(args.model, "small")

        with patch("sys.argv", ["vocalinux", "--model", "medium"]):
            args = parse_arguments()
            self.assertEqual(args.model, "medium")

        with patch("sys.argv", ["vocalinux", "--model", "large"]):
            args = parse_arguments()
            self.assertEqual(args.model, "large")

    def test_parse_arguments_engine_choices(self):
        """Test that engine only accepts valid choices."""
        with patch("sys.argv", ["vocalinux", "--engine", "vosk"]):
            args = parse_arguments()
            self.assertEqual(args.engine, "vosk")

        with patch("sys.argv", ["vocalinux", "--engine", "whisper"]):
            args = parse_arguments()
            self.assertEqual(args.engine, "whisper")

    def test_parse_arguments_language_choices(self):
        """Test that language only accepts valid choices."""
        for lang in [
            "auto",
            "en-us",
            "en-in",
            "hi",
            "es",
            "fr",
            "de",
            "it",
            "pt",
            "ru",
            "zh",
            "ja",
            "ko",
            "ar",
        ]:
            with patch("sys.argv", ["vocalinux", "--language", lang]):
                args = parse_arguments()
                self.assertEqual(args.language, lang)

    @patch("vocalinux.main.sys.exit")
    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.parse_arguments")
    def test_main_exits_on_missing_deps(self, mock_parse, mock_check_deps, mock_exit):
        """Test that main exits when dependencies are missing."""
        mock_check_deps.return_value = False
        mock_args = MagicMock()
        mock_args.debug = False
        mock_parse.return_value = mock_args

        # Make sys.exit raise SystemExit to stop execution
        mock_exit.side_effect = SystemExit(1)

        with patch("vocalinux.main.logger"):
            try:
                main()
            except SystemExit:
                pass
            mock_exit.assert_called_with(1)

    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.parse_arguments")
    @patch("vocalinux.main.sys.exit")
    @patch("vocalinux.ui.config_manager.ConfigManager")
    @patch("vocalinux.ui.logging_manager.initialize_logging")
    def test_main_exits_on_init_error(
        self, mock_init_logging, mock_config, mock_exit, mock_parse, mock_check_deps
    ):
        """Test that main exits when initialization fails."""
        mock_check_deps.return_value = True
        mock_args = MagicMock()
        mock_args.debug = False
        mock_args.model = "small"
        mock_args.engine = "vosk"
        mock_args.language = "en-us"
        mock_args.wayland = False
        mock_parse.return_value = mock_args

        # Mock config
        mock_config_instance = MagicMock()
        mock_config_instance.get_settings.return_value = {
            "general": {"first_run": False},
        }
        mock_config.return_value = mock_config_instance

        # Make SpeechRecognitionManager raise an exception
        with patch(
            "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager",
            side_effect=Exception("Init error"),
        ):
            with patch("vocalinux.main.logger"):
                main()
                mock_exit.assert_called_once_with(1)

    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.ui.action_handler.ActionHandler")
    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager")
    @patch("vocalinux.text_injection.text_injector.TextInjector")
    @patch("vocalinux.ui.tray_indicator.TrayIndicator")
    @patch("vocalinux.main.logging")
    @patch("vocalinux.ui.config_manager.ConfigManager")
    @patch("vocalinux.ui.logging_manager.initialize_logging")
    def test_main_initializes_components(
        self,
        mock_init_logging,
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
        mock_config_instance.get_settings.return_value = {
            "speech_recognition": {},
            "general": {"first_run": False},
        }
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
            mock_args.language = "en-us"
            mock_args.wayland = True
            mock_parse.return_value = mock_args

            # Call main function
            main()

            # Verify components were initialized correctly
            mock_speech.assert_called_once_with(
                engine="vosk",
                language="en-us",
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

    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.ui.action_handler.ActionHandler")
    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager")
    @patch("vocalinux.text_injection.text_injector.TextInjector")
    @patch("vocalinux.ui.tray_indicator.TrayIndicator")
    @patch("vocalinux.main.logging")
    @patch("vocalinux.ui.config_manager.ConfigManager")
    @patch("vocalinux.ui.logging_manager.initialize_logging")
    def test_main_with_debug_enabled(
        self,
        mock_init_logging,
        mock_config_manager,
        mock_logging,
        mock_tray,
        mock_text,
        mock_speech,
        mock_action_handler,
        mock_check_deps,
    ):
        """Test that debug mode enables debug logging."""
        import logging  # Import for DEBUG constant

        mock_check_deps.return_value = True

        # Mock ConfigManager
        mock_config_instance = MagicMock()
        mock_config_instance.get_settings.return_value = {
            "speech_recognition": {},
            "general": {"first_run": False},
        }
        mock_config_manager.return_value = mock_config_instance

        # Mock objects
        mock_speech_instance = MagicMock()
        mock_text_instance = MagicMock()
        mock_tray_instance = MagicMock()
        mock_action_instance = MagicMock()

        mock_speech.return_value = mock_speech_instance
        mock_text.return_value = mock_text_instance
        mock_tray.return_value = mock_tray_instance
        mock_action_handler.return_value = mock_action_instance

        with patch("vocalinux.main.parse_arguments") as mock_parse:
            # Create mock args with debug enabled
            mock_args = MagicMock()
            mock_args.debug = True
            mock_args.model = "small"
            mock_args.engine = "vosk"
            mock_args.language = "en-us"
            mock_args.wayland = False
            mock_parse.return_value = mock_args

            # Create mock loggers
            root_logger = MagicMock()
            mock_logging.getLogger.return_value = root_logger

            # Call main
            main()

            # Verify root logger had setLevel called with DEBUG
            root_logger.setLevel.assert_called()


class TestCheckDependencies(unittest.TestCase):
    """Test cases for check_dependencies function."""

    def test_check_dependencies_all_available(self):
        """Test when all dependencies are available."""
        # Mock all the imports that check_dependencies does
        mock_gi = MagicMock()
        mock_gi.require_version = MagicMock()
        mock_gtk = MagicMock()
        mock_appindicator = MagicMock()
        mock_pynput = MagicMock()
        mock_requests = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "gi": mock_gi,
                "gi.repository": MagicMock(Gtk=mock_gtk, AppIndicator3=mock_appindicator),
                "pynput": mock_pynput,
                "requests": mock_requests,
            },
        ):
            result = check_dependencies()
            self.assertTrue(result)

    def test_check_dependencies_missing_gtk(self):
        """Test when GTK is missing."""

        # Make gi.require_version raise ValueError for Gtk
        def require_version_side_effect(name, version):
            if name == "Gtk":
                raise ValueError("Gtk not found")

        mock_gi = MagicMock()
        mock_gi.require_version = MagicMock(side_effect=require_version_side_effect)
        mock_pynput = MagicMock()
        mock_requests = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "gi": mock_gi,
                "pynput": mock_pynput,
                "requests": mock_requests,
            },
        ):
            with patch("vocalinux.main.logger"):
                result = check_dependencies()
                self.assertFalse(result)

    def test_check_dependencies_missing_appindicator_with_ayatana_fallback(self):
        """Test when AppIndicator3 is missing but AyatanaAppIndicator3 is available."""

        # Make gi.require_version raise ValueError for AppIndicator3 only
        # AyatanaAppIndicator3 should work as fallback
        def require_version_side_effect(name, version):
            if name == "AppIndicator3":
                raise ValueError("AppIndicator3 not found")
            # AyatanaAppIndicator3 works fine

        mock_gi = MagicMock()
        mock_gi.require_version = MagicMock(side_effect=require_version_side_effect)
        mock_gtk = MagicMock()
        mock_ayatana = MagicMock()
        mock_pynput = MagicMock()
        mock_requests = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "gi": mock_gi,
                "gi.repository": MagicMock(Gtk=mock_gtk, AyatanaAppIndicator3=mock_ayatana),
                "pynput": mock_pynput,
                "requests": mock_requests,
            },
        ):
            with patch("vocalinux.main.logger"):
                result = check_dependencies()
                # Should return True because AyatanaAppIndicator3 fallback works
                self.assertTrue(result)

    def test_check_dependencies_missing_both_appindicators(self):
        """Test when both AppIndicator3 and AyatanaAppIndicator3 are missing."""

        # Make gi.require_version raise ValueError for both AppIndicator variants
        def require_version_side_effect(name, version):
            if name in ("AppIndicator3", "AyatanaAppIndicator3"):
                raise ValueError(f"{name} not found")

        mock_gi = MagicMock()
        mock_gi.require_version = MagicMock(side_effect=require_version_side_effect)
        mock_gtk = MagicMock()
        mock_pynput = MagicMock()
        mock_requests = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "gi": mock_gi,
                "gi.repository": MagicMock(Gtk=mock_gtk),
                "pynput": mock_pynput,
                "requests": mock_requests,
            },
        ):
            with patch("vocalinux.main.logger"):
                result = check_dependencies()
                # Should return False because both indicators are missing
                self.assertFalse(result)


class TestMainConfigPrecedence(unittest.TestCase):
    """Test cases for configuration precedence in main."""

    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.ui.action_handler.ActionHandler")
    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager")
    @patch("vocalinux.text_injection.text_injector.TextInjector")
    @patch("vocalinux.ui.tray_indicator.TrayIndicator")
    @patch("vocalinux.ui.config_manager.ConfigManager")
    @patch("vocalinux.ui.logging_manager.initialize_logging")
    def test_cli_args_override_config(
        self,
        mock_init_logging,
        mock_config_manager,
        mock_tray,
        mock_text,
        mock_speech,
        mock_action_handler,
        mock_check_deps,
    ):
        """Test that CLI arguments take precedence over saved config."""
        mock_check_deps.return_value = True

        # Mock ConfigManager to return saved settings
        mock_config_instance = MagicMock()
        mock_config_instance.get_settings.return_value = {
            "speech_recognition": {
                "engine": "vosk",
                "model_size": "small",
                "language": "en-us",
            },
            "general": {"first_run": False},
        }
        mock_config_manager.return_value = mock_config_instance

        mock_speech_instance = MagicMock()
        mock_text_instance = MagicMock()
        mock_tray_instance = MagicMock()
        mock_action_instance = MagicMock()

        mock_speech.return_value = mock_speech_instance
        mock_text.return_value = mock_text_instance
        mock_tray.return_value = mock_tray_instance
        mock_action_handler.return_value = mock_action_instance

        # Simulate CLI args being set
        with patch(
            "sys.argv",
            [
                "vocalinux",
                "--engine",
                "whisper",
                "--model",
                "large",
                "--language",
                "fr",
            ],
        ):
            with patch("vocalinux.main.logger"):
                main()

                # CLI args should override config
                mock_speech.assert_called_once()
                call_kwargs = mock_speech.call_args[1]
                self.assertEqual(call_kwargs["engine"], "whisper")
                self.assertEqual(call_kwargs["model_size"], "large")
                self.assertEqual(call_kwargs["language"], "fr")

    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.ui.action_handler.ActionHandler")
    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager")
    @patch("vocalinux.text_injection.text_injector.TextInjector")
    @patch("vocalinux.ui.tray_indicator.TrayIndicator")
    @patch("vocalinux.ui.config_manager.ConfigManager")
    @patch("vocalinux.ui.logging_manager.initialize_logging")
    def test_config_used_when_no_cli_args(
        self,
        mock_init_logging,
        mock_config_manager,
        mock_tray,
        mock_text,
        mock_speech,
        mock_action_handler,
        mock_check_deps,
    ):
        """Test that saved config is used when CLI args not provided."""
        mock_check_deps.return_value = True

        # Mock ConfigManager to return saved settings
        mock_config_instance = MagicMock()
        mock_config_instance.get_settings.return_value = {
            "speech_recognition": {
                "engine": "whisper",
                "model_size": "medium",
                "language": "de",
            },
            "audio": {
                "device_index": 2,
            },
            "general": {"first_run": False},
        }
        mock_config_manager.return_value = mock_config_instance

        mock_speech_instance = MagicMock()
        mock_text_instance = MagicMock()
        mock_tray_instance = MagicMock()
        mock_action_instance = MagicMock()

        mock_speech.return_value = mock_speech_instance
        mock_text.return_value = mock_text_instance
        mock_tray.return_value = mock_tray_instance
        mock_action_handler.return_value = mock_action_instance

        # No CLI args for engine/model/language
        with patch("sys.argv", ["vocalinux"]):
            with patch("vocalinux.main.logger"):
                main()

                # Config values should be used
                mock_speech.assert_called_once()
                call_kwargs = mock_speech.call_args[1]
                self.assertEqual(call_kwargs["engine"], "whisper")
                self.assertEqual(call_kwargs["model_size"], "medium")
                self.assertEqual(call_kwargs["language"], "de")
                self.assertEqual(call_kwargs["audio_device_index"], 2)


if __name__ == "__main__":
    unittest.main()
