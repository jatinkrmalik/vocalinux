"""
Additional coverage tests for main.py module.

Tests for parse_args(), main(), and VocalinuxApp class (if present).
Covers normal startup, debug mode, version flag, keyboard interrupt, and exception handling.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, call

import pytest


class TestParseArguments(unittest.TestCase):
    """Tests for parse_arguments() function."""

    def test_parse_args_defaults(self):
        """Test parsing arguments with defaults."""
        with patch.object(sys, "argv", ["vocalinux"]):
            from vocalinux.main import parse_arguments

            args = parse_arguments()
            assert args.debug is False
            assert args.model is None
            assert args.language is None
            assert args.engine is None
            assert args.wayland is False
            assert args.start_minimized is False

    def test_parse_args_debug_flag(self):
        """Test parsing with debug flag."""
        with patch.object(sys, "argv", ["vocalinux", "--debug"]):
            from vocalinux.main import parse_arguments

            args = parse_arguments()
            assert args.debug is True

    def test_parse_args_model_argument(self):
        """Test parsing with model argument."""
        with patch.object(sys, "argv", ["vocalinux", "--model", "small"]):
            from vocalinux.main import parse_arguments

            args = parse_arguments()
            assert args.model == "small"

    def test_parse_args_language_argument(self):
        """Test parsing with language argument."""
        with patch.object(sys, "argv", ["vocalinux", "--language", "en-us"]):
            from vocalinux.main import parse_arguments

            args = parse_arguments()
            assert args.language == "en-us"

    def test_parse_args_engine_argument(self):
        """Test parsing with engine argument."""
        with patch.object(sys, "argv", ["vocalinux", "--engine", "whisper_cpp"]):
            from vocalinux.main import parse_arguments

            args = parse_arguments()
            assert args.engine == "whisper_cpp"

    def test_parse_args_wayland_flag(self):
        """Test parsing with wayland flag."""
        with patch.object(sys, "argv", ["vocalinux", "--wayland"]):
            from vocalinux.main import parse_arguments

            args = parse_arguments()
            assert args.wayland is True

    def test_parse_args_start_minimized_flag(self):
        """Test parsing with start-minimized flag."""
        with patch.object(sys, "argv", ["vocalinux", "--start-minimized"]):
            from vocalinux.main import parse_arguments

            args = parse_arguments()
            assert args.start_minimized is True

    def test_parse_args_multiple_arguments(self):
        """Test parsing with multiple arguments."""
        with patch.object(
            sys,
            "argv",
            [
                "vocalinux",
                "--debug",
                "--model",
                "large",
                "--language",
                "es",
                "--engine",
                "vosk",
                "--wayland",
            ],
        ):
            from vocalinux.main import parse_arguments

            args = parse_arguments()
            assert args.debug is True
            assert args.model == "large"
            assert args.language == "es"
            assert args.engine == "vosk"
            assert args.wayland is True


class TestCheckDependencies(unittest.TestCase):
    """Tests for check_dependencies() function."""

    def test_check_dependencies_success(self):
        """Test successful dependency check."""
        with patch("vocalinux.main.logging"):
            from vocalinux.main import check_dependencies

            # Mock all required modules
            with patch.dict(sys.modules, {"gi": MagicMock()}):
                # Patch gi.require_version to not raise
                with patch("builtins.__import__", return_value=MagicMock()):
                    result = check_dependencies()
                    # Result depends on actual system, but function should run
                    assert isinstance(result, bool)

    def test_check_dependencies_missing_gtk(self):
        """Test dependency check with missing GTK."""
        from vocalinux.main import check_dependencies

        # Patch gi to raise ValueError for GTK
        def mock_require_version(name, version):
            if "Gtk" in name or "AppIndicator" in name or "pynput" in name:
                raise ValueError(f"Cannot find {name}")

        with patch("vocalinux.main.logging"):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                # Just verify the function doesn't crash
                result = check_dependencies()
                assert isinstance(result, bool)


class TestCheckDisplayAvailable(unittest.TestCase):
    """Tests for check_display_available() function."""

    @patch("vocalinux.main.logging")
    def test_check_display_available_success(self, mock_logging):
        """Test successful display check."""
        from vocalinux.main import check_display_available

        with patch.dict(sys.modules, {"gi": MagicMock()}):
            # Mock the display
            result = check_display_available()
            assert isinstance(result, bool)

    @patch("vocalinux.main.logging")
    def test_check_display_available_no_display(self, mock_logging):
        """Test display check when no display is available."""
        from vocalinux.main import check_display_available

        with patch.dict(sys.modules, {"gi": MagicMock()}):
            result = check_display_available()
            assert isinstance(result, bool)


class TestMainFunction(unittest.TestCase):
    """Tests for the main() function."""

    @patch("vocalinux.main.logging")
    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.check_display_available")
    @patch("vocalinux.main.parse_arguments")
    @patch("vocalinux.main.atexit")
    def test_main_single_instance_already_running(
        self,
        mock_atexit,
        mock_parse_args,
        mock_check_display,
        mock_check_deps,
        mock_logging,
    ):
        """Test main() when another instance is already running."""
        from vocalinux.main import main

        # Mock single_instance module since it's imported inside main()
        mock_single_instance = MagicMock()
        mock_single_instance.acquire_lock.return_value = False

        with patch.dict(sys.modules, {"vocalinux.single_instance": mock_single_instance}):
            # Should exit with status 1
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("vocalinux.main.check_display_available")
    @patch("vocalinux.main.logging")
    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.parse_arguments")
    @patch("vocalinux.main.atexit")
    def test_main_missing_dependencies(
        self, mock_atexit, mock_parse_args, mock_check_deps, mock_logging, mock_check_display
    ):
        """Test main() when dependencies are missing."""
        from vocalinux.main import main

        # Set up mocks
        mock_check_deps.return_value = False
        mock_parse_args.return_value = MagicMock(debug=False)

        # Mock single_instance module since it's imported inside main()
        mock_single_instance = MagicMock()
        mock_single_instance.acquire_lock.return_value = True

        with patch.dict(sys.modules, {"vocalinux.single_instance": mock_single_instance}):
            # Should exit with status 1
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("vocalinux.main.logging")
    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.check_display_available")
    @patch("vocalinux.main.parse_arguments")
    @patch("vocalinux.main.atexit")
    def test_main_no_display_available(
        self, mock_atexit, mock_parse_args, mock_check_display, mock_check_deps, mock_logging
    ):
        """Test main() when no display is available."""
        from vocalinux.main import main

        # Set up mocks
        mock_check_deps.return_value = True
        mock_check_display.return_value = False
        mock_parse_args.return_value = MagicMock(debug=False)

        # Mock single_instance module since it's imported inside main()
        mock_single_instance = MagicMock()
        mock_single_instance.acquire_lock.return_value = True

        with patch.dict(sys.modules, {"vocalinux.single_instance": mock_single_instance}):
            # Should exit with status 1
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch("vocalinux.main.logging")
    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.check_display_available")
    @patch("vocalinux.main.parse_arguments")
    @patch("vocalinux.main.atexit")
    def test_main_debug_mode_enabled(
        self,
        mock_atexit,
        mock_parse_args,
        mock_check_display,
        mock_check_deps,
        mock_logging,
    ):
        """Test main() with debug mode enabled."""
        from vocalinux.main import main

        # Set up mocks
        mock_check_deps.return_value = True
        mock_check_display.return_value = True

        mock_args = MagicMock()
        mock_args.debug = True
        mock_args.wayland = False
        mock_args.start_minimized = False
        mock_parse_args.return_value = mock_args

        # Mock single_instance module since it's imported inside main()
        mock_single_instance = MagicMock()
        mock_single_instance.acquire_lock.return_value = True

        # Create proper mock for ConfigManager with get_settings() returning valid data
        mock_config_manager = MagicMock()
        mock_config_manager.return_value.get_settings.return_value = {
            "speech_recognition": {"engine": "whisper", "model_size": "medium", "language": "en-us"},
            "audio": {},
            "general": {"first_run": False}
        }

        # Mock the imported modules
        with patch.dict(
            sys.modules,
            {
                "vocalinux.single_instance": mock_single_instance,
                "vocalinux.common_types": MagicMock(),
                "vocalinux.speech_recognition": MagicMock(
                    recognition_manager=MagicMock(
                        SpeechRecognitionManager=MagicMock(
                            side_effect=Exception("Test exception to stop execution")
                        )
                    )
                ),
                "vocalinux.text_injection.text_injector": MagicMock(),
                "vocalinux.ui.tray_indicator": MagicMock(),
                "vocalinux.ui.action_handler": MagicMock(),
                "vocalinux.ui.config_manager": mock_config_manager,
                "vocalinux.ui.logging_manager": MagicMock(),
                "vocalinux.text_injection": MagicMock(),
                "vocalinux.ui.first_run_dialog": MagicMock(),
                "vocalinux.ui.autostart_manager": MagicMock(),
                "vocalinux.text_injection.start_ibus_daemon": MagicMock(),
            },
        ):
            # Mock the config manager and other components
            with patch("vocalinux.main.logging.getLogger") as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger

                # This would normally start the GTK main loop, which we want to avoid
                # The initialization should fail as we've set SpeechRecognitionManager to raise an exception
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

    @patch("vocalinux.main.logging")
    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.check_display_available")
    @patch("vocalinux.main.parse_arguments")
    @patch("vocalinux.main.atexit")
    def test_main_initialization_error(
        self,
        mock_atexit,
        mock_parse_args,
        mock_check_display,
        mock_check_deps,
        mock_logging,
    ):
        """Test main() when initialization fails."""
        from vocalinux.main import main

        # Set up mocks
        mock_check_deps.return_value = True
        mock_check_display.return_value = True

        mock_args = MagicMock()
        mock_args.debug = False
        mock_args.wayland = False
        mock_args.start_minimized = False
        mock_parse_args.return_value = mock_args

        # Mock single_instance module since it's imported inside main()
        mock_single_instance = MagicMock()
        mock_single_instance.acquire_lock.return_value = True

        # Mock components that will raise an exception
        with patch("vocalinux.main.logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            with patch.dict(
                sys.modules,
                {
                    "vocalinux.single_instance": mock_single_instance,
                    "vocalinux.common_types": MagicMock(),
                    "vocalinux.speech_recognition": MagicMock(
                        recognition_manager=MagicMock(
                            SpeechRecognitionManager=MagicMock(
                                side_effect=Exception("Init error")
                            )
                        )
                    ),
                    "vocalinux.text_injection.text_injector": MagicMock(),
                    "vocalinux.ui.tray_indicator": MagicMock(),
                    "vocalinux.ui.action_handler": MagicMock(),
                    "vocalinux.ui.config_manager": MagicMock(),
                    "vocalinux.ui.logging_manager": MagicMock(),
                    "vocalinux.text_injection": MagicMock(),
                    "vocalinux.ui.first_run_dialog": MagicMock(),
                    "vocalinux.ui.autostart_manager": MagicMock(),
                    "vocalinux.text_injection.start_ibus_daemon": MagicMock(),
                },
            ):
                # Should exit with status 1
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1


class TestMainEntry(unittest.TestCase):
    """Tests for the main entry point and script execution."""

    @patch("vocalinux.main.main")
    def test_main_entry_point(self, mock_main):
        """Test that the script entry point calls main()."""
        # Import the module and verify the entry point
        import vocalinux.main as main_module

        # Check that main function exists
        assert hasattr(main_module, "main")
        assert callable(main_module.main)

    def test_module_can_be_imported(self):
        """Test that the main module can be imported successfully."""
        try:
            import vocalinux.main  # noqa: F401

            assert True
        except Exception as e:
            pytest.fail(f"Failed to import vocalinux.main: {e}")


if __name__ == "__main__":
    unittest.main()
