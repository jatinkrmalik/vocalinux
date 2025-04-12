#!/usr/bin/env python3
"""
Main entry point for Vocalinux application.
"""

import argparse
import logging
import os
import sys

# Add package to path for development mode
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from speech_recognition import recognition_manager
from text_injection import text_injector
from ui import tray_indicator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Vocalinux")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--model", type=str, default="small", 
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
    
    # Initialize main components
    logger.info("Initializing Vocalinux...")
    
    # Initialize speech recognition engine
    speech_engine = recognition_manager.SpeechRecognitionManager(
        engine=args.engine,
        model_size=args.model,
    )
    
    # Initialize text injection system
    text_system = text_injector.TextInjector(wayland_mode=args.wayland)
    
    # Connect speech recognition to text injection
    speech_engine.register_text_callback(text_system.inject_text)
    
    # Initialize and start the system tray indicator
    indicator = tray_indicator.TrayIndicator(
        speech_engine=speech_engine,
        text_injector=text_system,
    )
    
    # Start the GTK main loop
    indicator.run()
    
    
if __name__ == "__main__":
    main()