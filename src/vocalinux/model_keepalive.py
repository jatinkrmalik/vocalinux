"""
Model keep-alive: unload the speech model after a configurable idle timeout.

Mirrors :class:`~vocalinux.auto_pause_monitor.AutoPauseMonitor` / SuspendHandler
style — the tray owns lifecycle, callbacks run on the GLib main loop when used
with ``use_glib=True``. Designed so unit tests can drive the timer without GTK.
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# Default idle timeout when keep-alive is enabled but config omits a value
DEFAULT_IDLE_TIMEOUT_SECONDS = 300

# Reasonable bounds when enabled (seconds)
_MIN_IDLE_TIMEOUT = 60
_MAX_IDLE_TIMEOUT = 3600


def clamp_idle_timeout(seconds: float) -> float:
    """Clamp an idle timeout to the supported range."""
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        return float(DEFAULT_IDLE_TIMEOUT_SECONDS)
    return max(_MIN_IDLE_TIMEOUT, min(_MAX_IDLE_TIMEOUT, value))


class ModelKeepAlive:
    """Schedules idle unload of the speech model after inactivity.

    Args:
        get_config: Callable returning ``(enabled, idle_timeout_seconds)``.
            Re-read on each bump so Settings changes apply without restart.
        on_idle_unload: Called once when the idle timeout elapses.
        is_safe_to_unload: Optional predicate; unload only runs when this
            returns True (default: always). Use to require IDLE + not auto-paused.
        use_glib: If True (default), schedule with GLib.timeout_add_seconds.
            If False, only ``fire_if_due`` / manual ``tick`` is available (tests).
    """

    def __init__(
        self,
        get_config: Callable[[], tuple[bool, float]],
        on_idle_unload: Optional[Callable[[], None]] = None,
        is_safe_to_unload: Optional[Callable[[], bool]] = None,
        use_glib: bool = True,
    ):
        self._get_config = get_config
        self._on_idle_unload = on_idle_unload
        self._is_safe_to_unload = is_safe_to_unload
        self._use_glib = use_glib
        self._timeout_id: Optional[int] = None
        self._running = False
        self._armed = False

    @property
    def active(self) -> bool:
        """True if the keep-alive helper has been started."""
        return self._running

    @property
    def armed(self) -> bool:
        """True while an idle timer is scheduled."""
        return self._armed

    def start(self) -> None:
        """Mark the helper as running. Safe to call if already started."""
        if self._running:
            return
        self._running = True
        logger.info("Model keep-alive started")

    def stop(self) -> None:
        """Cancel any pending timer and mark stopped."""
        self._running = False
        self.cancel()
        logger.info("Model keep-alive stopped")

    def shutdown(self) -> None:
        """Alias for :meth:`stop` (mirrors SuspendHandler.shutdown)."""
        self.stop()

    def bump(self) -> None:
        """Reset the idle deadline from now (call when recognition becomes IDLE)."""
        if not self._running:
            return

        enabled, timeout = self._read_config()
        if not enabled:
            self.cancel()
            return

        self._schedule(timeout)

    def cancel(self) -> None:
        """Cancel any pending idle unload (call while LISTENING/PROCESSING)."""
        self._cancel_timeout()
        self._armed = False

    def fire_if_due(self) -> bool:
        """Manually run the idle unload path (tests / non-GLib). Returns True if fired."""
        if not self._running or not self._armed:
            return False
        return self._fire_unload()

    def _read_config(self) -> tuple[bool, float]:
        try:
            enabled, timeout = self._get_config()
        except Exception:
            logger.error("Failed to read model keep-alive config", exc_info=True)
            return False, float(DEFAULT_IDLE_TIMEOUT_SECONDS)

        timeout_f = clamp_idle_timeout(timeout)
        return bool(enabled), timeout_f

    def _schedule(self, timeout_seconds: float) -> None:
        self._cancel_timeout()
        self._armed = True

        if not self._use_glib:
            # Tests drive fire_if_due explicitly; still mark armed.
            return

        try:
            from gi.repository import GLib
        except Exception:
            logger.warning("GLib unavailable; model keep-alive timer not scheduled")
            self._armed = False
            return

        delay = max(1, int(timeout_seconds))
        self._timeout_id = GLib.timeout_add_seconds(delay, self._glib_timeout)

    def _cancel_timeout(self) -> None:
        if self._timeout_id is None:
            return
        try:
            from gi.repository import GLib

            GLib.source_remove(self._timeout_id)
        except Exception:
            pass
        self._timeout_id = None

    def _glib_timeout(self) -> bool:
        """GLib source callback: attempt idle unload once."""
        self._timeout_id = None
        self._fire_unload()
        return False  # SOURCE_REMOVE — bump() reschedules after next activity

    def _fire_unload(self) -> bool:
        if not self._running:
            self._armed = False
            return False

        enabled, _timeout = self._read_config()
        if not enabled:
            self._armed = False
            return False

        if self._is_safe_to_unload is not None:
            try:
                if not self._is_safe_to_unload():
                    logger.debug("Keep-alive unload skipped: not safe to unload")
                    self._armed = False
                    return False
            except Exception:
                logger.error("Keep-alive is_safe_to_unload failed", exc_info=True)
                self._armed = False
                return False

        self._armed = False
        logger.info("Model keep-alive idle timeout reached — unloading model")
        if self._on_idle_unload:
            try:
                self._on_idle_unload()
            except Exception:
                logger.error("Error in keep-alive on_idle_unload callback", exc_info=True)
                return False
        return True
