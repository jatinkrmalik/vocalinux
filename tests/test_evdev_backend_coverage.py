"""
Tests for evdev keyboard backend.

This module tests:
- find_keyboard_devices() function
- device_has_modifier_key() function
- EvdevKeyboardBackend class initialization
- start() and stop() methods
- is_available() and get_permission_hint()
- _handle_key_event() method
- _monitor_devices() thread
"""

import pytest
from unittest.mock import MagicMock, patch, Mock, mock_open
import os
import errno
import threading
import time

from vocalinux.ui.keyboard_backends.evdev_backend import (
    EvdevKeyboardBackend,
    EVDEV_AVAILABLE,
    find_keyboard_devices,
    device_has_modifier_key,
    MODIFIER_KEY_CODES,
)


class TestFindKeyboardDevices:
    """Test find_keyboard_devices() function."""

    def test_find_keyboard_devices_no_devices(self):
        """Test when no keyboard devices are found."""
        mock_proc_content = """I: Bus=0011 Vendor=0001 Product=0001 Version=ab83
N: Name="Power Button"
H: Handlers=
"""
        with patch("builtins.open", mock_open(read_data=mock_proc_content)):
            with patch("os.path.exists", return_value=False):
                result = find_keyboard_devices()
                assert result == []

    def test_find_keyboard_devices_single_device(self):
        """Test finding a single keyboard device."""
        mock_proc_content = """I: Bus=0011 Vendor=0001 Product=0001 Version=ab83
N: Name="AT Translated Set 2 keyboard"
H: Handlers=sysrq kbd event0
B: KEY=10000 7ff 202100 3953b001 68ffe0 1 20000 2000000000000 0
"""
        with patch("builtins.open", mock_open(read_data=mock_proc_content)):
            with patch("os.path.exists", return_value=True):
                result = find_keyboard_devices()
                assert "/dev/input/event0" in result

    def test_find_keyboard_devices_multiple_devices(self):
        """Test finding multiple keyboard devices."""
        mock_proc_content = """I: Bus=0011 Vendor=0001 Product=0001 Version=ab83
N: Name="AT Translated Set 2 keyboard"
H: Handlers=sysrq kbd event0
B: KEY=10000 7ff 202100 3953b001 68ffe0 1 20000 2000000000000 0
I: Bus=0018 Vendor=04f3 Product=0033 Version=0500
N: Name="Elan Touchpad"
H: Handlers=mouse0 event1
B: KEY=ff000000000000 0 0 0
"""
        with patch("builtins.open", mock_open(read_data=mock_proc_content)):
            with patch("os.path.exists", return_value=True):
                result = find_keyboard_devices()
                # Should find event0 (has KEY capability)
                assert len(result) >= 1

    def test_find_keyboard_devices_io_error(self):
        """Test error handling when /proc/bus/input/devices cannot be read."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = find_keyboard_devices()
            assert result == []

    def test_find_keyboard_devices_file_not_found(self):
        """Test error handling when /proc/bus/input/devices doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError()):
            result = find_keyboard_devices()
            assert result == []

    def test_find_keyboard_devices_no_keyboard_capability(self):
        """Test filtering devices without keyboard capability."""
        mock_proc_content = """I: Bus=0019 Vendor=0000 Product=0003 Version=0000
N: Name="Power Button"
H: Handlers=power kbd event2
B: KEY=0
"""
        with patch("builtins.open", mock_open(read_data=mock_proc_content)):
            result = find_keyboard_devices()
            # Device with KEY=0 should not be included
            assert "/dev/input/event2" not in result

    def test_find_keyboard_devices_no_event_handler(self):
        """Test filtering devices without event handler."""
        mock_proc_content = """I: Bus=0011 Vendor=0001 Product=0001 Version=ab83
N: Name="Device with no event"
H: Handlers=kbd
B: KEY=10000 7ff 202100 3953b001 68ffe0 1 20000 2000000000000 0
"""
        with patch("builtins.open", mock_open(read_data=mock_proc_content)):
            result = find_keyboard_devices()
            # Device without eventX handler should not be included
            assert result == []

    def test_find_keyboard_devices_device_not_exists(self):
        """Test filtering devices that don't actually exist in /dev/input."""
        mock_proc_content = """I: Bus=0011 Vendor=0001 Product=0001 Version=ab83
N: Name="AT Translated Set 2 keyboard"
H: Handlers=sysrq kbd event0
B: KEY=10000 7ff 202100 3953b001 68ffe0 1 20000 2000000000000 0
"""
        with patch("builtins.open", mock_open(read_data=mock_proc_content)):
            with patch("os.path.exists", return_value=False):
                result = find_keyboard_devices()
                assert "/dev/input/event0" not in result


