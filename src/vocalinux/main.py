#!/usr/bin/env python3
"""
Main entry point for Vocalinux application.
"""

import argparse
import atexit
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Note: GTK-dependent modules (tray_indicator) are imported lazily after
# dependency checking to provide better error messages for pip/pipx users


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Vocalinux")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    # default model, language and engine are loaded from default config
    # due to priority of args over config
    parser.add_argument(
        "--model",
        type=str,
        choices=["small", "medium", "large"],
        help="Speech recognition model size (small, medium, large)",
    )
    parser.add_argument(
        "--language",
        type=str,
        choices=[
            "auto",
            "en-us",
            "en-in",
            "hi",
            "es",
            "fr",
            "de",
            "it",
            "pt",
            "ru",
            "zh",
            "ja",
            "ko",
            "ar",
        ],
        help=(
            "Speech recognition language (auto for auto-detect, en-us, "
            "hi, es, fr, de, it, pt, ru, zh, etc.)"
        ),
    )
    parser.add_argument(
        "--engine",
        type=str,
        choices=["vosk", "whisper", "whisper_cpp"],
        help="Speech recognition engine to use (whisper_cpp recommended for best performance)",
    )
    parser.add_argument(
        "--gpu",
        type=str,
        help=(
            "GPU name to use for acceleration. The selected name is persisted in the config. "
            "Use 'auto' to clear the saved GPU preference."
        ),
    )
    parser.add_argument(
        "--gpus",
        action="store_true",
        help="List detected GPUs that can be used with --gpu and exit",
    )
    parser.add_argument("--wayland", action="store_true", help="Force Wayland compatibility mode")
    parser.add_argument(
        "--start-minimized",
        action="store_true",
        help="Start minimized to system tray",
    )
    return parser.parse_args()


def list_available_gpus() -> int:
    """Print the currently detectable GPUs and return a process exit code."""
    from .utils.whispercpp_model_info import list_cuda_devices, list_vulkan_devices

    vulkan_devices = list_vulkan_devices()
    cuda_devices = list_cuda_devices()

    if not vulkan_devices and not cuda_devices:
        print("No GPUs detected.")
        return 1

    if vulkan_devices:
        print("Vulkan GPUs:")
        for device_index, device_name in vulkan_devices:
            print(f"  [{device_index}] {device_name}")

    if cuda_devices:
        print("CUDA GPUs:")
        for device_index, device_name in cuda_devices:
            print(f"  [{device_index}] {device_name}")

    return 0


def check_dependencies():
    """Check for required dependencies and provide helpful error messages."""
    missing_system_deps = []
    missing_python_deps = []

    # Check for GTK3
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk  # noqa: F401
    except (ImportError, ValueError):
        missing_system_deps.append(
            "GTK3 (install with: sudo apt install python3-gi gir1.2-gtk-3.0)"
        )

    # Check for AppIndicator3 / Ayatana AppIndicator
    try:
        import gi

        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3  # noqa: F401
    except (ImportError, ValueError):
        try:
            import gi

            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3  # noqa: F401
        except (ImportError, ValueError):
            missing_system_deps.append(
                "AppIndicator3/AyatanaAppIndicator3 - Required for system tray icon"
            )

    # pynput is used for keyboard detection but we check at module startup
    # requests is used by various components
    # These are intentional checks to provide user-friendly error messages
    try:
        import pynput  # noqa: F401
    except ImportError:
        missing_python_deps.append("pynput (install with: pip install pynput)")

    try:
        import requests  # noqa: F401
    except ImportError:
        missing_python_deps.append("requests (install with: pip install requests)")

    if missing_system_deps or missing_python_deps:
        logger.error("Missing required dependencies:")
        for dep in missing_system_deps + missing_python_deps:
            logger.error(f"  - {dep}")
        if missing_system_deps:
            logger.error("")
            logger.error("System GTK packages are required. Install them first:")
            logger.error("")
            logger.error("  Ubuntu/Debian:")
            logger.error(
                "    sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1"
            )
            logger.error("")
            logger.error("  NOTE: On GNOME Shell (default on Debian), you also need:")
            logger.error("    sudo apt install gnome-shell-extension-appindicator")
            logger.error("  Then log out and back in. Ubuntu includes this by default.")
            logger.error("")
            logger.error("  Fedora:")
            logger.error("    sudo dnf install python3-gobject gtk3 libappindicator-gtk3")
            logger.error("")
            logger.error("  Arch Linux:")
            logger.error("    sudo pacman -S python-gobject gtk3 libappindicator")
            logger.error("")
            logger.error(
                "For pipx users: Install system packages BEFORE running 'pipx install vocalinux'"
            )
            logger.error("")
            logger.error("For the best experience, use the recommended installer:")
            logger.error(
                "  curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh | bash"
            )
        return False

    return True


