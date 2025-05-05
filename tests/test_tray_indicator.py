"""
Tests for system tray indicator functionality.
"""

import os
import signal
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest

# Import mock GTK classes
from tests.mock_gtk import MockAppIndicator, MockGLib, MockGtk
from vocalinux.common_types import RecognitionState

# Set up environment variables for testing
os.environ["VOCALINUX_ENV"] = "testing"
os.environ["VOCALINUX_ENABLE_GUI"] = "true"

# Create mock GTK instances
mock_gtk = MockGtk()
mock_glib = MockGLib()
mock_app_indicator = MockAppIndicator()

# Create module structure for GTK imports
mock_gi = MagicMock()
mock_gi_repository = MagicMock()
mock_gi_repository.Gtk = mock_gtk
mock_gi_repository.GLib = mock_glib
mock_gi_repository.AppIndicator3 = mock_app_indicator
mock_gi_repository.GObject = MagicMock()
mock_gi_repository.GdkPixbuf = MagicMock()

# Patch sys.modules
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = mock_gi_repository
sys.modules["gi.repository.Gtk"] = mock_gtk
sys.modules["gi.repository.GLib"] = mock_glib
sys.modules["gi.repository.AppIndicator3"] = mock_app_indicator
sys.modules["gi.repository.GObject"] = mock_gi_repository.GObject
sys.modules["gi.repository.GdkPixbuf"] = mock_gi_repository.GdkPixbuf

# Set up mock keyboard shortcut manager
keyboard_shortcut_manager_mock = MagicMock()
keyboard_shortcut_manager_mock.keyboard_available = True
keyboard_shortcut_manager_mock.register_toggle_callback = MagicMock()
keyboard_shortcut_manager_mock.start = MagicMock()
keyboard_shortcut_manager_mock.stop = MagicMock()