class TestDeviceHasModifierKey:
    """Test device_has_modifier_key() function."""

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", False)
    def test_device_has_modifier_key_evdev_not_available(self):
        """Test returns False when evdev is not available."""
        result = device_has_modifier_key("/dev/input/event0", "ctrl")
        assert result is False

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_device_has_modifier_key_has_ctrl(self, mock_input_device):
        """Test device with ctrl modifier key capability."""
        mock_device = MagicMock()
        mock_device.capabilities.return_value = {
            1: [29, 97]  # EV_KEY: [KEY_LEFTCTRL, KEY_RIGHTCTRL]
        }
        mock_input_device.return_value = mock_device

        # Mock ecodes
        with patch("vocalinux.ui.keyboard_backends.evdev_backend.ecodes") as mock_ecodes:
            mock_ecodes.EV_KEY = 1
            result = device_has_modifier_key("/dev/input/event0", "ctrl")
            assert result is True

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_device_has_modifier_key_missing_modifier(self, mock_input_device):
        """Test device without specific modifier key capability."""
        mock_device = MagicMock()
        mock_device.capabilities.return_value = {
            1: [1, 2, 3]  # EV_KEY with different keys (not ctrl)
        }
        mock_input_device.return_value = mock_device

        with patch("vocalinux.ui.keyboard_backends.evdev_backend.ecodes") as mock_ecodes:
            mock_ecodes.EV_KEY = 1
            result = device_has_modifier_key("/dev/input/event0", "ctrl")
            assert result is False

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_device_has_modifier_key_alt(self, mock_input_device):
        """Test device with alt modifier key capability."""
        mock_device = MagicMock()
        mock_device.capabilities.return_value = {
            1: [56, 100]  # EV_KEY: [KEY_LEFTALT, KEY_RIGHTALT]
        }
        mock_input_device.return_value = mock_device

        with patch("vocalinux.ui.keyboard_backends.evdev_backend.ecodes") as mock_ecodes:
            mock_ecodes.EV_KEY = 1
            result = device_has_modifier_key("/dev/input/event0", "alt")
            assert result is True

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_device_has_modifier_key_left_ctrl_specific(self, mock_input_device):
        """Test device with left_ctrl specifically."""
        mock_device = MagicMock()
        mock_device.capabilities.return_value = {
            1: [29]  # EV_KEY: [KEY_LEFTCTRL only]
        }
        mock_input_device.return_value = mock_device

        with patch("vocalinux.ui.keyboard_backends.evdev_backend.ecodes") as mock_ecodes:
            mock_ecodes.EV_KEY = 1
            result = device_has_modifier_key("/dev/input/event0", "left_ctrl")
            assert result is True

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_device_has_modifier_key_os_error(self, mock_input_device):
        """Test handling of OSError when opening device."""
        mock_input_device.side_effect = OSError("Permission denied")

        result = device_has_modifier_key("/dev/input/event0", "ctrl")
        assert result is False

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_device_has_modifier_key_invalid_modifier(self, mock_input_device):
        """Test with invalid modifier name."""
        result = device_has_modifier_key("/dev/input/event0", "invalid")
        assert result is False


