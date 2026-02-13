"""
IBus engine for Vocalinux text injection.

This module provides an IBus input method engine that acts as a transparent
proxy - it passes all keystrokes through normally while allowing Vocalinux
to inject text directly via commit_text().

The engine should be set as the user's default input method. It will:
1. Pass all keyboard input through unchanged
2. Listen for text injection requests via a Unix socket or file
3. Commit injected text directly without switching engines

This is the preferred method for Wayland environments as it works universally
without requiring compositor-specific protocols.
"""

import logging
import os
import socket
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Check if IBus is available
try:
    import gi

    gi.require_version("IBus", "1.0")
    from gi.repository import GLib, GObject, IBus

    IBUS_AVAILABLE = True
except (ImportError, ValueError) as e:
    logger.debug(f"IBus not available: {e}")
    IBUS_AVAILABLE = False
    IBus = None
    GLib = None
    GObject = None


# File paths for communication
VOCALINUX_IBUS_DIR = Path.home() / ".local" / "share" / "vocalinux-ibus"
SOCKET_PATH = VOCALINUX_IBUS_DIR / "inject.sock"

# Engine identification
ENGINE_NAME = "vocalinux"
ENGINE_LONGNAME = "Vocalinux"
ENGINE_DESCRIPTION = "Vocalinux voice dictation (use as default input method)"
COMPONENT_NAME = "org.freedesktop.IBus.Vocalinux"


def ensure_ibus_dir() -> None:
    """Ensure the IBus data directory exists."""
    VOCALINUX_IBUS_DIR.mkdir(parents=True, exist_ok=True)


def is_ibus_available() -> bool:
    """Check if IBus is available on the system."""
    return IBUS_AVAILABLE


