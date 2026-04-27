"""
Final comprehensive tests for IBus engine.

These tests exercise code paths to improve coverage without platform-specific issues.
"""

import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock GI imports before importing any vocalinux modules that use gi.
# On CI, real gi/IBus may be installed; importing ibus_engine without mocks
# would set IBUS_AVAILABLE=True and VocalinuxEngine would inherit from real
# IBus.Engine, causing hangs when super().__init__() tries to connect to IBus.
_mock_gi = MagicMock()
_mock_ibus = MagicMock()
_mock_glib = MagicMock()
_mock_gobject = MagicMock()
_mock_ibus.Engine = MagicMock
_mock_glib.MainLoop = MagicMock

_mock_gi_repo = MagicMock()
_mock_gi_repo.IBus = _mock_ibus
_mock_gi_repo.GLib = _mock_glib
_mock_gi_repo.GObject = _mock_gobject

sys.modules["gi"] = _mock_gi
sys.modules["gi.repository"] = _mock_gi_repo

# Force reload ibus_engine so it picks up mocks (in case it was already imported)
for _key in list(sys.modules.keys()):
    if "vocalinux" in _key and "ibus_engine" in _key:
        del sys.modules[_key]


class TestIBusSetupError(unittest.TestCase):
    """Tests for IBusSetupError exception."""

    def test_ibus_setup_error_is_runtime_error(self):
        """Test that IBusSetupError is a RuntimeError."""
        from vocalinux.text_injection.ibus_engine import IBusSetupError

        self.assertTrue(issubclass(IBusSetupError, RuntimeError))

    def test_ibus_setup_error_accepts_message(self):
        """Test that IBusSetupError accepts a message."""
        from vocalinux.text_injection.ibus_engine import IBusSetupError

        msg = "Test error message"
        error = IBusSetupError(msg)
        self.assertEqual(str(error), msg)


class TestEnsureIBusDir(unittest.TestCase):
    """Tests for ensure_ibus_dir function."""

    @patch("pathlib.Path.mkdir")
    @patch("pathlib.Path.chmod")
    def test_ensure_ibus_dir_creates_and_secures(self, mock_chmod, mock_mkdir):
        """Test that ensure_ibus_dir creates directory with proper permissions."""
        from vocalinux.text_injection.ibus_engine import ensure_ibus_dir

        ensure_ibus_dir()

        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_chmod.assert_called_once_with(0o700)


class TestIsIBusAvailable(unittest.TestCase):
    """Tests for is_ibus_available function."""

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    def test_is_ibus_available_true(self):
        """Test is_ibus_available when IBus is available."""
        from vocalinux.text_injection.ibus_engine import is_ibus_available

        result = is_ibus_available()
        # Verify the function returns True when IBUS_AVAILABLE flag is True
        self.assertTrue(result)
        # Verify it's checking the flag, not just always returning a value
        self.assertEqual(result, True)

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", False)
    def test_is_ibus_available_false(self):
        """Test is_ibus_available when IBus is not available."""
        from vocalinux.text_injection.ibus_engine import is_ibus_available

        result = is_ibus_available()
        self.assertFalse(result)


class TestIsIBusDaemonRunning(unittest.TestCase):
    """Tests for is_ibus_daemon_running function."""

    @patch("subprocess.run")
    def test_is_ibus_daemon_running_true(self, mock_run):
        """Test is_ibus_daemon_running returns True when daemon is running."""
        from vocalinux.text_injection.ibus_engine import is_ibus_daemon_running

        mock_run.return_value.returncode = 0
        result = is_ibus_daemon_running()
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_is_ibus_daemon_running_false(self, mock_run):
        """Test is_ibus_daemon_running returns False when daemon is not running."""
        from vocalinux.text_injection.ibus_engine import is_ibus_daemon_running

        mock_run.return_value.returncode = 1
        result = is_ibus_daemon_running()
        self.assertFalse(result)

    @patch("subprocess.run", side_effect=FileNotFoundError("pgrep not found"))
    def test_is_ibus_daemon_running_file_not_found(self, mock_run):
        """Test is_ibus_daemon_running handles FileNotFoundError."""
        from vocalinux.text_injection.ibus_engine import is_ibus_daemon_running

        result = is_ibus_daemon_running()
        self.assertFalse(result)


