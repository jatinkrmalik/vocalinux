"""
Comprehensive test coverage for IBus engine module.

This test file provides extensive coverage for the IBus text injection engine,
testing initialization, signal handlers, socket communication, and text injection.
"""

import os
import socket
import struct
import subprocess
import sys
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, call, patch

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# Mock GI imports before importing the module (follow test_ibus_engine.py pattern)
mock_gi = MagicMock()
mock_ibus = MagicMock()
mock_glib = MagicMock()
mock_gobject = MagicMock()

# Set up IBus mock - Engine should be the actual MagicMock class, not an instance
mock_ibus.Engine = MagicMock
mock_ibus.Bus = MagicMock
mock_ibus.Factory = MagicMock
mock_ibus.Factory.new = MagicMock(return_value=MagicMock())
mock_ibus.Text = MagicMock()
mock_ibus.Text.new_from_string = MagicMock(return_value=MagicMock())

# Mock GLib.MainLoop
mock_glib.MainLoop = MagicMock

# Mock socket.SO_PEERCRED (Linux-specific constant)
if not hasattr(socket, 'SO_PEERCRED'):
    socket.SO_PEERCRED = 17

sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository"].IBus = mock_ibus
sys.modules["gi.repository"].GLib = mock_glib
sys.modules["gi.repository"].GObject = mock_gobject


