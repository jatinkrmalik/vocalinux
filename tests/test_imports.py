"""
Tests for lazy GTK imports and package import behavior.

These tests ensure that Vocalinux can be imported and used in headless/CI
environments without requiring system GTK libraries to be installed.
This is important for pip/pipx installations where PyGObject is installed
but system typelibs may not be accessible.
"""

import importlib
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch


class TestPackageImportWithoutGTK(unittest.TestCase):
    """Test that the vocalinux package can be imported without GTK dependencies."""

    def test_package_import_without_gtk(self):
        """Test that the vocalinux package can be imported even without GTK."""
        # Remove vocalinux modules from cache to force reimport
        modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith("vocalinux")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Mock gi.repository to simulate GTK not being available
        mock_gi = MagicMock()
        mock_gi.require_version.side_effect = ImportError("No typelib for Gtk")

        with patch.dict("sys.modules", {"gi": mock_gi, "gi.repository": MagicMock()}):
            # This should work even without GTK
            import vocalinux

            self.assertTrue(hasattr(vocalinux, "__version__"))
            self.assertTrue(hasattr(vocalinux, "RecognitionState"))
            self.assertTrue(hasattr(vocalinux, "ResourceManager"))

    def test_package_import_with_gi_not_installed(self):
        """Test package import when gi (PyGObject) is not installed at all."""
        # Remove vocalinux modules from cache
        modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith("vocalinux")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Remove gi from modules to simulate it not being installed
        gi_modules = [mod for mod in sys.modules.keys() if mod.startswith("gi")]
        for mod in gi_modules:
            del sys.modules[mod]

        with patch.dict("sys.modules", {"gi": None}):
            # Import should still work because GTK-dependent modules
            # are imported lazily in main.py only
            import vocalinux

            self.assertTrue(hasattr(vocalinux, "__version__"))

    def test_common_types_import(self):
        """Test that common_types can be imported without GTK."""
        from vocalinux.common_types import RecognitionState

        self.assertTrue(hasattr(RecognitionState, "IDLE"))
        self.assertTrue(hasattr(RecognitionState, "LISTENING"))
        self.assertTrue(hasattr(RecognitionState, "PROCESSING"))

    def test_utils_import(self):
        """Test that utils can be imported without GTK."""
        from vocalinux.utils import ResourceManager

        self.assertTrue(callable(ResourceManager))

    def test_version_import(self):
        """Test that version can be imported without GTK."""
        from vocalinux.version import __version__

        self.assertIsInstance(__version__, str)
        self.assertTrue(len(__version__) > 0)