class TestTrayIndicator(unittest.TestCase):
    """Test cases for the tray indicator."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mocks for dependencies
        self.mock_speech_engine = MagicMock()
        self.mock_text_injector = MagicMock()

        # Reset keyboard shortcut manager mock
        keyboard_shortcut_manager_mock.reset_mock()

        # Set up patches that need cleanup
        self.patches = [
            patch(
                "vocalinux.ui.tray_indicator.environment",
                MagicMock(is_feature_available=MagicMock(return_value=True)),
            ),
            patch(
                "vocalinux.ui.tray_indicator.find_resources_dir",
                MagicMock(return_value="/mock/resources/dir"),
            ),
            patch("os.path.exists", MagicMock(return_value=True)),
            patch("os.makedirs", MagicMock()),
            patch("os.listdir", MagicMock(return_value=[])),
            patch("signal.signal", MagicMock()),
            patch(
                "vocalinux.ui.keyboard_shortcuts.KeyboardShortcutManager",
                return_value=keyboard_shortcut_manager_mock,
            ),
        ]

        # Start all patches
        for p in self.patches:
            p.start()

        # Import tray indicator components after mocking is set up
        from vocalinux.ui.tray_indicator import TrayIndicator

        # Create tray indicator
        self.tray_indicator = TrayIndicator(
            speech_engine=self.mock_speech_engine, text_injector=self.mock_text_injector
        )

        # Make sure GUI is available
        self.tray_indicator.gui_available = True

    def tearDown(self):
        """Clean up test environment after each test."""
        # Stop all patches
        for p in self.patches:
            p.stop()

    @pytest.mark.timeout(30)
    def test_initialization(self):
        """Test initialization of the tray indicator."""
        # Verify initialization
        self.assertEqual(self.tray_indicator.speech_engine, self.mock_speech_engine)
        self.assertEqual(self.tray_indicator.text_injector, self.mock_text_injector)

        # Verify callback was registered
        self.mock_speech_engine.register_state_callback.assert_called()

        # Verify shortcut manager was configured
        keyboard_shortcut_manager_mock.register_toggle_callback.assert_called_once()
        keyboard_shortcut_manager_mock.start.assert_called_once()

    @pytest.mark.timeout(30)
    def test_toggle_recognition_from_idle(self):
        """Test toggling recognition state from IDLE."""
        # Set state to IDLE
        self.mock_speech_engine.state = RecognitionState.IDLE

        # Call toggle method
        self.tray_indicator._toggle_recognition()

        # Verify start_recognition was called
        self.mock_speech_engine.start_recognition.assert_called_once()
        self.mock_speech_engine.stop_recognition.assert_not_called()

    @pytest.mark.timeout(30)
    def test_toggle_recognition_from_listening(self):
        """Test toggling recognition state from LISTENING."""
        # Set state to LISTENING
        self.mock_speech_engine.state = RecognitionState.LISTENING

        # Call toggle method
        self.tray_indicator._toggle_recognition()

        # Verify stop_recognition was called
        self.mock_speech_engine.stop_recognition.assert_called_once()
        self.mock_speech_engine.start_recognition.assert_not_called()

    @pytest.mark.timeout(30)
    def test_toggle_recognition_from_processing(self):
        """Test toggling recognition state from PROCESSING."""
        # Set state to PROCESSING
        self.mock_speech_engine.state = RecognitionState.PROCESSING

        # Call toggle method
        self.tray_indicator._toggle_recognition()

        # Verify stop_recognition was called
        self.mock_speech_engine.stop_recognition.assert_called_once()
        self.mock_speech_engine.start_recognition.assert_not_called()

    @pytest.mark.timeout(30)
    def test_on_start_clicked(self):
        """Test start button click handler."""
        # Reset mock
        self.mock_speech_engine.start_recognition.reset_mock()

        # Call the start handler
        self.tray_indicator._on_start_clicked(None)

        # Verify start_recognition was called
        self.mock_speech_engine.start_recognition.assert_called_once()

    @pytest.mark.timeout(30)
    def test_on_stop_clicked(self):
        """Test stop button click handler."""
        # Reset mock
        self.mock_speech_engine.stop_recognition.reset_mock()

        # Call the stop handler
        self.tray_indicator._on_stop_clicked(None)

        # Verify stop_recognition was called
        self.mock_speech_engine.stop_recognition.assert_called_once()

    @pytest.mark.timeout(30)
    def test_on_recognition_state_changed(self):
        """Test state change callback."""
        # Create a mock for _update_ui
        update_ui_mock = MagicMock()

        # Store original method and replace it
        original_update_ui = self.tray_indicator._update_ui
        self.tray_indicator._update_ui = update_ui_mock

        try:
            # Call the handler with our mocked GLib.idle_add
            with patch.object(
                MockGLib, "idle_add", side_effect=lambda func, *args: func(*args)
            ):
                self.tray_indicator._on_recognition_state_changed(RecognitionState.IDLE)

                # Verify _update_ui was called
                update_ui_mock.assert_called_once_with(RecognitionState.IDLE)
        finally:
            # Restore original method
            self.tray_indicator._update_ui = original_update_ui

    @pytest.mark.timeout(30)
    def test_quit(self):
        """Test quit functionality."""
        # Reset mock
        keyboard_shortcut_manager_mock.stop.reset_mock()

        # Create a mock for Gtk.main_quit
        main_quit_mock = MagicMock()

        # Store original and replace
        original_main_quit = mock_gtk.main_quit
        mock_gtk.main_quit = main_quit_mock

        try:
            # Call quit
            self.tray_indicator._quit()

            # Verify shortcut manager was stopped
            keyboard_shortcut_manager_mock.stop.assert_called_once()

            # Verify Gtk.main_quit was called
            main_quit_mock.assert_called_once()
        finally:
            # Restore original
            mock_gtk.main_quit = original_main_quit

    @pytest.mark.timeout(30)
    def test_signal_handler(self):
        """Test signal handler."""
        # Create mock _quit method
        quit_mock = MagicMock()

        # Store original and replace
        original_quit = self.tray_indicator._quit
        self.tray_indicator._quit = quit_mock

        try:
            # Call signal handler with our mocked GLib.idle_add
            with patch.object(
                MockGLib, "idle_add", side_effect=lambda func, *args: func(*args)
            ):
                self.tray_indicator._signal_handler(15, None)  # SIGTERM

                # Verify _quit was called
                quit_mock.assert_called_once()
        finally:
            # Restore original
            self.tray_indicator._quit = original_quit

    @pytest.mark.timeout(30)
    def test_run(self):
        """Test run method."""
        # Mock signal.signal
        with patch("signal.signal") as mock_signal:
            # Call run method
            self.tray_indicator.run()

            # Verify signal handlers were set up
            self.assertEqual(mock_signal.call_count, 2)  # SIGINT and SIGTERM

    @pytest.mark.timeout(30)
    def test_settings_callback(self):
        """Test settings callback."""
        # Test that it doesn't raise exceptions
        self.tray_indicator._on_settings_clicked(None)

    @pytest.mark.skip("GUI not available")
    def test_about_dialog(self):
        """Test about dialog creation."""
        # Create a dialog instance
        about_dialog = mock_gtk.AboutDialog()

        # Patch AboutDialog.new() at the module level where it's used
        with patch(
            "vocalinux.ui.tray_indicator.Gtk.AboutDialog.new", return_value=about_dialog
        ):
            # Also patch environment to ensure GUI is available
            with patch(
                "vocalinux.ui.tray_indicator.environment.is_feature_available",
                return_value=True,
            ):
                # Call the about handler
                self.tray_indicator._on_about_clicked(None)

        # Verify dialog was configured correctly
        self.assertEqual(about_dialog.program_name, "Vocalinux")
        self.assertEqual(about_dialog.version, "0.1.0")
        self.assertEqual(
            about_dialog.comments, "A seamless voice dictation system for Ubuntu"
        )
        self.assertEqual(
            about_dialog.website, "https://github.com/jatinkrmalik/vocalinux"
        )
        self.assertEqual(about_dialog.website_label, "GitHub Repository")
        self.assertEqual(about_dialog.copyright, "© 2025 | @jatinkrmalik")
        self.assertEqual(about_dialog.authors, ["Jatin K Malik"])
        self.assertEqual(about_dialog.license_type, mock_gtk.License.GPL_3_0)

    @pytest.mark.timeout(30)
    def test_headless_mode(self):
        """Test tray indicator in headless mode (when GUI is not available)."""
        # Create a custom environment mock that disables GUI
        headless_env_mock = MagicMock()
        headless_env_mock.is_feature_available = MagicMock(return_value=False)

        # Reset sys.modules cache for tray_indicator to force reimport
        if "vocalinux.ui.tray_indicator" in sys.modules:
            del sys.modules["vocalinux.ui.tray_indicator"]

        # Create a fresh TrayIndicator with our patched environment
        with patch("vocalinux.utils.environment.environment", headless_env_mock):
            # Import after patching to ensure our mock takes effect
            from vocalinux.ui.tray_indicator import TrayIndicator

            headless_indicator = TrayIndicator(
                speech_engine=self.mock_speech_engine,
                text_injector=self.mock_text_injector,
            )

            # Verify it's in headless mode
            self.assertFalse(headless_indicator.gui_available)
