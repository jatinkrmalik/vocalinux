"""
Tests for the text injection module.
"""

import os
import shutil
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock dependencies
sys.modules['src.ui.audio_feedback'] = MagicMock()

# Import the module after mocking
from src.text_injection.text_injector import DesktopEnvironment, TextInjector


class TestTextInjector(unittest.TestCase):
    """Test cases for the text injection functionality."""

    def setUp(self):
        """Set up for tests."""
        # Create patches for external functions
        self.patch_which = patch('shutil.which')
        self.mock_which = self.patch_which.start()
        
        self.patch_subprocess = patch('subprocess.run')
        self.mock_subprocess = self.patch_subprocess.start()
        
        self.patch_sleep = patch('time.sleep')
        self.mock_sleep = self.patch_sleep.start()
        
        # Setup environment variable patching
        self.env_patcher = patch.dict('os.environ', {
            'XDG_SESSION_TYPE': 'x11',
            'DISPLAY': ':0'
        })
        self.env_patcher.start()
        
        # Set default return values
        self.mock_which.return_value = '/usr/bin/xdotool'  # Default to having xdotool
        
        # Setup subprocess mock
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "1234"
        mock_process.stderr = ""
        self.mock_subprocess.return_value = mock_process
    
    def tearDown(self):
        """Clean up after tests."""
        self.patch_which.stop()
        self.patch_subprocess.stop()
        self.patch_sleep.stop()
        self.env_patcher.stop()
    
    def test_detect_x11_environment(self):
        """Test detection of X11 environment."""
        with patch.dict('os.environ', {'XDG_SESSION_TYPE': 'x11'}):
            injector = TextInjector()
            self.assertEqual(injector.environment, DesktopEnvironment.X11)
    
    def test_detect_wayland_environment(self):
        """Test detection of Wayland environment."""
        with patch.dict('os.environ', {'XDG_SESSION_TYPE': 'wayland'}):
            # Make wtype available for Wayland
            self.mock_which.side_effect = lambda cmd: '/usr/bin/wtype' if cmd == 'wtype' else None
            
            # Mock wtype test call to return success
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stderr = ""
            self.mock_subprocess.return_value = mock_process
            
            injector = TextInjector()
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)
            self.assertEqual(injector.wayland_tool, 'wtype')
    
    def test_force_wayland_mode(self):
        """Test forcing Wayland mode."""
        with patch.dict('os.environ', {'XDG_SESSION_TYPE': 'x11'}):
            # Make wtype available
            self.mock_which.side_effect = lambda cmd: '/usr/bin/wtype' if cmd == 'wtype' else None
            
            # Create injector with wayland_mode=True
            injector = TextInjector(wayland_mode=True)
            
            # Should be forced to Wayland
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)
    
    def test_wayland_fallback_to_xdotool(self):
        """Test fallback to XWayland with xdotool when wtype fails."""
        with patch.dict('os.environ', {'XDG_SESSION_TYPE': 'wayland'}):
            # Make both wtype and xdotool available
            self.mock_which.side_effect = lambda cmd: {
                'wtype': '/usr/bin/wtype',
                'xdotool': '/usr/bin/xdotool'
            }.get(cmd)
            
            # Make wtype test fail with compositor error
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr = "compositor does not support virtual keyboard protocol"
            self.mock_subprocess.return_value = mock_process
            
            # Initialize injector
            injector = TextInjector()
            
            # Should fall back to XWayland
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND_XDOTOOL)
    
    def test_x11_text_injection(self):
        """Test text injection in X11 environment."""
        # Setup X11 environment
        with patch.dict('os.environ', {'XDG_SESSION_TYPE': 'x11'}):
            injector = TextInjector()
            
            # Inject text
            injector.inject_text("Hello world")
            
            # Verify xdotool was called correctly
            # Because of chunking, we need to check all calls
            calls = [call[0][0] for call in self.mock_subprocess.call_args_list]
            
            # We should have at least one call with xdotool type
            xdotool_calls = [call for call in calls if 'xdotool' in call and 'type' in call]
            self.assertTrue(len(xdotool_calls) > 0, "No xdotool type calls were made")
    
    def test_wayland_text_injection(self):
        """Test text injection in Wayland environment using wtype."""
        with patch.dict('os.environ', {'XDG_SESSION_TYPE': 'wayland'}):
            # Make wtype available
            self.mock_which.side_effect = lambda cmd: '/usr/bin/wtype' if cmd == 'wtype' else None
            
            # Successful wtype test
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.stderr = ""
            self.mock_subprocess.return_value = mock_process
            
            # Initialize injector
            injector = TextInjector()
            self.assertEqual(injector.wayland_tool, 'wtype')
            
            # Inject text
            injector.inject_text("Hello world")
            
            # Verify wtype was called correctly
            self.mock_subprocess.assert_any_call(
                ['wtype', 'Hello world'], 
                check=True, 
                stderr=subprocess.PIPE, 
                text=True
            )
    
    def test_wayland_with_ydotool(self):
        """Test text injection in Wayland environment using ydotool."""
        with patch.dict('os.environ', {'XDG_SESSION_TYPE': 'wayland'}):
            # Make only ydotool available
            self.mock_which.side_effect = lambda cmd: '/usr/bin/ydotool' if cmd == 'ydotool' else None
            
            # Initialize injector
            injector = TextInjector()
            self.assertEqual(injector.wayland_tool, 'ydotool')
            
            # Inject text
            injector.inject_text("Hello world")
            
            # Verify ydotool was called correctly
            self.mock_subprocess.assert_any_call(
                ['ydotool', 'type', 'Hello world'], 
                check=True, 
                stderr=subprocess.PIPE, 
                text=True
            )
    
    def test_inject_special_characters(self):
        """Test injecting text with special characters that need escaping."""
        injector = TextInjector()
        
        # Text with special characters
        special_text = "Special 'quotes' and \"double quotes\" and $dollar signs"
        
        # Inject text
        injector.inject_text(special_text)
        
        # Check that the text was properly escaped
        calls = self.mock_subprocess.call_args_list
        
        # At least one call should contain the escaped special characters
        found_escaped = False
        for call in calls:
            args = call[0][0]
            if 'xdotool' in args and 'type' in args:
                # The text might be split into chunks, so we check if any call contains our escaped characters
                for chunk_index in range(3, len(args)):
                    if chunk_index < len(args):
                        chunk = args[chunk_index]
                        if "\'" in chunk or "\\\"" in chunk or "\\$" in chunk:
                            found_escaped = True
                            break
            if found_escaped:
                break
        
        self.assertTrue(found_escaped, "Special characters were not properly escaped")
    
    def test_empty_text_injection(self):
        """Test injecting empty text (should do nothing)."""
        injector = TextInjector()
        
        # Reset the subprocess mock to clear previous calls
        self.mock_subprocess.reset_mock()
        
        # Inject empty text
        injector.inject_text("")
        
        # No subprocess calls should have been made
        self.mock_subprocess.assert_not_called()
        
        # Try with just whitespace
        injector.inject_text("   ")
        
        # Still no subprocess calls
        self.mock_subprocess.assert_not_called()
    
    def test_missing_dependencies(self):
        """Test error when no text injection dependencies are available."""
        # No tools available
        self.mock_which.return_value = None
        
        # Should raise RuntimeError
        with self.assertRaises(RuntimeError):
            TextInjector()
    
    def test_xdotool_error_handling(self):
        """Test handling of xdotool errors."""
        # Setup xdotool to fail
        mock_error = subprocess.CalledProcessError(1, ['xdotool', 'type'], stderr="Error")
        self.mock_subprocess.side_effect = mock_error
        
        injector = TextInjector()
        
        # Get the audio feedback mock
        audio_feedback = sys.modules['src.ui.audio_feedback']
        audio_feedback.play_error_sound.reset_mock()
        
        # Inject text - this should call play_error_sound
        injector.inject_text("Test text")
        
        # Check that error sound was triggered
        audio_feedback.play_error_sound.assert_called_once()
