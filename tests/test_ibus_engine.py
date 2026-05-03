"""
Tests for IBus engine functionality.
"""

import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Mock GI imports before importing the module
mock_gi = MagicMock()
mock_ibus = MagicMock()
mock_glib = MagicMock()
mock_gobject = MagicMock()

# Set up IBus mock
mock_ibus.Engine = MagicMock
mock_ibus.Bus = MagicMock
mock_ibus.Factory = MagicMock
mock_ibus.Text = MagicMock()
mock_ibus.Text.new_from_string = MagicMock(return_value=MagicMock())

sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository"].IBus = mock_ibus
sys.modules["gi.repository"].GLib = mock_glib
sys.modules["gi.repository"].GObject = mock_gobject


class TestIBusSetupError(unittest.TestCase):
    """Tests for IBusSetupError exception."""

    def test_is_runtime_error_subclass(self):
        """Test that IBusSetupError inherits from RuntimeError."""
        from vocalinux.text_injection.ibus_engine import IBusSetupError

        self.assertTrue(issubclass(IBusSetupError, RuntimeError))

    def test_accepts_message(self):
        """Test that IBusSetupError accepts a message."""
        from vocalinux.text_injection.ibus_engine import IBusSetupError

        error = IBusSetupError("Test message")
        self.assertEqual(str(error), "Test message")


class TestIBusTextInjectorSetupFailures(unittest.TestCase):
    """Tests for IBusTextInjector raising IBusSetupError on setup failures."""

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.start_engine_process")
    def test_raises_on_engine_process_failure(self, mock_start_engine, mock_ensure_dir):
        """Test that IBusSetupError is raised when engine process fails to start."""
        mock_start_engine.return_value = False  # Process start fails

        from vocalinux.text_injection.ibus_engine import IBusSetupError, IBusTextInjector

        with self.assertRaises(IBusSetupError) as context:
            IBusTextInjector(auto_activate=True)

        self.assertIn("Failed to start IBus engine process", str(context.exception))

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    @patch("vocalinux.text_injection.ibus_engine.start_engine_process")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_active")
    @patch("vocalinux.text_injection.ibus_engine.get_current_engine")
    @patch("vocalinux.text_injection.ibus_engine.switch_engine")
    def test_raises_on_activation_failure(
        self,
        mock_switch,
        mock_get_current,
        mock_is_active,
        mock_start_engine,
        mock_socket_path,
        mock_ensure_dir,
    ):
        """Test that IBusSetupError is raised when engine activation fails."""
        mock_start_engine.return_value = True
        mock_socket_path.exists.return_value = True
        mock_is_active.return_value = False
        mock_get_current.return_value = "xkb:us::eng"
        mock_switch.return_value = False  # Activation fails

        from vocalinux.text_injection.ibus_engine import IBusSetupError, IBusTextInjector

        with self.assertRaises(IBusSetupError) as context:
            IBusTextInjector(auto_activate=True)

        self.assertIn("Failed to activate Vocalinux IBus engine", str(context.exception))

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    @patch("vocalinux.text_injection.ibus_engine.time")
    @patch("vocalinux.text_injection.ibus_engine.start_engine_process")
    @patch("vocalinux.text_injection.ibus_engine.get_current_xkb_layout")
    @patch("vocalinux.text_injection.ibus_engine.restore_xkb_layout")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_active")
    @patch("vocalinux.text_injection.ibus_engine.get_current_engine")
    @patch("vocalinux.text_injection.ibus_engine.switch_engine")
    def test_warns_and_proceeds_when_socket_not_ready(
        self,
        mock_switch,
        mock_get_engine,
        mock_is_active,
        mock_restore_xkb,
        mock_get_xkb,
        mock_start_engine,
        mock_time,
        mock_socket_path,
        mock_ensure_dir,
    ):
        """Covers the for/else warning branch: all 15 socket-readiness retries exhaust,
        warning is logged, and activation proceeds anyway (graceful degradation)."""
        mock_start_engine.return_value = True
        mock_socket_path.exists.return_value = False
        mock_is_active.return_value = False
        mock_get_engine.return_value = "xkb:us::eng"
        mock_switch.return_value = True
        mock_get_xkb.return_value = ("us", "", "")

        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        with self.assertLogs("vocalinux.text_injection.ibus_engine", level="WARNING") as log:
            injector = IBusTextInjector(auto_activate=True)

        self.assertTrue(any("socket not ready" in msg for msg in log.output))
        self.assertEqual(mock_socket_path.exists.call_count, 15)
        self.assertEqual(mock_time.sleep.call_count, 15)
        self.assertIsNotNone(injector)


