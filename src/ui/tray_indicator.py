"""
System tray indicator module for Ubuntu Voice Typing.

This module provides a system tray indicator for controlling the speech
recognition process and displaying its status.
"""

import gi
import logging
import os
import signal
import sys
import threading
from typing import Callable, Dict, Optional

# Import GTK
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
from gi.repository import Gtk, AppIndicator3, GObject, GLib

# Import local modules
from speech_recognition.recognition_manager import SpeechRecognitionManager, RecognitionState
from text_injection.text_injector import TextInjector

logger = logging.getLogger(__name__)

# Define constants
APP_ID = "ubuntu-voice-typing"
ICON_DIR = os.path.expanduser("~/.local/share/ubuntu-voice-typing/icons")
DEFAULT_ICON = "microphone-off"
ACTIVE_ICON = "microphone"
PROCESSING_ICON = "microphone-process"


class TrayIndicator:
    """
    System tray indicator for Ubuntu Voice Typing.
    
    This class provides a system tray icon with a menu for controlling
    the speech recognition process.
    """
    
    def __init__(self, speech_engine: SpeechRecognitionManager, text_injector: TextInjector):
        """
        Initialize the system tray indicator.
        
        Args:
            speech_engine: The speech recognition manager instance
            text_injector: The text injector instance
        """
        self.speech_engine = speech_engine
        self.text_injector = text_injector
        
        # Ensure icon directory exists
        os.makedirs(ICON_DIR, exist_ok=True)
        
        # Register for speech recognition state changes
        self.speech_engine.register_state_callback(self._on_recognition_state_changed)
        
        # Initialize the icon files
        self._init_icons()
        
        # Initialize the indicator (in the GTK main thread)
        GLib.idle_add(self._init_indicator)
    
    def _init_icons(self):
        """Initialize the icon files for the tray indicator."""
        # TODO: Copy default icons to the icon directory if they don't exist
        pass
    
    def _init_indicator(self):
        """Initialize the system tray indicator."""
        logger.info("Initializing system tray indicator")
        
        # Create the indicator
        self.indicator = AppIndicator3.Indicator.new(
            APP_ID,
            DEFAULT_ICON,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        
        # Set the icon path
        self.indicator.set_icon_theme_path(ICON_DIR)
        
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
            self.indicator.set_icon(DEFAULT_ICON)
            self._set_menu_item_enabled("Start Voice Typing", True)
            self._set_menu_item_enabled("Stop Voice Typing", False)
        elif state == RecognitionState.LISTENING:
            self.indicator.set_icon(ACTIVE_ICON)
            self._set_menu_item_enabled("Start Voice Typing", False)
            self._set_menu_item_enabled("Stop Voice Typing", True)
        elif state == RecognitionState.PROCESSING:
            self.indicator.set_icon(PROCESSING_ICON)
            self._set_menu_item_enabled("Start Voice Typing", False)
            self._set_menu_item_enabled("Stop Voice Typing", True)
        elif state == RecognitionState.ERROR:
            self.indicator.set_icon(DEFAULT_ICON)
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
        about_dialog.set_program_name("Ubuntu Voice Typing")
        about_dialog.set_version("0.1.0")
        about_dialog.set_copyright("© 2025 Ubuntu Voice Typing Team")
        about_dialog.set_comments("A seamless voice dictation system for Ubuntu")
        about_dialog.set_website("https://github.com/ubuntu-voice-typing")
        about_dialog.set_website_label("GitHub Repository")
        about_dialog.set_license_type(Gtk.License.GPL_3_0)
        
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