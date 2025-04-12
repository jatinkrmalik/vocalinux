#!/usr/bin/env python3
"""
Main entry point for the Vocalinux application.
"""

import argparse
import atexit
import logging
import os
import sys
import signal
import threading
from pathlib import Path

# Add package to path for development mode
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Use absolute imports instead of relative imports
from src.speech_recognition.recognition_manager import SpeechRecognitionManager, RecognitionState
from src.text_injection.text_injector import TextInjector
from src.ui.audio_feedback import AudioFeedback
from src.ui.config_manager import ConfigManager
from src.ui.keyboard_shortcuts import KeyboardShortcuts
from src.ui.tray_indicator import TrayIndicator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global variables
recognition_manager = None
text_injector = None
audio_feedback = None
keyboard_shortcuts = None
tray_indicator = None
exit_event = threading.Event()

def cleanup():
    """Clean up resources when the application exits."""
    logger.info("Cleaning up resources...")
    
    # Stop recognition if it's running
    if recognition_manager:
        recognition_manager.stop_recognition()
    
    # Stop the keyboard listener
    if keyboard_shortcuts:
        keyboard_shortcuts.stop_listener()
        
    # Clean up audio resources - important to prevent memory corruption
    global audio_feedback
    if audio_feedback is not None:
        # Force PyAudio termination
        try:
            audio_feedback = None
        except Exception:
            pass
    
    # Signal exit event to stop any running threads
    exit_event.set()

def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info(f"Received signal {sig}, shutting down")
    cleanup()
    sys.exit(0)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Vocalinux")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--model-size", type=str, default="small", 
        help="Speech recognition model size (small, medium, large)"
    )
    parser.add_argument(
        "--engine", type=str, default="vosk", choices=["vosk", "whisper"],
        help="Speech recognition engine to use"
    )
    parser.add_argument(
        "--wayland", action="store_true", 
        help="Force Wayland compatibility mode"
    )
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    # Configure debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    logger.info("Initializing Vocalinux...")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function to run on exit
    atexit.register(cleanup)
    
    # Initialize components
    global recognition_manager, text_injector, audio_feedback, keyboard_shortcuts, tray_indicator
    
    # Initialize config manager first (used by other components)
    config_manager = ConfigManager()
    
    # Initialize text injector
    text_injector = TextInjector(wayland_mode=args.wayland)
    
    # Speech recognition manager
    recognition_manager = SpeechRecognitionManager(
        engine=args.engine,
        model_size=args.model_size
    )
    
    # Set up text callback to inject text
    recognition_manager.register_text_callback(text_injector.inject_text)
    
    # Initialize audio feedback (for sound notifications)
    try:
        audio_feedback = AudioFeedback()
    except Exception as e:
        logger.error(f"Failed to initialize audio feedback: {e}")
        audio_feedback = None
    
    # Initialize keyboard shortcuts
    keyboard_shortcut_config = config_manager.get('shortcuts', 'toggle_recognition', 'alt+shift+v')
    keyboard_shortcuts = KeyboardShortcuts()
    
    # Set up toggle callback
    def toggle_recognition():
        if recognition_manager.state == RecognitionState.IDLE:
            recognition_manager.start_recognition()
        else:
            recognition_manager.stop_recognition()
    
    # Register the shortcut with the callback
    keyboard_shortcuts.register_shortcut(keyboard_shortcut_config, toggle_recognition)
    
    # Initialize system tray
    tray_indicator = TrayIndicator(
        speech_engine=recognition_manager,
        text_injector=text_injector,
    )
    
    # Register the toggle function with the recognition manager's state callbacks
    # This will update the tray icon when the recognition state changes
    recognition_manager.register_state_callback(tray_indicator.update_recording_state)
    
    # Start the system tray
    tray_indicator.run()

if __name__ == "__main__":
    main()