class TestIBusEngineHelpers(unittest.TestCase):
    """Tests for IBus engine helper functions."""

    def test_ensure_ibus_dir_creates_directory(self):
        """Test that ensure_ibus_dir creates the directory."""
        with patch("vocalinux.text_injection.ibus_engine.VOCALINUX_IBUS_DIR") as mock_dir:
            mock_dir.mkdir = MagicMock()
            from vocalinux.text_injection.ibus_engine import ensure_ibus_dir

            ensure_ibus_dir()
            mock_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_is_ibus_available_returns_constant(self):
        """Test is_ibus_available returns the module constant."""
        from vocalinux.text_injection.ibus_engine import IBUS_AVAILABLE, is_ibus_available

        self.assertEqual(is_ibus_available(), IBUS_AVAILABLE)


class TestIsEngineActive(unittest.TestCase):
    """Tests for is_engine_active function."""

    @patch("subprocess.run")
    def test_engine_active(self, mock_run):
        """Test detection when engine is active."""
        mock_run.return_value = MagicMock(stdout="vocalinux", returncode=0)

        from vocalinux.text_injection.ibus_engine import is_engine_active

        result = is_engine_active()
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_engine_not_active(self, mock_run):
        """Test detection when engine is not active."""
        mock_run.return_value = MagicMock(stdout="xkb:us::eng", returncode=0)

        from vocalinux.text_injection.ibus_engine import is_engine_active

        result = is_engine_active()
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_subprocess_error(self, mock_run):
        """Test handling of subprocess errors."""
        import subprocess

        mock_run.side_effect = subprocess.SubprocessError("Command failed")

        from vocalinux.text_injection.ibus_engine import is_engine_active

        result = is_engine_active()
        self.assertFalse(result)


class TestGetCurrentEngine(unittest.TestCase):
    """Tests for get_current_engine function."""

    @patch("subprocess.run")
    def test_get_current_engine_success(self, mock_run):
        """Test getting current engine successfully."""
        mock_run.return_value = MagicMock(stdout="xkb:fr::fra\n", returncode=0)

        from vocalinux.text_injection.ibus_engine import get_current_engine

        result = get_current_engine()
        self.assertEqual(result, "xkb:fr::fra")

    @patch("subprocess.run")
    def test_get_current_engine_error(self, mock_run):
        """Test handling of errors when getting current engine."""
        mock_run.return_value = MagicMock(returncode=1)

        from vocalinux.text_injection.ibus_engine import get_current_engine

        result = get_current_engine()
        self.assertIsNone(result)

    @patch("subprocess.run")
    def test_subprocess_exception(self, mock_run):
        """Test handling of subprocess exceptions."""
        import subprocess

        mock_run.side_effect = subprocess.SubprocessError("Failed")

        from vocalinux.text_injection.ibus_engine import get_current_engine

        result = get_current_engine()
        self.assertIsNone(result)


class TestSwitchEngine(unittest.TestCase):
    """Tests for switch_engine function."""

    @patch("subprocess.run")
    def test_switch_engine_success(self, mock_run):
        """Test switching engine successfully."""
        # First call: ibus engine <name> (switch)
        # Second call: ibus engine (get current) - for verification
        switch_result = MagicMock(returncode=0)
        verify_result = MagicMock(returncode=0, stdout="vocalinux\n")
        mock_run.side_effect = [switch_result, verify_result]

        from vocalinux.text_injection.ibus_engine import switch_engine

        result = switch_engine("vocalinux")
        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)

    @patch("subprocess.run")
    def test_switch_engine_failure(self, mock_run):
        """Test switching engine failure."""
        # First call: ibus engine <name> (switch)
        # Second call: ibus engine (get current) - returns different engine
        switch_result = MagicMock(returncode=1)
        verify_result = MagicMock(returncode=0, stdout="xkb:us::eng\n")
        mock_run.side_effect = [switch_result, verify_result]

        from vocalinux.text_injection.ibus_engine import switch_engine

        result = switch_engine("nonexistent")
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_switch_engine_exception(self, mock_run):
        """Test handling of subprocess exceptions."""
        import subprocess

        mock_run.side_effect = subprocess.SubprocessError("Failed")

        from vocalinux.text_injection.ibus_engine import switch_engine

        result = switch_engine("vocalinux")
        self.assertFalse(result)