class TestIBusEngineModuleFunctions(unittest.TestCase):
    """Test module-level functions in ibus_engine.py."""

    def setUp(self):
        """Set up test fixtures."""
        # No patching needed - module mocks are already set up at module level
        pass

    def tearDown(self):
        """Clean up after tests."""
        # Module cache cleanup not needed since mocks are global
        pass

    def test_ibus_setup_error_exception(self):
        """Test that IBusSetupError is a RuntimeError."""
        from vocalinux.text_injection.ibus_engine import IBusSetupError

        error = IBusSetupError("Test error")
        self.assertIsInstance(error, RuntimeError)
        self.assertEqual(str(error), "Test error")

    @patch("subprocess.run")
    def test_is_ibus_daemon_running_success(self, mock_run):
        """Test ibus daemon detection when daemon is running."""
        mock_run.return_value = MagicMock(returncode=0)
        from vocalinux.text_injection.ibus_engine import is_ibus_daemon_running

        result = is_ibus_daemon_running()
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["pgrep", "-x", "ibus-daemon"],
            capture_output=True,
            timeout=2,
        )

    @patch("subprocess.run")
    def test_is_ibus_daemon_running_not_running(self, mock_run):
        """Test ibus daemon detection when daemon is not running."""
        mock_run.return_value = MagicMock(returncode=1)
        from vocalinux.text_injection.ibus_engine import is_ibus_daemon_running

        result = is_ibus_daemon_running()
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_is_ibus_daemon_running_command_not_found(self, mock_run):
        """Test ibus daemon detection when pgrep is not found."""
        mock_run.side_effect = FileNotFoundError()
        from vocalinux.text_injection.ibus_engine import is_ibus_daemon_running

        result = is_ibus_daemon_running()
        self.assertFalse(result)

    def test_is_ibus_active_input_method_gtk_im_module(self):
        """Test IBus detection via GTK_IM_MODULE environment variable."""
        with patch.dict("os.environ", {"GTK_IM_MODULE": "ibus"}):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_is_ibus_active_input_method_qt_im_module(self):
        """Test IBus detection via QT_IM_MODULE environment variable."""
        with patch.dict("os.environ", {"QT_IM_MODULE": "ibus", "GTK_IM_MODULE": ""}):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_is_ibus_active_input_method_xmodifiers(self):
        """Test IBus detection via XMODIFIERS environment variable."""
        with patch.dict(
            "os.environ",
            {"XMODIFIERS": "@im=ibus", "GTK_IM_MODULE": "", "QT_IM_MODULE": ""},
        ):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_is_ibus_active_input_method_not_active(self):
        """Test when IBus is not the active input method."""
        with patch.dict(
            "os.environ",
            {"GTK_IM_MODULE": "fcitx", "QT_IM_MODULE": "", "XMODIFIERS": ""},
            clear=True,
        ):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertFalse(result)

    @patch("subprocess.run")
    def test_is_engine_registered_success(self, mock_run):
        """Test engine registration detection."""
        mock_run.return_value = MagicMock(returncode=0, stdout="vocalinux other-engine")
        from vocalinux.text_injection.ibus_engine import is_engine_registered

        result = is_engine_registered()
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_is_engine_registered_not_found(self, mock_run):
        """Test when engine is not registered."""
        mock_run.return_value = MagicMock(returncode=0, stdout="other-engine")
        from vocalinux.text_injection.ibus_engine import is_engine_registered

        result = is_engine_registered()
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_is_engine_active_success(self, mock_run):
        """Test when engine is active."""
        mock_run.return_value = MagicMock(returncode=0, stdout="vocalinux")
        from vocalinux.text_injection.ibus_engine import is_engine_active

        result = is_engine_active()
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_is_engine_active_not_active(self, mock_run):
        """Test when engine is not active."""
        mock_run.return_value = MagicMock(returncode=0, stdout="other-engine")
        from vocalinux.text_injection.ibus_engine import is_engine_active

        result = is_engine_active()
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_get_current_engine_success(self, mock_run):
        """Test getting the current engine."""
        mock_run.return_value = MagicMock(returncode=0, stdout="current-engine\n")
        from vocalinux.text_injection.ibus_engine import get_current_engine

        result = get_current_engine()
        self.assertEqual(result, "current-engine")

    @patch("subprocess.run")
    def test_get_current_engine_failure(self, mock_run):
        """Test when unable to get current engine."""
        mock_run.return_value = MagicMock(returncode=1)
        from vocalinux.text_injection.ibus_engine import get_current_engine

        result = get_current_engine()
        self.assertIsNone(result)

    @patch("subprocess.run")
    @patch("vocalinux.text_injection.ibus_engine.get_current_engine")
    def test_switch_engine_success(self, mock_get_current, mock_run):
        """Test switching engine successfully."""
        mock_get_current.return_value = "vocalinux"
        from vocalinux.text_injection.ibus_engine import switch_engine

        result = switch_engine("vocalinux")
        self.assertTrue(result)

    @patch("subprocess.run")
    @patch("vocalinux.text_injection.ibus_engine.get_current_engine")
    def test_switch_engine_failure(self, mock_get_current, mock_run):
        """Test when engine switch fails."""
        mock_get_current.return_value = "other-engine"
        from vocalinux.text_injection.ibus_engine import switch_engine

        result = switch_engine("vocalinux")
        self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.PID_FILE")
    def test_is_engine_process_running_no_pid_file(self, mock_pid_file):
        """Test when PID file doesn't exist."""
        mock_pid_file.exists.return_value = False
        from vocalinux.text_injection.ibus_engine import is_engine_process_running

        result = is_engine_process_running()
        self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.PID_FILE")
    @patch("os.kill")
    def test_is_engine_process_running_process_exists(self, mock_kill, mock_pid_file):
        """Test when engine process is running."""
        mock_pid_file.exists.return_value = True
        mock_pid_file.read_text.return_value = "1234"
        mock_kill.return_value = None  # No exception means process exists

        with patch("pathlib.Path.exists", return_value=False):  # /proc check fails
            from vocalinux.text_injection.ibus_engine import is_engine_process_running

            result = is_engine_process_running()
            self.assertTrue(result)

    @patch("vocalinux.text_injection.ibus_engine.PID_FILE")
    @patch("os.kill")
    def test_is_engine_process_running_process_not_exists(self, mock_kill, mock_pid_file):
        """Test when engine process doesn't exist."""
        mock_pid_file.exists.return_value = True
        mock_pid_file.read_text.return_value = "1234"
        mock_kill.side_effect = OSError()  # Process doesn't exist

        from vocalinux.text_injection.ibus_engine import is_engine_process_running

        result = is_engine_process_running()
        self.assertFalse(result)

    @patch("subprocess.run")
    @patch("vocalinux.text_injection.ibus_engine.start_engine_process")
    def test_start_ibus_daemon_already_running(self, mock_start_process, mock_run):
        """Test when ibus-daemon is already running."""
        with patch(
            "vocalinux.text_injection.ibus_engine.is_ibus_daemon_running", return_value=True
        ):
            from vocalinux.text_injection.ibus_engine import start_ibus_daemon

            result = start_ibus_daemon()
            self.assertTrue(result)
            mock_run.assert_not_called()

    @patch("vocalinux.text_injection.ibus_engine.is_ibus_available", return_value=False)
    def test_start_ibus_daemon_not_available(self, mock_available):
        """Test when IBus is not available."""
        with patch("vocalinux.text_injection.ibus_engine.is_ibus_daemon_running", return_value=False):
            from vocalinux.text_injection.ibus_engine import start_ibus_daemon

            result = start_ibus_daemon()
            self.assertFalse(result)

    def test_ensure_ibus_dir(self):
        """Test directory creation and permissions."""
        with patch("pathlib.Path.mkdir") as mock_mkdir, patch("pathlib.Path.chmod") as mock_chmod:
            from vocalinux.text_injection.ibus_engine import ensure_ibus_dir

            ensure_ibus_dir()
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_chmod.assert_called_once_with(0o700)

    def test_verify_peer_credentials_same_user(self):
        """Test peer credential verification for same user."""
        mock_socket = MagicMock()
        mock_uid = os.getuid()
        cred_data = struct.pack("iII", 1234, mock_uid, 1000)
        mock_socket.getsockopt.return_value = cred_data

        from vocalinux.text_injection.ibus_engine import verify_peer_credentials

        result = verify_peer_credentials(mock_socket)
        self.assertTrue(result)

    def test_verify_peer_credentials_different_user(self):
        """Test peer credential verification rejects different user."""
        mock_socket = MagicMock()
        mock_uid = os.getuid()
        other_uid = mock_uid + 1000  # Different user
        cred_data = struct.pack("iII", 1234, other_uid, 1000)
        mock_socket.getsockopt.return_value = cred_data

        from vocalinux.text_injection.ibus_engine import verify_peer_credentials

        result = verify_peer_credentials(mock_socket)
        self.assertFalse(result)

    def test_verify_peer_credentials_error(self):
        """Test peer credential verification error handling."""
        mock_socket = MagicMock()
        mock_socket.getsockopt.side_effect = OSError("Permission denied")

        from vocalinux.text_injection.ibus_engine import verify_peer_credentials

        result = verify_peer_credentials(mock_socket)
        self.assertFalse(result)


