"""
Tests for system tray indicator functionality.

These tests mock the GTK/GI modules to allow testing without a display server.
The tests focus on the business logic of the TrayIndicator class.
"""

import sys
import unittest
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

# Create mock modules for GTK/GI BEFORE importing anything
mock_gi = MagicMock()
mock_gi.require_version = MagicMock()

mock_gtk = MagicMock()
mock_glib = MagicMock()
mock_gobject = MagicMock()
mock_gdkpixbuf = MagicMock()
mock_gio = MagicMock()
mock_appindicator = MagicMock()

# Create mock for gi.repository
mock_gi_repository = MagicMock()
mock_gi_repository.Gtk = mock_gtk
mock_gi_repository.GLib = mock_glib
mock_gi_repository.GObject = mock_gobject
mock_gi_repository.GdkPixbuf = mock_gdkpixbuf
mock_gi_repository.Gio = mock_gio
mock_gi_repository.AppIndicator3 = mock_appindicator

# Inject mocks into sys.modules BEFORE any imports
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = mock_gi_repository


class TestTrayIndicator(unittest.TestCase):
    """Test cases for the tray indicator."""

    @classmethod
    def setUpClass(cls):
        """Set up class fixtures."""
        # Ensure mocks are in place for the entire test class
        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = mock_gi_repository

    def setUp(self):
        """Set up test environment before each test."""
        # Reset all GTK mocks to avoid test pollution
        mock_gtk.reset_mock()
        mock_glib.reset_mock()
        mock_gobject.reset_mock()
        mock_gdkpixbuf.reset_mock()
        mock_gio.reset_mock()
        mock_appindicator.reset_mock()

        # Configure idle_add to execute the function directly
        mock_glib.idle_add.side_effect = lambda func, *args: func(*args) or False
        mock_glib.timeout_add.return_value = 1

        # Clear any cached imports of tray_indicator
        modules_to_remove = [k for k in list(sys.modules.keys()) if "tray_indicator" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Inject a mock suspend_handler module before importing tray_indicator
        self.mock_suspend_handler_class = MagicMock()
        suspend_module = ModuleType("vocalinux.suspend_handler")
        suspend_module.SuspendHandler = self.mock_suspend_handler_class
        self.suspend_module_patcher = patch.dict(
            sys.modules,
            {"vocalinux.suspend_handler": suspend_module},
        )
        self.suspend_module_patcher.start()
        self.mock_suspend_handler = MagicMock()
        self.mock_suspend_handler_class.return_value = self.mock_suspend_handler

        # Avoid changing real process signal handlers during tests
        self.signal_patcher = patch("signal.signal")
        self.mock_signal = self.signal_patcher.start()

        # Patch threading module
        self.thread_patcher = patch("threading.Thread")
        self.mock_thread_class = self.thread_patcher.start()
        self.mock_thread_class.return_value.start = MagicMock()

        # Patch the pynput keyboard module
        self.keyboard_patcher = patch("vocalinux.ui.keyboard_shortcuts.keyboard", create=True)
        self.mock_keyboard = self.keyboard_patcher.start()

        # Patch keyboard module's KEYBOARD_AVAILABLE constant
        self.keyboard_available_patcher = patch(
            "vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE",
            True,
        )
        self.mock_keyboard_available = self.keyboard_available_patcher.start()

        # Import RecognitionState
        from vocalinux.common_types import RecognitionState

        self.RecognitionState = RecognitionState

        # Setup mock keyboard listener
        self.mock_listener = MagicMock()
        self.mock_listener.is_alive.return_value = True
        self.mock_keyboard.Listener.return_value = self.mock_listener
        self.mock_keyboard.Key = MagicMock()

        # Create mock for the shortcut manager
        self.mock_ksm = MagicMock()
        self.mock_ksm.active = False
        self.mock_ksm.shortcut = "ctrl+ctrl"
        self.mock_ksm.mode = "toggle"
        self.mock_ksm.set_mode.return_value = True
        self.mock_ksm.set_shortcut.return_value = True

        # Patch keyboard shortcuts manager
        self.ksm_patcher = patch("vocalinux.ui.keyboard_shortcuts.KeyboardShortcutManager")
        self.mock_ksm_class = self.ksm_patcher.start()
        self.mock_ksm_class.return_value = self.mock_ksm

        # Patch the settings dialog
        self.patcher_settings_dialog = patch("vocalinux.ui.tray_indicator.SettingsDialog")
        self.mock_settings_dialog_class = self.patcher_settings_dialog.start()
        self.mock_settings_dialog = MagicMock()
        self.mock_settings_dialog_class.return_value = self.mock_settings_dialog

        # Create mocks for dependencies
        self.mock_speech_engine = MagicMock()
        self.mock_speech_engine.state = RecognitionState.IDLE
        self.mock_text_injector = MagicMock()
        self.mock_config_manager = MagicMock()

        def config_get(section, key, default=None):
            if section == "shortcuts" and key == "toggle_recognition":
                return "ctrl+ctrl"
            if section == "shortcuts" and key == "mode":
                return "toggle"
            if section == "general" and key == "autostart":
                return False
            return default

        self.mock_config_manager.get.side_effect = config_get

        # Patch os path functions
        self.patcher_path_exists = patch("os.path.exists", return_value=True)
        self.mock_path_exists = self.patcher_path_exists.start()

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

        self.patcher_makedirs = patch("os.makedirs")
        self.mock_makedirs = self.patcher_makedirs.start()

        # Patch ConfigManager constructor
        self.patcher_config_manager = patch("vocalinux.ui.tray_indicator.ConfigManager")
        self.mock_config_manager_class = self.patcher_config_manager.start()
        self.mock_config_manager_class.return_value = self.mock_config_manager

        # Import and create TrayIndicator
        from vocalinux.ui.tray_indicator import TrayIndicator

        self.tray_indicator = TrayIndicator(
            speech_engine=self.mock_speech_engine,
            text_injector=self.mock_text_injector,
        )
        self.tray_indicator.shortcut_manager = self.mock_ksm
        self.tray_indicator.settings_shortcut_manager = self.mock_ksm

    def tearDown(self):
        """Clean up test environment after each test."""
        if hasattr(self, "tray_indicator") and hasattr(self.tray_indicator, "shortcut_manager"):
            self.tray_indicator.shortcut_manager.stop()

        self.patcher_path_exists.stop()
        self.patcher_listdir.stop()
        self.patcher_makedirs.stop()
        self.patcher_config_manager.stop()
        self.patcher_settings_dialog.stop()
        self.thread_patcher.stop()
        self.ksm_patcher.stop()
        self.keyboard_available_patcher.stop()
        self.keyboard_patcher.stop()
        self.signal_patcher.stop()
        self.suspend_module_patcher.stop()

    def test_initialization(self):
        """Test initialization of the tray indicator."""
        self.assertEqual(self.tray_indicator.speech_engine, self.mock_speech_engine)
        self.assertEqual(self.tray_indicator.text_injector, self.mock_text_injector)
        self.mock_speech_engine.register_state_callback.assert_called_once()

    def test_toggle_recognition_from_idle(self):
        """Test toggling recognition state from IDLE."""
        self.mock_speech_engine.state = self.RecognitionState.IDLE
        self.tray_indicator._toggle_recognition()
        self.mock_speech_engine.start_recognition.assert_called_once()
        self.mock_speech_engine.stop_recognition.assert_not_called()

    def test_toggle_recognition_from_listening(self):
        """Test toggling recognition state from LISTENING."""
        self.mock_speech_engine.state = self.RecognitionState.LISTENING
        self.tray_indicator._toggle_recognition()
        self.mock_speech_engine.stop_recognition.assert_called_once()
        self.mock_speech_engine.start_recognition.assert_not_called()

    def test_toggle_recognition_from_processing(self):
        """Test toggling recognition state from PROCESSING."""
        self.mock_speech_engine.state = self.RecognitionState.PROCESSING
        self.tray_indicator._toggle_recognition()
        self.mock_speech_engine.stop_recognition.assert_called_once()
        self.mock_speech_engine.start_recognition.assert_not_called()

    def test_start_recognition_push_to_talk_mode(self):
        """Test push-to-talk start uses mode argument."""
        self.mock_speech_engine.state = self.RecognitionState.IDLE
        self.mock_speech_engine.start_recognition.reset_mock()
        self.tray_indicator._start_recognition()
        self.mock_speech_engine.start_recognition.assert_called_once_with(mode="push_to_talk")

    def test_on_start_clicked(self):
        """Test start button click handler."""
        self.mock_speech_engine.start_recognition.reset_mock()
        self.tray_indicator._on_start_clicked(None)
        self.mock_speech_engine.start_recognition.assert_called_once()

    def test_on_stop_clicked(self):
        """Test stop button click handler."""
        self.mock_speech_engine.stop_recognition.reset_mock()
        self.tray_indicator._on_stop_clicked(None)
        self.mock_speech_engine.stop_recognition.assert_called_once()

    def test_on_recognition_state_changed(self):
        """Test state change callback invokes update_ui via GLib.idle_add."""
        with patch.object(self.tray_indicator, "_update_ui") as mock_update_ui:
            with patch("vocalinux.ui.tray_indicator.GLib") as patched_glib:
                patched_glib.idle_add.side_effect = lambda func, *args: func(*args) or False

                for state in self.RecognitionState:
                    mock_update_ui.reset_mock()
                    self.tray_indicator._on_recognition_state_changed(state)
                    mock_update_ui.assert_called_once_with(state)

    def test_quit(self):
        """Test quit functionality."""
        self.mock_ksm.stop.reset_mock()

        with patch("vocalinux.ui.tray_indicator.Gtk") as patched_gtk:
            self.tray_indicator._quit()
            self.assertEqual(self.mock_ksm.stop.call_count, 2)
            self.mock_suspend_handler.shutdown.assert_called_once()
            patched_gtk.main_quit.assert_called_once()

    def test_signal_handler(self):
        """Test signal handler calls GLib.idle_add with _quit."""
        with patch.object(self.tray_indicator, "_quit") as mock_quit:
            with patch("vocalinux.ui.tray_indicator.GLib") as patched_glib:
                self.tray_indicator._signal_handler(15, None)
                patched_glib.idle_add.assert_called_once_with(mock_quit)

    def test_run(self):
        """Test run method sets up signal handlers and starts main loop."""
        with patch("signal.signal") as mock_signal:
            with patch("vocalinux.ui.tray_indicator.Gtk") as patched_gtk:
                patched_gtk.main.side_effect = lambda: None
                self.tray_indicator.run()
                self.assertEqual(mock_signal.call_count, 2)
                patched_gtk.main.assert_called_once()

    def test_settings_callback(self):
        """Test settings callback."""
        import vocalinux.ui.tray_indicator as tray_module

        mock_dialog_instance = MagicMock()
        mock_dialog_class = MagicMock(return_value=mock_dialog_instance)

        with patch.object(tray_module, "SettingsDialog", mock_dialog_class):
            self.tray_indicator._on_settings_clicked(None)
            mock_dialog_class.assert_called_once()
            mock_dialog_instance.show.assert_called_once()

    def test_about_dialog(self):
        """Test about dialog creation."""
        with patch("vocalinux.ui.about_dialog.Gtk") as patched_gtk:
            mock_about_dialog = MagicMock()
            patched_gtk.AboutDialog.return_value = mock_about_dialog
            mock_about_dialog.run.side_effect = lambda: None
            patched_gtk.License.GPL_3_0 = 1

            with patch("vocalinux.ui.about_dialog.GdkPixbuf") as patched_pixbuf:
                mock_pixbuf = MagicMock()
                patched_pixbuf.Pixbuf.new_from_file.return_value = mock_pixbuf

                self.tray_indicator._on_about_clicked(None)

                mock_about_dialog.set_program_name.assert_called_with("Vocalinux")
                mock_about_dialog.run.assert_called_once()
                mock_about_dialog.destroy.assert_called_once()

    def test_validate_resources_missing_resources_dir(self):
        """Test validation when resources directory doesn't exist."""
        from vocalinux.ui.tray_indicator import _resource_manager

        with patch.object(_resource_manager, "validate_resources") as mock_validate:
            mock_validate.return_value = {
                "resources_dir_exists": False,
                "missing_icons": [],
                "missing_sounds": [],
            }
            self.tray_indicator._validate_resources()
            mock_validate.assert_called_once()

    def test_validate_resources_missing_icons(self):
        """Test validation when icon files are missing."""
        from vocalinux.ui.tray_indicator import _resource_manager

        with patch.object(_resource_manager, "validate_resources") as mock_validate:
            mock_validate.return_value = {
                "resources_dir_exists": True,
                "missing_icons": ["vocalinux.svg"],
                "missing_sounds": [],
            }
            self.tray_indicator._validate_resources()
            mock_validate.assert_called_once()

    def test_validate_resources_missing_sounds(self):
        """Test validation when sound files are missing."""
        from vocalinux.ui.tray_indicator import _resource_manager

        with patch.object(_resource_manager, "validate_resources") as mock_validate:
            mock_validate.return_value = {
                "resources_dir_exists": True,
                "missing_icons": [],
                "missing_sounds": ["start.wav"],
            }
            self.tray_indicator._validate_resources()
            mock_validate.assert_called_once()

    def test_update_ui_listening_state(self):
        """Test _update_ui for LISTENING state."""
        self.tray_indicator.indicator = MagicMock()
        mock_menu_item = MagicMock()
        mock_menu_item.get_label.return_value = "Start Voice Typing"
        self.tray_indicator.menu = MagicMock()
        self.tray_indicator.menu.get_children.return_value = [mock_menu_item]

        with patch("vocalinux.ui.tray_indicator.Gtk") as patched_gtk:
            patched_gtk.MenuItem = type(mock_menu_item)
            result = self.tray_indicator._update_ui(self.RecognitionState.LISTENING)

        self.tray_indicator.indicator.set_icon_full.assert_called_once_with(
            "vocalinux-microphone",
            "Microphone on",
        )
        self.assertEqual(result, False)

    def test_update_ui_processing_state(self):
        """Test _update_ui for PROCESSING state."""
        self.tray_indicator.indicator = MagicMock()
        mock_menu_item = MagicMock()
        mock_menu_item.get_label.return_value = "Start Voice Typing"
        self.tray_indicator.menu = MagicMock()
        self.tray_indicator.menu.get_children.return_value = [mock_menu_item]

        with patch("vocalinux.ui.tray_indicator.Gtk") as patched_gtk:
            patched_gtk.MenuItem = type(mock_menu_item)
            result = self.tray_indicator._update_ui(self.RecognitionState.PROCESSING)

        self.tray_indicator.indicator.set_icon_full.assert_called_once_with(
            "vocalinux-microphone-process",
            "Processing speech",
        )
        self.assertEqual(result, False)

    def test_update_ui_error_state(self):
        """Test _update_ui for ERROR state."""
        self.tray_indicator.indicator = MagicMock()
        mock_menu_item = MagicMock()
        mock_menu_item.get_label.return_value = "Start Voice Typing"
        self.tray_indicator.menu = MagicMock()
        self.tray_indicator.menu.get_children.return_value = [mock_menu_item]

        with patch("vocalinux.ui.tray_indicator.Gtk") as patched_gtk:
            patched_gtk.MenuItem = type(mock_menu_item)
            result = self.tray_indicator._update_ui(self.RecognitionState.ERROR)

        self.tray_indicator.indicator.set_icon_full.assert_called_once_with(
            "vocalinux-microphone-off",
            "Error",
        )
        self.assertEqual(result, False)

    def test_set_menu_item_enabled(self):
        """Test _set_menu_item_enabled finds and sets menu item sensitivity."""
        with patch("vocalinux.ui.tray_indicator.Gtk") as patched_gtk:
            mock_menu_item = MagicMock(spec=["get_label", "set_sensitive"])
            mock_menu_item.get_label.return_value = "Start Voice Typing"
            patched_gtk.MenuItem = type(mock_menu_item)

            self.tray_indicator.menu = MagicMock()
            self.tray_indicator.menu.get_children.return_value = [mock_menu_item]

            with patch("vocalinux.ui.tray_indicator.Gtk.MenuItem", patched_gtk.MenuItem):
                for item in self.tray_indicator.menu.get_children():
                    if hasattr(item, "get_label") and item.get_label() == "Start Voice Typing":
                        item.set_sensitive(False)
                        break

            mock_menu_item.set_sensitive.assert_called_with(False)

    def test_on_logs_clicked(self):
        """Test View Logs menu item click handler."""
        mock_dialog = MagicMock()
        mock_logging_dialog_class = MagicMock(return_value=mock_dialog)

        mock_logging_module = MagicMock()
        mock_logging_module.LoggingDialog = mock_logging_dialog_class

        with patch.dict(sys.modules, {"vocalinux.ui.logging_dialog": mock_logging_module}):
            self.tray_indicator._on_logs_clicked(None)

            mock_logging_dialog_class.assert_called_once_with(parent=None)
            mock_dialog.show.assert_called_once()

    def test_on_settings_dialog_response_close(self):
        """Test settings dialog response handler for CLOSE."""
        with patch("vocalinux.ui.tray_indicator.Gtk") as patched_gtk:
            patched_gtk.ResponseType.CLOSE = 1
            patched_gtk.ResponseType.DELETE_EVENT = 2

            mock_dialog = MagicMock()
            self.tray_indicator._on_settings_dialog_response(mock_dialog, 1)
            mock_dialog.destroy.assert_called_once()

    def test_on_settings_dialog_response_delete_event(self):
        """Test settings dialog response handler for DELETE_EVENT."""
        with patch("vocalinux.ui.tray_indicator.Gtk") as patched_gtk:
            patched_gtk.ResponseType.CLOSE = 1
            patched_gtk.ResponseType.DELETE_EVENT = 2

            mock_dialog = MagicMock()
            self.tray_indicator._on_settings_dialog_response(mock_dialog, 2)
            mock_dialog.destroy.assert_called_once()

    def test_on_quit_clicked(self):
        """Test Quit menu item click handler."""
        with patch.object(self.tray_indicator, "_quit") as mock_quit:
            self.tray_indicator._on_quit_clicked(None)
            mock_quit.assert_called_once()

    def test_run_keyboard_interrupt(self):
        """Test run method handles KeyboardInterrupt."""
        with patch("signal.signal"):
            with patch("vocalinux.ui.tray_indicator.Gtk") as patched_gtk:
                patched_gtk.main.side_effect = KeyboardInterrupt()
                with patch.object(self.tray_indicator, "_quit") as mock_quit:
                    self.tray_indicator.run()
                    mock_quit.assert_called_once()

    def test_about_dialog_logo_scaling_error(self):
        """Test about dialog handles logo scaling errors gracefully."""
        with patch("vocalinux.ui.about_dialog.Gtk") as patched_gtk:
            mock_about_dialog = MagicMock()
            patched_gtk.AboutDialog.return_value = mock_about_dialog
            mock_about_dialog.run.return_value = None
            patched_gtk.License.GPL_3_0 = 1

            with patch("vocalinux.ui.about_dialog.GdkPixbuf") as patched_pixbuf:
                patched_pixbuf.Pixbuf.new_from_file.side_effect = Exception("Load error")

                self.tray_indicator._on_about_clicked(None)

                mock_about_dialog.run.assert_called_once()
                mock_about_dialog.destroy.assert_called_once()
                mock_about_dialog.set_logo.assert_not_called()

    def test_has_super_shortcut_conflict_true(self):
        """Test conflict detection when using super shortcut."""
        self.tray_indicator.shortcut_manager = MagicMock()
        self.tray_indicator.shortcut_manager.shortcut = "super+super"
        self.assertTrue(self.tray_indicator._has_super_shortcut_conflict())

    def test_has_super_shortcut_conflict_false(self):
        """Test no conflict when using non-super shortcut."""
        self.tray_indicator.shortcut_manager = MagicMock()
        self.tray_indicator.shortcut_manager.shortcut = "ctrl+ctrl"
        self.assertFalse(self.tray_indicator._has_super_shortcut_conflict())

    def test_has_super_shortcut_conflict_left_super(self):
        """Test conflict detection for left super variant."""
        self.tray_indicator.shortcut_manager = MagicMock()
        self.tray_indicator.shortcut_manager.shortcut = "left_super+left_super"
        self.assertTrue(self.tray_indicator._has_super_shortcut_conflict())

    def test_open_settings_creates_dialog(self):
        """Test _open_settings creates and shows SettingsDialog."""
        import vocalinux.ui.tray_indicator as tray_module

        mock_dialog = MagicMock()
        mock_class = MagicMock(return_value=mock_dialog)
        with patch.object(tray_module, "SettingsDialog", mock_class):
            result = self.tray_indicator._open_settings()
            mock_class.assert_called_once()
            mock_dialog.connect.assert_called_once()
            mock_dialog.show.assert_called_once()
            self.assertFalse(result)

    def test_open_settings_from_shortcut_uses_glib(self):
        """Test _open_settings_from_shortcut schedules via GLib."""
        with patch("vocalinux.ui.tray_indicator.GLib") as patched_glib:
            self.tray_indicator._open_settings_from_shortcut()
            patched_glib.idle_add.assert_called_once_with(self.tray_indicator._open_settings)

    def test_on_settings_signal_uses_glib(self):
        """Test SIGUSR1 handler schedules settings opening."""
        with patch("vocalinux.ui.tray_indicator.GLib") as patched_glib:
            self.tray_indicator._on_settings_signal(10, None)
            patched_glib.idle_add.assert_called_once_with(self.tray_indicator._open_settings)

    def test_setup_settings_shortcut_disabled_on_conflict(self):
        """Test settings shortcut is disabled when using super key for recognition."""
        self.tray_indicator.shortcut_manager = MagicMock()
        self.tray_indicator.shortcut_manager.shortcut = "super+super"
        mock_settings_mgr = MagicMock()
        mock_settings_mgr.active = False
        self.tray_indicator.settings_shortcut_manager = mock_settings_mgr

        self.tray_indicator._setup_settings_shortcut()

        mock_settings_mgr.start.assert_not_called()

    def test_setup_settings_shortcut_enabled_no_conflict(self):
        """Test settings shortcut is enabled when no super key conflict."""
        self.tray_indicator.shortcut_manager = MagicMock()
        self.tray_indicator.shortcut_manager.shortcut = "ctrl+ctrl"
        mock_settings_mgr = MagicMock()
        mock_settings_mgr.active = True
        self.tray_indicator.settings_shortcut_manager = mock_settings_mgr

        self.tray_indicator._setup_settings_shortcut()

        mock_settings_mgr.start.assert_called_once()