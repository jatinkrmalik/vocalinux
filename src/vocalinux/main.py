#!/usr/bin/env python3
"""
Main entry point for Vocalinux application.
"""

import argparse
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import from the vocalinux package
from .speech_recognition import recognition_manager
from .text_injection import text_injector
from .ui import tray_indicator
from .ui.action_handler import ActionHandler


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Vocalinux")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--model",
        type=str,
        default="small",
        help="Speech recognition model size (small, medium, large)",
    )
    parser.add_argument(
        "--engine",
        type=str,
        default="vosk",
        choices=["vosk", "whisper"],
        help="Speech recognition engine to use",
    )
    parser.add_argument(
        "--wayland", action="store_true", help="Force Wayland compatibility mode"
    )
    return parser.parse_args()


def check_dependencies():
    """Check for required dependencies and provide helpful error messages."""
    missing_deps = []
    
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3, Gtk
    except (ImportError, ValueError) as e:
        missing_deps.append("GTK3 and AppIndicator3 (install with: sudo apt install python3-gi gir1.2-appindicator3-0.1)")
    
    try:
        import pynput
    except ImportError:
        missing_deps.append("pynput (install with: pip install pynput)")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests (install with: pip install requests)")
    
    if missing_deps:
        logger.error("Missing required dependencies:")
        for dep in missing_deps:
            logger.error(f"  - {dep}")
        logger.error("Please install the missing dependencies and try again.")
        return False
    
    return True


def main():
    """Main entry point for the application."""
    args = parse_arguments()

    # Configure debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Initialize logging manager early
    from .ui.logging_manager import initialize_logging
    initialize_logging()
    logger.info("Logging system initialized")

    # Check dependencies first
    if not check_dependencies():
        logger.error("Cannot start Vocalinux due to missing dependencies")
        sys.exit(1)

    # Initialize main components
    logger.info("Initializing Vocalinux...")

    try:
        # Initialize speech recognition engine
        speech_engine = recognition_manager.SpeechRecognitionManager(
            engine=args.engine,
            model_size=args.model,
        )

        # Initialize text injection system
        text_system = text_injector.TextInjector(wayland_mode=args.wayland)

        # Initialize action handler
        action_handler = ActionHandler(text_system)

        # Create a wrapper function to track injected text for action handler
        def text_callback_wrapper(text: str):
            """Wrapper to track injected text and handle it."""
            success = text_system.inject_text(text)
            if success:
                action_handler.set_last_injected_text(text)

        # Connect speech recognition to text injection and action handling
        speech_engine.register_text_callback(text_callback_wrapper)
        speech_engine.register_action_callback(action_handler.handle_action)

        # Initialize and start the system tray indicator
        indicator = tray_indicator.TrayIndicator(
            speech_engine=speech_engine,
            text_injector=text_system,
        )

        # Start the GTK main loop
        indicator.run()
        
    except Exception as e:
        logger.error(f"Failed to initialize Vocalinux: {e}")
        logger.error("Please check the logs above for more details")
        sys.exit(1)


if __name__ == "__main__":
    main()