class TestVocalinuxEngine(unittest.TestCase):
    """Test VocalinuxEngine class."""

    def setUp(self):
        """Set up test fixtures - force module reload to get fresh mocks."""
        import importlib
        # Ensure our mocks are in sys.modules
        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = MagicMock()
        sys.modules["gi.repository"].IBus = mock_ibus
        sys.modules["gi.repository"].GLib = mock_glib
        sys.modules["gi.repository"].GObject = mock_gobject
        # Force reload the module so it picks up our mocks
        if "vocalinux.text_injection.ibus_engine" in sys.modules:
            importlib.reload(sys.modules["vocalinux.text_injection.ibus_engine"])

    def tearDown(self):
        """Clean up after tests."""
        # Reset class-level state
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine
        VocalinuxEngine._active_instance = None
        VocalinuxEngine._socket_server = None
        VocalinuxEngine._server_socket = None
        VocalinuxEngine._server_running = False

    def test_vocalinux_engine_init(self):
        """Test VocalinuxEngine initialization."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine()
        self.assertIsNotNone(engine)
        # Verify the engine is properly initialized with expected attributes
        self.assertIsInstance(engine, VocalinuxEngine)
        # Verify class-level attributes exist
        self.assertIsNone(VocalinuxEngine._active_instance)
        self.assertIsNone(VocalinuxEngine._socket_server)
        self.assertIsNone(VocalinuxEngine._server_socket)
        self.assertFalse(VocalinuxEngine._server_running)

    def test_vocalinux_engine_do_enable(self):
        """Test engine enable signal handler."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine()
        with patch.object(engine, "_start_socket_server"):
            engine.do_enable()
            # Verify active instance is set
            self.assertEqual(VocalinuxEngine._active_instance, engine)

    def test_vocalinux_engine_do_disable(self):
        """Test engine disable signal handler."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine()
        engine.do_enable()
        engine.do_disable()
        # Instance should still be active (not cleared on disable)
        self.assertEqual(VocalinuxEngine._active_instance, engine)

    def test_vocalinux_engine_do_focus_in(self):
        """Test engine focus in signal handler."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine()
        engine.do_focus_in()
        self.assertEqual(VocalinuxEngine._active_instance, engine)

    def test_vocalinux_engine_do_focus_out(self):
        """Test engine focus out signal handler."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine()
        VocalinuxEngine._active_instance = engine
        engine.do_focus_out()
        # Focus out should not clear the active instance
        self.assertEqual(VocalinuxEngine._active_instance, engine)

    def test_vocalinux_engine_do_process_key_event(self):
        """Test engine key event processing."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine()
        result = engine.do_process_key_event(65, 38, 0)
        # Should return False to pass through all keys
        self.assertFalse(result)

    def test_vocalinux_engine_inject_text_empty(self):
        """Test text injection with empty text."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine()
        result = engine.inject_text("")
        # Empty text should return True (no-op)
        self.assertTrue(result)

    def test_vocalinux_engine_inject_text_success(self):
        """Test successful text injection."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine()
        mock_text = MagicMock()
        mock_ibus.Text.new_from_string.return_value = mock_text

        # Mock the commit_text method
        engine.commit_text = MagicMock()
        result = engine.inject_text("Hello World")
        self.assertTrue(result)
        engine.commit_text.assert_called_once()

    def test_vocalinux_engine_inject_text_failure(self):
        """Test text injection error handling."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine()
        # Mock commit_text to raise an exception
        engine.commit_text = MagicMock(side_effect=Exception("Test error"))
        result = engine.inject_text("Hello World")
        self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("socket.socket")
    def test_start_socket_server(self, mock_socket_cls, mock_ensure_dir, mock_socket_path):
        """Test socket server startup."""
        mock_socket_path.exists.return_value = False
        mock_socket = MagicMock()
        mock_socket_cls.return_value = mock_socket

        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        # Start socket server in background
        VocalinuxEngine._server_running = False
        with patch("threading.Thread"):
            VocalinuxEngine._start_socket_server()
            self.assertTrue(VocalinuxEngine._server_running)

    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    def test_stop_socket_server(self, mock_socket_path):
        """Test socket server shutdown."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        mock_socket = MagicMock()
        VocalinuxEngine._server_socket = mock_socket
        VocalinuxEngine._server_running = True
        mock_socket_path.exists.return_value = True

        VocalinuxEngine.stop_socket_server()
        self.assertFalse(VocalinuxEngine._server_running)
        self.assertIsNone(VocalinuxEngine._server_socket)


