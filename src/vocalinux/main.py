#!/usr/bin/env python3
"""
Main entry point for Vocalinux application.
"""

import argparse
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import from the vocalinux package
from .ui import tray_indicator  # noqa: E402
from .ui.action_handler import ActionHandler  # noqa: E402


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
    parser.add_argument("--wayland", action="store_true", help="Force Wayland compatibility mode")
    return parser.parse_args()


def check_dependencies():
    """Check for required dependencies and provide helpful error messages."""
    missing_deps = []

    # pynput is used for keyboard detection but we check at module startup
    # requests is used by various components
    # These are intentional checks to provide user-friendly error messages
    try:
        import pynput  # noqa: F401
    except ImportError:
        missing_deps.append("pynput (install with: pip install pynput)")

    try:
        import requests  # noqa: F401
    except ImportError:
        missing_deps.append("requests (install with: pip install requests)")

    try:
        import gi

        gi.require_version("Gtk", "3.0")
        gi.require_version("AppIndicator3", "0.1")
    except (ImportError, ValueError):
        missing_deps.append(
            "GTK3 and AppIndicator3 (install with: sudo apt install "
            "python3-gi gir1.2-appindicator3-0.1)"
        )

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

    # Load saved configuration to get engine/model settings
    from .speech_recognition import recognition_manager
    from .text_injection import text_injector
    from .ui.config_manager import ConfigManager

    config_manager = ConfigManager()
    saved_settings = config_manager.get_settings().get("speech_recognition", {})
    audio_settings = config_manager.get_settings().get("audio", {})

    # CLI arguments take precedence over saved config
    # We need to check if the user explicitly provided arguments
    # by examining sys.argv since argparse defaults don't tell us this
    cli_engine_set = any(arg.startswith("--engine") for arg in sys.argv[1:])
    cli_model_set = any(arg.startswith("--model") for arg in sys.argv[1:])

    # Use CLI args if explicitly set, otherwise fall back to saved config, then defaults
    if cli_engine_set:
        engine = args.engine
        logger.info(f"Using engine={engine} (from command line)")
    else:
        engine = saved_settings.get("engine", args.engine)
        logger.info(f"Using engine={engine} (from saved config)")

    if cli_model_set:
        model_size = args.model
        logger.info(f"Using model={model_size} (from command line)")
    else:
        model_size = saved_settings.get("model_size", args.model)
        logger.info(f"Using model={model_size} (from saved config)")

    vad_sensitivity = saved_settings.get("vad_sensitivity", 3)
    silence_timeout = saved_settings.get("silence_timeout", 2.0)
    audio_device_index = audio_settings.get("device_index", None)

    logger.info(f"Final settings: engine={engine}, model={model_size}")
    if audio_device_index is not None:
        logger.info(f"Using audio device index={audio_device_index} (from saved config)")

    # Initialize main components
    logger.info("Initializing Vocalinux...")

    try:
        # Initialize speech recognition engine with saved/configured settings
        speech_engine = recognition_manager.SpeechRecognitionManager(
            engine=engine,
            model_size=model_size,
            vad_sensitivity=vad_sensitivity,
            silence_timeout=silence_timeout,
            audio_device_index=audio_device_index,
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