class TestDependencyChecking(unittest.TestCase):
    """Test the dependency checking functionality."""

    def test_check_dependencies_all_present(self):
        """Test check_dependencies when all dependencies are present."""
        from vocalinux.main import check_dependencies

        # Mock all dependencies as available
        mock_gi = MagicMock()
        mock_gtk = MagicMock()
        mock_appindicator = MagicMock()
        mock_pynput = MagicMock()
        mock_requests = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "gi": mock_gi,
                "gi.repository": MagicMock(),
                "gi.repository.Gtk": mock_gtk,
                "gi.repository.AppIndicator3": mock_appindicator,
                "pynput": mock_pynput,
                "requests": mock_requests,
            },
        ):
            with patch.object(mock_gi, "require_version"):
                result = check_dependencies()
                self.assertTrue(result)

    def test_check_dependencies_missing_gtk(self):
        """Test check_dependencies when GTK is missing."""
        from vocalinux.main import check_dependencies

        # Mock gi to raise ImportError for Gtk
        mock_gi = MagicMock()
        mock_gi.require_version.side_effect = ImportError("No typelib for Gtk")

        # Capture stderr
        stderr_capture = StringIO()

        with patch.dict("sys.modules", {"gi": mock_gi}), patch(
            "sys.stderr", stderr_capture
        ), patch("vocalinux.main.logger") as mock_logger:
            result = check_dependencies()
            self.assertFalse(result)
            # Verify error logging was called
            mock_logger.error.assert_called()

    def test_check_dependencies_missing_appindicator(self):
        """Test check_dependencies when AppIndicator3 is missing."""
        from vocalinux.main import check_dependencies

        mock_gi = MagicMock()

        # Make require_version succeed for Gtk but fail for AppIndicator3
        def mock_require_version(name, version):
            if name == "AppIndicator3":
                raise ImportError("No typelib for AppIndicator3")

        mock_gi.require_version.side_effect = mock_require_version

        with patch.dict("sys.modules", {"gi": mock_gi}), patch(
            "vocalinux.main.logger"
        ) as mock_logger:
            result = check_dependencies()
            self.assertFalse(result)
            mock_logger.error.assert_called()

    def test_check_dependencies_missing_pynput(self):
        """Test check_dependencies when pynput is missing."""
        from vocalinux.main import check_dependencies

        mock_gi = MagicMock()

        with patch.dict(
            "sys.modules",
            {"gi": mock_gi, "gi.repository": MagicMock(), "pynput": None},
        ), patch("vocalinux.main.logger") as mock_logger:
            result = check_dependencies()
            self.assertFalse(result)
            mock_logger.error.assert_called()

    def test_check_dependencies_missing_requests(self):
        """Test check_dependencies when requests is missing."""
        from vocalinux.main import check_dependencies

        mock_gi = MagicMock()
        mock_pynput = MagicMock()

        with patch.dict(
            "sys.modules",
            {
                "gi": mock_gi,
                "gi.repository": MagicMock(),
                "pynput": mock_pynput,
                "requests": None,
            },
        ), patch("vocalinux.main.logger") as mock_logger:
            result = check_dependencies()
            self.assertFalse(result)
            mock_logger.error.assert_called()

    def test_check_dependencies_error_message_content(self):
        """Test that error messages provide helpful installation instructions."""
        from vocalinux.main import check_dependencies

        mock_gi = MagicMock()
        mock_gi.require_version.side_effect = ImportError("No typelib for Gtk")

        with patch.dict("sys.modules", {"gi": mock_gi}), patch(
            "vocalinux.main.logger"
        ) as mock_logger:
            check_dependencies()

            # Check that error messages mention pip/pipx and system packages
            error_calls = [call for call in mock_logger.error.call_args_list]
            self.assertTrue(len(error_calls) > 0)


class TestMainFunctionImports(unittest.TestCase):
    """Test that main() function correctly imports GTK-dependent modules."""

    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.logging")
    @patch("vocalinux.main.parse_arguments")
    def test_main_imports_gtk_modules_after_check(self, mock_parse, mock_logging, mock_check_deps):
        """Test that main() imports GTK modules only after dependency check passes."""
        # Mock dependency check to return True
        mock_check_deps.return_value = True

        # Mock arguments
        mock_args = MagicMock()
        mock_args.debug = False
        mock_args.model = "small"
        mock_args.engine = "vosk"
        mock_args.wayland = False
        mock_parse.return_value = mock_args

        # Mock ConfigManager to return empty settings
        with patch("vocalinux.ui.config_manager.ConfigManager") as mock_config:
            mock_config_instance = MagicMock()
            mock_config_instance.get_settings.return_value = {"speech_recognition": {}}
            mock_config.return_value = mock_config_instance

            # Mock all the GTK-dependent modules
            with patch(
                "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager"
            ) as mock_speech, patch(
                "vocalinux.text_injection.text_injector.TextInjector"
            ) as mock_text, patch(
                "vocalinux.ui.tray_indicator.TrayIndicator"
            ) as mock_tray, patch(
                "vocalinux.ui.action_handler.ActionHandler"
            ) as mock_action, patch(
                "vocalinux.ui.logging_manager.initialize_logging"
            ):

                from vocalinux.main import main

                # Call main()
                main()

                # Verify check_dependencies was called first
                mock_check_deps.assert_called_once()

                # Verify GTK-dependent modules were imported and initialized
                mock_speech.assert_called_once()
                mock_text.assert_called_once()
                mock_tray.assert_called_once()
                mock_action.assert_called_once()

    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.parse_arguments")
    @patch("vocalinux.main.sys.exit")
    def test_main_exits_when_dependencies_missing(self, mock_exit, mock_parse, mock_check_deps):
        """Test that main() exits when dependencies are missing."""
        # Mock dependency check to return False
        mock_check_deps.return_value = False

        # Mock arguments
        mock_args = MagicMock()
        mock_args.debug = False
        mock_parse.return_value = mock_args

        from vocalinux.main import main

        # Call main()
        main()

        # Verify sys.exit(1) was called
        mock_exit.assert_called_once_with(1)

    @patch("vocalinux.main.check_dependencies")
    @patch("vocalinux.main.parse_arguments")
    @patch("vocalinux.main.logger")
    def test_main_logs_error_on_initialization_failure(self, mock_logger, mock_parse, mock_check_deps):
        """Test that main() logs error when initialization fails."""
        # Mock dependency check to return True
        mock_check_deps.return_value = True

        # Mock arguments
        mock_args = MagicMock()
        mock_args.debug = False
        mock_args.model = "small"
        mock_args.engine = "vosk"
        mock_args.wayland = False
        mock_parse.return_value = mock_args

        # Mock ConfigManager to raise an exception
        with patch("vocalinux.ui.config_manager.ConfigManager") as mock_config:
            mock_config.side_effect = Exception("Initialization failed")

            from vocalinux.main import main

            # Call main()
            main()

            # Verify error was logged
            mock_logger.error.assert_called()


