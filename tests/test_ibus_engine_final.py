"""
Final comprehensive tests for IBus engine.

These tests exercise code paths to improve coverage without platform-specific issues.
"""

import subprocess
import unittest
from unittest.mock import MagicMock, patch


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


class TestGetExpectedComponentXml(unittest.TestCase):
    """Tests for _get_expected_component_xml function."""

    def test_get_expected_component_xml_returns_string(self):
        """Test that function returns valid XML string."""
        from vocalinux.text_injection.ibus_engine import _get_expected_component_xml

        result = _get_expected_component_xml()
        self.assertIsInstance(result, str)
        self.assertIn("<?xml", result)
        self.assertIn("</component>", result)

    def test_get_expected_component_xml_contains_vocalinux(self):
        """Test that XML contains Vocalinux references."""
        from vocalinux.text_injection.ibus_engine import _get_expected_component_xml

        result = _get_expected_component_xml()
        self.assertIn("vocalinux", result.lower())


class TestIsComponentUpToDate(unittest.TestCase):
    """Tests for is_component_up_to_date function."""

    @patch("pathlib.Path.exists")
    def test_is_component_up_to_date_not_exists(self, mock_exists):
        """Test when component file doesn't exist."""
        from vocalinux.text_injection.ibus_engine import is_component_up_to_date

        mock_exists.return_value = False
        result = is_component_up_to_date()
        self.assertFalse(result)

    @patch("vocalinux.text_injection.ibus_engine._get_expected_component_xml")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_is_component_up_to_date_matches(self, mock_exists, mock_read, mock_get_xml):
        """Test when XML matches."""
        from vocalinux.text_injection.ibus_engine import is_component_up_to_date

        xml_content = "<?xml><component></component>"
        mock_exists.return_value = True
        mock_read.return_value = xml_content
        mock_get_xml.return_value = xml_content

        result = is_component_up_to_date()
        self.assertTrue(result)

    @patch("vocalinux.text_injection.ibus_engine._get_expected_component_xml")
    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_is_component_up_to_date_mismatch(self, mock_exists, mock_read, mock_get_xml):
        """Test when XML differs."""
        from vocalinux.text_injection.ibus_engine import is_component_up_to_date

        mock_exists.return_value = True
        mock_read.return_value = "<?xml><old></old>"
        mock_get_xml.return_value = "<?xml><new></new>"

        result = is_component_up_to_date()
        self.assertFalse(result)


class TestIsEngineRegistered(unittest.TestCase):
    """Tests for is_engine_registered function."""

    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", False)
    def test_is_engine_registered_not_available(self):
        """Test when IBus is not available."""
        from vocalinux.text_injection.ibus_engine import is_engine_registered

        result = is_engine_registered()
        self.assertFalse(result)

    @patch("subprocess.run")
    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    def test_is_engine_registered_true(self, mock_run):
        """Test when engine is registered."""
        from vocalinux.text_injection.ibus_engine import ENGINE_NAME, is_engine_registered

        mock_run.return_value.stdout = f"other\n{ENGINE_NAME}\nmore"
        result = is_engine_registered()
        self.assertTrue(result)

    @patch("subprocess.run")
    @patch("vocalinux.text_injection.ibus_engine.IBUS_AVAILABLE", True)
    def test_is_engine_registered_false(self, mock_run):
        """Test when engine is not registered."""
        from vocalinux.text_injection.ibus_engine import is_engine_registered

        mock_run.return_value.stdout = "other\nengines"
        result = is_engine_registered()
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
