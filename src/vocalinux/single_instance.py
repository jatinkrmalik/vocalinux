"""
Single instance enforcement for Vocalinux.

Uses file locking to ensure only one instance runs at a time.
Works across sessions and handles stale locks from crashed processes.
"""

import fcntl
import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Lock file location: ~/.local/share/vocalinux/
LOCK_FILE_DIR = Path.home() / ".local" / "share" / "vocalinux"
LOCK_FILE_PATH = LOCK_FILE_DIR / "instance.lock"

# Global lock file handle
_lock_file: Optional[int] = None


def _get_lock_file_fd() -> int:
    """Get or create the lock file descriptor."""
    global _lock_file

    if _lock_file is not None:
        return _lock_file

    # Ensure directory exists
    LOCK_FILE_DIR.mkdir(parents=True, exist_ok=True)

    # Open lock file (create if doesn't exist)
    # O_RDWR: read/write, O_CREAT: create if not exists
    fd = os.open(str(LOCK_FILE_PATH), os.O_RDWR | os.O_CREAT, 0o644)
    _lock_file = fd

    return fd


def acquire_lock() -> bool:
    """
    Acquire the single instance lock.

    Returns:
        True if lock acquired (first instance), False if another instance is running.

    If another instance is running, logs a message and returns False.
    """
    try:
        fd = _get_lock_file_fd()

        # Try to acquire exclusive lock (non-blocking)
        # LOCK_EX: exclusive lock
        # LOCK_NB: non-blocking (fail immediately if lock held by another process)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, IOError):
            # Lock is held by another process
            logger.warning("Another instance of Vocalinux is already running. Exiting.")
            print("Another instance of Vocalinux is already running.", file=sys.stderr)
            print(
                f"If you're sure no other instance is running, delete: {LOCK_FILE_PATH}",
                file=sys.stderr,
            )
            return False

        # Lock acquired - write our PID for debugging purposes
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode())
        os.lseek(fd, 0, os.SEEK_SET)

        logger.info("Single instance lock acquired")
        return True

    except Exception as e:
        # Unexpected error - log and allow startup (fail open but warn)
        logger.error(f"Error acquiring single instance lock: {e}")
        return True


def release_lock():
    """Release the single instance lock."""
    global _lock_file

    if _lock_file is not None:
        try:
            # Release lock
            fcntl.flock(_lock_file, fcntl.LOCK_UN)
            os.close(_lock_file)
            _lock_file = None
            logger.debug("Single instance lock released")
        except (OSError, IOError) as e:
            logger.warning(f"Failed to release lock: {e}")
            # Ensure clean state
            _lock_file = None
