"""
Tests for system tray indicator functionality.
"""

import os
import unittest
from unittest.mock import MagicMock, patch


# We need to patch modules BEFORE they are imported
@patch("gi.repository.AppIndicator3", MagicMock())
@patch("gi.repository.Gtk", MagicMock())
@patch("gi.repository.GLib", MagicMock())
@patch("gi.repository.GObject", MagicMock())
@patch("gi.repository.GdkPixbuf", MagicMock())
@patch("gi.require_version", MagicMock())
class TestTrayIndicator(unittest.TestCase):
    """Test cases for the tray indicator."""

    def setUp(self):
        """Set up test environment before each test."""
        # Patch threading module before any imports
        self.thread_patcher = patch("threading.Thread")
        self.mock_thread_class = self.thread_patcher.start()

        # Make Thread.start() actually run the target function
        def fake_start(self_thread):
            if self_thread.target:
                args = self_thread.args or ()
                kwargs = self_thread.kwargs or {}
                self_thread.target(*args, **kwargs)

        self.mock_thread_class.return_value.start = fake_start

        # Patch the pynput keyboard module
        self.keyboard_patcher = patch("vocalinux.ui.keyboard_shortcuts.keyboard", create=True)
        self.mock_keyboard = self.keyboard_patcher.start()

        # Patch keyboard module's KEYBOARD_AVAILABLE constant before importing
        self.keyboard_available_patcher = patch(
            "vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE", True
        )
        self.mock_keyboard_available = self.keyboard_available_patcher.start()

        # Import here after patching for proper mocking
        from vocalinux.common_types import RecognitionState

        # Setup mock keyboard listener that works properly
        self.mock_listener = MagicMock()
        self.mock_listener.is_alive.return_value = True
        self.mock_keyboard.Listener.return_value = self.mock_listener

        # Define some fake keyboard keys for testing
        self.mock_keyboard.Key = MagicMock()
        self.mock_keyboard.Key.ctrl = "ctrl"
        self.mock_keyboard.Key.ctrl_l = "ctrl_l"
        self.mock_keyboard.Key.ctrl_r = "ctrl_r"

        # Create our mock for the shortcut manager
        self.mock_ksm = MagicMock()

        # Patch keyboard shortcuts manager to return our mock
        self.ksm_patcher = patch("vocalinux.ui.keyboard_shortcuts.KeyboardShortcutManager")
        self.mock_ksm_class = self.ksm_patcher.start()
        self.mock_ksm_class.return_value = self.mock_ksm

        # Patch the settings dialog BEFORE importing TrayIndicator
        self.patcher_settings_dialog = patch("vocalinux.ui.tray_indicator.SettingsDialog")
        self.mock_settings_dialog_class = self.patcher_settings_dialog.start()
        self.mock_settings_dialog = MagicMock()
        self.mock_settings_dialog_class.return_value = self.mock_settings_dialog

        # Now import TrayIndicator after all patches are applied
        from vocalinux.ui.tray_indicator import TrayIndicator

        self.RecognitionState = RecognitionState

        # Create mocks for dependencies
        self.mock_speech_engine = MagicMock()
        self.mock_speech_engine.state = RecognitionState.IDLE
        self.mock_text_injector = MagicMock()
        self.mock_config_manager = MagicMock()  # Mock the ConfigManager

        # Patch specific methods we need to control
        self.patcher_glib_idle = patch("gi.repository.GLib.idle_add")
        self.mock_glib_idle = self.patcher_glib_idle.start()
        # Make idle_add execute the function directly
        self.mock_glib_idle.side_effect = lambda func, *args: func(*args) or False

        # Patch os path exists to return True for icon files
        self.patcher_path_exists = patch("os.path.exists", return_value=True)
        self.mock_path_exists = self.patcher_path_exists.start()

        # Patch os.listdir to return mock icon files
        self.patcher_listdir = patch(
            "os.listdir",
            return_value=[
                "vocalinux.svg",
                "vocalinux-microphone-off.svg",
                "vocalinux-microphone.svg",
                "vocalinux-microphone-process.svg",
            ],
        )
        self.mock_listdir = self.patcher_listdir.start()

        # Patch ConfigManager constructor
        self.patcher_config_manager = patch("vocalinux.ui.tray_indicator.ConfigManager")
        self.mock_config_manager_class = self.patcher_config_manager.start()
        self.mock_config_manager_class.return_value = self.mock_config_manager

        # Create the indicator with our mocked dependencies
        self.tray_indicator = TrayIndicator(
            speech_engine=self.mock_speech_engine,
            text_injector=self.mock_text_injector,
        )

        # Manually set the shortcut_manager to our mock
        # This ensures the tray indicator uses our mock instead of creating a new one
        self.tray_indicator.shortcut_manager = self.mock_ksm

    def tearDown(self):
        """Clean up test environment after each test."""
        self.patcher_glib_idle.stop()
        self.patcher_path_exists.stop()
        self.patcher_listdir.stop()
        self.patcher_config_manager.stop()
        self.patcher_settings_dialog.stop()
        self.thread_patcher.stop()
        self.ksm_patcher.stop()
        self.keyboard_available_patcher.stop()
        self.keyboard_patcher.stop()

        # Ensure that the keyboard shortcut manager is stopped
        if hasattr(self, "tray_indicator") and hasattr(self.tray_indicator, "shortcut_manager"):
            self.tray_indicator.shortcut_manager.stop()

    def test_initialization(self):
        """Test initialization of the tray indicator."""
        # Verify initialization
        self.assertEqual(self.tray_indicator.speech_engine, self.mock_speech_engine)
        self.assertEqual(self.tray_indicator.text_injector, self.mock_text_injector)

        # Verify callback was registered
        self.mock_speech_engine.register_state_callback.assert_called_once()

        # NOTE: We're manually setting shortcut_manager after initialization, so we don't
        # verify register_toggle_callback or start being called

    def test_toggle_recognition_from_idle(self):
        """Test toggling recognition state from IDLE."""
        # Set state to IDLE
        self.mock_speech_engine.state = self.RecognitionState.IDLE

        # Call toggle method
        self.tray_indicator._toggle_recognition()

        # Verify start_recognition was called
        self.mock_speech_engine.start_recognition.assert_called_once()
        self.mock_speech_engine.stop_recognition.assert_not_called()

    def test_toggle_recognition_from_listening(self):
        """Test toggling recognition state from LISTENING."""
        # Set state to LISTENING
        self.mock_speech_engine.state = self.RecognitionState.LISTENING

        # Call toggle method
        self.tray_indicator._toggle_recognition()

        # Verify stop_recognition was called
        self.mock_speech_engine.stop_recognition.assert_called_once()
        self.mock_speech_engine.start_recognition.assert_not_called()

    def test_toggle_recognition_from_processing(self):
        """Test toggling recognition state from PROCESSING."""
        # Set state to PROCESSING
        self.mock_speech_engine.state = self.RecognitionState.PROCESSING

        # Call toggle method
        self.tray_indicator._toggle_recognition()

        # Verify stop_recognition was called
        self.mock_speech_engine.stop_recognition.assert_called_once()
        self.mock_speech_engine.start_recognition.assert_not_called()

    def test_on_start_clicked(self):
        """Test start button click handler."""
        # Reset mock
        self.mock_speech_engine.start_recognition.reset_mock()

        # Call the start handler
        self.tray_indicator._on_start_clicked(None)

        # Verify start_recognition was called
        self.mock_speech_engine.start_recognition.assert_called_once()

    def test_on_stop_clicked(self):
        """Test stop button click handler."""
        # Reset mock
        self.mock_speech_engine.stop_recognition.reset_mock()

        # Call the stop handler
        self.tray_indicator._on_stop_clicked(None)

        # Verify stop_recognition was called
        self.mock_speech_engine.stop_recognition.assert_called_once()

    def test_on_recognition_state_changed(self):
        """Test state change callback."""
        # Create patch for _update_ui to prevent any actual UI updates
        with patch.object(self.tray_indicator, "_update_ui") as mock_update_ui:
            # Override GLib.idle_add to execute functions directly
            self.mock_glib_idle.side_effect = lambda func, *args: func(*args) or False

            # Call state change callback with each state
            for state in self.RecognitionState:
                # Reset mock
                mock_update_ui.reset_mock()

                # Call callback
                self.tray_indicator._on_recognition_state_changed(state)

                # Verify update_ui was called with correct state
                mock_update_ui.assert_called_once_with(state)

    def test_quit(self):
        """Test quit functionality."""
        # Patch Gtk.main_quit
        with patch("gi.repository.Gtk.main_quit") as mock_main_quit:
            # Make sure it doesn't actually try to quit GTK
            mock_main_quit.side_effect = lambda: None

            # Call quit method
            self.tray_indicator._quit()

            # Verify shortcuts manager stopped and GTK main loop exited
            self.mock_ksm.stop.assert_called_once()
            mock_main_quit.assert_called_once()

    def test_signal_handler(self):
        """Test signal handler."""
        # Create a patch for _quit
        with patch.object(self.tray_indicator, "_quit") as mock_quit:
            # Reset mock for idle_add to clear previous calls
            self.mock_glib_idle.reset_mock()

            # Call signal handler
            self.tray_indicator._signal_handler(15, None)  # 15 is SIGTERM

            # Verify idle_add was called with _quit
            self.mock_glib_idle.assert_called_once_with(mock_quit)

    def test_run(self):
        """Test run method."""
        # Patch signal.signal and Gtk.main
        with patch("signal.signal") as mock_signal, patch("gi.repository.Gtk.main") as mock_main:
            # Configure mock_main to return immediately instead of blocking
            mock_main.side_effect = lambda: None

            # Call run method
            self.tray_indicator.run()

            # Verify signal handlers were set and main loop started
            self.assertEqual(mock_signal.call_count, 2)  # SIGINT and SIGTERM
            mock_main.assert_called_once()

    def test_settings_callback(self):
        """Test settings callback."""
        # Reset mocks
        self.mock_settings_dialog_class.reset_mock()
        self.mock_settings_dialog.reset_mock()

        # Call the settings handler
        self.tray_indicator._on_settings_clicked(None)

        # Verify SettingsDialog was created with correct parameters
        self.mock_settings_dialog_class.assert_called_once()
        # Verify dialog was shown
        self.mock_settings_dialog.show.assert_called_once()

    def test_about_dialog(self):
        """Test about dialog creation."""
        # Patch AboutDialog class and pixbuf
        with patch("gi.repository.Gtk.AboutDialog") as mock_about_dialog_class, patch(
            "gi.repository.GdkPixbuf.Pixbuf.new_from_file"
        ) as mock_pixbuf_new, patch(
            "gi.repository.GdkPixbuf.Pixbuf.scale_simple"
        ) as mock_pixbuf_scale:
            # Create mock for dialog instance
            mock_about_dialog = MagicMock()
            mock_about_dialog_class.return_value = mock_about_dialog

            # Make sure dialog run method doesn't block
            mock_about_dialog.run.side_effect = lambda: None

            # Mock pixbuf creation to prevent actual file operations
            mock_pixbuf = MagicMock()
            mock_pixbuf_new.return_value = mock_pixbuf
            mock_pixbuf_scale.return_value = mock_pixbuf

            # Call about handler
            self.tray_indicator._on_about_clicked(None)

            # Verify dialog was configured and shown
            mock_about_dialog.set_program_name.assert_called_with("Vocalinux")
            mock_about_dialog.run.assert_called_once()
            mock_about_dialog.destroy.assert_called_once()
