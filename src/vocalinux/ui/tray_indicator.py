"""
System tray indicator module for Vocalinux.

This module provides a system tray indicator for controlling the speech
recognition process and displaying its status.
"""

import logging
import os
import signal
import sys
import threading
from typing import Callable, Dict, Optional

import gi

# Import GTK
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import AppIndicator3, GdkPixbuf, GLib, GObject, Gtk

# Import local modules - Use protocols to avoid circular imports
from ..common_types import (
    RecognitionState,
    SpeechRecognitionManagerProtocol,
    TextInjectorProtocol,
)
from .keyboard_shortcuts import KeyboardShortcutManager

logger = logging.getLogger(__name__)

# Define constants
APP_ID = "vocalinux"


# Define a robust way to find the resources directory
def find_resources_dir():
    """Find the resources directory regardless of how the application is executed."""
    # First, check if we're running from the repository
    module_dir = os.path.dirname(os.path.abspath(__file__))

    # Try several methods to find the resources directory
    candidates = [
        # For direct repository execution
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(module_dir))), "resources"
        ),
        # For installed package or virtual environment
        os.path.join(sys.prefix, "share", "vocalinux", "resources"),
        # For development in virtual environment
        os.path.join(os.path.dirname(sys.prefix), "resources"),
        # Additional fallback
        "/usr/local/share/vocalinux/resources",
        "/usr/share/vocalinux/resources",
    ]

    # Log all candidates for debugging
    for candidate in candidates:
        logger.debug(
            f"Checking resources candidate: {candidate} (exists: {os.path.exists(candidate)})"
        )

    # Return the first candidate that exists
    for candidate in candidates:
        if os.path.exists(candidate):
            logger.info(f"Found resources directory: {candidate}")
            return candidate

    # If no candidate exists, default to the first one (with warning)
    logger.warning(
        f"Could not find resources directory, defaulting to: {candidates[0]}"
    )
    return candidates[0]


# Find resources directory and icon directory
RESOURCES_DIR = find_resources_dir()
ICON_DIR = os.path.join(RESOURCES_DIR, "icons/scalable")

# Icon file names
DEFAULT_ICON = "vocalinux-microphone-off"
ACTIVE_ICON = "vocalinux-microphone"
PROCESSING_ICON = "vocalinux-microphone-process"


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

        # Initialize keyboard shortcut manager
        self.shortcut_manager = KeyboardShortcutManager()

        # Ensure icon directory exists
        os.makedirs(ICON_DIR, exist_ok=True)

        # Set up icon file paths
        self.icon_paths = {
            "default": os.path.join(ICON_DIR, f"{DEFAULT_ICON}.svg"),
            "active": os.path.join(ICON_DIR, f"{ACTIVE_ICON}.svg"),
            "processing": os.path.join(ICON_DIR, f"{PROCESSING_ICON}.svg"),
        }

        # Register for speech recognition state changes
        self.speech_engine.register_state_callback(self._on_recognition_state_changed)

        # Initialize the icon files
        self._init_icons()

        # Initialize the indicator (in the GTK main thread)
        GLib.idle_add(self._init_indicator)

        # Set up keyboard shortcuts
        self.shortcut_manager.register_toggle_callback(self._toggle_recognition)
        self.shortcut_manager.start()

    def _init_icons(self):
        """Initialize the icon files for the tray indicator."""
        # TODO: Copy default icons to the icon directory if they don't exist
        pass

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
                logger.info(
                    f"Icon '{name}' ({path}): {'exists' if exists else 'missing'}"
                )

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
            self.indicator.set_icon_full(self.icon_paths["default"], "Microphone off")
            self._set_menu_item_enabled("Start Voice Typing", True)
            self._set_menu_item_enabled("Stop Voice Typing", False)
        elif state == RecognitionState.LISTENING:
            self.indicator.set_icon_full(self.icon_paths["active"], "Microphone on")
            self._set_menu_item_enabled("Start Voice Typing", False)
            self._set_menu_item_enabled("Stop Voice Typing", True)
        elif state == RecognitionState.PROCESSING:
            self.indicator.set_icon_full(
                self.icon_paths["processing"], "Processing speech"
            )
            self._set_menu_item_enabled("Start Voice Typing", False)
            self._set_menu_item_enabled("Stop Voice Typing", True)
        elif state == RecognitionState.ERROR:
            self.indicator.set_icon_full(self.icon_paths["default"], "Error")
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
        # TODO: Implement settings dialog

    def _on_about_clicked(self, widget):
        """Handle click on the About menu item."""
        logger.debug("About clicked")

        about_dialog = Gtk.AboutDialog()
        about_dialog.set_program_name("Vocalinux")
        about_dialog.set_version("0.1.0")
        about_dialog.set_copyright("© 2025 | @jatinkrmalik")
        about_dialog.set_authors(["Jatin K Malik"])
        about_dialog.set_comments("A seamless voice dictation system for Ubuntu")
        about_dialog.set_website("https://github.com/jatinkrmalik/vocalinux")
        about_dialog.set_website_label("GitHub Repository")
        about_dialog.set_license_type(Gtk.License.GPL_3_0)

        # Set the logo using our custom icon
        logo_path = os.path.join(ICON_DIR, "vocalinux.svg")
        if os.path.exists(logo_path):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(logo_path)
                scaled_pixbuf = pixbuf.scale_simple(
                    150, 150, GdkPixbuf.InterpType.BILINEAR
                )
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
