"""
Tests for D-Bus based external activation.

Covers:
- CLI dispatch: --toggle/--start/--stop forward the right D-Bus command.
- Config gate: external mode skips the internal hotkey listener.
- D-Bus handlers route to the correct recognition callbacks.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# gi is mocked globally by conftest, so these imports are safe headless.
from vocalinux import dbus_service
from vocalinux.main import main
from vocalinux.ui.tray_indicator import TrayIndicator

# -- CLI dispatch ----------------------------------------------------------


@pytest.mark.parametrize(
    "flag,command",
    [("--toggle", "toggle"), ("--start", "start"), ("--stop", "stop")],
)
def test_cli_flag_sends_matching_command(flag, command):
    """Each trigger flag forwards the matching command and exits with 0."""
    with patch("vocalinux.dbus_service.send_command", return_value=True) as mock_send:
        with patch.object(sys, "argv", ["vocalinux", flag]):
            with pytest.raises(SystemExit) as exc_info:
                main()
    assert exc_info.value.code == 0
    mock_send.assert_called_once_with(command)


def test_cli_flag_exits_nonzero_when_no_instance():
    """When no instance answers, the trigger exits with a non-zero code."""
    with patch("vocalinux.dbus_service.send_command", return_value=False):
        with patch.object(sys, "argv", ["vocalinux", "--toggle"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
    assert exc_info.value.code == 1


def test_no_trigger_flag_does_not_dispatch():
    """Without a trigger flag, main() proceeds past the dispatch shortcut."""
    with patch("vocalinux.dbus_service.send_command") as mock_send:
        # check_dependencies returns False so main() exits early after dispatch.
        with patch("vocalinux.main.check_dependencies", return_value=False):
            with patch("vocalinux.single_instance.acquire_lock", return_value=True):
                with patch.object(sys, "argv", ["vocalinux"]):
                    with pytest.raises(SystemExit):
                        main()
    mock_send.assert_not_called()


# -- Config gate -----------------------------------------------------------


def _fake_indicator(disable_internal_hotkey):
    """Minimal stand-in for calling _setup_keyboard_shortcuts in isolation."""
    fake = MagicMock()
    fake.shortcut_manager.active = False
    fake.config_manager.get_bool.return_value = disable_internal_hotkey
    fake.config_manager.get_str.return_value = "toggle"
    return fake


def test_external_mode_skips_listener_start():
    """With the option enabled, the evdev/pynput listener is not started."""
    fake = _fake_indicator(disable_internal_hotkey=True)
    TrayIndicator._setup_keyboard_shortcuts(fake)
    fake.shortcut_manager.start.assert_not_called()
    fake.shortcut_manager.register_toggle_callback.assert_called_once_with(None)


def test_default_mode_starts_listener():
    """With the option disabled (default), the listener starts as before."""
    fake = _fake_indicator(disable_internal_hotkey=False)
    TrayIndicator._setup_keyboard_shortcuts(fake)
    fake.shortcut_manager.start.assert_called_once()


# -- D-Bus handlers --------------------------------------------------------


@pytest.mark.parametrize(
    "method,expected",
    [("Toggle", "on_toggle"), ("Start", "on_start"), ("Stop", "on_stop")],
)
def test_method_call_routes_to_callback(method, expected):
    """A D-Bus method call invokes the matching callback on the main thread."""
    callbacks = {
        "on_toggle": MagicMock(),
        "on_start": MagicMock(),
        "on_stop": MagicMock(),
    }
    service = dbus_service.VocalinuxDBusService(
        on_toggle=callbacks["on_toggle"],
        on_start=callbacks["on_start"],
        on_stop=callbacks["on_stop"],
    )

    invocation = MagicMock()
    # Make idle_add run the marshalled call synchronously for the assertion.
    with patch.object(dbus_service.GLib, "idle_add", side_effect=lambda fn, *a: fn(*a)):
        service._handle_method_call(
            MagicMock(),
            "sender",
            dbus_service.OBJECT_PATH,
            dbus_service.INTERFACE_NAME,
            method,
            None,
            invocation,
        )

    callbacks[expected].assert_called_once_with()
    for name, cb in callbacks.items():
        if name != expected:
            cb.assert_not_called()
    invocation.return_value.assert_called_once()


def test_unknown_method_returns_error():
    """An unknown method name returns a D-Bus error and no callback runs."""
    on_toggle = MagicMock()
    service = dbus_service.VocalinuxDBusService(
        on_toggle=on_toggle, on_start=MagicMock(), on_stop=MagicMock()
    )
    invocation = MagicMock()
    service._handle_method_call(
        MagicMock(),
        "sender",
        dbus_service.OBJECT_PATH,
        dbus_service.INTERFACE_NAME,
        "Bogus",
        None,
        invocation,
    )
    invocation.return_error_literal.assert_called_once()
    on_toggle.assert_not_called()


def test_shutdown_releases_name_and_object():
    """shutdown() unregisters the object and unowns the bus name, idempotently."""
    service = dbus_service.VocalinuxDBusService(
        on_toggle=MagicMock(), on_start=MagicMock(), on_stop=MagicMock()
    )
    # Simulate a successful registration having happened.
    connection = MagicMock()
    service._connection = connection
    service._registration_id = 42
    service._owner_id = 7

    with patch.object(dbus_service.Gio, "bus_unown_name") as mock_unown:
        service.shutdown()
        connection.unregister_object.assert_called_once_with(42)
        mock_unown.assert_called_once_with(7)

        # A second shutdown must be a no-op (ids cleared).
        connection.unregister_object.reset_mock()
        mock_unown.reset_mock()
        service.shutdown()
        connection.unregister_object.assert_not_called()
        mock_unown.assert_not_called()


def test_send_command_uses_proxy_call():
    """send_command forwards the mapped method name through a D-Bus proxy."""
    mock_proxy = MagicMock()
    with patch.object(dbus_service.Gio.DBusProxy, "new_for_bus_sync", return_value=mock_proxy):
        result = dbus_service.send_command("toggle")
    assert result is True
    args = mock_proxy.call_sync.call_args.args
    assert args[0] == "Toggle"


def test_send_command_rejects_unknown():
    """An unknown command name raises ValueError."""
    with pytest.raises(ValueError):
        dbus_service.send_command("explode")
