#!/usr/bin/env python3
"""
System tray indicator module for Vocalinux.
"""

import gi
import logging
import os
import signal
import subprocess
import sys
import webbrowser

from pathlib import Path

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GLib

from ..speech_recognition import recognition_manager
from ..text_injection import text_injector
from . import audio_feedback, keyboard_shortcuts, config_manager

# Configure logging
logger = logging.getLogger(__name__)

# Constants
APP_ID = "vocalinux"
ICON_DIR = os.path.expanduser("~/.local/share/vocalinux/icons")

# Ensure icon directory exists
os.makedirs(ICON_DIR, exist_ok=True)

DEFAULT_ICON = os.path.join(ICON_DIR, "idle.svg")
RECORDING_ICON = os.path.join(ICON_DIR, "recording.svg")


class TrayIndicator:
    """
    System tray indicator for Vocalinux.
    
    Provides a system tray icon with menu for controlling the application.
    Handles keyboard shortcut registration and audio feedback.
    """

    def __init__(self, speech_engine, text_injector):
        """
        Initialize the tray indicator.
        
        Args:
            speech_engine: The speech recognition engine
            text_injector: The text injection system
        """
        self.speech_engine = speech_engine
        self.text_injector = text_injector
        self.is_recording = False
        
        # Initialize configuration
        self.config = config_manager.ConfigManager()
        
        # Initialize audio feedback
        self.audio = audio_feedback.AudioFeedback()
        
        # Create indicator
        self.indicator = AppIndicator3.Indicator.new(
            APP_ID,
            DEFAULT_ICON,
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        
        # Set indicator properties
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self._create_menu())
        
        # Initialize keyboard shortcuts
        self.keyboard = keyboard_shortcuts.KeyboardShortcuts()
        self.keyboard.register_shortcut(
            self.config.get("shortcuts", "toggle_recognition"),
            self._toggle_recording
        )
        
        # Start with recognition off
        self._update_status(False)
        
    def _create_menu(self):
        """Create the indicator menu."""
        menu = Gtk.Menu()
        
        # Toggle recognition menu item
        self.toggle_item = Gtk.MenuItem(label="Start Recognition")
        self.toggle_item.connect("activate", self._on_toggle_activate)
        menu.append(self.toggle_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Settings menu itemF
        settings_item = Gtk.MenuItem(label="Settings")
        settings_item.connect("activate", self._on_settings_activate)
        menu.append(settings_item)
        
        # Help menu item
        help_item = Gtk.MenuItem(label="Help")
        help_item.connect("activate", self._on_help_activate)
        menu.append(help_item)
        
        # About menu item
        about_item = Gtk.MenuItem(label="About")
        about_item.connect("activate", self._on_about_activate)
        menu.append(about_item)
        
        # Separator
        menu.append(Gtk.SeparatorMenuItem())
        
        # Quit menu item
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self._on_quit_activate)
        menu.append(quit_item)
        
        menu.show_all()
        return menu
        
    def _toggle_recording(self):
        """Toggle recording state."""
        self.is_recording = not self.is_recording
        
        if self.is_recording:
            # Start recognition
            self.speech_engine.start_recognition()
            self.audio.play_start()
        else:
            # Stop recognition
            self.speech_engine.stop_recognition()
            self.audio.play_stop()
            
        self._update_status(self.is_recording)
        
    def update_recording_state(self, state):
        """Update the recording state based on speech engine state."""
        from ..speech_recognition.recognition_manager import RecognitionState
        
        # Convert RecognitionState to boolean recording state
        is_recording = (state == RecognitionState.LISTENING or 
                       state == RecognitionState.PROCESSING)
        
        # Only update if the state has changed
        if is_recording != self.is_recording:
            self._toggle_recording()
        
    def _update_status(self, is_recording):
        """Update the indicator status."""
        if is_recording:
            self.indicator.set_icon(RECORDING_ICON)
            self.toggle_item.set_label("Stop Recognition")
        else:
            self.indicator.set_icon(DEFAULT_ICON)
            self.toggle_item.set_label("Start Recognition")
            
    def _on_toggle_activate(self, _):
        """Handle toggle menu item activation."""
        self._toggle_recording()
        
    def _on_settings_activate(self, _):
        """Handle settings menu item activation."""
        # Open settings dialog or config file
        config_path = os.path.join(config_manager.CONFIG_DIR, "config.json")
        subprocess.Popen(["xdg-open", config_path])
        
    def _on_help_activate(self, _):
        """Handle help menu item activation."""
        # Open help page
        webbrowser.open("https://github.com/vocalinux/vocalinux/blob/main/docs/USER_GUIDE.md")
        
    def _on_about_activate(self, _):
        """Handle about menu item activation."""
        about_dialog = Gtk.AboutDialog()
        about_dialog.set_program_name("Vocalinux")
        about_dialog.set_version("1.0.0")
        about_dialog.set_copyright("© 2025 Vocalinux Team")
        about_dialog.set_comments("Voice dictation for Linux")
        about_dialog.set_website("https://github.com/vocalinux")
        about_dialog.set_logo_icon_name(APP_ID)
        
        about_dialog.run()
        about_dialog.destroy()
        
    def _on_quit_activate(self, _):
        """Handle quit menu item activation."""
        self.quit()
        
    def run(self):
        """Run the application main loop."""
        # Install signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Run the GTK main loop
        Gtk.main()
        
    def _signal_handler(self, sig, frame):
        """Handle signals like SIGINT and SIGTERM."""
        self.quit()
        
    def quit(self):
        """Quit the application."""
        # Clean up resources
        if self.is_recording:
            self.speech_engine.stop_recognition()
            
        self.keyboard.unregister_all()
        
        # Quit GTK main loop
        Gtk.main_quit()
        
        logger.info("Application terminated")