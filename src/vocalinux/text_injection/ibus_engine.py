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
import signal
import socket
import struct
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class IBusSetupError(RuntimeError):
    """
    Exception raised when IBus engine setup fails.

    This exception is raised when the IBus text injector cannot be properly
    initialized, allowing the caller to fall back to alternative text
    injection methods.
    """

    pass


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
PID_FILE = VOCALINUX_IBUS_DIR / "engine.pid"

# Engine identification
ENGINE_NAME = "vocalinux"
ENGINE_LONGNAME = "Vocalinux"
ENGINE_DESCRIPTION = "Vocalinux voice dictation (use as default input method)"
COMPONENT_NAME = "org.freedesktop.IBus.Vocalinux"


def ensure_ibus_dir() -> None:
    """Ensure the IBus data directory exists with secure permissions."""
    VOCALINUX_IBUS_DIR.mkdir(parents=True, exist_ok=True)
    # Secure the directory - only owner can access (prevents socket hijacking)
    VOCALINUX_IBUS_DIR.chmod(0o700)


def verify_peer_credentials(conn: socket.socket) -> bool:
    """
    Verify that the connecting process belongs to the same user.

    Uses SO_PEERCRED to get the UID of the peer process and compares
    it to our own UID. This prevents other users from injecting text.

    Args:
        conn: The connected socket

    Returns:
        True if peer is same user, False otherwise
    """
    try:
        # SO_PEERCRED returns a struct with pid, uid, gid
        # struct ucred { pid_t pid; uid_t uid; gid_t gid; }
        cred = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("iII"))
        pid, uid, gid = struct.unpack("iII", cred)

        my_uid = os.getuid()
        if uid != my_uid:
            logger.warning(f"Rejected connection from UID {uid} (expected {my_uid})")
            return False

        logger.debug(f"Accepted connection from PID {pid}, UID {uid}")
        return True
    except (OSError, struct.error) as e:
        logger.error(f"Failed to verify peer credentials: {e}")
        return False


def is_ibus_available() -> bool:
    """Check if IBus is available on the system."""
    return IBUS_AVAILABLE