def is_engine_registered() -> bool:
    """Check if the Vocalinux IBus engine is registered."""
    if not IBUS_AVAILABLE:
        return False

    try:
        import subprocess

        result = subprocess.run(
            ["ibus", "list-engine"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return ENGINE_NAME in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def is_engine_active() -> bool:
    """Check if the Vocalinux IBus engine is currently active."""
    try:
        import subprocess

        result = subprocess.run(
            ["ibus", "engine"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and ENGINE_NAME in result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_current_engine() -> Optional[str]:
    """Get the currently active IBus engine name."""
    try:
        import subprocess

        result = subprocess.run(
            ["ibus", "engine"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def switch_engine(engine_name: str) -> bool:
    """Switch to the specified IBus engine."""
    import time

    try:
        import subprocess

        subprocess.run(
            ["ibus", "engine", engine_name],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # ibus engine command may return non-zero even on success
        # So we verify by checking the current engine
        time.sleep(0.2)
        current = get_current_engine()
        if current == engine_name:
            return True
        else:
            logger.warning(f"Engine switch failed: expected {engine_name}, got {current}")
            return False
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.error(f"Failed to switch IBus engine: {e}")
        return False


def is_engine_process_running() -> bool:
    """Check if the Vocalinux IBus engine process is running."""
    try:
        import subprocess

        result = subprocess.run(
            ["pgrep", "-f", "ibus_engine.py"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def start_engine_process() -> bool:
    """
    Start the IBus engine process in the background.

    This should be called by Vocalinux on startup to ensure the engine
    is running before attempting to switch to it.

    Returns:
        True if the engine was started or is already running, False otherwise
    """
    import subprocess
    import time

    if is_engine_process_running():
        logger.debug("IBus engine process already running")
        return True

    engine_script = Path(__file__).resolve()
    logger.info(f"Starting IBus engine process: {engine_script}")

    try:
        # Start the engine process in the background
        subprocess.Popen(
            ["python3", str(engine_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        # Wait a bit for the engine to start
        for _ in range(10):
            time.sleep(0.2)
            if is_engine_process_running():
                logger.info("IBus engine process started successfully")
                return True

        logger.error("IBus engine process failed to start")
        return False

    except Exception as e:
        logger.error(f"Failed to start IBus engine process: {e}")
        return False


def stop_engine_process() -> None:
    """Stop the IBus engine process if running."""
    try:
        import subprocess

        subprocess.run(
            ["pkill", "-f", "ibus_engine.py"],
            capture_output=True,
        )
        logger.info("IBus engine process stopped")
    except Exception as e:
        logger.debug(f"Failed to stop IBus engine process: {e}")


class VocalinuxEngine(IBus.Engine if IBUS_AVAILABLE else object):
    """
    IBus proxy engine for Vocalinux text injection.

    This engine acts as a transparent proxy:
    - All keyboard input passes through unchanged
    - Text injection requests are received via Unix socket
    - Injected text is committed directly to the focused application

    Users should set this as their default input method for seamless
    voice dictation support.
    """

    if IBUS_AVAILABLE:
        __gtype_name__ = "VocalinuxEngine"

    # Class-level reference to active engine instance
    _active_instance: Optional["VocalinuxEngine"] = None
    _socket_server: Optional[threading.Thread] = None
    _server_socket: Optional[socket.socket] = None

    def __init__(self):
        """Initialize the Vocalinux IBus engine."""
        if IBUS_AVAILABLE:
            super().__init__()
        logger.debug("VocalinuxEngine instance created")

    def do_enable(self) -> None:
        """Called when the engine is enabled/selected."""
        logger.info("VocalinuxEngine enabled - ready for text injection")
        VocalinuxEngine._active_instance = self

        # Start socket server if not already running
        if VocalinuxEngine._socket_server is None:
            self._start_socket_server()

    def do_disable(self) -> None:
        """Called when the engine is disabled/deselected."""
        logger.debug("VocalinuxEngine disabled (keeping instance for injection)")
        # NOTE: We intentionally do NOT clear _active_instance here.
        # IBus calls do_disable when focus changes between windows, but we still
        # want to be able to inject text. The engine process keeps running and
        # the instance remains valid for text injection.

    def do_focus_in(self) -> None:
        """Called when the engine gains focus."""
        logger.debug("VocalinuxEngine focus in")
        VocalinuxEngine._active_instance = self

    def do_focus_out(self) -> None:
        """Called when the engine loses focus."""
        logger.debug("VocalinuxEngine focus out")

    def do_process_key_event(self, keyval: int, keycode: int, state: int) -> bool:
        """
        Process key events.

        We pass through ALL keys unchanged since this is a proxy engine.
        The actual keyboard layout handling is done by the system.
        """
        return False  # Don't consume any keys - pass through

    def inject_text(self, text: str) -> bool:
        """
        Inject text into the currently focused application.

        Args:
            text: The text to inject

        Returns:
            True if injection was successful, False otherwise
        """
        if not text:
            return True

        try:
            logger.debug(f"Injecting text: {text[:50]}...")
            self.commit_text(IBus.Text.new_from_string(text))
            logger.info(f"Text injected via IBus: '{text[:20]}...' ({len(text)} chars)")
            return True
        except Exception as e:
            logger.error(f"Failed to inject text: {e}")
            return False

    @classmethod
    def _start_socket_server(cls) -> None:
        """Start the Unix socket server for receiving injection requests."""
        ensure_ibus_dir()

        # Remove existing socket
        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()

        def server_thread():
            try:
                cls._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                cls._server_socket.bind(str(SOCKET_PATH))
                cls._server_socket.listen(1)
                SOCKET_PATH.chmod(0o600)  # Only user can access

                logger.info(f"Socket server listening on {SOCKET_PATH}")

                while True:
                    try:
                        conn, _ = cls._server_socket.accept()
                        with conn:
                            data = conn.recv(65536)  # Max text size
                            if data:
                                text = data.decode("utf-8")
                                # Schedule injection on main thread
                                if cls._active_instance:

                                    def do_inject(t):
                                        cls._active_instance.inject_text(t)
                                        return False  # Run only once

                                    GLib.idle_add(do_inject, text)
                                    conn.sendall(b"OK")
                                else:
                                    logger.warning("No active engine instance")
                                    conn.sendall(b"NO_ENGINE")
                    except Exception as e:
                        logger.error(f"Socket connection error: {e}")

            except Exception as e:
                logger.error(f"Socket server error: {e}")

        cls._socket_server = threading.Thread(target=server_thread, daemon=True)
        cls._socket_server.start()

    @classmethod
    def stop_socket_server(cls) -> None:
        """Stop the socket server."""
        if cls._server_socket:
            try:
                cls._server_socket.close()
            except Exception:
                pass
            cls._server_socket = None

        if SOCKET_PATH.exists():
            SOCKET_PATH.unlink()


class VocalinuxEngineApplication:
    """
    Application wrapper for running the Vocalinux IBus engine.

    This is used when the engine is launched by IBus as a separate process.
    """

    def __init__(self):
        """Initialize the engine application."""
        if not IBUS_AVAILABLE:
            raise RuntimeError("IBus is not available")

        self.mainloop = GLib.MainLoop()
        self.bus = IBus.Bus()
        self.bus.connect("disconnected", self._on_disconnected)

        self.factory = IBus.Factory.new(self.bus.get_connection())
        self.factory.add_engine(
            ENGINE_NAME,
            GObject.type_from_name("VocalinuxEngine"),
        )

        self.bus.request_name(COMPONENT_NAME, 0)
        logger.info("Vocalinux IBus engine started")

        # Start the socket server immediately so it's ready for connections
        # even before the engine is activated via `ibus engine vocalinux`
        VocalinuxEngine._start_socket_server()

    def _on_disconnected(self, bus: "IBus.Bus") -> None:
        """Handle IBus disconnection."""
        logger.info("IBus disconnected, exiting")
        VocalinuxEngine.stop_socket_server()
        self.mainloop.quit()

    def run(self) -> None:
        """Run the engine main loop."""
        self.mainloop.run()


class IBusTextInjector:
    """
    Text injector that uses IBus for text injection.

    This class connects to the Vocalinux IBus engine via Unix socket
    and sends text to be injected. On initialization, it automatically:
    1. Installs the IBus component if not registered
    2. Saves the current engine
    3. Switches to the Vocalinux engine

    On cleanup (stop), it restores the previous engine.
    """

    def __init__(self, auto_activate: bool = True):
        """
        Initialize the IBus text injector.

        Args:
            auto_activate: If True, automatically install and activate the engine
        """
        if not IBUS_AVAILABLE:
            raise RuntimeError("IBus is not available")

        ensure_ibus_dir()
        self._previous_engine: Optional[str] = None

        if auto_activate:
            self._setup_engine()

    def _setup_engine(self) -> None:
        """Install and activate the IBus engine."""
        # Install component if not registered
        if not is_engine_registered():
            logger.info("IBus engine not registered, installing...")
            # Try user-level first (no sudo needed)
            if not install_ibus_component(system_wide=False):
                logger.info("User-level install failed, trying system-wide...")
                install_ibus_component(system_wide=True)

        # Check again after installation
        if not is_engine_registered():
            logger.error("Failed to register IBus engine")
            return

        # Start the engine process (Vocalinux starts it, not IBus)
        if not start_engine_process():
            logger.error("Failed to start IBus engine process")
            return

        # Save current engine and switch to Vocalinux
        if not is_engine_active():
            self._previous_engine = get_current_engine()
            if self._previous_engine:
                logger.info(f"Saving current engine: {self._previous_engine}")

            logger.info("Activating Vocalinux IBus engine...")
            if switch_engine(ENGINE_NAME):
                logger.info("Vocalinux IBus engine activated")
            else:
                logger.error("Failed to activate Vocalinux IBus engine")

    def stop(self) -> None:
        """
        Stop the IBus text injector and restore previous engine.

        Call this when Vocalinux is shutting down.
        """
        if self._previous_engine:
            logger.info(f"Restoring previous engine: {self._previous_engine}")
            switch_engine(self._previous_engine)
            self._previous_engine = None

        # Stop the engine process
        stop_engine_process()

    def inject_text(self, text: str) -> bool:
        """
        Inject text using the IBus engine.

        Args:
            text: The text to inject

        Returns:
            True if injection was successful, False otherwise
        """
        if not text or not text.strip():
            logger.debug("Empty text provided, skipping injection")
            return True

        logger.info(f"Starting IBus text injection: '{text[:20]}...' (length: {len(text)})")

        # Ensure vocalinux engine is active (user may have switched keyboard)
        if not is_engine_active():
            logger.debug("Vocalinux engine not active, re-activating...")
            switch_engine(ENGINE_NAME)

        try:
            if not SOCKET_PATH.exists():
                logger.error(
                    "IBus engine socket not found. " "Make sure Vocalinux IBus engine is running."
                )
                return False

            # Connect to engine socket and send text
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)
                sock.connect(str(SOCKET_PATH))
                sock.sendall(text.encode("utf-8"))

                # Wait for response
                response = sock.recv(64).decode("utf-8")
                if response == "OK":
                    logger.debug("Text injection successful")
                    return True
                else:
                    logger.error(f"Text injection failed: {response}")
                    return False

        except socket.timeout:
            logger.error("Timeout connecting to IBus engine")
            return False
        except FileNotFoundError:
            logger.error("IBus engine socket not found")
            return False
        except Exception as e:
            logger.error(f"Failed to inject text via IBus: {e}")
            return False


def install_ibus_component(system_wide: bool = False) -> bool:
    """
    Install the IBus component XML file.

    Args:
        system_wide: If True, install to /usr/share/ibus/component/ (requires root).
                    If False, install to user directory and set IBUS_COMPONENT_PATH.

    Returns:
        True if installation was successful, False otherwise
    """
    import subprocess

    # Get the path to the engine script
    engine_script = Path(__file__).resolve()

    component_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<component>
    <name>{COMPONENT_NAME}</name>
    <description>{ENGINE_DESCRIPTION}</description>
    <exec>python3 {engine_script}</exec>
    <version>1.0</version>
    <author>Vocalinux</author>
    <license>GPL-3.0</license>
    <homepage>https://github.com/jatinkrmalik/vocalinux</homepage>
    <textdomain>vocalinux</textdomain>
    <engines>
        <engine>
            <name>{ENGINE_NAME}</name>
            <language>other</language>
            <license>GPL-3.0</license>
            <author>Vocalinux</author>
            <icon>audio-input-microphone</icon>
            <layout>default</layout>
            <longname>{ENGINE_LONGNAME}</longname>
            <description>{ENGINE_DESCRIPTION}</description>
            <rank>50</rank>
        </engine>
    </engines>
</component>
"""

    try:
        if system_wide:
            component_dir = Path("/usr/share/ibus/component")
            component_file = component_dir / "vocalinux.xml"

            # Write to temp file and move with sudo
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
                f.write(component_xml)
                temp_path = f.name

            result = subprocess.run(
                ["sudo", "cp", temp_path, str(component_file)],
                capture_output=True,
                text=True,
            )
            os.unlink(temp_path)

            if result.returncode != 0:
                logger.error(f"Failed to install component: {result.stderr}")
                return False

            subprocess.run(
                ["sudo", "chmod", "644", str(component_file)],
                capture_output=True,
            )
        else:
            # User-level installation
            component_dir = Path.home() / ".local" / "share" / "ibus" / "component"
            component_dir.mkdir(parents=True, exist_ok=True)
            component_file = component_dir / "vocalinux.xml"
            component_file.write_text(component_xml)
            logger.info(f"Component installed to {component_file}")

        # Refresh IBus - restart with component path set so it picks up user components
        import time
        user_component_dir = Path.home() / ".local" / "share" / "ibus" / "component"
        env = os.environ.copy()
        env["IBUS_COMPONENT_PATH"] = f"{user_component_dir}:/usr/share/ibus/component"

        subprocess.run(["ibus", "write-cache"], capture_output=True, env=env)
        subprocess.run(["ibus", "restart"], capture_output=True, env=env)
        time.sleep(1)  # Give IBus time to restart

        logger.info(
            "IBus component installed successfully.\n"
            "Set 'Vocalinux' as your input method in system settings "
            "to enable voice dictation."
        )
        return True

    except Exception as e:
        logger.error(f"Failed to install IBus component: {e}")
        return False


def main():
    """Entry point when run as IBus engine process."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if not IBUS_AVAILABLE:
        logger.error("IBus is not available")
        return 1

    IBus.init()
    app = VocalinuxEngineApplication()
    app.run()
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
