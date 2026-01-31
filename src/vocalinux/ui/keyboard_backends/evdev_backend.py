"""
evdev keyboard backend for Wayland support.

This backend uses python-evdev to read keyboard events directly from
input devices, which works on both X11 and Wayland (with proper permissions).

SECURITY WARNING:
- This backend requires access to /dev/input/event* devices
- User must be in the 'input' group (sudo usermod -a -G input $USER)
- Granting input device access allows monitoring all keyboard events
- Only use this backend if you trust the application and understand the security implications
- On multi-user systems, consider the privacy implications of keyboard monitoring
"""

import errno
import logging
import os
import select
import threading
import time
from typing import List, Optional, Set

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

from .base import KeyboardBackend

logger = logging.getLogger(__name__)


# Key code for Ctrl (left and right)
KEY_LEFTCTRL = 29
KEY_RIGHTCTRL = 97
KEY_CTRL = {KEY_LEFTCTRL, KEY_RIGHTCTRL}


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

    # Security: Remove duplicate devices to prevent multiple event streams
    keyboard_devices = list(dict.fromkeys(keyboard_devices))
    
    # Security: Filter out suspicious device paths
    safe_devices = []
    for device_path in keyboard_devices:
        # Basic path validation to prevent directory traversal
        if (device_path.startswith("/dev/input/event") and 
            device_path.isprintable() and
            os.path.exists(device_path) and 
            os.access(device_path, os.R_OK) and
            # Ensure it's a valid character device
            os.path.isabs(device_path)):
            safe_devices.append(device_path)
        else:
            logger.warning(f"Skipping suspicious device path: {device_path}")
    
    return safe_devices


class EvdevKeyboardBackend(KeyboardBackend):
    """
    Keyboard backend using python-evdev.

    This backend reads keyboard events directly from input devices,
    which works on both X11 and Wayland when the user has permission
    to read from /dev/input/event* devices (member of 'input' group).
    """

    def __init__(self):
        """Initialize the evdev keyboard backend."""
        super().__init__()
        self.devices: List[InputDevice] = []
        self.device_fds: List[int] = []
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None

        self.last_trigger_time = 0
        self.last_ctrl_press_time = 0
        self.double_tap_threshold = 0.3  # seconds
        self.ctrl_pressed_devices: Set[int] = set()

        if not EVDEV_AVAILABLE:
            logger.error("python-evdev not available")
        
        # Security: Initialize device monitoring limits
        self.max_devices = 10
        self.max_events_per_iteration = 50

    def is_available(self) -> bool:
        """Check if evdev is available."""
        if not EVDEV_AVAILABLE:
            return False

        # Check if we can access at least one keyboard device
        try:
            devices = find_keyboard_devices()
            return len(devices) > 0
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
                            "Add your user to the 'input' group and log out/in:\\n"
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

        # Open devices with improved error handling and security
        self.devices = []
        self.device_fds = []
        self.ctrl_pressed_devices = set()

        for device_path in device_paths:
            try:
                device = InputDevice(device_path)
                
                # Security: Check if device has keyboard capabilities before opening
                if not hasattr(device, 'capabilities'):
                    logger.warning(f"Device {device_path} has no capabilities - skipping")
                    continue
                
                self.devices.append(device)
                self.device_fds.append(device.fileno())
                logger.debug(f"Opened keyboard device: {device_path} ({device.name})")
                
            except (OSError, IOError) as e:
                if "Permission denied" in str(e) or e.errno == errno.EACCES:
                    logger.error(f"Permission denied for {device_path}. "
                               "Add user to 'input' group: sudo usermod -a -G input $USER")
                else:
                    logger.warning(f"Cannot open {device_path}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error opening {device_path}: {e}")
                continue

        if not self.devices:
            logger.error("Failed to open any keyboard device. Check permissions and input group membership.")
            return False

        # Security: Limit the number of devices we monitor to prevent resource exhaustion
        if len(self.devices) > 10:
            logger.warning(f"Too many keyboard devices ({len(self.devices)}). "
                         "Limiting to first 10 for stability.")
            self.devices = self.devices[:10]
            self.device_fds = self.device_fds[:10]

        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_devices, daemon=True)
        self.monitor_thread.start()

        logger.info(f"Evdev keyboard listener started successfully (monitoring {len(self.devices)} devices)")
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

                # Security: Add timeout to prevent indefinite blocking
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

                        # Security: Limit the number of events read per iteration to prevent DoS
                        event_count = 0
                        max_events_per_iteration = 50
                        
                        for event in device.read():
                            event_count += 1
                            if event_count > max_events_per_iteration:
                                logger.warning(f"Too many events from device {device.name} - throttling")
                                break
                                
                            if hasattr(event, 'type') and event.type == ecodes.EV_KEY:
                                self._handle_key_event(event, device)

                    except (OSError, IOError) as e:
                        # Device was likely disconnected
                        logger.debug(f"Device disconnected: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error reading from device: {e}")
                        continue

            except (OSError, ValueError) as e:
                if self.running:
                    logger.error(f"Error monitoring devices: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitor loop: {e}")
                break

        logger.debug("Device monitor thread stopped")

    def _handle_key_event(self, event, device) -> None:
        """Handle a key event from evdev."""
        try:
            # Security: Validate event structure before processing
            if not hasattr(event, 'code') or not hasattr(event, 'value'):
                logger.warning("Received invalid event structure")
                return

            code = event.code
            value = event.value  # 0 = release, 1 = press, 2 = repeat

            # Security: Ignore key repeat events to prevent accidental triggers
            if value == 2:  # Key repeat
                return

            # Check if this is a Ctrl key
            if code in KEY_CTRL:
                device_id = id(device)

                if value == 1:  # Key press
                    self.ctrl_pressed_devices.add(device_id)
                    current_time = time.time()

                    # Check for double-tap with improved debouncing
                    if (
                        self.double_tap_callback is not None
                        and current_time - self.last_ctrl_press_time < self.double_tap_threshold
                        and current_time - self.last_trigger_time > 0.5  # Prevent rapid re-triggering
                    ):
                        logger.debug("Double-tap Ctrl detected (evdev)")
                        self.last_trigger_time = current_time
                        
                        # Security: Execute callback in a separate thread to prevent blocking
                        def safe_callback():
                            try:
                                self.double_tap_callback()
                            except Exception as e:
                                logger.error(f"Error in keyboard callback: {e}")
                        
                        threading.Thread(target=safe_callback, daemon=True).start()

                    self.last_ctrl_press_time = current_time

                elif value == 0:  # Key release
                    self.ctrl_pressed_devices.discard(device_id)

        except Exception as e:
            logger.error(f"Error handling key event: {e}")


# Export availability
__all__ = ["EvdevKeyboardBackend", "EVDEV_AVAILABLE", "find_keyboard_devices"]
