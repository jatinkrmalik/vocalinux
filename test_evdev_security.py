#!/usr/bin/env python3
"""
Test script to verify evdev backend security improvements.
This script should be run as part of the QA process.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from vocalinux.ui.keyboard_backends.evdev_backend import find_keyboard_devices, EvdevKeyboardBackend
    from vocalinux.ui.keyboard_backends import EVDEV_AVAILABLE
except ImportError:
    print("WARNING: Could not import evdev backend - running without evdev")
    EVDEV_AVAILABLE = False


class TestEvdevSecurity(unittest.TestCase):
    """Test security improvements in evdev backend."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_find_keyboard_devices_security(self):
        """Test that find_keyboard_devices properly validates device paths."""
        if not EVDEV_AVAILABLE:
            self.skipTest("evdev not available")
            
        # Mock /proc/bus/input/devices content with suspicious paths
        mock_devices_content = """
I: Bus=0019 Vendor=0000 Product=0000 Version=0000
N: Name="Test Keyboard"
P: Phys=isa0060/serio0/input/input0
S: Sysfs=/devices/platform/i8042/serio0/input/input0
U: Uniq=
H: Handlers=sysrq kbd event0 leds
B: PROP=0
B: EV=120013
B: KEY=402000000 30030 1000000000000 7ff8000000016 fe0ffdf01cfffff ffffffffff feffffff ffffffffffffff
B: MSC=10
B: LED=7

I: Bus=0019 Vendor=0000 Product=0000 Version=0000
N: Name="Malicious Device"
P: Phys=isa0060/serio1/input/input1
S: Sysfs=/devices/platform/i8042/serio1/input/input1
U: Uniq=
H: Handlers=../../../../../../../etc/passwd event1
B: PROP=0
B: EV=120013
B: KEY=402000000 30030 1000000000000 7ff8000000016 fe0ffdf01cfffff ffffffffff feffffff ffffffffffffff
B: MSC=10
B: LED=7
"""

        with patch('builtins.open', create=True) as mock_open:
            with patch('os.path.exists') as mock_exists:
                with patch('os.access') as mock_access:
                    with patch('os.path.isabs') as mock_isabs:
                        mock_open.return_value.__enter__.return_value = iter(mock_devices_content.split('\n'))
                        # Only event0 exists and is accessible
                        mock_exists.side_effect = lambda path: path == '/dev/input/event0'
                        mock_access.return_value = True
                        mock_isabs.return_value = True
                        
                        devices = find_keyboard_devices()
                        
                        # Should only include valid devices, not the malicious one
                        self.assertEqual(len(devices), 1)
                        self.assertTrue(all('/dev/input/event' in device for device in devices))
                        self.assertFalse(any('etc/passwd' in device for device in devices))

    def test_device_limiting(self):
        """Test that we limit the number of devices monitored."""
        if not EVDEV_AVAILABLE:
            self.skipTest("evdev not available")
            
        # Create many mock devices
        mock_devices = [f'/dev/input/event{i}' for i in range(15)]
        
        # Mock evdev module completely since it's not installed
        mock_evdev = MagicMock()
        mock_evdev.InputDevice = MagicMock()
        mock_evdev.InputDevice.return_value = MagicMock()
        mock_evdev.InputDevice.return_value.fileno.return_value = 1
        mock_evdev.InputDevice.return_value.capabilities = {}
        
        with patch.dict('sys.modules', {'evdev': mock_evdev}):
            # Need to re-import after mocking
            import importlib
            import vocalinux.ui.keyboard_backends.evdev_backend
            importlib.reload(vocalinux.ui.keyboard_backends.evdev_backend)
            
            from vocalinux.ui.keyboard_backends.evdev_backend import EvdevKeyboardBackend
            
            with patch('vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices') as mock_find:
                mock_find.return_value = mock_devices
                
                backend = EvdevKeyboardBackend()
                backend.max_devices = 10  # Override for testing
                
                with patch.object(backend, 'is_available', return_value=True):
                    success = backend.start()
                    
                    # Should succeed but limit devices
                    self.assertTrue(success)
                    self.assertLessEqual(len(backend.devices), 10)

    def test_double_tap_security(self):
        """Test that double-tap callback is executed safely."""
        if not EVDEV_AVAILABLE:
            self.skipTest("evdev not available")
            
        backend = EvdevKeyboardBackend()
        
        # Mock a malicious callback that raises an exception
        def malicious_callback():
            raise Exception("Malicious callback executed")
            
        backend.double_tap_callback = malicious_callback
        
        # Mock an event
        mock_event = MagicMock()
        mock_event.code = 29  # KEY_LEFTCTRL
        mock_event.value = 1  # Key press
        
        mock_device = MagicMock()
        
        # This should not raise an exception
        try:
            backend._handle_key_event(mock_event, mock_device)
        except Exception as e:
            self.fail(f"_handle_key_event raised an exception: {e}")

    def test_path_validation(self):
        """Test that device paths are properly validated."""
        if not EVDEV_AVAILABLE:
            self.skipTest("evdev not available")
            
        # Test suspicious paths
        suspicious_paths = [
            '/dev/input/event0',
            '/dev/input/../../../etc/passwd',
            '/dev/input/event1',
            '/tmp/malicious_device',
            '/dev/input/event2',
        ]
        
        with patch('os.path.exists') as mock_exists:
            with patch('os.access') as mock_access:
                with patch('os.path.isabs') as mock_isabs:
                    # Make only the valid paths exist
                    def exists_func(path):
                        return path in ['/dev/input/event0', '/dev/input/event1', '/dev/input/event2']
                    
                    mock_exists.side_effect = exists_func
                    mock_access.return_value = True
                    mock_isabs.return_value = True
                    
                    # Mock the find_keyboard_devices to return suspicious paths
                    with patch('vocalinux.ui.keyboard_backends.evdev_backend.find_keyboard_devices', return_value=suspicious_paths):
                        devices = find_keyboard_devices()
                        
                        # Should filter out suspicious paths
                        self.assertEqual(len(devices), 3)  # Only the valid event devices
                        self.assertTrue(all(path.startswith('/dev/input/event') for path in devices))
                        self.assertFalse(any('etc/passwd' in path for path in devices))
                        self.assertFalse(any('tmp' in path for path in devices))

    def test_environment_detection_security(self):
        """Test that environment detection is secure."""
        from vocalinux.ui.keyboard_backends import DesktopEnvironment
        
        # Test with malicious environment variables
        with patch.dict(os.environ, {
            'XDG_SESSION_TYPE': 'wayland; rm -rf /',
            'WAYLAND_DISPLAY': 'normal',
            'DISPLAY': 'normal:0'
        }):
            env = DesktopEnvironment.detect()
            # Should not execute the malicious command
            self.assertEqual(env, 'wayland')
            
        # Test with empty values
        with patch.dict(os.environ, {
            'XDG_SESSION_TYPE': '',
            'WAYLAND_DISPLAY': '',
            'DISPLAY': ''
        }):
            env = DesktopEnvironment.detect()
            # Should not crash, should return unknown
            self.assertEqual(env, 'unknown')


def main():
    """Run the security tests."""
    print("Running evdev backend security tests...")
    print("=" * 50)
    
    unittest.main(verbosity=2)


if __name__ == '__main__':
    main()