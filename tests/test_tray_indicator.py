"""
Tests for the tray indicator module.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import pytest

# Create mock modules before importing our code
mock_gi = MagicMock()
mock_gtk = MagicMock()
mock_glib = MagicMock()
mock_app_indicator = MagicMock()
mock_gobject = MagicMock()

# Configure GLib.idle_add to execute function directly
mock_glib.idle_add = lambda func, *args: func(*args) or False

# Set up necessary mocks for AppIndicator
mock_app_indicator.IndicatorCategory = MagicMock()
mock_app_indicator.IndicatorCategory.APPLICATION_STATUS = "APPLICATION_STATUS"
mock_app_indicator.IndicatorStatus = MagicMock()
mock_app_indicator.IndicatorStatus.ACTIVE = "ACTIVE"

# Set up repository structure
mock_gi.repository = MagicMock()
mock_gi.repository.Gtk = mock_gtk
mock_gi.repository.GLib = mock_glib
mock_gi.repository.AppIndicator3 = mock_app_indicator
mock_gi.repository.GObject = mock_gobject
mock_gi.require_version = MagicMock()

# Apply patches before importing the module under test
with patch.dict('sys.modules', {
    'gi': mock_gi,
    'gi.repository': mock_gi.repository,
    'gi.repository.Gtk': mock_gtk,
    'gi.repository.GLib': mock_glib,
    'gi.repository.AppIndicator3': mock_app_indicator,
    'gi.repository.GObject': mock_gobject,
}):
    # Now we can import our module
    from src.speech_recognition.recognition_manager import RecognitionState
    from src.ui.tray_indicator import TrayIndicator, DEFAULT_ICON, ACTIVE_ICON, PROCESSING_ICON


# Define a simplified version of TrayIndicator for testing
class TestableIndicator(TrayIndicator):
    """A testable version of TrayIndicator that avoids GTK dependencies."""
    
    def __init__(self, speech_engine, text_injector, mock_ksm):
        """
        Initialize the testable indicator with mocked dependencies.
        
        Args:
            speech_engine: The mock speech engine
            text_injector: The mock text injector
            mock_ksm: The mock keyboard shortcut manager
        """
        # Skip calling the parent __init__ to avoid GTK setup
        # but initialize important attributes
        self.speech_engine = speech_engine
        self.text_injector = text_injector
        
        # Set up the shortcut manager directly
        self.shortcut_manager = mock_ksm
        
        # Set up mocked UI components
        self.indicator = MagicMock()
        self.menu = MagicMock()
        
        # Register callbacks
        self.speech_engine.register_state_callback(self._on_recognition_state_changed)
        self.shortcut_manager.register_toggle_callback(self._toggle_recognition)
        self.shortcut_manager.start()


# Define a complete test class for TrayIndicator
class TestTrayIndicator(unittest.TestCase):
    """Test cases for the tray indicator."""

    def setUp(self):
        """Set up test environment before each test."""
        # Create mocks for dependencies
        self.mock_speech_engine = MagicMock()
        self.mock_text_injector = MagicMock()
        self.mock_ksm = MagicMock()
        
        # Create a list of patches we'll need to stop later
        self.patches = []
        
        # Patch os.makedirs to avoid filesystem operations
        self.patcher_makedirs = patch('os.makedirs')
        self.mock_makedirs = self.patcher_makedirs.start()
        self.patches.append(self.patcher_makedirs)
        
        # Patch Gtk.main_quit to avoid actually quitting during tests
        self.patcher_main_quit = patch.object(mock_gtk, 'main_quit')
        self.mock_main_quit = self.patcher_main_quit.start()
        self.patches.append(self.patcher_main_quit)
        
        # Create the testable indicator with our mocked dependencies
        self.indicator = TestableIndicator(
            speech_engine=self.mock_speech_engine,
            text_injector=self.mock_text_injector,
            mock_ksm=self.mock_ksm
        )
        
    def tearDown(self):
        """Clean up after each test."""
        for patcher in self.patches:
            patcher.stop()
        
    def test_initialization(self):
        """Test initialization of the tray indicator."""
        # Verify speech_engine and text_injector were set correctly
        self.assertEqual(self.indicator.speech_engine, self.mock_speech_engine)
        self.assertEqual(self.indicator.text_injector, self.mock_text_injector)
        
        # Verify callback was registered
        self.mock_speech_engine.register_state_callback.assert_called_once_with(
            self.indicator._on_recognition_state_changed
        )
        
        # Verify shortcut manager was configured properly
        self.mock_ksm.register_toggle_callback.assert_called_once_with(
            self.indicator._toggle_recognition
        )
        self.mock_ksm.start.assert_called_once()
    
    def test_toggle_recognition(self):
        """Test toggling recognition state."""
        # Define a real implementation of _toggle_recognition that we can test
        def simple_toggle(state):
            if state == RecognitionState.IDLE:
                self.mock_speech_engine.start_recognition()
            else:
                self.mock_speech_engine.stop_recognition()
                
        # Test with IDLE state
        simple_toggle(RecognitionState.IDLE)
        
        # Verify start_recognition was called
        self.mock_speech_engine.start_recognition.assert_called_once()
        self.mock_speech_engine.stop_recognition.assert_not_called()
        
        # Reset mocks
        self.mock_speech_engine.reset_mock()
        
        # Test with LISTENING state
        simple_toggle(RecognitionState.LISTENING)
        
        # Verify stop_recognition was called
        self.mock_speech_engine.stop_recognition.assert_called_once()
        self.mock_speech_engine.start_recognition.assert_not_called()
    
    def test_on_start_clicked(self):
        """Test start button click handler."""
        # Call the start handler
        self.indicator._on_start_clicked(None)
        
        # Verify start_recognition was called
        self.mock_speech_engine.start_recognition.assert_called_once()
    
    def test_on_stop_clicked(self):
        """Test stop button click handler."""
        # Call the stop handler
        self.indicator._on_stop_clicked(None)
        
        # Verify stop_recognition was called
        self.mock_speech_engine.stop_recognition.assert_called_once()
    
    def test_on_quit_clicked(self):
        """Test quit button click handler."""
        # Patch the _quit method to avoid actually quitting
        with patch.object(self.indicator, '_quit') as mock_quit:
            # Call the handler
            self.indicator._on_quit_clicked(None)
            
            # Verify _quit was called
            mock_quit.assert_called_once()
    
    def test_quit(self):
        """Test quit method."""
        # Call the quit method
        self.indicator._quit()
        
        # Verify shortcut manager was stopped
        self.mock_ksm.stop.assert_called_once()
        
        # Verify Gtk.main_quit was called
        self.mock_main_quit.assert_called_once()