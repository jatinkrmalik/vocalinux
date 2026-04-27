"""
Suspend/resume handler for Vocalinux.

Monitors systemd-logind via D-Bus for PrepareForSleep signals and
automatically reinitializes the audio pipeline and speech model
after the system resumes from suspend or hibernation.
"""

import logging
from typing import Callable, Optional

from gi.repository import Gio, GLib

logger = logging.getLogger(__name__)

_LOGIND_BUS_NAME = "org.freedesktop.login1"
_LOGIND_OBJECT_PATH = "/org/freedesktop/login1"
_LOGIND_INTERFACE = "org.freedesktop.login1.Manager"
_PREPARE_FOR_SLEEP_SIGNAL = "PrepareForSleep"


class SuspendHandler:
    """Handles system suspend/resume events via D-Bus.

    Subscribes to org.freedesktop.login1.Manager.PrepareForSleep and
    invokes callbacks when the system is about to suspend or has just
    resumed.  All callbacks run on the GLib main loop thread so GTK
    operations are safe.

    Usage::

        handler = SuspendHandler(
            on_suspend=my_stop_fn,
            on_resume=my_resume_fn,
        )
        # ... later, on shutdown:
        handler.shutdown()
    """

    def __init__(
        self,
        on_suspend: Optional[Callable[[], None]] = None,
        on_resume: Optional[Callable[[], None]] = None,
    ):
        self._on_suspend = on_suspend
        self._on_resume = on_resume
        self._proxy: Optional[Gio.DBusProxy] = None
        self._was_suspended = False
        self._connect()

    def _connect(self) -> None:
        """Create a D-Bus proxy and subscribe to PrepareForSleep."""
        try:
            self._proxy = Gio.DBusProxy.new_for_bus_sync(
                bus_type=Gio.BusType.SYSTEM,
                flags=Gio.DBusProxyFlags.NONE,
                info=None,
                name=_LOGIND_BUS_NAME,
                object_path=_LOGIND_OBJECT_PATH,
                interface_name=_LOGIND_INTERFACE,
                cancellable=None,
            )
            self._proxy.connect("g-signal", self._on_signal)
            logger.info("Suspend/resume handler initialized (logind D-Bus)")
        except Exception as exc:
            logger.warning(
                "Unexpected error connecting to logind D-Bus: %s",
                exc,
            )
            self._proxy = None

    def _on_signal(
        self,
        proxy: Gio.DBusProxy,
        sender_name: str,
        signal_name: str,
        parameters: GLib.Variant,
    ) -> None:
        """Handle incoming D-Bus signals from logind."""
        if signal_name != _PREPARE_FOR_SLEEP_SIGNAL:
            return

        # The parameter is a tuple (b entering_sleep,)
        if parameters.get_type_string() != "(b)":
            logger.warning(
                "Unexpected PrepareForSleep parameter type: %s",
                parameters.get_type_string(),
            )
            return

        entering_sleep = parameters.unpack()[0]

        if entering_sleep:
            logger.info("System preparing to suspend")
            self._was_suspended = True
            if self._on_suspend:
                try:
                    self._on_suspend()
                except Exception:
                    logger.error("Error in suspend callback", exc_info=True)
        else:
            logger.info("System resuming from suspend")
            # Also handles the edge-case where we missed the
            # PrepareForSleep(true) (e.g. hibernation resume —
            # see systemd issue #30666).
            self._was_suspended = False
            if self._on_resume:
                try:
                    self._on_resume()
                except Exception:
                    logger.error("Error in resume callback", exc_info=True)

    def shutdown(self) -> None:
        """Disconnect from D-Bus. Call from GTK destroy / quit handler."""
        if self._proxy is not None:
            try:
                self._proxy.disconnect_by_func(self._on_signal)
            except Exception:
                pass
            self._proxy = None
        logger.info("Suspend/resume handler shut down")

    @property
    def active(self) -> bool:
        """Return True if the D-Bus proxy is connected."""
        return self._proxy is not None
