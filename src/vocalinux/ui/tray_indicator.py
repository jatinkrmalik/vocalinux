"""
System tray indicator module for Vocalinux.

This module provides a system tray indicator for controlling the speech
recognition process and displaying its status.
"""

import logging
import os
import signal
from typing import Callable, Optional

import gi

# Import GTK
gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
except (ImportError, ValueError):
    try:
        gi.require_version("AyatanaAppIndicator3", "0.1")
        from gi.repository import AyatanaAppIndicator3 as AppIndicator3
    except (ImportError, ValueError):
        gi.require_version("AyatanaAppindicator3", "0.1")
        from gi.repository import AyatanaAppindicator3 as AppIndicator3

from gi.repository import GdkPixbuf, Gio, GLib, GObject, Gtk

# Import local modules - Use protocols to avoid circular imports
from ..common_types import RecognitionState, SpeechRecognitionManagerProtocol, TextInjectorProtocol
from ..suspend_handler import SuspendHandler  # noqa: E402

# Import necessary components
from .config_manager import ConfigManager  # noqa: E402
from .keyboard_shortcuts import KeyboardShortcutManager  # noqa: E402
from .settings_dialog import SettingsDialog  # noqa: E402

logger = logging.getLogger(__name__)

# Define constants
APP_ID = "vocalinux"


# Import the centralized resource manager
from ..utils.resource_manager import ResourceManager  # noqa: E402

# Initialize resource manager
_resource_manager = ResourceManager()
ICON_DIR = _resource_manager.icons_dir

# Icon file names
DEFAULT_ICON = "vocalinux-microphone-off"
ACTIVE_ICON = "vocalinux-microphone"
PROCESSING_ICON = "vocalinux-microphone-process"

# /dev/input settle-detection tuning (used after resume)
_INPUT_SETTLE_SECONDS = 2
_INPUT_MONITOR_CAP_SECONDS = 10
_FALLBACK_KEYBOARD_RESTART_SECONDS = 6