class TestIsIBusActiveInputMethod(unittest.TestCase):
    """Tests for is_ibus_active_input_method function."""

    @patch.dict("os.environ", {"GTK_IM_MODULE": "ibus"})
    def test_is_ibus_active_gtk_im_module(self):
        """Test detection via GTK_IM_MODULE."""
        from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

        result = is_ibus_active_input_method()
        self.assertTrue(result)

    @patch.dict("os.environ", {"QT_IM_MODULE": "ibus"}, clear=True)
    def test_is_ibus_active_qt_im_module(self):
        """Test detection via QT_IM_MODULE."""
        from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

        result = is_ibus_active_input_method()
        self.assertTrue(result)

    @patch.dict("os.environ", {"XMODIFIERS": "@im=ibus"}, clear=True)
    def test_is_ibus_active_xmodifiers(self):
        """Test detection via XMODIFIERS."""
        from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

        result = is_ibus_active_input_method()
        self.assertTrue(result)

    @patch.dict("os.environ", {}, clear=True)
    def test_is_ibus_active_not_active(self):
        """Test when IBus is not the active input method."""
        from vocalinux.text_injection.ibus_engine import is_ibus_active_input_method

        result = is_ibus_active_input_method()
        self.assertFalse(result)


class TestStartIBusDaemon(unittest.TestCase):
    """Tests for start_ibus_daemon function."""

    @patch("vocalinux.text_injection.ibus_engine.is_ibus_daemon_running")
    def test_start_ibus_daemon_already_running(self, mock_is_running):
        """Test when daemon is already running."""
        from vocalinux.text_injection.ibus_engine import start_ibus_daemon

        mock_is_running.return_value = True
        result = start_ibus_daemon()
        self.assertTrue(result)

    @patch("vocalinux.text_injection.ibus_engine.is_ibus_available")
    @patch("vocalinux.text_injection.ibus_engine.is_ibus_daemon_running")
    def test_start_ibus_daemon_not_available(self, mock_is_running, mock_available):
        """Test when IBus is not available."""
        from vocalinux.text_injection.ibus_engine import start_ibus_daemon

        mock_is_running.return_value = False
        mock_available.return_value = False
        result = start_ibus_daemon()
        self.assertFalse(result)


class TestIsEngineActive(unittest.TestCase):
    """Tests for is_engine_active function."""

    @patch("subprocess.run")
    def test_is_engine_active_true(self, mock_run):
        """Test when engine is active."""
        from vocalinux.text_injection.ibus_engine import ENGINE_NAME, is_engine_active

        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ENGINE_NAME
        result = is_engine_active()
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_is_engine_active_false(self, mock_run):
        """Test when engine is not active."""
        from vocalinux.text_injection.ibus_engine import is_engine_active

        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "other"
        result = is_engine_active()
        self.assertFalse(result)


class TestGetCurrentEngine(unittest.TestCase):
    """Tests for get_current_engine function."""

    @patch("subprocess.run")
    def test_get_current_engine_success(self, mock_run):
        """Test successfully retrieving current engine."""
        from vocalinux.text_injection.ibus_engine import get_current_engine

        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "test-engine\n"
        result = get_current_engine()
        self.assertEqual(result, "test-engine")

    @patch("subprocess.run", side_effect=FileNotFoundError("ibus not found"))
    def test_get_current_engine_not_found(self, mock_run):
        """Test when ibus command is not found."""
        from vocalinux.text_injection.ibus_engine import get_current_engine

        result = get_current_engine()
        self.assertIsNone(result)


class TestSwitchEngine(unittest.TestCase):
    """Tests for switch_engine function."""

    @patch("vocalinux.text_injection.ibus_engine.get_current_engine")
    @patch("time.sleep")
    @patch("subprocess.run")
    def test_switch_engine_success(self, mock_run, mock_sleep, mock_get_engine):
        """Test successfully switching engines."""
        from vocalinux.text_injection.ibus_engine import switch_engine

        mock_get_engine.return_value = "vocalinux"
        result = switch_engine("vocalinux")
        self.assertTrue(result)

    @patch("vocalinux.text_injection.ibus_engine.get_current_engine")
    @patch("time.sleep")
    @patch("subprocess.run")
    def test_switch_engine_failure(self, mock_run, mock_sleep, mock_get_engine):
        """Test when engine switch fails."""
        from vocalinux.text_injection.ibus_engine import switch_engine

        mock_get_engine.return_value = "other"
        result = switch_engine("vocalinux")
        self.assertFalse(result)


class TestIsEngineProcessRunning(unittest.TestCase):
    """Tests for is_engine_process_running function."""

    @patch("pathlib.Path.exists")
    def test_is_engine_process_running_no_pid_file(self, mock_exists):
        """Test when PID file doesn't exist."""
        from vocalinux.text_injection.ibus_engine import is_engine_process_running

        mock_exists.return_value = False
        result = is_engine_process_running()
        self.assertFalse(result)


class TestStopEngineProcess(unittest.TestCase):
    """Tests for stop_engine_process function."""

    @patch("pathlib.Path.exists")
    def test_stop_engine_process_no_pid_file(self, mock_exists):
        """Test when no PID file exists."""
        from vocalinux.text_injection.ibus_engine import stop_engine_process

        mock_exists.return_value = False
        # Should not raise any exception
        result = stop_engine_process()
        # Verify the function handles missing PID file gracefully
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