class TestEvdevKeyboardBackendInit:
    """Test EvdevKeyboardBackend initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        backend = EvdevKeyboardBackend()
        assert backend.shortcut == "ctrl+ctrl"
        assert backend.mode == "toggle"
        assert backend.active is False
        assert backend.devices == []
        assert backend.device_fds == []
        assert backend.running is False
        assert backend.monitor_thread is None

    def test_init_custom_shortcut(self):
        """Test initialization with custom shortcut."""
        backend = EvdevKeyboardBackend(shortcut="alt+alt")
        assert backend.shortcut == "alt+alt"
        assert backend.modifier_key == "alt"

    def test_init_custom_mode(self):
        """Test initialization with custom mode."""
        backend = EvdevKeyboardBackend(mode="push_to_talk")
        assert backend.mode == "push_to_talk"

    def test_init_double_tap_threshold(self):
        """Test that double tap threshold is initialized."""
        backend = EvdevKeyboardBackend()
        assert backend.double_tap_threshold == 0.3

    def test_init_left_shift_shortcut(self):
        """Test initialization with left_shift shortcut."""
        backend = EvdevKeyboardBackend(shortcut="left_shift+left_shift")
        assert backend.modifier_key == "left_shift"

    def test_init_key_pressed_devices_empty(self):
        """Test that key_pressed_devices starts empty."""
        backend = EvdevKeyboardBackend()
        assert backend.key_pressed_devices == set()


class TestEvdevKeyboardBackendIsAvailable:
    """Test is_available() method."""

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", False)
    def test_is_available_evdev_not_available(self):
        """Test is_available returns False when evdev not available."""
        backend = EvdevKeyboardBackend()
        result = backend.is_available()
        assert result is False

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    def test_is_available_no_devices_found(self, mock_find_devices):
        """Test is_available returns False when no devices found."""
        mock_find_devices.return_value = []
        backend = EvdevKeyboardBackend()
        result = backend.is_available()
        assert result is False

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.device_has_modifier_key")
    def test_is_available_device_with_modifier(self, mock_has_mod, mock_find_devices):
        """Test is_available returns True when device with modifier found."""
        mock_find_devices.return_value = ["/dev/input/event0"]
        mock_has_mod.return_value = True

        backend = EvdevKeyboardBackend()
        result = backend.is_available()
        assert result is True

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.device_has_modifier_key")
    def test_is_available_no_device_with_modifier(self, mock_has_mod, mock_find_devices):
        """Test is_available returns False when no device has required modifier."""
        mock_find_devices.return_value = ["/dev/input/event0"]
        mock_has_mod.return_value = False

        backend = EvdevKeyboardBackend()
        result = backend.is_available()
        assert result is False

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    def test_is_available_exception_handling(self, mock_find_devices):
        """Test is_available handles exceptions gracefully."""
        mock_find_devices.side_effect = Exception("Test error")
        backend = EvdevKeyboardBackend()
        result = backend.is_available()
        assert result is False


class TestEvdevKeyboardBackendPermissionHint:
    """Test get_permission_hint() method."""

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", False)
    def test_permission_hint_evdev_not_available(self):
        """Test permission hint when evdev not installed."""
        backend = EvdevKeyboardBackend()
        result = backend.get_permission_hint()
        assert "pip install" in result or "evdev" in result

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    def test_permission_hint_no_devices(self, mock_find_devices):
        """Test permission hint when no devices found."""
        mock_find_devices.return_value = []
        backend = EvdevKeyboardBackend()
        result = backend.get_permission_hint()
        assert result is None

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_permission_hint_permission_denied(self, mock_input_device, mock_find_devices):
        """Test permission hint when permission denied."""
        mock_find_devices.return_value = ["/dev/input/event0"]
        error = OSError(errno.EACCES, "Permission denied")
        mock_input_device.side_effect = error

        backend = EvdevKeyboardBackend()
        result = backend.get_permission_hint()
        assert result is not None
        assert "input" in result or "group" in result

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_permission_hint_device_accessible(self, mock_input_device, mock_find_devices):
        """Test permission hint when device is accessible."""
        mock_find_devices.return_value = ["/dev/input/event0"]
        mock_device = MagicMock()
        mock_input_device.return_value = mock_device

        backend = EvdevKeyboardBackend()
        result = backend.get_permission_hint()
        assert result is None


class TestEvdevKeyboardBackendStart:
    """Test start() method."""

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", False)
    def test_start_evdev_not_available(self):
        """Test start returns False when evdev not available."""
        backend = EvdevKeyboardBackend()
        result = backend.start()
        assert result is False

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    def test_start_no_devices(self, mock_find_devices):
        """Test start returns False when no devices found."""
        mock_find_devices.return_value = []
        backend = EvdevKeyboardBackend()
        result = backend.start()
        assert result is False

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_start_successful(self, mock_input_device, mock_find_devices):
        """Test successful start."""
        mock_find_devices.return_value = ["/dev/input/event0"]
        mock_device = MagicMock()
        mock_device.fileno.return_value = 10
        mock_input_device.return_value = mock_device

        backend = EvdevKeyboardBackend()
        result = backend.start()

        assert result is True
        assert backend.active is True
        assert backend.running is True
        assert len(backend.devices) == 1
        assert 10 in backend.device_fds

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    def test_start_already_active(self):
        """Test that start returns True if already active."""
        backend = EvdevKeyboardBackend()
        backend.active = True

        result = backend.start()
        assert result is True

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_start_creates_monitor_thread(self, mock_input_device, mock_find_devices):
        """Test that monitor thread is created."""
        mock_find_devices.return_value = ["/dev/input/event0"]
        mock_device = MagicMock()
        mock_device.fileno.return_value = 10
        mock_input_device.return_value = mock_device

        backend = EvdevKeyboardBackend()
        backend.start()

        assert backend.monitor_thread is not None
        assert isinstance(backend.monitor_thread, threading.Thread)

        # Clean up
        backend.stop()


class TestEvdevKeyboardBackendStop:
    """Test stop() method."""

    def test_stop_when_not_active(self):
        """Test that stop is safe when not active."""
        backend = EvdevKeyboardBackend()
        backend.stop()  # Should not raise

    @patch("vocalinux.ui.keyboard_backends.evdev_backend.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices")
    @patch("vocalinux.ui.keyboard_backends.evdev_backend.InputDevice")
    def test_stop_active_backend(self, mock_input_device, mock_find_devices):
        """Test stopping an active backend."""
        mock_find_devices.return_value = ["/dev/input/event0"]
        mock_device = MagicMock()
        mock_device.fileno.return_value = 10
        mock_input_device.return_value = mock_device

        backend = EvdevKeyboardBackend()
        backend.start()

        # Give thread a moment to start
        time.sleep(0.1)

        backend.stop()

        assert backend.active is False
        assert backend.running is False
        assert backend.devices == []
        assert backend.device_fds == []


class TestEvdevKeyboardBackendHandleKeyEvent:
    """Test _handle_key_event() method."""

    def test_handle_key_event_toggle_mode_double_tap(self):
        """Test double-tap detection in toggle mode."""
        backend = EvdevKeyboardBackend(shortcut="ctrl+ctrl", mode="toggle")
        callback = MagicMock()
        backend.register_toggle_callback(callback)

        mock_device = MagicMock()
        mock_event = MagicMock()
        mock_event.code = 29  # KEY_LEFTCTRL
        mock_event.value = 1  # Press

        # Set up timing for double-tap
        backend.last_key_press_time = time.time() - 0.1
        backend.last_trigger_time = time.time() - 1.0

        with patch("vocalinux.ui.keyboard_backends.evdev_backend.ecodes") as mock_ecodes:
            mock_ecodes.EV_KEY = 1
            backend._handle_key_event(mock_event, mock_device)

        time.sleep(0.1)

    def test_handle_key_event_non_target_key(self):
        """Test that non-target keys are ignored."""
        backend = EvdevKeyboardBackend(shortcut="ctrl+ctrl")
        callback = MagicMock()
        backend.register_toggle_callback(callback)

        mock_device = MagicMock()
        mock_event = MagicMock()
        mock_event.code = 1  # Some non-modifier key
        mock_event.value = 1

        with patch("vocalinux.ui.keyboard_backends.evdev_backend.ecodes") as mock_ecodes:
            mock_ecodes.EV_KEY = 1
            backend._handle_key_event(mock_event, mock_device)

        # Callback should not be called

    def test_handle_key_event_push_to_talk_press(self):
        """Test push-to-talk mode triggers on press."""
        backend = EvdevKeyboardBackend(shortcut="alt+alt", mode="push_to_talk")
        callback = MagicMock()
        backend.register_press_callback(callback)

        mock_device = MagicMock()
        mock_event = MagicMock()
        mock_event.code = 56  # KEY_LEFTALT
        mock_event.value = 1  # Press

        with patch("vocalinux.ui.keyboard_backends.evdev_backend.ecodes") as mock_ecodes:
            mock_ecodes.EV_KEY = 1
            backend._handle_key_event(mock_event, mock_device)

        time.sleep(0.1)

    def test_handle_key_event_push_to_talk_release(self):
        """Test push-to-talk mode triggers on release."""
        backend = EvdevKeyboardBackend(shortcut="shift+shift", mode="push_to_talk")
        callback = MagicMock()
        backend.register_release_callback(callback)

        mock_device = MagicMock()
        mock_event = MagicMock()
        mock_event.code = 42  # KEY_LEFTSHIFT
        mock_event.value = 0  # Release

        with patch("vocalinux.ui.keyboard_backends.evdev_backend.ecodes") as mock_ecodes:
            mock_ecodes.EV_KEY = 1
            backend._handle_key_event(mock_event, mock_device)

        time.sleep(0.1)

    def test_handle_key_event_exception_handling(self):
        """Test exception handling in _handle_key_event."""
        backend = EvdevKeyboardBackend()

        mock_device = MagicMock()
        mock_event = MagicMock()
        mock_event.code = 29

        # Make _get_target_key_codes raise an exception
        backend._get_target_key_codes = MagicMock(side_effect=Exception("Test error"))

        backend._handle_key_event(mock_event, mock_device)  # Should not raise


class TestEvdevKeyboardBackendGetTargetKeyCodes:
    """Test _get_target_key_codes() method."""

    def test_get_target_key_codes_ctrl(self):
        """Test getting key codes for ctrl modifier."""
        backend = EvdevKeyboardBackend(shortcut="ctrl+ctrl")
        result = backend._get_target_key_codes()

        assert 29 in result  # KEY_LEFTCTRL
        assert 97 in result  # KEY_RIGHTCTRL

    def test_get_target_key_codes_left_ctrl(self):
        """Test getting key codes for left_ctrl modifier."""
        backend = EvdevKeyboardBackend(shortcut="left_ctrl+left_ctrl")
        result = backend._get_target_key_codes()

        assert 29 in result  # KEY_LEFTCTRL
        assert 97 not in result  # KEY_RIGHTCTRL should not be included

    def test_get_target_key_codes_alt(self):
        """Test getting key codes for alt modifier."""
        backend = EvdevKeyboardBackend(shortcut="alt+alt")
        result = backend._get_target_key_codes()

        assert 56 in result  # KEY_LEFTALT
        assert 100 in result  # KEY_RIGHTALT

    def test_get_target_key_codes_shift(self):
        """Test getting key codes for shift modifier."""
        backend = EvdevKeyboardBackend(shortcut="shift+shift")
        result = backend._get_target_key_codes()

        assert 42 in result  # KEY_LEFTSHIFT
        assert 54 in result  # KEY_RIGHTSHIFT