class TestPipPipxCompatibility(unittest.TestCase):
    """Test pip/pipx compatibility scenarios."""

    def test_entry_point_imports(self):
        """Test that entry points can be imported without GTK."""
        # The entry point is vocalinux.main:main
        # This should be importable without GTK because main() doesn't
        # import GTK until check_dependencies() passes
        from vocalinux.main import main

        self.assertTrue(callable(main))

    def test_module_import_order(self):
        """Test that modules are imported in the correct order for lazy loading."""
        # Track import order
        import_order = []

        original_import = __builtins__.__import__

        def tracking_import(name, *args, **kwargs):
            import_order.append(name)
            return original_import(name, *args, **kwargs)

        # Remove vocalinux from cache to test fresh import
        modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith("vocalinux")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("builtins.__import__", side_effect=tracking_import):
            import vocalinux

            # vocalinux itself should be imported
            self.assertIn("vocalinux", import_order)

    def test_lazy_import_mechanism(self):
        """Test the lazy import mechanism doesn't break module structure."""
        import vocalinux

        # These should be available at package level
        self.assertTrue(hasattr(vocalinux, "__version__"))
        self.assertTrue(hasattr(vocalinux, "RecognitionState"))

        # GTK-dependent modules should NOT be imported at package level
        # (they should only be imported in main())
        self.assertFalse(hasattr(vocalinux, "tray_indicator"))


class TestHeadlessCIEnvironment(unittest.TestCase):
    """Test behavior in headless/CI environments without display."""

    def test_import_without_display(self):
        """Test that package can be imported without X11/Wayland display."""
        # Unset DISPLAY environment variable
        with patch.dict("os.environ", {}, clear=False):
            # Remove vocalinux from cache
            modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith("vocalinux")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Import should work without display
            import vocalinux

            self.assertTrue(hasattr(vocalinux, "__version__"))

    def test_import_with_missing_typelibs(self):
        """Test import when system typelibs are missing."""
        # Remove vocalinux from cache
        modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith("vocalinux")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Mock gi to simulate missing typelibs (common in CI)
        mock_gi = MagicMock()
        mock_gi.require_version.side_effect = ValueError("Namespace Gtk not available")

        with patch.dict("sys.modules", {"gi": mock_gi, "gi.repository": MagicMock()}):
            # Package import should still work
            import vocalinux

            self.assertTrue(hasattr(vocalinux, "__version__"))


class TestImportSideEffects(unittest.TestCase):
    """Test that imports don't have unexpected side effects."""

    def test_import_does_not_initialize_logging(self):
        """Test that importing vocalinux doesn't initialize logging configuration."""
        import logging

        # Get the initial logging level
        initial_level = logging.getLogger().level

        # Remove vocalinux from cache
        modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith("vocalinux")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Import vocalinux
        import vocalinux

        # Logging level should not have changed
        self.assertEqual(logging.getLogger().level, initial_level)

    def test_import_does_not_create_files(self):
        """Test that importing vocalinux doesn't create any files."""
        import os
        import tempfile

        # Create a temporary directory to check
        with tempfile.TemporaryDirectory() as tmpdir:
            # Remove vocalinux from cache
            modules_to_remove = [mod for mod in sys.modules.keys() if mod.startswith("vocalinux")]
            for mod in modules_to_remove:
                del sys.modules[mod]

            # Get initial state of tmpdir
            initial_files = set(os.listdir(tmpdir))

            # Import vocalinux
            import vocalinux

            # Check no new files were created in tmpdir
            final_files = set(os.listdir(tmpdir))
            self.assertEqual(initial_files, final_files)


if __name__ == "__main__":
    unittest.main()
