"""Background GitHub release checks for Vocalinux.

Periodically fetches the latest release for the configured channel and reports
whether an update is available. Networking runs off the GLib main loop; the
result callback is marshalled back onto it via ``GLib.idle_add`` when GTK is
available.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from ..version import __version__
from .update_checker import (
    DEFAULT_UPDATE_CHANNEL,
    ReleaseInfo,
    fetch_latest_release,
    is_update_available,
    normalize_channel,
)

logger = logging.getLogger(__name__)

# Check once shortly after launch, then every six hours while the app runs.
DEFAULT_STARTUP_DELAY_SECONDS = 45
DEFAULT_CHECK_INTERVAL_SECONDS = 6 * 60 * 60


class UpdateMonitor:
    """Schedule periodic update checks and notify when a newer release exists.

    Args:
        get_channel: Callable returning the configured channel (``stable`` /
            ``nightly``). Re-read on each check so Settings changes apply.
        on_result: Called as ``on_result(available, release)`` on the GLib
            main loop when ``use_glib`` is True. ``release`` is None when the
            lookup failed or no update is available.
        get_current_version: Optional override of the installed version string
            (defaults to :data:`vocalinux.version.__version__`).
        startup_delay_seconds: Delay before the first check after :meth:`start`.
        check_interval_seconds: Interval between subsequent checks.
        use_glib: If True (default), schedule with GLib and deliver results via
            ``idle_add``. If False, only :meth:`check_now` / :meth:`tick` drive
            the monitor (unit tests).
    """

    def __init__(
        self,
        get_channel: Callable[[], str],
        on_result: Optional[Callable[[bool, Optional[ReleaseInfo]], None]] = None,
        get_current_version: Optional[Callable[[], str]] = None,
        startup_delay_seconds: float = DEFAULT_STARTUP_DELAY_SECONDS,
        check_interval_seconds: float = DEFAULT_CHECK_INTERVAL_SECONDS,
        use_glib: bool = True,
    ):
        self._get_channel = get_channel
        self._on_result = on_result
        self._get_current_version = get_current_version or (lambda: __version__)
        self._startup_delay = max(0.0, float(startup_delay_seconds))
        self._check_interval = max(60.0, float(check_interval_seconds))
        self._use_glib = use_glib

        self._running = False
        self._check_in_progress = False
        self._timeout_id: Optional[int] = None
        self._generation = 0
        self._next_due_at: Optional[float] = None
        self._last_available = False
        self._last_release: Optional[ReleaseInfo] = None

    @property
    def active(self) -> bool:
        """True if the monitor has been started."""
        return self._running

    @property
    def last_available(self) -> bool:
        """Whether the most recent successful check found an update."""
        return self._last_available

    @property
    def last_release(self) -> Optional[ReleaseInfo]:
        """Release from the most recent successful check, if any."""
        return self._last_release

    def start(self) -> None:
        """Arm the first check after the startup delay. Safe to call twice."""
        if self._running:
            return
        self._running = True
        logger.info(
            "Update monitor started (first check in %.0fs, then every %.0fs)",
            self._startup_delay,
            self._check_interval,
        )
        self._schedule(self._startup_delay)

    def stop(self) -> None:
        """Cancel pending timers and mark stopped."""
        self._running = False
        self._cancel_timeout()
        self._generation += 1  # drop in-flight worker results
        logger.info("Update monitor stopped")

    def shutdown(self) -> None:
        """Alias for :meth:`stop` (mirrors other tray helpers)."""
        self.stop()

    def check_now(self) -> None:
        """Run a check immediately (skips if one is already in flight)."""
        if not self._running:
            return
        self._cancel_timeout()
        self._run_check()

    def tick(self) -> bool:
        """Fire a due check without GLib (tests). Returns True if a check started."""
        if not self._running or self._check_in_progress:
            return False
        if self._next_due_at is None or time.monotonic() < self._next_due_at:
            return False
        self._run_check()
        return True

    def _schedule(self, delay_seconds: float) -> None:
        self._cancel_timeout()
        delay = max(0.0, float(delay_seconds))
        self._next_due_at = time.monotonic() + delay
        if not self._use_glib:
            return
        try:
            from gi.repository import GLib
        except Exception:
            logger.debug("GLib unavailable; update monitor will not auto-schedule")
            return

        # GLib.timeout_add_seconds takes an integer; sub-second delays use timeout_add.
        if delay >= 1.0:
            self._timeout_id = GLib.timeout_add_seconds(int(delay), self._on_timer)
        else:
            self._timeout_id = GLib.timeout_add(max(1, int(delay * 1000)), self._on_timer)

    def _cancel_timeout(self) -> None:
        if self._timeout_id is None:
            return
        if self._use_glib:
            try:
                from gi.repository import GLib

                GLib.source_remove(self._timeout_id)
            except Exception:
                pass
        self._timeout_id = None
        self._next_due_at = None

    def _on_timer(self):
        self._timeout_id = None
        self._next_due_at = None
        if self._running:
            self._run_check()
        return False  # one-shot; next interval scheduled after the check

    def _run_check(self) -> None:
        if self._check_in_progress:
            return
        self._check_in_progress = True
        self._generation += 1
        generation = self._generation
        channel = normalize_channel(self._safe_channel())
        current = str(self._get_current_version() or "")
        threading.Thread(
            target=self._worker,
            args=(channel, current, generation),
            daemon=True,
            name="vocalinux-update-check",
        ).start()

    def _worker(self, channel: str, current: str, generation: int) -> None:
        try:
            release = fetch_latest_release(channel=channel)
        except Exception:
            logger.warning("Update check failed", exc_info=True)
            release = None

        if release is None:
            logger.debug("Update check (%s): no release returned; keeping prior state", channel)
            # Network / API failure — do not clear a previously known update.
            self._finish_check(generation, notify=False)
            return

        available = is_update_available(current, release, channel)
        self._finish_check(
            generation,
            notify=True,
            available=available,
            release=release if available else None,
        )

    def _finish_check(
        self,
        generation: int,
        *,
        notify: bool,
        available: bool = False,
        release: Optional[ReleaseInfo] = None,
    ) -> None:
        def _apply() -> bool:
            self._check_in_progress = False
            if not self._running or generation != self._generation:
                return False
            if notify:
                self._last_available = available
                self._last_release = release
                if self._on_result is not None:
                    try:
                        self._on_result(available, release)
                    except Exception:
                        logger.error("Update monitor callback failed", exc_info=True)
            if self._running:
                self._schedule(self._check_interval)
            return False

        if self._use_glib:
            try:
                from gi.repository import GLib

                GLib.idle_add(_apply)
                return
            except Exception:
                logger.debug("GLib idle_add unavailable; applying update result inline")
        _apply()

    def _safe_channel(self) -> str:
        try:
            return normalize_channel(self._get_channel())
        except Exception:
            logger.error("Failed to read update channel", exc_info=True)
            return DEFAULT_UPDATE_CHANNEL
