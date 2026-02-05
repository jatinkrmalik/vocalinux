"""
System tray indicator module for Vocalinux.

This module provides a system tray indicator for controlling the speech
recognition process and displaying its status.
"""

import logging
import os
import signal
from typing import Callable

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

from gi.repository import GdkPixbuf, GLib, GObject, Gtk

# Import local modules - Use protocols to avoid circular imports
from ..common_types import RecognitionState, SpeechRecognitionManagerProtocol, TextInjectorProtocol

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

# Animated icon frames for listening state (sound waves emanating)
ACTIVE_ICON_FRAMES = [
    "vocalinux-microphone-active-1",
    "vocalinux-microphone-active-2",
    "vocalinux-microphone-active-3",
]

# Animation settings
ANIMATION_INTERVAL_MS = 300  # Time between frame changes (milliseconds)


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

        # Initialize keyboard shortcut manager
        self.shortcut_manager = (
            KeyboardShortcutManager()
        )  # Pass config_manager - Removed config_manager argument

        # Animation state
        self._animation_timeout_id = None
        self._animation_frame_index = 0

        # Ensure icon directory exists
        os.makedirs(ICON_DIR, exist_ok=True)

        # Set up icon file paths using resource manager
        self.icon_paths = {
            "default": _resource_manager.get_icon_path(DEFAULT_ICON),
            "active": _resource_manager.get_icon_path(ACTIVE_ICON),
            "processing": _resource_manager.get_icon_path(PROCESSING_ICON),
        }

        # Set up animated icon frame paths
        self.animation_frame_paths = [
            _resource_manager.get_icon_path(frame) for frame in ACTIVE_ICON_FRAMES
        ]

        # Register for speech recognition state changes
        self.speech_engine.register_state_callback(self._on_recognition_state_changed)

        # Initialize the icon files and validate resources
        self._init_icons()
        self._validate_resources()

        # Initialize the indicator (in the GTK main thread)
        GLib.idle_add(self._init_indicator)

        # Set up keyboard shortcuts
        self.shortcut_manager.register_toggle_callback(self._toggle_recognition)
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

        # Set the indicator status
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        # Create the menu
        self.menu = Gtk.Menu()

        # Add menu items
        self._add_menu_item("Start Voice Typing", self._on_start_clicked)
        self._add_menu_item("Stop Voice Typing", self._on_stop_clicked)
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
            self._stop_icon_animation()
            self.indicator.set_icon_full(DEFAULT_ICON, "Microphone off")
            self._set_menu_item_enabled("Start Voice Typing", True)
            self._set_menu_item_enabled("Stop Voice Typing", False)
        elif state == RecognitionState.LISTENING:
            self._start_icon_animation()
            self._set_menu_item_enabled("Start Voice Typing", False)
            self._set_menu_item_enabled("Stop Voice Typing", True)
        elif state == RecognitionState.PROCESSING:
            self._stop_icon_animation()
            self.indicator.set_icon_full(PROCESSING_ICON, "Processing speech")
            self._set_menu_item_enabled("Start Voice Typing", False)
            self._set_menu_item_enabled("Stop Voice Typing", True)
        elif state == RecognitionState.ERROR:
            self._stop_icon_animation()
            self.indicator.set_icon_full(DEFAULT_ICON, "Error")
            self._set_menu_item_enabled("Start Voice Typing", True)
            self._set_menu_item_enabled("Stop Voice Typing", False)

        return False  # Remove idle callback

    def _start_icon_animation(self):
        """Start the animated icon cycling for listening state."""
        if self._animation_timeout_id is not None:
            return  # Already animating

        logger.debug("Starting tray icon animation")
        self._animation_frame_index = 0
        self._update_animation_frame()
        self._animation_timeout_id = GLib.timeout_add(
            ANIMATION_INTERVAL_MS, self._update_animation_frame
        )

    def _stop_icon_animation(self):
        """Stop the animated icon cycling."""
        if self._animation_timeout_id is not None:
            logger.debug("Stopping tray icon animation")
            GLib.source_remove(self._animation_timeout_id)
            self._animation_timeout_id = None
            self._animation_frame_index = 0

    def _update_animation_frame(self):
        """Update the icon to the next animation frame."""
        if not ACTIVE_ICON_FRAMES:
            # Fallback to static icon if no animation frames available
            self.indicator.set_icon_full(ACTIVE_ICON, "Listening")
            return False

        # Get current frame icon name
        frame_name = ACTIVE_ICON_FRAMES[self._animation_frame_index]

        # Update icon (use icon name, not full path - AppIndicator uses icon_theme_path)
        self.indicator.set_icon_full(frame_name, "Listening...")

        # Advance to next frame (cycle back to start)
        self._animation_frame_index = (self._animation_frame_index + 1) % len(ACTIVE_ICON_FRAMES)

        return True  # Continue animation

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

    def _on_about_clicked(self, widget):
        """Handle click on the About menu item."""
        from ..version import __copyright__, __description__, __url__, __version__

        logger.debug("About clicked")

        about_dialog = Gtk.AboutDialog()
        about_dialog.set_program_name("Vocalinux")
        about_dialog.set_version(__version__)
        about_dialog.set_copyright(__copyright__)

        # Authors and credits
        about_dialog.set_authors(["Jatin K Malik"])
        about_dialog.set_documenters(["Jatin K Malik"])
        about_dialog.set_artists(["Jatin K Malik"])

        # Add credits section with social links
        about_dialog.add_credit_section(
            "Connect",
            [
                "GitHub: github.com/jatinkrmalik",
                "Twitter/X: @jatinkrmalik",
            ],
        )

        # Comments with better formatting
        about_dialog.set_comments(
            f"{__description__}\n\n" "🌟 Open Source Project\n" "Contributions Welcome!"
        )

        about_dialog.set_website(__url__)
        about_dialog.set_website_label("⭐ Star on GitHub")
        about_dialog.set_license_type(Gtk.License.GPL_3_0)

        # Set the logo using our custom icon
        logo_path = _resource_manager.get_icon_path("vocalinux")
        if os.path.exists(logo_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(logo_path)
                scaled_pixbuf = pixbuf.scale_simple(128, 128, GdkPixbuf.InterpType.BILINEAR)
                about_dialog.set_logo(scaled_pixbuf)
            except Exception as e:
                logger.warning(f"Failed to load or scale logo: {e}")

        # Run the dialog
        about_dialog.run()
        about_dialog.destroy()

    def _on_quit_clicked(self, widget):
        """Handle click on the Quit menu item."""
        logger.debug("Quit clicked")
        self._quit()

    def _quit(self):
        """Quit the application."""
        logger.info("Quitting application")

        # Stop the icon animation
        self._stop_icon_animation()

        # Stop the keyboard shortcut manager
        self.shortcut_manager.stop()

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