class TrayIndicator:
    """
    System tray indicator for Vocalinux.

    This class provides a system tray icon with a menu for controlling
    the speech recognition process.
    """

    def __init__(
        self,
        speech_engine: SpeechRecognitionManagerProtocol,
        text_injector: TextInjectorProtocol,
    ):
        """
        Initialize the system tray indicator.

        Args:
            speech_engine: The speech recognition manager instance
            text_injector: The text injector instance
        """
        self.speech_engine = speech_engine
        self.text_injector = text_injector
        self.config_manager = ConfigManager()  # Added: Initialize ConfigManager
        self._syncing_autostart_menu = False

        # Get configured shortcut and mode from config
        shortcut = self.config_manager.get("shortcuts", "toggle_recognition", "ctrl+ctrl")
        mode = self.config_manager.get("shortcuts", "mode", "toggle")

        # Initialize keyboard shortcut manager with configured shortcut and mode
        self.shortcut_manager = KeyboardShortcutManager(shortcut=shortcut, mode=mode)

        # Ensure icon directory exists
        os.makedirs(ICON_DIR, exist_ok=True)

        # Set up icon file paths using resource manager
        self.icon_paths = {
            "default": _resource_manager.get_icon_path(DEFAULT_ICON),
            "active": _resource_manager.get_icon_path(ACTIVE_ICON),
            "processing": _resource_manager.get_icon_path(PROCESSING_ICON),
        }
        self.icon_names = {
            "default": DEFAULT_ICON,
            "active": ACTIVE_ICON,
            "processing": PROCESSING_ICON,
        }

        # Register for speech recognition state changes
        self.speech_engine.register_state_callback(self._on_recognition_state_changed)

        # Initialize the icon files and validate resources
        self._init_icons()
        self._validate_resources()

        # Initialize the indicator (in the GTK main thread)
        GLib.idle_add(self._init_indicator)

        self._suspend_handler = SuspendHandler(
            on_suspend=self._on_system_suspend,
            on_resume=self._on_system_resume,
        )

        # Set up keyboard shortcuts with mode support
        self._setup_keyboard_shortcuts()

    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts based on configured mode."""
        # Stop existing shortcut manager if running
        if self.shortcut_manager.active:
            logger.info("Stopping existing shortcut manager before reconfiguration")
            self.shortcut_manager.stop()

        # Clear any existing callbacks to prevent duplicate triggers
        self.shortcut_manager.register_toggle_callback(None)
        self.shortcut_manager.register_press_callback(None)
        self.shortcut_manager.register_release_callback(None)

        # Get configured mode from config
        mode = self.config_manager.get("shortcuts", "mode", "toggle")
        logger.info(f"Setting up keyboard shortcuts with mode: {mode}")

        if mode == "toggle":
            # Register toggle callback for double-tap mode
            self.shortcut_manager.register_toggle_callback(self._toggle_recognition)
        elif mode == "push_to_talk":
            # Register press/release callbacks for push-to-talk mode
            self.shortcut_manager.register_press_callback(self._start_recognition)
            self.shortcut_manager.register_release_callback(self._stop_recognition)

        # Start the keyboard shortcut manager
        self.shortcut_manager.start()

    def _init_icons(self):
        """Initialize the icon files for the tray indicator."""
        # Ensure icon directory exists
        _resource_manager.ensure_directories_exist()

    def _validate_resources(self):
        """Validate that required resources are available."""
        validation_results = _resource_manager.validate_resources()

        if not validation_results["resources_dir_exists"]:
            logger.warning("Resources directory not found")

        if validation_results["missing_icons"]:
            logger.warning(f"Missing icon files: {validation_results['missing_icons']}")

        if validation_results["missing_sounds"]:
            logger.warning(f"Missing sound files: {validation_results['missing_sounds']}")

        # Log successful validation
        if (
            validation_results["resources_dir_exists"]
            and not validation_results["missing_icons"]
            and not validation_results["missing_sounds"]
        ):
            logger.info("All required resources validated successfully")

    def _init_indicator(self):
        """Initialize the system tray indicator."""
        logger.info("Initializing system tray indicator")

        # Log the icon directory path
        logger.info(f"Using icon directory: {ICON_DIR}")
        logger.info(f"Icon directory exists: {os.path.exists(ICON_DIR)}")

        # List available icon files and check if they exist
        if os.path.exists(ICON_DIR):
            icon_files = os.listdir(ICON_DIR)
            logger.info(f"Available icon files: {icon_files}")

            for name, path in self.icon_paths.items():
                exists = os.path.exists(path)
                logger.info(f"Icon '{name}' ({path}): {'exists' if exists else 'missing'}")

        # Create the indicator with absolute path to the default icon
        self.indicator = AppIndicator3.Indicator.new_with_path(
            APP_ID,
            DEFAULT_ICON,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            ICON_DIR,
        )
        self.indicator.set_icon_theme_path(ICON_DIR)

        # Set the indicator status
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # Create the menu
        self.menu = Gtk.Menu()

        # Add menu items
        self._add_menu_item("Start Voice Typing", self._on_start_clicked)
        self._add_menu_item("Stop Voice Typing", self._on_stop_clicked)
        self._add_menu_separator()

        self._autostart_menu_item = self._add_menu_checkbox(
            "Start on Login", self._on_autostart_toggled
        )
        self._update_autostart_checkbox()

        self._add_menu_separator()
        self._add_menu_item("Settings", self._on_settings_clicked)
        self._add_menu_item("View Logs", self._on_logs_clicked)
        self._add_menu_separator()
        self._add_menu_item("About", self._on_about_clicked)
        self._add_menu_item("Quit", self._on_quit_clicked)

        # Set the indicator menu
        self.indicator.set_menu(self.menu)

        # Show the menu
        self.menu.show_all()

        # Update the UI based on the initial state
        self._update_ui(RecognitionState.IDLE)

        return False  # Remove idle callback

    def _toggle_recognition(self):
        """Toggle the recognition state between IDLE and LISTENING."""
        if self.speech_engine.state == RecognitionState.IDLE:
            self.speech_engine.start_recognition()
        else:
            self.speech_engine.stop_recognition()

    def _start_recognition(self):
        """Start voice recognition (for push-to-talk mode)."""
        if self.speech_engine.state == RecognitionState.IDLE:
            self.speech_engine.start_recognition(mode="push_to_talk")

    def _stop_recognition(self):
        """Stop voice recognition (for push-to-talk mode)."""
        if self.speech_engine.state != RecognitionState.IDLE:
            self.speech_engine.stop_recognition()

    def _add_menu_item(self, label: str, callback: Callable):
        """
        Add a menu item to the indicator menu.

        Args:
            label: The label for the menu item
            callback: The callback function to call when the item is clicked
        """
        item = Gtk.MenuItem.new_with_label(label)
        item.connect("activate", callback)
        self.menu.append(item)
        return item

    def _add_menu_separator(self):
        """Add a separator to the indicator menu."""
        separator = Gtk.SeparatorMenuItem()
        self.menu.append(separator)

    def _add_menu_checkbox(self, label: str, callback: Callable) -> Gtk.CheckMenuItem:
        """
        Add a checkbox menu item to the indicator menu.

        Args:
            label: The label for the menu item
            callback: The callback function to call when the item is toggled

        Returns:
            The checkbox menu item
        """
        item = Gtk.CheckMenuItem.new_with_label(label)
        item.connect("toggled", callback)
        self.menu.append(item)
        return item

    def _update_autostart_checkbox(self):
        """Update the autostart checkbox state based on current config."""
        from . import autostart_manager

        autostart_enabled = autostart_manager.is_autostart_enabled()
        config_enabled = self.config_manager.get("general", "autostart", False)
        if config_enabled != autostart_enabled:
            self.config_manager.set("general", "autostart", autostart_enabled)
            self.config_manager.save_settings()

        self._syncing_autostart_menu = True
        self._autostart_menu_item.set_active(autostart_enabled)
        self._syncing_autostart_menu = False

    def _on_autostart_toggled(self, widget):
        """Handle toggle of the Start on Login menu item."""
        if self._syncing_autostart_menu:
            return

        enabled = widget.get_active()
        logger.info(f"Autostart toggled: {enabled}")

        from . import autostart_manager

        if autostart_manager.set_autostart(enabled):
            self.config_manager.set("general", "autostart", enabled)
            self.config_manager.save_settings()
            status = "enabled" if enabled else "disabled"
            logger.info(f"Autostart {status}")
        else:
            self._syncing_autostart_menu = True
            widget.set_active(not enabled)
            self._syncing_autostart_menu = False

    def _on_recognition_state_changed(self, state: RecognitionState):
        """
        Handle changes in the speech recognition state.

        Args:
            state: The new recognition state
        """
        # Update the UI in the GTK main thread
        GLib.idle_add(self._update_ui, state)

    def _update_ui(self, state: RecognitionState):
        """
        Update the UI based on the recognition state.

        Args:
            state: The current recognition state
        """
        if state == RecognitionState.IDLE:
            self.indicator.set_icon_full(self.icon_names["default"], "Microphone off")
            self._set_menu_item_enabled("Start Voice Typing", True)
            self._set_menu_item_enabled("Stop Voice Typing", False)
        elif state == RecognitionState.LISTENING:
            self.indicator.set_icon_full(self.icon_names["active"], "Microphone on")
            self._set_menu_item_enabled("Start Voice Typing", False)
            self._set_menu_item_enabled("Stop Voice Typing", True)
        elif state == RecognitionState.PROCESSING:
            self.indicator.set_icon_full(self.icon_names["processing"], "Processing speech")
            self._set_menu_item_enabled("Start Voice Typing", False)
            self._set_menu_item_enabled("Stop Voice Typing", True)
        elif state == RecognitionState.ERROR:
            self.indicator.set_icon_full(self.icon_names["default"], "Error")
            self._set_menu_item_enabled("Start Voice Typing", True)
            self._set_menu_item_enabled("Stop Voice Typing", False)

        return False  # Remove idle callback

    def _set_menu_item_enabled(self, label: str, enabled: bool):
        """
        Set the enabled state of a menu item by its label.

        Args:
            label: The label of the menu item
            enabled: Whether the item should be enabled
        """
        for item in self.menu.get_children():
            if isinstance(item, Gtk.MenuItem) and item.get_label() == label:
                item.set_sensitive(enabled)
                break

    def _on_start_clicked(self, widget):
        """Handle click on the Start Voice Typing menu item."""
        logger.debug("Start Voice Typing clicked")
        self.speech_engine.start_recognition()

    def _on_stop_clicked(self, widget):
        """Handle click on the Stop Voice Typing menu item."""
        logger.debug("Stop Voice Typing clicked")
        self.speech_engine.stop_recognition()

    def _on_settings_clicked(self, widget):
        """Handle click on the Settings menu item."""
        logger.debug("Settings clicked")

        # Create the settings dialog
        dialog = SettingsDialog(
            parent=None,  # Or get the main window if available
            config_manager=self.config_manager,
            speech_engine=self.speech_engine,
            shortcut_update_callback=self.update_shortcut,
        )

        # Connect to the response signal
        dialog.connect("response", self._on_settings_dialog_response)

        # Show the dialog (non-modal)
        dialog.show()

    def _on_logs_clicked(self, widget):
        """Handle click on the View Logs menu item."""
        logger.debug("View Logs clicked")

        # Import here to avoid circular imports
        from .logging_dialog import LoggingDialog

        # Create and show the logging dialog
        dialog = LoggingDialog(parent=None)
        dialog.show()

    def _on_settings_dialog_response(self, dialog, response):
        """Handle responses from the settings dialog."""
        # With auto-apply, we just close the dialog on any response
        if response == Gtk.ResponseType.CLOSE or response == Gtk.ResponseType.DELETE_EVENT:
            logger.info("Settings dialog closed.")
            dialog.destroy()

    def update_shortcut(self, shortcut: str, mode: Optional[str] = None) -> bool:
        """
        Update the keyboard shortcut for toggling voice recognition.

        This performs a live shortcut switch without requiring an app restart.

        Args:
            shortcut: The new shortcut string (e.g., "ctrl+ctrl", "alt+alt")
            mode: Optional new mode ("toggle" or "push_to_talk"). If None, keeps current mode.

        Returns:
            True if the shortcut was updated successfully, False otherwise
        """
        current_mode = self.shortcut_manager.mode
        mode_changed = mode is not None and mode != current_mode
        shortcut_changed = shortcut != self.shortcut_manager.shortcut

        if mode_changed:
            logger.info(f"Mode changing from {current_mode} to {mode}")
            assert mode is not None
            if not self.shortcut_manager.set_mode(mode):
                logger.error(f"Failed to set shortcut mode: {mode}")
                return False

        if shortcut_changed:
            if not self.shortcut_manager.set_shortcut(shortcut):
                logger.error(f"Failed to set shortcut: {shortcut}")
                return False

        if mode_changed or shortcut_changed:
            self._setup_keyboard_shortcuts()
            return self.shortcut_manager.active

        logger.debug("No changes needed - shortcut and mode unchanged")
        return True

    def _on_about_clicked(self, widget):
        """Handle click on the About menu item."""
        from .about_dialog import show_about_dialog

        logger.debug("About clicked")
        show_about_dialog(parent=None)

    def _on_system_suspend(self):
        """Stop active recognition before the system goes to sleep."""
        if self.speech_engine.state != RecognitionState.IDLE:
            logger.info("System suspending — stopping active recognition")
            self.speech_engine.stop_recognition()

    def _on_system_resume(self):
        """Reinitialize subsystems after the system wakes up.

        Speech engine reinitializes after 2s (audio hardware recovers fast).
        Keyboard backend waits for /dev/input to settle using inotify-backed
        directory monitoring, with a timer fallback if monitoring unavailable.
        """
        logger.info("System resumed — scheduling reinit")
        GLib.timeout_add_seconds(2, self._reinit_speech_after_resume)
        GLib.timeout_add_seconds(2, self._start_input_device_monitor)

    def _reinit_speech_after_resume(self):
        try:
            self.speech_engine.reinitialize_after_resume()
        except Exception:
            logger.error("Failed to reinitialize after resume", exc_info=True)
        return GLib.SOURCE_REMOVE

    def _start_input_device_monitor(self):
        """Watch /dev/input for changes; restart keyboard when devices settle."""
        try:
            gfile = Gio.File.new_for_path("/dev/input")
            self._input_monitor = gfile.monitor_directory(Gio.FileMonitorFlags.NONE, None)
            self._input_monitor.connect("changed", self._on_input_device_changed)

            self._settle_timer_id = GLib.timeout_add_seconds(
                _INPUT_SETTLE_SECONDS, self._on_devices_settled
            )
            self._monitor_timeout_id = GLib.timeout_add_seconds(
                _INPUT_MONITOR_CAP_SECONDS, self._on_input_monitor_timeout
            )
            logger.info("Monitoring /dev/input for device changes after resume")
        except Exception:
            logger.error("Failed to monitor /dev/input, falling back to timer", exc_info=True)
            GLib.timeout_add_seconds(
                _FALLBACK_KEYBOARD_RESTART_SECONDS, self._reinit_keyboard_fallback
            )
        return GLib.SOURCE_REMOVE

    def _on_input_device_changed(self, monitor, file, other_file, event_type):
        if getattr(self, "_settle_timer_id", None) is not None:
            GLib.source_remove(self._settle_timer_id)
        self._settle_timer_id = GLib.timeout_add_seconds(
            _INPUT_SETTLE_SECONDS, self._on_devices_settled
        )

    def _on_devices_settled(self):
        logger.info("Input devices settled — restarting keyboard shortcuts")
        self._cleanup_input_monitor()
        self._setup_keyboard_shortcuts()
        return GLib.SOURCE_REMOVE

    def _on_input_monitor_timeout(self):
        logger.warning("Input device monitor timed out — restarting keyboard shortcuts")
        self._cleanup_input_monitor()
        self._setup_keyboard_shortcuts()
        return GLib.SOURCE_REMOVE

    def _reinit_keyboard_fallback(self):
        logger.info("Restarting keyboard shortcuts (fallback timer)")
        self._setup_keyboard_shortcuts()
        return GLib.SOURCE_REMOVE

    def _cleanup_input_monitor(self):
        if getattr(self, "_settle_timer_id", None) is not None:
            GLib.source_remove(self._settle_timer_id)
            self._settle_timer_id = None
        if getattr(self, "_monitor_timeout_id", None) is not None:
            GLib.source_remove(self._monitor_timeout_id)
            self._monitor_timeout_id = None
        if getattr(self, "_input_monitor", None) is not None:
            self._input_monitor.cancel()
            self._input_monitor = None

    def _on_quit_clicked(self, widget):
        """Handle click on the Quit menu item."""
        logger.debug("Quit clicked")
        self._quit()

    def _quit(self):
        """Quit the application."""
        logger.info("Quitting application")

        if self._suspend_handler is not None:
            self._suspend_handler.shutdown()

        self._cleanup_input_monitor()

        # Stop the keyboard shortcut manager
        self.shortcut_manager.stop()

        # Stop the text injector (restores previous IBus engine)
        if hasattr(self, "text_injector") and self.text_injector is not None:
            self.text_injector.stop()

        Gtk.main_quit()

    def run(self):
        """Run the application main loop."""
        logger.info("Starting GTK main loop")

        # Set up signal handlers for graceful termination
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Start the GTK main loop
        try:
            Gtk.main()
        except KeyboardInterrupt:
            self._quit()

    def _signal_handler(self, sig, frame):
        """
        Handle signals (e.g., SIGINT, SIGTERM).

        Args:
            sig: The signal number
            frame: The current stack frame
        """
        logger.info(f"Received signal {sig}, shutting down...")
        GLib.idle_add(self._quit)