class TestIBusTextInjector(unittest.TestCase):
    """Test IBusTextInjector class."""

    def setUp(self):
        """Set up test fixtures."""
        # Module mocks are already set up at module level
        pass

    def tearDown(self):
        """Clean up after tests."""
        # No cleanup needed
        pass

    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_ibus_text_injector_init_no_auto_activate(self, mock_ensure_dir):
        """Test IBusTextInjector initialization without auto-activation."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)
        self.assertIsNotNone(injector)
        # Verify auto_activate=False means _previous_engine is not set
        self.assertFalse(hasattr(injector, '_previous_engine') and injector._previous_engine is not None)
        # Verify the auto_activate flag is properly False (no setup was called)
        self.assertIsNone(injector._previous_engine)

    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_registered", return_value=True)
    @patch("vocalinux.text_injection.ibus_engine.is_component_up_to_date", return_value=True)
    @patch("vocalinux.text_injection.ibus_engine.start_engine_process", return_value=True)
    @patch("vocalinux.text_injection.ibus_engine.is_engine_active", return_value=True)
    def test_ibus_text_injector_init_with_auto_activate(
        self, mock_active, mock_start, mock_update, mock_registered, mock_ensure_dir
    ):
        """Test IBusTextInjector initialization with auto-activation."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=True)
        self.assertIsNotNone(injector)

    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.switch_engine")
    @patch("vocalinux.text_injection.ibus_engine.get_current_engine", return_value="other-engine")
    def test_ibus_text_injector_stop(
        self, mock_current_engine, mock_switch, mock_ensure_dir
    ):
        """Test IBusTextInjector stop restores previous engine."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)
        injector._previous_engine = "other-engine"

        injector.stop()
        mock_switch.assert_called_once_with("other-engine")

    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("socket.socket")
    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_active", return_value=True)
    def test_ibus_text_injector_inject_text_success(
        self, mock_active, mock_socket_path, mock_socket_cls, mock_ensure_dir
    ):
        """Test successful text injection."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        mock_socket_path.exists.return_value = True
        mock_socket = MagicMock()
        mock_socket.__enter__.return_value = mock_socket
        mock_socket.__exit__.return_value = None
        mock_socket.recv.return_value = b"OK"
        mock_socket_cls.return_value = mock_socket

        injector = IBusTextInjector(auto_activate=False)
        result = injector.inject_text("Hello World")
        self.assertTrue(result)

    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_active", return_value=True)
    def test_ibus_text_injector_inject_text_empty(self, mock_active, mock_ensure_dir):
        """Test text injection with empty text."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)
        result = injector.inject_text("")
        self.assertTrue(result)

    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_active", return_value=True)
    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    def test_ibus_text_injector_socket_not_found(self, mock_socket_path, mock_active, mock_ensure_dir):
        """Test text injection when socket is not found."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        mock_socket_path.exists.return_value = False

        injector = IBusTextInjector(auto_activate=False)
        result = injector.inject_text("Hello World")
        self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_active", return_value=True)
    @patch("socket.socket")
    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    def test_ibus_text_injector_socket_timeout(
        self, mock_socket_path, mock_socket_cls, mock_active, mock_ensure_dir
    ):
        """Test text injection with socket timeout."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        mock_socket_path.exists.return_value = True
        mock_socket = MagicMock()
        mock_socket.__enter__.return_value = mock_socket
        mock_socket.__exit__.return_value = None
        mock_socket.connect.side_effect = socket.timeout()
        mock_socket_cls.return_value = mock_socket

        injector = IBusTextInjector(auto_activate=False)
        result = injector.inject_text("Hello World")
        self.assertFalse(result)


class TestVocalinuxEngineApplication(unittest.TestCase):
    """Test VocalinuxEngineApplication class."""

    def setUp(self):
        """Set up test fixtures - force module reload to get fresh mocks."""
        import importlib
        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = MagicMock()
        sys.modules["gi.repository"].IBus = mock_ibus
        sys.modules["gi.repository"].GLib = mock_glib
        sys.modules["gi.repository"].GObject = mock_gobject
        if "vocalinux.text_injection.ibus_engine" in sys.modules:
            importlib.reload(sys.modules["vocalinux.text_injection.ibus_engine"])

    def tearDown(self):
        """Clean up after tests."""
        pass

    @patch("vocalinux.text_injection.ibus_engine.VocalinuxEngine._start_socket_server")
    def test_vocalinux_engine_application_init(self, mock_start_server):
        """Test VocalinuxEngineApplication initialization."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngineApplication

        app = VocalinuxEngineApplication()
        self.assertIsNotNone(app)
        # Verify bus attribute is properly initialized
        self.assertIsNotNone(app.bus)
        # Verify mainloop attribute is properly initialized
        self.assertIsNotNone(app.mainloop)
        # Verify they are the correct types (mocked in test)
        self.assertEqual(type(app.bus).__name__, 'MagicMock')
        self.assertEqual(type(app.mainloop).__name__, 'MagicMock')

    @patch("vocalinux.text_injection.ibus_engine.VocalinuxEngine._start_socket_server")
    def test_vocalinux_engine_application_on_disconnected(self, mock_start_server):
        """Test IBus disconnection handler."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngineApplication

        app = VocalinuxEngineApplication()
        mock_bus = MagicMock()

        with patch.object(app.mainloop, "quit"):
            app._on_disconnected(mock_bus)
            app.mainloop.quit.assert_called_once()

    @patch("vocalinux.text_injection.ibus_engine.VocalinuxEngine._start_socket_server")
    def test_vocalinux_engine_application_run(self, mock_start_server):
        """Test engine application main loop."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngineApplication

        app = VocalinuxEngineApplication()
        with patch.object(app.mainloop, "run"):
            app.run()
            app.mainloop.run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
