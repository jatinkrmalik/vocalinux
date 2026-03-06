"""
evdev keyboard backend for Wayland support.

This backend uses python-evdev to read keyboard events directly from
input devices, which works on both X11 and Wayland (with proper permissions).
"""

import errno
import logging
import os
import select
import threading
import time
from typing import Dict, List, Optional, Set

# Try to import evdev
try:
    import evdev
    from evdev import InputDevice, ecodes

    EVDEV_AVAILABLE = True
except ImportError:
    evdev = None  # type: ignore
    InputDevice = None  # type: ignore
    ecodes = None  # type: ignore
    EVDEV_AVAILABLE = False

from .base import (
    DEFAULT_SHORTCUT,
    DEFAULT_SHORTCUT_MODE,
    KeyboardBackend,
    is_double_tap_shortcut,
    parse_keys,
)

logger = logging.getLogger(__name__)


# Key codes for modifier keys (left and right variants)
KEY_LEFTCTRL = 29
KEY_RIGHTCTRL = 97
KEY_LEFTALT = 56
KEY_RIGHTALT = 100
KEY_LEFTSHIFT = 42
KEY_RIGHTSHIFT = 54
KEY_LEFTMETA = 125  # Super/Windows key
KEY_RIGHTMETA = 126

# Map modifier key names to evdev key codes
MODIFIER_KEY_CODES: Dict[str, Set[int]] = {
    "ctrl": {KEY_LEFTCTRL, KEY_RIGHTCTRL},
    "alt": {KEY_LEFTALT, KEY_RIGHTALT},
    "shift": {KEY_LEFTSHIFT, KEY_RIGHTSHIFT},
    "super": {KEY_LEFTMETA, KEY_RIGHTMETA},
}

# Regular key codes (letters)
LETTER_KEY_CODES: Dict[str, Set[int]] = {}
if EVDEV_AVAILABLE:
    for _i, _letter in enumerate("abcdefghijklmnopqrstuvwxyz"):
        _code = getattr(ecodes, f"KEY_{_letter.upper()}", None)
        if _code is not None:
            LETTER_KEY_CODES[_letter] = {_code}

# F-key codes
FKEY_CODES: Dict[str, Set[int]] = {}
if EVDEV_AVAILABLE:
    for _fi in range(1, 25):
        _code = getattr(ecodes, f"KEY_F{_fi}", None)
        if _code is not None:
            FKEY_CODES[f"f{_fi}"] = {_code}

# Special key codes
SPECIAL_KEY_CODES: Dict[str, Set[int]] = {}
if EVDEV_AVAILABLE:
    _special_map = {
        "space": "KEY_SPACE",
        "tab": "KEY_TAB",
        "pause": "KEY_PAUSE",
        "scrolllock": "KEY_SCROLLLOCK",
        "printscreen": "KEY_SYSRQ",
        "insert": "KEY_INSERT",
        "delete": "KEY_DELETE",
        "home": "KEY_HOME",
        "end": "KEY_END",
        "pageup": "KEY_PAGEUP",
        "pagedown": "KEY_PAGEDOWN",
        "enter": "KEY_ENTER",
        "return": "KEY_ENTER",
        "escape": "KEY_ESC",
        "backspace": "KEY_BACKSPACE",
        "up": "KEY_UP",
        "down": "KEY_DOWN",
        "left": "KEY_LEFT",
        "right": "KEY_RIGHT",
        "capslock": "KEY_CAPSLOCK",
        "numlock": "KEY_NUMLOCK",
        "menu": "KEY_COMPOSE",
    }
    for _name, _ecode_name in _special_map.items():
        _code = getattr(ecodes, _ecode_name, None)
        if _code is not None:
            SPECIAL_KEY_CODES[_name] = {_code}

# Digit key codes
DIGIT_KEY_CODES: Dict[str, Set[int]] = {}
if EVDEV_AVAILABLE:
    _digit_map = {
        "0": "KEY_0",
        "1": "KEY_1",
        "2": "KEY_2",
        "3": "KEY_3",
        "4": "KEY_4",
        "5": "KEY_5",
        "6": "KEY_6",
        "7": "KEY_7",
        "8": "KEY_8",
        "9": "KEY_9",
    }
    for _digit, _ecode_name in _digit_map.items():
        _code = getattr(ecodes, _ecode_name, None)
        if _code is not None:
            DIGIT_KEY_CODES[_digit] = {_code}