def _get_expected_component_xml() -> str:
    """Generate the expected component XML content for the current installation."""
    engine_script = Path(__file__).resolve()
    python_exec = sys.executable

    return f"""<?xml version="1.0" encoding="utf-8"?>
<component>
    <name>{COMPONENT_NAME}</name>
    <description>{ENGINE_DESCRIPTION}</description>
    <exec>{python_exec} {engine_script}</exec>
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


def is_component_up_to_date() -> bool:
    """
    Check if the installed IBus component XML matches the current installation.

    Returns:
        True if component exists and matches expected content, False otherwise
    """
    component_file = Path.home() / ".local" / "share" / "ibus" / "component" / "vocalinux.xml"

    if not component_file.exists():
        return False

    try:
        installed_content = component_file.read_text()
        expected_content = _get_expected_component_xml()
        return installed_content.strip() == expected_content.strip()
    except Exception as e:
        logger.debug(f"Failed to check component XML: {e}")
        return False


def is_engine_registered() -> bool:
    """Check if the Vocalinux IBus engine is registered."""
    if not IBUS_AVAILABLE:
        return False

    try:
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
        if not PID_FILE.exists():
            return False

        pid = int(PID_FILE.read_text().strip())
        # Check if process exists and is our engine
        os.kill(pid, 0)  # Raises OSError if process doesn't exist
        # Verify it's actually our process by checking cmdline
        cmdline_path = Path(f"/proc/{pid}/cmdline")
        if cmdline_path.exists():
            cmdline = cmdline_path.read_text()
            return "ibus_engine.py" in cmdline and "vocalinux" in cmdline
        return True  # Process exists but can't verify cmdline
    except (OSError, ValueError, FileNotFoundError):
        # Process doesn't exist or PID file is invalid
        if PID_FILE.exists():
            PID_FILE.unlink()  # Clean up stale PID file
        return False


def start_engine_process() -> bool:
    """
    Start the IBus engine process in the background.

    This should be called by Vocalinux on startup to ensure the engine
    is running before attempting to switch to it.

    Returns:
        True if the engine was started or is already running, False otherwise
    """
    import time

    if is_engine_process_running():
        logger.debug("IBus engine process already running")
        return True

    engine_script = Path(__file__).resolve()
    logger.info(f"Starting IBus engine process: {engine_script}")

    try:
        # Start the engine process using the same Python interpreter
        # and inherit the current environment (for venv compatibility)
        env = os.environ.copy()
        # Ensure PYTHONPATH includes current site-packages if in a venv
        if hasattr(sys, "prefix") and sys.prefix != sys.base_prefix:
            # We're in a virtual environment - ensure it's preserved
            env["VIRTUAL_ENV"] = sys.prefix
            # Keep PATH so the venv's bin is first

        process = subprocess.Popen(
            [sys.executable, str(engine_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env=env,
        )

        # Write PID file for tracking
        ensure_ibus_dir()
        PID_FILE.write_text(str(process.pid))

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
        if not PID_FILE.exists():
            logger.debug("No PID file found, engine not running")
            return

        pid = int(PID_FILE.read_text().strip())
        # Verify it's our process before killing
        cmdline_path = Path(f"/proc/{pid}/cmdline")
        if cmdline_path.exists():
            cmdline = cmdline_path.read_text()
            if "ibus_engine.py" not in cmdline or "vocalinux" not in cmdline:
                logger.warning(f"PID {pid} is not our engine process, skipping kill")
                PID_FILE.unlink()
                return

        os.kill(pid, signal.SIGTERM)
        logger.info(f"IBus engine process (PID {pid}) stopped")
        PID_FILE.unlink()
    except (OSError, ValueError, FileNotFoundError) as e:
        logger.debug(f"Failed to stop IBus engine process: {e}")
        if PID_FILE.exists():
            PID_FILE.unlink()


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
    _server_running: bool = False

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

        cls._server_running = True

        def server_thread():
            try:
                cls._server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                cls._server_socket.bind(str(SOCKET_PATH))
                cls._server_socket.listen(1)
                SOCKET_PATH.chmod(0o600)  # Only user can access

                logger.info(f"Socket server listening on {SOCKET_PATH}")

                while cls._server_running:
                    try:
                        conn, _ = cls._server_socket.accept()
                        with conn:
                            # Verify peer is same user (defense in depth)
                            if not verify_peer_credentials(conn):
                                conn.sendall(b"UNAUTHORIZED")
                                continue

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
                    except OSError as e:
                        # Check if we're shutting down
                        if not cls._server_running:
                            logger.debug("Socket server shutting down")
                            break
                        logger.error(f"Socket connection error: {e}")
                    except Exception as e:
                        logger.error(f"Socket connection error: {e}")

            except Exception as e:
                if cls._server_running:
                    logger.error(f"Socket server error: {e}")

        cls._socket_server = threading.Thread(target=server_thread, daemon=True)
        cls._socket_server.start()

    @classmethod
    def stop_socket_server(cls) -> None:
        """Stop the socket server."""
        cls._server_running = False
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
        # Install or update component if needed
        if not is_engine_registered():
            logger.info("IBus engine not registered, installing...")
            if not install_ibus_component(system_wide=False):
                logger.info("User-level install failed, trying system-wide...")
                install_ibus_component(system_wide=True)
        elif not is_component_up_to_date():
            logger.info("IBus component XML is outdated, updating...")
            install_ibus_component(system_wide=False)

        # Check again after installation
        if not is_engine_registered():
            raise IBusSetupError(
                "Failed to register IBus engine. "
                "Try running 'ibus list-engine' to verify installation."
            )

        # Start the engine process (Vocalinux starts it, not IBus)
        if not start_engine_process():
            raise IBusSetupError("Failed to start IBus engine process. Check logs for details.")

        # Save current engine and switch to Vocalinux
        if not is_engine_active():
            self._previous_engine = get_current_engine()
            if self._previous_engine:
                logger.info(f"Saving current engine: {self._previous_engine}")

            logger.info("Activating Vocalinux IBus engine...")
            if switch_engine(ENGINE_NAME):
                logger.info("Vocalinux IBus engine activated")
            else:
                raise IBusSetupError(
                    "Failed to activate Vocalinux IBus engine. "
                    "Try manually: ibus engine vocalinux"
                )

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
    component_xml = _get_expected_component_xml()

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
