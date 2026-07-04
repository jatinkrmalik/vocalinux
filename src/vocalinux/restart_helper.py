"""
Delayed restart helper for Vocalinux.

Starts a fresh Vocalinux process only after the current instance has exited
and released its single-instance lock.
"""

import fcntl
import os
import subprocess
import sys
import time
from typing import List, Optional

from .single_instance import LOCK_FILE_DIR, LOCK_FILE_PATH

POLL_INTERVAL_SECONDS = 0.1
WAIT_TIMEOUT_SECONDS = 10.0


def _pid_exists(pid: int) -> bool:
    """Return True while the target PID is still alive."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _wait_for_process_exit(pid: int, timeout_seconds: float = WAIT_TIMEOUT_SECONDS) -> bool:
    """Wait until the parent process exits."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _pid_exists(pid):
            return True
        time.sleep(POLL_INTERVAL_SECONDS)
    return not _pid_exists(pid)


def _wait_for_lock_release(timeout_seconds: float = WAIT_TIMEOUT_SECONDS) -> bool:
    """Wait until the Vocalinux single-instance lock can be acquired."""
    LOCK_FILE_DIR.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(LOCK_FILE_PATH), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
                return True
            except (OSError, IOError):
                time.sleep(POLL_INTERVAL_SECONDS)
        return False
    finally:
        os.close(fd)


def restart_after_exit(parent_pid: int) -> bool:
    """Launch Vocalinux after the original process has fully exited."""
    if not _wait_for_process_exit(parent_pid):
        return False

    if not _wait_for_lock_release():
        return False

    subprocess.Popen([sys.executable, "-m", "vocalinux.main"], close_fds=True)
    return True


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for delayed restart."""
    argv = argv or sys.argv
    if len(argv) < 2:
        return 1

    try:
        parent_pid = int(argv[1])
    except ValueError:
        return 1

    return 0 if restart_after_exit(parent_pid) else 1


if __name__ == "__main__":
    raise SystemExit(main())
