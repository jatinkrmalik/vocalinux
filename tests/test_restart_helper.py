"""Tests for the delayed restart helper."""

from unittest.mock import patch

from vocalinux import restart_helper


class TestRestartHelper:
    """Test the delayed restart helper workflow."""

    @patch("vocalinux.restart_helper.subprocess.Popen")
    @patch("vocalinux.restart_helper._wait_for_lock_release", return_value=True)
    @patch("vocalinux.restart_helper._wait_for_process_exit", return_value=True)
    def test_restart_after_exit_launches_new_instance(
        self, _mock_wait_exit, _mock_wait_lock, mock_popen
    ):
        """A successful wait sequence should launch a new Vocalinux instance."""
        assert restart_helper.restart_after_exit(1234) is True
        mock_popen.assert_called_once_with(
            [restart_helper.sys.executable, "-m", "vocalinux.main"], close_fds=True
        )

    @patch("vocalinux.restart_helper._wait_for_lock_release", return_value=False)
    @patch("vocalinux.restart_helper._wait_for_process_exit", return_value=True)
    def test_restart_after_exit_aborts_when_lock_never_releases(
        self, _mock_wait_exit, _mock_wait_lock
    ):
        """The helper must not start a second instance while the lock is busy."""
        with patch("vocalinux.restart_helper.subprocess.Popen") as mock_popen:
            assert restart_helper.restart_after_exit(1234) is False
            mock_popen.assert_not_called()
