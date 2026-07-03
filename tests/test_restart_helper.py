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

    @patch("vocalinux.restart_helper._wait_for_process_exit", return_value=False)
    def test_restart_after_exit_aborts_when_parent_stays_alive(self, mock_wait_exit):
        """The helper must not wait on the lock or launch while the old process is alive."""
        with (
            patch("vocalinux.restart_helper._wait_for_lock_release") as mock_wait_lock,
            patch("vocalinux.restart_helper.subprocess.Popen") as mock_popen,
        ):
            assert restart_helper.restart_after_exit(1234) is False

        mock_wait_exit.assert_called_once_with(1234)
        mock_wait_lock.assert_not_called()
        mock_popen.assert_not_called()

    @patch("vocalinux.restart_helper.os.kill")
    def test_pid_exists_returns_true_for_running_process(self, mock_kill):
        """os.kill(pid, 0) succeeds while a process exists."""
        assert restart_helper._pid_exists(1234) is True
        mock_kill.assert_called_once_with(1234, 0)

    @patch("vocalinux.restart_helper.os.kill", side_effect=ProcessLookupError)
    def test_pid_exists_returns_false_for_missing_process(self, _mock_kill):
        """ProcessLookupError means the process is gone."""
        assert restart_helper._pid_exists(1234) is False

    @patch("vocalinux.restart_helper.os.kill", side_effect=PermissionError)
    def test_pid_exists_treats_permission_error_as_alive(self, _mock_kill):
        """PermissionError still proves that the PID exists."""
        assert restart_helper._pid_exists(1234) is True

    def test_wait_for_process_exit_returns_true_when_pid_is_gone(self):
        """The process wait should finish immediately after the PID disappears."""
        with (
            patch("vocalinux.restart_helper.time.monotonic", side_effect=[0.0, 0.0]),
            patch("vocalinux.restart_helper._pid_exists", return_value=False),
            patch("vocalinux.restart_helper.time.sleep") as mock_sleep,
        ):
            assert restart_helper._wait_for_process_exit(1234, timeout_seconds=1.0) is True

        mock_sleep.assert_not_called()

    def test_wait_for_process_exit_polls_until_pid_disappears(self):
        """The process wait should sleep between polls while the PID is still alive."""
        with (
            patch("vocalinux.restart_helper.time.monotonic", side_effect=[0.0, 0.0, 0.05]),
            patch("vocalinux.restart_helper._pid_exists", side_effect=[True, False]),
            patch("vocalinux.restart_helper.time.sleep") as mock_sleep,
        ):
            assert restart_helper._wait_for_process_exit(1234, timeout_seconds=1.0) is True

        mock_sleep.assert_called_once_with(restart_helper.POLL_INTERVAL_SECONDS)

    def test_wait_for_process_exit_returns_false_after_timeout(self):
        """A still-running process after the deadline should abort restart."""
        with (
            patch("vocalinux.restart_helper.time.monotonic", side_effect=[0.0, 2.0]),
            patch("vocalinux.restart_helper._pid_exists", return_value=True),
        ):
            assert restart_helper._wait_for_process_exit(1234, timeout_seconds=1.0) is False

    def test_wait_for_lock_release_acquires_available_lock(self, tmp_path):
        """An unlocked instance file should allow the helper to continue."""
        lock_path = tmp_path / "instance.lock"
        with (
            patch("vocalinux.restart_helper.LOCK_FILE_DIR", tmp_path),
            patch("vocalinux.restart_helper.LOCK_FILE_PATH", lock_path),
        ):
            assert restart_helper._wait_for_lock_release(timeout_seconds=0.1) is True

        assert lock_path.exists()

    def test_wait_for_lock_release_returns_false_after_timeout(self, tmp_path):
        """A busy lock past the deadline should stop the delayed restart."""
        lock_path = tmp_path / "instance.lock"
        with (
            patch("vocalinux.restart_helper.LOCK_FILE_DIR", tmp_path),
            patch("vocalinux.restart_helper.LOCK_FILE_PATH", lock_path),
            patch("vocalinux.restart_helper.fcntl.flock", side_effect=OSError("busy")),
            patch("vocalinux.restart_helper.time.monotonic", side_effect=[0.0, 0.0, 2.0]),
            patch("vocalinux.restart_helper.time.sleep") as mock_sleep,
        ):
            assert restart_helper._wait_for_lock_release(timeout_seconds=1.0) is False

        mock_sleep.assert_called_once_with(restart_helper.POLL_INTERVAL_SECONDS)

    def test_main_requires_parent_pid_argument(self):
        """The CLI should reject missing parent PID arguments."""
        assert restart_helper.main(["restart_helper"]) == 1

    def test_main_rejects_invalid_parent_pid(self):
        """The CLI should reject non-integer parent PIDs."""
        assert restart_helper.main(["restart_helper", "not-a-pid"]) == 1

    @patch("vocalinux.restart_helper.restart_after_exit", return_value=True)
    def test_main_returns_zero_when_restart_succeeds(self, mock_restart):
        """The CLI should return zero after a successful delayed restart."""
        assert restart_helper.main(["restart_helper", "1234"]) == 0
        mock_restart.assert_called_once_with(1234)

    @patch("vocalinux.restart_helper.restart_after_exit", return_value=False)
    def test_main_returns_one_when_restart_fails(self, mock_restart):
        """The CLI should return one after a failed delayed restart."""
        assert restart_helper.main(["restart_helper", "1234"]) == 1
        mock_restart.assert_called_once_with(1234)