def check_display_available():
    """Check if a display is available for GTK."""
    try:
        import gi

        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk

        display = Gdk.Display.get_default()
        if display is None:
            logger.error("No display available. Vocalinux requires a graphical environment.")
            logger.error("")
            logger.error("If running remotely, ensure DISPLAY is set:")
            logger.error("  export DISPLAY=:0")
            logger.error("")
            logger.error("If running in a headless environment, Vocalinux cannot run.")
            return False
        return True
    except Exception as e:
        logger.error(f"Failed to initialize display: {e}")
        return False


def check_appindicator_support():
    try:
        from gi.repository import Gio

        proxy = Gio.DBusProxy.new_for_bus_sync(
            Gio.BusType.SESSION,
            Gio.DBusProxyFlags.DO_NOT_AUTO_START_AT_CONSTRUCTION,
            None,
            "org.freedesktop.DBus",
            "/org/freedesktop/DBus",
            "org.freedesktop.DBus",
            None,
        )
        names_variant = proxy.call_sync(
            "ListNames",
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
        if names_variant is not None:
            name_list = names_variant.unpack()[0]
            return "org.kde.StatusNotifierWatcher" in name_list
    except Exception:
        pass

    return True


def main():
    """Main entry point for the application."""
    args = parse_arguments()

    if getattr(args, "gpus", False):
        sys.exit(list_available_gpus())

    # Check for single instance BEFORE any initialization
    from . import single_instance

    if not single_instance.acquire_lock():
        # Another instance is already running - show notification and exit
        try:
            import time

            from gi.repository import Notify

            Notify.init("Vocalinux")
            notification = Notify.Notification.new(
                "Vocalinux",
                "Another instance is already running. Only one instance is allowed at a time.",
                "dialog-error",
            )
            notification.show()
            # Give notification time to display before exiting
            time.sleep(0.5)
        except Exception:
            # Fallback if notification fails (e.g., no display)
            pass
        sys.exit(1)

    # Register cleanup to release lock on exit
    atexit.register(single_instance.release_lock)

    # Configure debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Check dependencies first (before importing GTK-dependent modules)
    if not check_dependencies():
        logger.error("Cannot start Vocalinux due to missing dependencies")
        sys.exit(1)

    # Check if display is available before creating any GTK widgets
    if not check_display_available():
        sys.exit(1)

    if not check_appindicator_support():
        logger.warning("No StatusNotifierWatcher found on D-Bus session bus.")
        logger.warning("The system tray icon may not appear.")
        logger.warning("")
        logger.warning("If you are using GNOME Shell, install the AppIndicator extension:")
        logger.warning("  Debian:  sudo apt install gnome-shell-extension-appindicator")
        logger.warning("  Fedora:  sudo dnf install gnome-shell-extension-appindicator")
        logger.warning("  Arch:    sudo pacman -S gnome-shell-extension-appindicator")
        logger.warning("")
        logger.warning("After installing, log out and back in (or restart GNOME Shell).")

    # Now it's safe to import GTK-dependent modules
    from .common_types import RecognitionState
    from .speech_recognition import recognition_manager
    from .text_injection import text_injector
    from .ui import tray_indicator
    from .ui.action_handler import ActionHandler
    from .ui.config_manager import ConfigManager
    from .ui.logging_manager import initialize_logging

    # Initialize logging manager early
    initialize_logging()
    logger.info("Logging system initialized")

    # Try to start IBus daemon if not running (for text injection)
    # This helps on desktop environments where IBus doesn't start automatically
    try:
        from .text_injection import start_ibus_daemon

        if start_ibus_daemon():
            logger.debug("IBus daemon started for text injection")
    except Exception as e:
        logger.debug(f"Could not start IBus daemon: {e}")

    config_manager = ConfigManager()
    initialize_logging()
    logger.info("Logging system initialized")

    config_manager = ConfigManager()
    saved_settings = config_manager.get_settings().get("speech_recognition", {})
    audio_settings = config_manager.get_settings().get("audio", {})

    general_settings = config_manager.get_settings().get("general", {})
    first_run = general_settings.get("first_run", True)
    should_prompt_first_run = first_run and not args.start_minimized

    if should_prompt_first_run:
        from .ui.first_run_dialog import show_first_run_dialog

        result = show_first_run_dialog()
        if result == "yes":
            from .ui import autostart_manager

            if autostart_manager.set_autostart(True):
                config_manager.set("general", "autostart", True)
            else:
                config_manager.set("general", "autostart", False)
        elif result == "no":
            from .ui import autostart_manager

            autostart_manager.set_autostart(False)
            config_manager.set("general", "autostart", False)

        if result in {"yes", "no"}:
            config_manager.set("general", "first_run", False)
            config_manager.save_settings()

    # CLI arguments take precedence over saved config
    # We need to check if the user explicitly provided arguments
    # by examining sys.argv since argparse defaults don't tell us this
    cli_engine_set = any(arg.startswith("--engine") for arg in sys.argv[1:])
    cli_model_set = any(arg.startswith("--model") for arg in sys.argv[1:])
    cli_language_set = any(arg.startswith("--language") for arg in sys.argv[1:])
    cli_gpu_set = any(arg == "--gpu" or arg.startswith("--gpu=") for arg in sys.argv[1:])

    raw_gpu_arg = getattr(args, "gpu", None)
    clear_gpu_preference = (
        cli_gpu_set
        and isinstance(raw_gpu_arg, str)
        and raw_gpu_arg.strip().casefold() in {"auto", "default", "none", "cpu"}
    )
    if cli_gpu_set:
        gpu_name = None if clear_gpu_preference else raw_gpu_arg
        gpu_backend = None
        logger.info(
            "Using GPU selection from command line: %s",
            gpu_name if gpu_name is not None else "automatic",
        )
    else:
        gpu_name = saved_settings.get("gpu_name")
        gpu_backend = saved_settings.get("gpu_backend")
        if gpu_name:
            logger.info(f"Using GPU selection from saved config: {gpu_name} ({gpu_backend})")

    # Use CLI args if explicitly set, otherwise fall back to saved config, then defaults
    if cli_engine_set:
        engine = args.engine
        logger.info(f"Using engine={engine} (from command line)")
    else:
        engine = saved_settings.get("engine", args.engine)
        logger.info(f"Using engine={engine} (from saved config)")

    if cli_language_set:
        language = args.language
        logger.info(f"Using language={language} (from command line)")
    else:
        language = saved_settings.get("language", args.language)
        logger.info(f"Using language={language} (from saved config)")

    if cli_model_set:
        model_size = args.model
        logger.info(f"Using model={model_size} (from command line)")
    else:
        model_size = saved_settings.get("model_size", args.model)
        logger.info(f"Using model={model_size} (from saved config)")

    vad_sensitivity = saved_settings.get("vad_sensitivity", 3)
    silence_timeout = saved_settings.get("silence_timeout", 2.0)
    voice_commands_enabled = saved_settings.get("voice_commands_enabled")  # None = auto
    audio_device_index = audio_settings.get("device_index", None)

    logger.info(f"Final settings: engine={engine}, language={language}, model={model_size}")
    if audio_device_index is not None:
        logger.info(f"Using audio device index={audio_device_index} (from saved config)")

    # Initialize main components
    logger.info("Initializing Vocalinux...")

    try:
        # Initialize speech recognition engine with saved/configured settings
        speech_engine = recognition_manager.SpeechRecognitionManager(
            engine=engine,
            model_size=model_size,
            language=language,
            vad_sensitivity=vad_sensitivity,
            silence_timeout=silence_timeout,
            voice_commands_enabled=voice_commands_enabled,
            audio_device_index=audio_device_index,
            gpu_name=gpu_name,
            gpu_backend=gpu_backend,
        )

        should_persist_gpu_preference = cli_gpu_set or saved_settings.get("gpu_name") is not None
        if should_persist_gpu_preference:
            persisted_gpu_name = None if clear_gpu_preference else speech_engine.selected_gpu_name
            persisted_gpu_backend = (
                None if clear_gpu_preference else speech_engine.selected_gpu_backend
            )

            if (
                saved_settings.get("gpu_name") != persisted_gpu_name
                or saved_settings.get("gpu_backend") != persisted_gpu_backend
            ):
                config_manager.set("speech_recognition", "gpu_name", persisted_gpu_name)
                config_manager.set("speech_recognition", "gpu_backend", persisted_gpu_backend)
                config_manager.save_config()

        # Initialize text injection system
        text_system = text_injector.TextInjector(wayland_mode=args.wayland)

        # Initialize action handler
        action_handler = ActionHandler(text_system)

        # --- Callback wiring ---------------------------------------------------
        # The speech engine emits three kinds of events, each handled by a
        # dedicated callback registered below:
        #
        #   text_callback(text: str)
        #       Called on the recognition thread when a transcription segment
        #       is finalised.  The wrapper below strips whitespace, inserts
        #       inter-segment spaces, injects the text, and records it so
        #       "delete that" can undo it.
        #
        #   action_callback(action: str) -> bool
        #       Called when a voice command (e.g. "undo", "select all") is
        #       recognised.  Delegated directly to ActionHandler.handle_action.
        #
        #   state_callback(state: RecognitionState)
        #       Called whenever the engine transitions state (IDLE → LISTENING,
        #       etc.).  Used here to clear the "last injected" buffer when a
        #       new listening session starts.
        # ------------------------------------------------------------------

        def text_callback_wrapper(text: str) -> None:
            """Bridge between speech engine text events and the text injector.

            Called on the recognition thread with each finalised transcription
            segment.  Strips leading/trailing whitespace (whisper tokenizer
            sometimes prepends spaces), inserts a single space between
            consecutive segments, then injects via TextInjector.

            Args:
                text: Raw transcription segment from the speech engine.
            """
            text_to_inject = text.strip()
            if not text_to_inject:
                return

            # Add a separating space between consecutive dictation segments,
            # but never for the very first segment (avoids unwanted leading space
            # when starting dictation in an empty text field).
            if action_handler.last_injected_text and action_handler.last_injected_text.strip():
                text_to_inject = " " + text_to_inject
                logger.debug("Added space separator before new segment")

            success = text_system.inject_text(text_to_inject)
            if success:
                action_handler.set_last_injected_text(text)

        def on_state_change(state: RecognitionState) -> None:
            """Reset the last-injected buffer when a new listening session starts."""
            if state == RecognitionState.LISTENING:
                action_handler.set_last_injected_text("")

        # Connect speech recognition to text injection and action handling
        speech_engine.register_text_callback(text_callback_wrapper)
        speech_engine.register_action_callback(action_handler.handle_action)
        speech_engine.register_state_callback(on_state_change)

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