def resolve_evdev_codes(key_name: str) -> Set[int]:
    """Resolve a key name to evdev key code(s). Returns set of codes (left/right variants)."""
    if key_name in MODIFIER_KEY_CODES:
        return MODIFIER_KEY_CODES[key_name]
    if key_name in LETTER_KEY_CODES:
        return LETTER_KEY_CODES[key_name]
    if key_name in FKEY_CODES:
        return FKEY_CODES[key_name]
    if key_name in SPECIAL_KEY_CODES:
        return SPECIAL_KEY_CODES[key_name]
    if key_name in DIGIT_KEY_CODES:
        return DIGIT_KEY_CODES[key_name]
    return set()


def find_keyboard_devices() -> List[str]:
    """
    Find all keyboard input devices.

    Returns:
        List of device paths for keyboard devices
    """
    keyboard_devices = []

    try:
        # Read from /proc/bus/input/devices to find keyboards
        with open("/proc/bus/input/devices", "r") as f:
            current_device = None
            for line in f:
                line = line.rstrip("\n")
                if line.startswith("I: Bus="):
                    current_device = {"handlers": []}
                elif line.startswith("H: Handlers=") and current_device is not None:
                    handlers = line.split("=", 1)[1].strip()
                    current_device["handlers"] = handlers.split()
                elif line.startswith("B: KEY=") and current_device is not None:
                    # Check if this device has keyboard keys (bit 0 is set)
                    key_bits = line.split("=", 1)[1].strip()
                    # The first hex digit after KEY= contains keyboard capability
                    # If it's not 0, 1, or ffffffffff, it has keyboard keys
                    if key_bits and key_bits != "0":
                        # Check if event handler exists
                        for handler in current_device.get("handlers", []):
                            if handler.startswith("event"):
                                device_path = f"/dev/input/{handler}"
                                if os.path.exists(device_path):
                                    keyboard_devices.append(device_path)
                    current_device = None

    except (IOError, OSError) as e:
        logger.error(f"Error reading input devices: {e}")

    return keyboard_devices


def device_has_key(device_path: str, key_name: str) -> bool:
    """
    Check if a device has a specific key capability.

    Args:
        device_path: Path to the input device
        key_name: The key name (e.g., "ctrl", "alt", "d", "f5")

    Returns:
        True if the device can send the specified key events
    """
    if not EVDEV_AVAILABLE:
        return False

    key_codes = resolve_evdev_codes(key_name)
    if not key_codes:
        return False

    try:
        device = InputDevice(device_path)
        capabilities = device.capabilities()
        device.close()

        # Check if device has EV_KEY capability and supports the key
        if ecodes.EV_KEY in capabilities:
            key_caps = capabilities[ecodes.EV_KEY]
            for key_code in key_codes:
                if key_code in key_caps:
                    return True
    except (OSError, IOError):
        pass

    return False


def device_has_modifier_key(device_path: str, modifier: str = "ctrl") -> bool:
    """
    Check if a device has a specific modifier key capability.

    Args:
        device_path: Path to the input device
        modifier: The modifier key name ("ctrl", "alt", "shift", "super")

    Returns:
        True if the device can send the specified modifier key events
    """
    return device_has_key(device_path, modifier)


