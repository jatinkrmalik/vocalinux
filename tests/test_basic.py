"""
Basic tests for the Vocalinux application.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.speech_recognition.recognition_manager import SpeechRecognitionManager, RecognitionState
from src.text_injection.text_injector import TextInjector, DesktopEnvironment


class TestSpeechRecognition(unittest.TestCase):
    """Test cases for the speech recognition manager."""
    
    @patch('src.speech_recognition.recognition_manager.os.makedirs')
    def test_init_state(self, mock_makedirs):
        """Test the initial state of the speech recognition manager."""
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")
        self.assertEqual(manager.state, RecognitionState.IDLE)
        self.assertEqual(manager.engine, "vosk")
        self.assertEqual(manager.model_size, "small")
    
    @patch('src.speech_recognition.recognition_manager.os.makedirs')
    def test_callbacks(self, mock_makedirs):
        """Test callback registration and invocation."""
        manager = SpeechRecognitionManager(engine="vosk", model_size="small")
        
        # Mock callbacks
        text_callback = MagicMock()
        state_callback = MagicMock()
        
        # Register callbacks
        manager.register_text_callback(text_callback)
        manager.register_state_callback(state_callback)
        
        # Verify callbacks were registered
        self.assertIn(text_callback, manager.text_callbacks)
        self.assertIn(state_callback, manager.state_callbacks)
        
        # Test state update
        manager._update_state(RecognitionState.LISTENING)
        state_callback.assert_called_once_with(RecognitionState.LISTENING)


class TestTextInjection(unittest.TestCase):
    """Test cases for the text injector."""
    
    @patch('src.text_injection.text_injector.shutil.which')
    @patch('src.text_injection.text_injector.TextInjector._detect_environment')
    def test_init_x11(self, mock_detect, mock_which):
        """Test initialization in X11 environment."""
        mock_detect.return_value = DesktopEnvironment.X11
        mock_which.return_value = '/usr/bin/xdotool'  # Simulate xdotool exists
        
        injector = TextInjector()
        self.assertEqual(injector.environment, DesktopEnvironment.X11)
    
    @patch('src.text_injection.text_injector.subprocess.run')
    @patch('src.text_injection.text_injector.shutil.which')
    @patch('src.text_injection.text_injector.TextInjector._detect_environment')
    def test_inject_text_x11(self, mock_detect, mock_which, mock_run):
        """Test text injection in X11 environment."""
        mock_detect.return_value = DesktopEnvironment.X11
        mock_which.return_value = '/usr/bin/xdotool'
        
        injector = TextInjector()
        injector.inject_text("Hello, world!")
        
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(args[0][0], "xdotool")
        self.assertEqual(args[0][2], "--clearmodifiers")
        self.assertEqual(args[0][3], "Hello, world!")


if __name__ == '__main__':
    unittest.main()