class TestIBusTextInjector(unittest.TestCase):
    """Tests for IBusTextInjector class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temp directory for socket
        self.temp_dir = tempfile.mkdtemp()
        self.socket_path = Path(self.temp_dir) / "inject.sock"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_active")
    @patch("vocalinux.text_injection.ibus_engine.start_engine_process")
    @patch("vocalinux.text_injection.ibus_engine.get_current_engine")
    @patch("vocalinux.text_injection.ibus_engine.switch_engine")
    def test_init_auto_activate(
        self,
        mock_switch,
        mock_get_current,
        mock_start_engine,
        mock_is_active,
        mock_socket_path,
        mock_ensure_dir,
    ):
        """Test initialization with auto_activate=True."""
        mock_socket_path.exists.return_value = True
        mock_is_active.return_value = False
        mock_start_engine.return_value = True
        mock_get_current.return_value = "xkb:us::eng"
        mock_switch.return_value = True

        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=True)

        # ensure_ibus_dir is called at least once
        self.assertGreaterEqual(mock_ensure_dir.call_count, 1)
        # Engine should be started
        mock_start_engine.assert_called_once()
        # Should switch to vocalinux engine
        mock_switch.assert_called_once_with("vocalinux")
        self.assertEqual(injector._previous_engine, "xkb:us::eng")

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_init_no_auto_activate(self, mock_ensure_dir):
        """Test initialization with auto_activate=False."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)

        mock_ensure_dir.assert_called_once()
        self.assertIsNone(injector._previous_engine)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", False)
    def test_init_ibus_not_available(self):
        """Test initialization raises when IBus is not available."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        with self.assertRaises(RuntimeError):
            IBusTextInjector()

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.switch_engine")
    def test_stop_restores_engine(self, mock_switch, mock_ensure_dir):
        """Test stop() restores previous engine."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)
        injector._previous_engine = "xkb:fr::fra"

        injector.stop()

        mock_switch.assert_called_once_with("xkb:fr::fra")
        self.assertIsNone(injector._previous_engine)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_stop_no_previous_engine(self, mock_ensure_dir):
        """Test stop() when no previous engine was saved."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)

        # Should not raise
        injector.stop()

    @patch("vocalinux.text_injection.ibus_engine.restore_xkb_layout")
    @patch("vocalinux.text_injection.ibus_engine.stop_engine_process")
    @patch("vocalinux.text_injection.ibus_engine.switch_engine")
    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_stop_restores_xkb_layout(
        self, mock_ensure_dir, mock_switch, mock_stop_proc, mock_restore_xkb
    ):
        """Test stop() restores the captured XKB layout (#292)."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)
        injector._previous_xkb_layout = ("es", "catalan", "compose:menu")

        injector.stop()

        mock_restore_xkb.assert_called_once_with("es", "catalan", "compose:menu")
        self.assertIsNone(injector._previous_xkb_layout)

    @patch("vocalinux.text_injection.ibus_engine.restore_xkb_layout")
    @patch("vocalinux.text_injection.ibus_engine.stop_engine_process")
    @patch("vocalinux.text_injection.ibus_engine.switch_engine")
    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_stop_skips_xkb_restore_when_no_layout(
        self, mock_ensure_dir, mock_switch, mock_stop_proc, mock_restore_xkb
    ):
        """Test stop() skips XKB restore when no layout was captured."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)
        injector._previous_xkb_layout = None

        injector.stop()

        mock_restore_xkb.assert_not_called()

    @patch("vocalinux.text_injection.ibus_engine.restore_xkb_layout")
    @patch("vocalinux.text_injection.ibus_engine.get_current_xkb_layout")
    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    @patch("vocalinux.text_injection.ibus_engine.start_engine_process", return_value=True)
    @patch("vocalinux.text_injection.ibus_engine.switch_engine", return_value=True)
    @patch("vocalinux.text_injection.ibus_engine.get_current_engine", return_value="xkb:us::eng")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_active", return_value=False)
    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_setup_engine_captures_and_restores_xkb(
        self,
        mock_ensure_dir,
        mock_active,
        mock_get_engine,
        mock_switch,
        mock_start_proc,
        mock_socket_path,
        mock_get_xkb,
        mock_restore_xkb,
    ):
        """Test _setup_engine captures XKB layout and restores it after activation (#292)."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        mock_socket_path.exists.return_value = True
        mock_get_xkb.return_value = ("fr", "azerty", "")

        injector = IBusTextInjector(auto_activate=False)
        injector._setup_engine()

        mock_get_xkb.assert_called_once()
        self.assertEqual(injector._previous_xkb_layout, ("fr", "azerty", ""))
        mock_restore_xkb.assert_called_once_with("fr", "azerty", "")

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_inject_text_empty(self, mock_ensure_dir):
        """Test inject_text with empty text returns True."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)

        result = injector.inject_text("")
        self.assertTrue(result)

        result = injector.inject_text("   ")
        self.assertTrue(result)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    def test_inject_text_socket_not_found(self, mock_socket_path, mock_ensure_dir):
        """Test inject_text when socket doesn't exist."""
        mock_socket_path.exists.return_value = False

        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        injector = IBusTextInjector(auto_activate=False)

        result = injector.inject_text("Hello")
        self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_inject_text_success(self, mock_ensure_dir):
        """Test successful text injection via socket."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        # Create a mock server socket
        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.bind(str(self.socket_path))
        server_sock.listen(1)

        def handle_connection():
            conn, _ = server_sock.accept()
            with conn:
                data = conn.recv(65536)
                self.assertEqual(data.decode("utf-8"), "Hello World")
                conn.sendall(b"OK")

        server_thread = threading.Thread(target=handle_connection, daemon=True)
        server_thread.start()

        with patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH", self.socket_path):
            injector = IBusTextInjector(auto_activate=False)
            result = injector.inject_text("Hello World")

        server_sock.close()
        self.assertTrue(result)

    @patch("vocalinux.text_injection.ibus_engine.switch_engine")
    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_inject_text_no_engine_retries_and_recovers(self, mock_ensure_dir, mock_switch):
        """Test inject_text retries once on NO_ENGINE and succeeds on second attempt."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.bind(str(self.socket_path))
        server_sock.listen(2)

        call_count = 0

        def handle_connection():
            nonlocal call_count
            for _ in range(2):
                conn, _ = server_sock.accept()
                with conn:
                    conn.recv(65536)
                    call_count += 1
                    if call_count == 1:
                        conn.sendall(b"NO_ENGINE")
                    else:
                        conn.sendall(b"OK")

        server_thread = threading.Thread(target=handle_connection, daemon=True)
        server_thread.start()

        with patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH", self.socket_path):
            with patch("vocalinux.text_injection.ibus_engine.time"):
                injector = IBusTextInjector(auto_activate=False)
                result = injector.inject_text("Hello")

        server_sock.close()
        self.assertTrue(result)
        self.assertEqual(call_count, 2)
        mock_switch.assert_called_with("vocalinux")

    @patch("vocalinux.text_injection.ibus_engine.switch_engine")
    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_inject_text_no_engine_fails_after_retry(self, mock_ensure_dir, mock_switch):
        """Test inject_text returns False when NO_ENGINE persists after retry."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.bind(str(self.socket_path))
        server_sock.listen(2)

        def handle_connection():
            for _ in range(2):
                conn, _ = server_sock.accept()
                with conn:
                    conn.recv(65536)
                    conn.sendall(b"NO_ENGINE")

        server_thread = threading.Thread(target=handle_connection, daemon=True)
        server_thread.start()

        with patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH", self.socket_path):
            with patch("vocalinux.text_injection.ibus_engine.time"):
                injector = IBusTextInjector(auto_activate=False)
                result = injector.inject_text("Hello")

        server_sock.close()
        self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    @patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH")
    def test_inject_text_timeout(self, mock_socket_path, mock_ensure_dir):
        """Test text injection timeout handling."""
        mock_socket_path.exists.return_value = True

        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        with patch("socket.socket") as mock_socket_class:
            mock_socket_instance = MagicMock()
            mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket_instance)
            mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)
            mock_socket_instance.connect.side_effect = socket.timeout("Connection timeout")

            injector = IBusTextInjector(auto_activate=False)
            result = injector.inject_text("Hello")

        self.assertFalse(result)


class TestTextInjectorWithIBus(unittest.TestCase):
    """Tests for TextInjector integration with IBus."""

    def setUp(self):
        """Set up test fixtures."""
        self.patch_which = patch("shutil.which")
        self.mock_which = self.patch_which.start()

        self.patch_subprocess = patch("subprocess.run")
        self.mock_subprocess = self.patch_subprocess.start()

        self.patch_sleep = patch("time.sleep")
        self.mock_sleep = self.patch_sleep.start()

        # Default to having xdotool available
        self.mock_which.return_value = "/usr/bin/xdotool"

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

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.is_ibus_available")
    @patch("vocalinux.text_injection.ibus_engine.is_ibus_active_input_method")
    @patch("vocalinux.text_injection.ibus_engine.IBusTextInjector")
    def test_wayland_prefers_ibus(
        self, mock_injector_class, mock_is_active_im, mock_ibus_available
    ):
        """Test that Wayland environment prefers IBus when available."""
        mock_ibus_available.return_value = True
        mock_is_active_im.return_value = True
        mock_injector_instance = MagicMock()
        mock_injector_class.return_value = mock_injector_instance

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

            # Patch the import inside text_injector
            with patch(
                "vocalinux.text_injection.text_injector.is_ibus_available",
                return_value=True,
            ):
                with patch(
                    "vocalinux.text_injection.text_injector.is_ibus_active_input_method",
                    return_value=True,
                ):
                    with patch(
                        "vocalinux.text_injection.text_injector.IBusTextInjector",
                        mock_injector_class,
                    ):
                        injector = TextInjector()

                        # Should be using IBus
                        self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND_IBUS)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.is_ibus_available")
    @patch("vocalinux.text_injection.ibus_engine.is_ibus_active_input_method")
    @patch("vocalinux.text_injection.ibus_engine.IBusTextInjector")
    def test_x11_prefers_ibus(self, mock_injector_class, mock_is_active_im, mock_ibus_available):
        """Test that X11 environment prefers IBus when available."""
        mock_ibus_available.return_value = True
        mock_is_active_im.return_value = True
        mock_injector_instance = MagicMock()
        mock_injector_class.return_value = mock_injector_instance

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

            with patch(
                "vocalinux.text_injection.text_injector.is_ibus_available",
                return_value=True,
            ):
                with patch(
                    "vocalinux.text_injection.text_injector.is_ibus_active_input_method",
                    return_value=True,
                ):
                    with patch(
                        "vocalinux.text_injection.text_injector.IBusTextInjector",
                        mock_injector_class,
                    ):
                        injector = TextInjector()

                        self.assertEqual(injector.environment, DesktopEnvironment.X11_IBUS)

    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    def test_x11_fallback_when_ibus_unavailable(self, mock_ibus_available):
        """Test X11 falls back to xdotool when IBus unavailable."""
        mock_ibus_available.return_value = False

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            self.mock_which.side_effect = lambda cmd: (
                "/usr/bin/xdotool" if cmd == "xdotool" else None
            )

            from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

            injector = TextInjector()

            self.assertEqual(injector.environment, DesktopEnvironment.X11)

    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    def test_wayland_fallback_when_ibus_unavailable(self, mock_ibus_available):
        """Test Wayland falls back to other tools when IBus unavailable."""
        mock_ibus_available.return_value = False

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            # Make ydotool available
            self.mock_which.side_effect = lambda cmd: (
                "/usr/bin/ydotool" if cmd == "ydotool" else None
            )

            from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

            injector = TextInjector()

            # Should fall back to WAYLAND with ydotool
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)
            self.assertEqual(injector.wayland_tool, "ydotool")

    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    @patch("vocalinux.text_injection.text_injector.IBusTextInjector")
    def test_ibus_inject_text(self, mock_injector_class, mock_ibus_available):
        """Test text injection via IBus."""
        mock_ibus_available.return_value = True
        mock_injector_instance = MagicMock()
        mock_injector_instance.inject_text.return_value = True
        mock_injector_class.return_value = mock_injector_instance

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from vocalinux.text_injection.text_injector import TextInjector

            injector = TextInjector()
            result = injector.inject_text("Hello via IBus")

            self.assertTrue(result)
            mock_injector_instance.inject_text.assert_called_once_with("Hello via IBus")

    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    @patch("vocalinux.text_injection.text_injector.IBusTextInjector")
    def test_stop_calls_ibus_stop(self, mock_injector_class, mock_ibus_available):
        """Test that stop() calls IBus injector stop."""
        mock_ibus_available.return_value = True
        mock_injector_instance = MagicMock()
        mock_injector_class.return_value = mock_injector_instance

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from vocalinux.text_injection.text_injector import TextInjector

            injector = TextInjector()
            injector.stop()

    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    @patch("vocalinux.text_injection.text_injector.is_ibus_active_input_method")
    @patch("vocalinux.text_injection.text_injector.IBusTextInjector")
    def test_ibus_inject_text(self, mock_injector_class, mock_is_active_im, mock_ibus_available):
        """Test text injection via IBus."""
        mock_ibus_available.return_value = True
        mock_is_active_im.return_value = True
        mock_injector_instance = MagicMock()
        mock_injector_instance.inject_text.return_value = True
        mock_injector_class.return_value = mock_injector_instance

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from vocalinux.text_injection.text_injector import TextInjector

            injector = TextInjector()
            result = injector.inject_text("Hello via IBus")

            self.assertTrue(result)
            mock_injector_instance.inject_text.assert_called_once_with("Hello via IBus")

    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    @patch("vocalinux.text_injection.text_injector.is_ibus_active_input_method")
    @patch("vocalinux.text_injection.text_injector.IBusTextInjector")
    def test_stop_calls_ibus_stop(
        self, mock_injector_class, mock_is_active_im, mock_ibus_available
    ):
        """Test that stop() calls IBus injector stop."""
        mock_ibus_available.return_value = True
        mock_is_active_im.return_value = True
        mock_injector_instance = MagicMock()
        mock_injector_class.return_value = mock_injector_instance

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from vocalinux.text_injection.text_injector import TextInjector

            injector = TextInjector()
            injector.stop()

            mock_injector_instance.stop.assert_called_once()


class TestDesktopEnvironmentEnumWithIBus(unittest.TestCase):
    """Tests for DesktopEnvironment enum including IBus variants."""

    def test_enum_includes_wayland_ibus(self):
        """Test that WAYLAND_IBUS enum value exists."""
        from vocalinux.text_injection.text_injector import DesktopEnvironment

        self.assertEqual(DesktopEnvironment.WAYLAND_IBUS.value, "wayland-ibus")

    def test_enum_includes_x11_ibus(self):
        """Test that X11_IBUS enum value exists."""
        from vocalinux.text_injection.text_injector import DesktopEnvironment

        self.assertEqual(DesktopEnvironment.X11_IBUS.value, "x11-ibus")


class TestIsIbusActiveInputMethod(unittest.TestCase):
    """Tests for is_ibus_active_input_method function."""

    def test_detects_ibus_via_gtk_im_module(self):
        """Test detection when GTK_IM_MODULE is set to ibus."""
        with patch.dict(os.environ, {"GTK_IM_MODULE": "ibus"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_detects_ibus_python_via_gtk_im_module(self):
        """Test detection when GTK_IM_MODULE is set to ibus-python."""
        with patch.dict(os.environ, {"GTK_IM_MODULE": "ibus-python"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_detects_ibus_via_qt_im_module(self):
        """Test detection when QT_IM_MODULE is set to ibus."""
        with patch.dict(os.environ, {"QT_IM_MODULE": "ibus"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_detects_ibus_via_xmodifiers(self):
        """Test detection when XMODIFIERS contains @im=ibus."""
        with patch.dict(os.environ, {"XMODIFIERS": "@im=ibus"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_not_active_when_gtk_is_xim(self):
        """Test returns False when GTK_IM_MODULE is xim."""
        with patch.dict(os.environ, {"GTK_IM_MODULE": "xim"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertFalse(result)

    def test_not_active_when_qt_is_fcitx(self):
        """Test returns False when QT_IM_MODULE is fcitx."""
        with patch.dict(os.environ, {"QT_IM_MODULE": "fcitx"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertFalse(result)

    def test_not_active_when_xmodifiers_is_fcitx(self):
        """Test returns False when XMODIFIERS is @im=fcitx."""
        with patch.dict(os.environ, {"XMODIFIERS": "@im=fcitx"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.is_ibus_daemon_running", return_value=False)
    def test_not_active_when_no_env_vars_and_no_daemon(self, mock_daemon):
        """Test returns False when no env vars set and daemon is not running."""
        with patch.dict(os.environ, {}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.get_current_engine", return_value="xkb:us::eng")
    @patch("vocalinux.text_injection.ibus_engine.is_ibus_daemon_running", return_value=True)
    def test_active_via_daemon_when_no_env_vars(self, mock_daemon, mock_engine):
        """Test returns True when no env vars but daemon is running with active engine."""
        with patch.dict(os.environ, {}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    @patch("vocalinux.text_injection.ibus_engine.get_current_engine", return_value=None)
    @patch("vocalinux.text_injection.ibus_engine.is_ibus_daemon_running", return_value=True)
    def test_not_active_when_daemon_running_but_no_engine(self, mock_daemon, mock_engine):
        """Test returns False when daemon is running but no engine is active."""
        with patch.dict(os.environ, {}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertFalse(result)

    def test_not_active_when_other_im_configured(self):
        """Test returns False when another IM is explicitly configured, even if daemon runs."""
        with patch.dict(os.environ, {"GTK_IM_MODULE": "fcitx"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.is_ibus_daemon_running", return_value=False)
    def test_empty_string_env_vars_return_false(self, mock_daemon):
        """Test returns False when env vars are empty strings and daemon not running."""
        with patch.dict(
            os.environ,
            {"GTK_IM_MODULE": "", "QT_IM_MODULE": "", "XMODIFIERS": ""},
            clear=True,
        ):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertFalse(result)

    def test_gtk_im_module_case_insensitive(self):
        """Test detection is case-insensitive for GTK_IM_MODULE."""
        with patch.dict(os.environ, {"GTK_IM_MODULE": "IBUS"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_qt_im_module_case_insensitive(self):
        """Test detection is case-insensitive for QT_IM_MODULE."""
        with patch.dict(os.environ, {"QT_IM_MODULE": "IBUS"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_xmodifiers_case_insensitive(self):
        """Test detection is case-insensitive for XMODIFIERS."""
        with patch.dict(os.environ, {"XMODIFIERS": "@IM=IBUS"}, clear=True):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_priority_order_gtk_over_qt(self):
        """Test GTK_IM_MODULE takes priority over QT_IM_MODULE."""
        with patch.dict(
            os.environ,
            {"GTK_IM_MODULE": "ibus", "QT_IM_MODULE": "fcitx"},
            clear=True,
        ):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)

    def test_priority_order_qt_over_xmodifiers(self):
        """Test QT_IM_MODULE takes priority over XMODIFIERS."""
        with patch.dict(
            os.environ,
            {"QT_IM_MODULE": "ibus", "XMODIFIERS": "@im=fcitx"},
            clear=True,
        ):
            from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

            result = is_ibus_active_input_method()
            self.assertTrue(result)


class TestTextInjectorWithIbusActiveInputMethod(unittest.TestCase):
    """Tests for TextInjector with is_ibus_active_input_method check."""

    def setUp(self):
        """Set up test fixtures."""
        self.patch_which = patch("shutil.which")
        self.mock_which = self.patch_which.start()

        self.patch_subprocess = patch("subprocess.run")
        self.mock_subprocess = self.patch_subprocess.start()

        # Default to having ydotool available
        self.mock_which.side_effect = lambda cmd: ("/usr/bin/ydotool" if cmd == "ydotool" else None)

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = ""
        mock_process.stderr = ""
        self.mock_subprocess.return_value = mock_process

    def tearDown(self):
        """Clean up after tests."""
        self.patch_which.stop()
        self.patch_subprocess.stop()

    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    @patch("vocalinux.text_injection.text_injector.is_ibus_active_input_method")
    @patch("vocalinux.text_injection.text_injector.is_ibus_daemon_running")
    def test_skips_ibus_when_not_active_input_method(
        self, mock_daemon_running, mock_is_active_im, mock_is_available
    ):
        """Test that IBus is skipped when not the active input method."""
        mock_is_available.return_value = True
        mock_is_active_im.return_value = False  # IBus installed but not active
        mock_daemon_running.return_value = True

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

            injector = TextInjector()

            # Should fall back to WAYLAND with ydotool, not WAYLAND_IBUS
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)
            self.assertEqual(injector.wayland_tool, "ydotool")

    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    @patch("vocalinux.text_injection.text_injector.is_ibus_active_input_method")
    @patch("vocalinux.text_injection.text_injector.is_ibus_daemon_running")
    @patch("vocalinux.text_injection.text_injector.IBusTextInjector")
    def test_uses_ibus_when_active_input_method(
        self, mock_injector_class, mock_daemon_running, mock_is_active_im, mock_is_available
    ):
        """Test that IBus is used when it is the active input method."""
        mock_is_available.return_value = True
        mock_is_active_im.return_value = True  # IBus is the active input method
        mock_daemon_running.return_value = True

        mock_injector_instance = MagicMock()
        mock_injector_class.return_value = mock_injector_instance

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

            with patch(
                "vocalinux.text_injection.text_injector.IBusTextInjector",
                mock_injector_class,
            ):
                injector = TextInjector()

                # Should use IBus
                self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND_IBUS)
                # Should use IBus
                self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND_IBUS)

    @patch("vocalinux.text_injection.text_injector.shutil.which")
    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    @patch("vocalinux.text_injection.text_injector.is_ibus_active_input_method")
    @patch("vocalinux.text_injection.text_injector.is_ibus_daemon_running")
    def test_x11_falls_back_when_ibus_not_active_input_method(
        self, mock_daemon_running, mock_is_active_im, mock_is_available, mock_which
    ):
        """Test that X11 falls back to xdotool when IBus is not the active input method."""
        mock_is_available.return_value = True
        mock_is_active_im.return_value = False  # IBus installed but not active
        mock_daemon_running.return_value = True
        mock_which.return_value = "/usr/bin/xdotool"  # xdotool is available

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

            injector = TextInjector()

            # Should fall back to X11 (xdotool), not X11_IBUS
            self.assertEqual(injector.environment, DesktopEnvironment.X11)

    @patch("vocalinux.text_injection.text_injector.is_ibus_available")
    @patch("vocalinux.text_injection.text_injector.is_ibus_active_input_method")
    @patch("vocalinux.text_injection.text_injector.is_ibus_daemon_running")
    @patch("vocalinux.text_injection.text_injector.IBusTextInjector")
    def test_ibus_setup_exception_falls_back(
        self, mock_injector_class, mock_daemon_running, mock_is_active_im, mock_is_available
    ):
        """Test that exceptions during IBus setup fall back to alternative methods."""
        mock_is_available.return_value = True
        mock_is_active_im.return_value = True  # IBus is the active input method
        mock_daemon_running.return_value = True
        mock_injector_class.side_effect = Exception("IBus setup failed")

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from vocalinux.text_injection.text_injector import DesktopEnvironment, TextInjector

            injector = TextInjector()

            # Should fall back to WAYLAND with ydotool after IBus setup fails
            self.assertEqual(injector.environment, DesktopEnvironment.WAYLAND)
            self.assertEqual(injector.wayland_tool, "ydotool")


class TestWaylandXkbLayoutSkipping(unittest.TestCase):
    """Tests for skipping setxkbmap operations on Wayland sessions."""

    def test_get_current_xkb_layout_returns_empty_on_wayland(self):
        """Test that get_current_xkb_layout returns empty tuple on Wayland."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=False):
            from vocalinux.text_injection.ibus_engine import get_current_xkb_layout

            layout, variant, option = get_current_xkb_layout()
            self.assertEqual(layout, "")
            self.assertEqual(variant, "")
            self.assertEqual(option, "")

    @patch("subprocess.run")
    def test_get_current_xkb_layout_queries_setxkbmap_on_x11(self, mock_run):
        """Test that get_current_xkb_layout uses setxkbmap on X11."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="layout:    de\nvariant:   nodeadkeys\noptions:   ctrl:nocaps\n",
        )
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=False):
            from vocalinux.text_injection.ibus_engine import get_current_xkb_layout

            layout, variant, option = get_current_xkb_layout()
            self.assertEqual(layout, "de")
            self.assertEqual(variant, "nodeadkeys")
            self.assertEqual(option, "ctrl:nocaps")
            mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_get_current_xkb_layout_skips_subprocess_on_wayland(self, mock_run):
        """Test that setxkbmap is never called on Wayland."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=False):
            from vocalinux.text_injection.ibus_engine import get_current_xkb_layout

            get_current_xkb_layout()
            mock_run.assert_not_called()

    def test_restore_xkb_layout_skips_empty_layout(self):
        """Test that restore_xkb_layout returns False for empty layout string."""
        from vocalinux.text_injection.ibus_engine import restore_xkb_layout

        result = restore_xkb_layout("", "", "")
        self.assertFalse(result)

    def test_is_wayland_session_detects_wayland(self):
        """Test _is_wayland_session returns True for Wayland."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=False):
            from vocalinux.text_injection.ibus_engine import _is_wayland_session

            self.assertTrue(_is_wayland_session())

    def test_is_wayland_session_detects_x11(self):
        """Test _is_wayland_session returns False for X11."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=False):
            from vocalinux.text_injection.ibus_engine import _is_wayland_session

            self.assertFalse(_is_wayland_session())

    def test_is_wayland_session_returns_false_when_unset(self):
        """Test _is_wayland_session returns False when env var not set."""
        env = os.environ.copy()
        env.pop("XDG_SESSION_TYPE", None)
        with patch.dict(os.environ, env, clear=True):
            from vocalinux.text_injection.ibus_engine import _is_wayland_session

            self.assertFalse(_is_wayland_session())


class TestVocalinuxEngineDestroy(unittest.TestCase):
    """Tests for VocalinuxEngine.do_destroy (layout switch resilience)."""

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", False)
    def test_do_destroy_clears_active_instance(self):
        """Test do_destroy clears _active_instance when called on the active engine."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine.__new__(VocalinuxEngine)
        VocalinuxEngine._active_instance = engine

        engine.do_destroy()

        self.assertIsNone(VocalinuxEngine._active_instance)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", False)
    def test_do_destroy_ignores_different_instance(self):
        """Test do_destroy doesn't clear _active_instance if called on a different engine."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        active_engine = VocalinuxEngine.__new__(VocalinuxEngine)
        old_engine = VocalinuxEngine.__new__(VocalinuxEngine)
        VocalinuxEngine._active_instance = active_engine

        old_engine.do_destroy()

        self.assertIs(VocalinuxEngine._active_instance, active_engine)

    def test_do_destroy_calls_super_when_ibus_available(self):
        """Test do_destroy calls super().do_destroy() when IBus is available."""
        from vocalinux.text_injection.ibus_engine import VocalinuxEngine

        engine = VocalinuxEngine.__new__(VocalinuxEngine)
        VocalinuxEngine._active_instance = None

        mock_super = MagicMock()
        with (
            patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True),
            patch("builtins.super", return_value=mock_super),
        ):
            engine.do_destroy()
            mock_super.do_destroy.assert_called_once()


if __name__ == "__main__":
    unittest.main()