class EvdevKeyboardBackend(KeyboardBackend):
    """
    Keyboard backend using python-evdev.

    This backend reads keyboard events directly from input devices,
    which works on both X11 and Wayland when the user has permission
    to read from /dev/input/event* devices (member of 'input' group).
    """

    def __init__(self, shortcut: str = DEFAULT_SHORTCUT, mode: str = DEFAULT_SHORTCUT_MODE):
        """
        Initialize the evdev keyboard backend.

        Args:
            shortcut: The shortcut string to listen for (e.g., "ctrl+ctrl")
            mode: The shortcut mode ("toggle" or "push_to_talk")
        """
        super().__init__(shortcut, mode)
        self.devices: List[InputDevice] = []
        self.device_fds: List[int] = []
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None

        self.last_trigger_time = 0
        self.last_key_press_time = 0
        self.double_tap_threshold = 0.3  # seconds
        self.key_pressed_devices: Set[int] = set()

        self._devices_lock = threading.Lock()

        # Combo tracking
        self._pressed_key_codes: Set[int] = set()
        self._combo_active: bool = False
        self._target_code_groups: List[Set[int]] = []
        self._all_target_codes: Set[int] = set()
        self._update_target_keys()

        if not EVDEV_AVAILABLE:
            logger.error("python-evdev not available")

    def _update_target_keys(self) -> None:
        """Update the target key code groups from the current shortcut."""
        if self._is_double_tap():
            # For double-tap, we only need the single modifier codes
            key_name = self._shortcut.lower().strip().split("+")[0]
            codes = resolve_evdev_codes(key_name)
            self._target_code_groups = [codes] if codes else []
            self._all_target_codes = codes.copy() if codes else set()
        else:
            # For combo shortcuts, build a group per key
            try:
                keys = parse_keys(self._shortcut)
                self._target_code_groups = []
                self._all_target_codes = set()
                for k in keys:
                    codes = resolve_evdev_codes(k)
                    if codes:
                        self._target_code_groups.append(codes)
                        self._all_target_codes |= codes
            except ValueError:
                self._target_code_groups = []
                self._all_target_codes = set()

    def _is_double_tap(self) -> bool:
        """Check if the current shortcut is a double-tap shortcut."""
        return is_double_tap_shortcut(self._shortcut)

    def set_shortcut(self, shortcut: str) -> None:
        """Update the shortcut. Should be called while backend is stopped or during init."""
        super().set_shortcut(shortcut)
        self._update_target_keys()
        # Reset combo state
        self._pressed_key_codes = set()
        self._combo_active = False

    def _combo_is_satisfied(self) -> bool:
        """Check if all target code groups have at least one code pressed."""
        for group in self._target_code_groups:
            if not (group & self._pressed_key_codes):
                return False
        return len(self._target_code_groups) > 0

    def is_available(self) -> bool:
        """Check if evdev is available and we can access a keyboard device with the needed keys."""
        if not EVDEV_AVAILABLE:
            return False

        try:
            devices = find_keyboard_devices()
            if not devices:
                return False

            if self._is_double_tap():
                # For double-tap, just check the modifier key
                for device_path in devices:
                    if device_has_key(device_path, self._modifier_key):
                        return True
            else:
                # For combo shortcuts, check that all keys in the shortcut
                # can be found across available devices
                try:
                    keys = parse_keys(self._shortcut)
                except ValueError:
                    return False

                for key_name in keys:
                    found = False
                    for device_path in devices:
                        if device_has_key(device_path, key_name):
                            found = True
                            break
                    if not found:
                        return False
                return True

            return False
        except Exception:
            return False

    def get_permission_hint(self) -> Optional[str]:
        """
        Get permission hint for evdev backend.

        Returns:
            Instructions if permissions are missing, None otherwise
        """
        if not EVDEV_AVAILABLE:
            return "Install python-evdev: pip install evdev"

        try:
            devices = find_keyboard_devices()
            if not devices:
                return None  # No devices found, not a permission issue

            # Try to open the first device to check permissions
            for device_path in devices[:1]:  # Just check the first one
                try:
                    InputDevice(device_path)
                    return None  # Successfully opened, permissions OK
                except (OSError, IOError) as e:
                    if "Permission denied" in str(e) or e.errno == errno.EACCES:
                        return (
                            "Add your user to the 'input' group and log out/in:\n"
                            "sudo usermod -a -G input $USER"
                        )
        except Exception:
            pass

        return None

    def start(self) -> bool:
        """
        Start the evdev keyboard listener.

        Returns:
            True if started successfully, False otherwise
        """
        if not EVDEV_AVAILABLE:
            logger.error("Cannot start: python-evdev not available")
            return False

        if self.active:
            return True

        # Find keyboard devices
        device_paths = find_keyboard_devices()
        if not device_paths:
            logger.error("No keyboard devices found")
            return False

        logger.info(f"Found {len(device_paths)} keyboard device(s)")
        logger.info(f"Listening for shortcut: {self._shortcut} (mode: {self._mode})")

        # Open devices
        self.devices = []
        self.device_fds = []
        self.key_pressed_devices = set()
        self._pressed_key_codes = set()
        self._combo_active = False

        for device_path in device_paths:
            try:
                device = InputDevice(device_path)
                self.devices.append(device)
                self.device_fds.append(device.fileno())
                logger.debug(f"Opened keyboard device: {device_path} ({device.name})")
            except (OSError, IOError) as e:
                logger.warning(f"Cannot open {device_path}: {e}")
                continue

        if not self.devices:
            logger.error("Failed to open any keyboard device (permission denied?)")
            return False

        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
        self.monitor_thread.start()

        logger.info("Evdev keyboard listener started successfully")
        self.active = True
        return True

    def stop(self) -> None:
        """Stop the evdev keyboard listener."""
        if not self.active:
            return

        logger.info("Stopping evdev keyboard listener")
        self.running = False
        self.active = False

        # Close devices
        for device in self.devices:
            try:
                device.close()
            except Exception:
                pass

        self.devices = []
        self.device_fds = []

        # Wait for monitor thread to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            self.monitor_thread = None

    def _monitor_devices(self) -> None:
        """Monitor keyboard devices for events."""
        logger.debug("Starting device monitor thread")

        while self.running:
            try:
                # Use select to wait for events on any device
                if not self.device_fds:
                    break

                readable, _, _ = select.select(self.device_fds, [], [], 1.0)  # 1 second timeout

                for fd in readable:
                    try:
                        # Find the device for this fd
                        device = None
                        for d in self.devices:
                            if d.fileno() == fd:
                                device = d
                                break

                        if device is None:
                            continue

                        # Read events from this device
                        for event in device.read():
                            if event.type == ecodes.EV_KEY:
                                self._handle_key_event(event, device)

                    except (OSError, IOError):
                        # Device was disconnected - remove it to avoid busy loop
                        device_name = (
                            device.name if device and hasattr(device, "name") else "unknown"
                        )
                        logger.info(f"Device disconnected: {device_name} (fd={fd})")
                        if device is not None:
                            try:
                                device.close()
                            except Exception:
                                pass
                            try:
                                with self._devices_lock:
                                    self.devices.remove(device)
                            except ValueError:
                                pass
                        if fd in self.device_fds:
                            with self._devices_lock:
                                self.device_fds.remove(fd)
                        continue

            except (OSError, ValueError) as e:
                if self.running:
                    logger.error(f"Error monitoring devices: {e}")
                break

        logger.debug("Device monitor thread stopped")

    def _handle_key_event(self, event, device) -> None:
        """Handle a key event from evdev."""
        try:
            code = event.code
            value = event.value  # 0 = release, 1 = press, 2 = repeat

            if self._is_double_tap():
                self._handle_double_tap_event(code, value, device)
            else:
                self._handle_combo_event(code, value)

        except Exception as e:
            logger.error(f"Error handling key event: {e}")

    def _handle_double_tap_event(self, code: int, value: int, device) -> None:
        """Handle key events for double-tap shortcuts."""
        target_codes = self._all_target_codes

        if code not in target_codes:
            return

        device_id = id(device)

        if value == 1:  # Key press
            self.key_pressed_devices.add(device_id)
            current_time = time.time()

            if self._mode == "toggle":
                # Check for double-tap
                if (
                    current_time - self.last_key_press_time < self.double_tap_threshold
                    and self.double_tap_callback is not None
                    and current_time - self.last_trigger_time > 0.5
                ):
                    logger.debug(f"Double-tap {self._modifier_key} detected (evdev)")
                    self.last_trigger_time = current_time
                    threading.Thread(target=self.double_tap_callback, daemon=True).start()
            elif self._mode == "push_to_talk":
                # Trigger on press
                if self.key_press_callback is not None:
                    logger.debug(f"Key press {self._modifier_key} detected (evdev)")
                    threading.Thread(target=self.key_press_callback, daemon=True).start()

            self.last_key_press_time = current_time

        elif value == 0:  # Key release
            self.key_pressed_devices.discard(device_id)

            if self._mode == "push_to_talk":
                # Trigger on release
                if self.key_release_callback is not None:
                    logger.debug(f"Key release {self._modifier_key} detected (evdev)")
                    threading.Thread(target=self.key_release_callback, daemon=True).start()

    def _handle_combo_event(self, code: int, value: int) -> None:
        """Handle key events for combo shortcuts."""
        # Only track keys that are part of our target combo
        if code not in self._all_target_codes:
            return

        if value == 1:  # Key press
            self._pressed_key_codes.add(code)

            if self._combo_is_satisfied() and not self._combo_active:
                self._combo_active = True
                if self._mode == "toggle":
                    if self.double_tap_callback is not None:
                        logger.debug(f"Combo {self._shortcut} activated (evdev)")
                        threading.Thread(target=self.double_tap_callback, daemon=True).start()
                elif self._mode == "push_to_talk":
                    if self.key_press_callback is not None:
                        logger.debug(f"Combo press {self._shortcut} detected (evdev)")
                        threading.Thread(target=self.key_press_callback, daemon=True).start()

        elif value == 0:  # Key release
            self._pressed_key_codes.discard(code)

            if self._combo_active and not self._combo_is_satisfied():
                self._combo_active = False
                if self._mode == "push_to_talk":
                    if self.key_release_callback is not None:
                        logger.debug(f"Combo release {self._shortcut} detected (evdev)")
                        threading.Thread(target=self.key_release_callback, daemon=True).start()


# Export availability
__all__ = [
    "EvdevKeyboardBackend",
    "EVDEV_AVAILABLE",
    "find_keyboard_devices",
    "device_has_modifier_key",
    "device_has_key",
    "resolve_evdev_codes",
]
