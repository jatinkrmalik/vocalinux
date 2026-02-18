"""
Tests for IBus engine functionality.
"""

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
        from vocalinux.text_injection.ibus_engine import (
            IBUS_AVAILABLE,
            is_ibus_available,
        )

        self.assertEqual(is_ibus_available(), IBUS_AVAILABLE)


class TestIsEngineRegistered(unittest.TestCase):
    """Tests for is_engine_registered function."""

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("subprocess.run")
    def test_engine_registered(self, mock_run):
        """Test detection when engine is registered."""
        mock_run.return_value = MagicMock(stdout="vocalinux\nxkb:us::eng\n", returncode=0)

        from vocalinux.text_injection.ibus_engine import is_engine_registered

        result = is_engine_registered()
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("subprocess.run")
    def test_engine_not_registered(self, mock_run):
        """Test detection when engine is not registered."""
        mock_run.return_value = MagicMock(stdout="xkb:us::eng\n", returncode=0)

        from vocalinux.text_injection.ibus_engine import is_engine_registered

        result = is_engine_registered()
        self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("subprocess.run")
    def test_subprocess_error(self, mock_run):
        """Test handling of subprocess errors."""
        import subprocess

        mock_run.side_effect = subprocess.SubprocessError("Command failed")

        from vocalinux.text_injection.ibus_engine import is_engine_registered

        result = is_engine_registered()
        self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", False)
    def test_ibus_not_available(self):
        """Test returns False when IBus is not available."""
        from vocalinux.text_injection.ibus_engine import is_engine_registered

        result = is_engine_registered()
        self.assertFalse(result)


class TestIsComponentUpToDate(unittest.TestCase):
    """Tests for is_component_up_to_date function."""

    def test_component_missing(self):
        """Test returns False when component file doesn't exist."""
        with patch("pathlib.Path.home") as mock_home:
            mock_home.return_value = Path("/nonexistent")
            from vocalinux.text_injection.ibus_engine import is_component_up_to_date

            result = is_component_up_to_date()
            self.assertFalse(result)

    def test_component_matches(self):
        """Test returns True when component content matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            component_dir = Path(tmpdir) / ".local" / "share" / "ibus" / "component"
            component_dir.mkdir(parents=True)
            component_file = component_dir / "vocalinux.xml"

            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                from vocalinux.text_injection.ibus_engine import (
                    _get_expected_component_xml,
                    is_component_up_to_date,
                )

                # Write expected content
                component_file.write_text(_get_expected_component_xml())

                result = is_component_up_to_date()
                self.assertTrue(result)

    def test_component_differs(self):
        """Test returns False when component content differs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            component_dir = Path(tmpdir) / ".local" / "share" / "ibus" / "component"
            component_dir.mkdir(parents=True)
            component_file = component_dir / "vocalinux.xml"

            with patch("pathlib.Path.home", return_value=Path(tmpdir)):
                from vocalinux.text_injection.ibus_engine import is_component_up_to_date

                # Write stale content
                component_file.write_text("<component>stale</component>")

                result = is_component_up_to_date()
                self.assertFalse(result)


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
    @patch("vocalinux.text_injection.ibus_engine.install_ibus_component")
    @patch("vocalinux.text_injection.ibus_engine.is_engine_registered")
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
        mock_is_registered,
        mock_install,
        mock_ensure_dir,
    ):
        """Test initialization with auto_activate=True."""
        mock_is_registered.return_value = True
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

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    @patch("vocalinux.text_injection.ibus_engine.ensure_ibus_dir")
    def test_inject_text_engine_error(self, mock_ensure_dir):
        """Test text injection when engine returns error."""
        from vocalinux.text_injection.ibus_engine import IBusTextInjector

        # Create a mock server socket that returns error
        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.bind(str(self.socket_path))
        server_sock.listen(1)

        def handle_connection():
            conn, _ = server_sock.accept()
            with conn:
                conn.recv(65536)
                conn.sendall(b"NO_ENGINE")

        server_thread = threading.Thread(target=handle_connection, daemon=True)
        server_thread.start()

        with patch("vocalinux.text_injection.ibus_engine.SOCKET_PATH", self.socket_path):
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


class TestInstallIBusComponent(unittest.TestCase):
    """Tests for install_ibus_component function."""

    @patch("subprocess.run")
    def test_user_install_success(self, mock_run):
        """Test successful user-level installation."""
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as temp_dir:
            component_dir = Path(temp_dir)

            with patch(
                "vocalinux.text_injection.ibus_engine.Path.home",
                return_value=Path(temp_dir),
            ):
                from vocalinux.text_injection.ibus_engine import install_ibus_component

                # Force reload to use patched home
                result = install_ibus_component(system_wide=False)

        self.assertTrue(result)

    @patch("subprocess.run")
    def test_system_install_needs_sudo(self, mock_run):
        """Test system-wide installation calls sudo."""
        mock_run.return_value = MagicMock(returncode=0)

        from vocalinux.text_injection.ibus_engine import install_ibus_component

        with patch("tempfile.NamedTemporaryFile"):
            with patch("os.unlink"):
                result = install_ibus_component(system_wide=True)

        # Verify sudo was called
        sudo_calls = [
            call for call in mock_run.call_args_list if call[0][0] and "sudo" in call[0][0]
        ]
        self.assertTrue(len(sudo_calls) > 0)

    @patch("subprocess.run")
    def test_system_install_failure(self, mock_run):
        """Test system-wide installation failure."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Permission denied")

        from vocalinux.text_injection.ibus_engine import install_ibus_component

        with patch("tempfile.NamedTemporaryFile") as mock_tmp:
            mock_tmp.return_value.__enter__ = MagicMock()
            mock_tmp.return_value.__exit__ = MagicMock()
            mock_tmp.return_value.name = "/tmp/test.xml"
            mock_tmp.return_value.write = MagicMock()
            with patch("os.unlink"):
                result = install_ibus_component(system_wide=True)

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
    @patch("vocalinux.text_injection.ibus_engine.IBusTextInjector")
    def test_wayland_prefers_ibus(self, mock_injector_class, mock_ibus_available):
        """Test that Wayland environment prefers IBus when available."""
        mock_ibus_available.return_value = True
        mock_injector_instance = MagicMock()
        mock_injector_class.return_value = mock_injector_instance

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"}):
            from vocalinux.text_injection.text_injector import (
                DesktopEnvironment,
                TextInjector,
            )

            # Patch the import inside text_injector
            with patch(
                "vocalinux.text_injection.text_injector.is_ibus_available",
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
    @patch("vocalinux.text_injection.ibus_engine.IBusTextInjector")
    def test_x11_prefers_ibus(self, mock_injector_class, mock_ibus_available):
        """Test that X11 environment prefers IBus when available."""
        mock_ibus_available.return_value = True
        mock_injector_instance = MagicMock()
        mock_injector_class.return_value = mock_injector_instance

        with patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"}):
            from vocalinux.text_injection.text_injector import (
                DesktopEnvironment,
                TextInjector,
            )

            with patch(
                "vocalinux.text_injection.text_injector.is_ibus_available",
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

            from vocalinux.text_injection.text_injector import (
                DesktopEnvironment,
                TextInjector,
            )

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

            from vocalinux.text_injection.text_injector import (
                DesktopEnvironment,
                TextInjector,
            )

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


if __name__ == "__main__":
    unittest.main()
