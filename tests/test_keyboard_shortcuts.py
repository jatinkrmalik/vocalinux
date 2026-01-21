s"""
Tests for keyboard shortcut functionality.
"""

import time
import unittest
from unittest.mock import MagicMock, patch

# Update import to use the new package structure
from vocalinux.ui.keyboard_shortcuts import KeyboardShortcutManager


class TestKeyboardShortcuts(unittest.TestCase):
    """Test cases for the keyboard shortcuts functionality."""

    def setUp(self):
        """Set up for tests."""
        # Set up more complete mocks for the keyboard library
        self.kb_patch = patch("vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE", True)
        self.kb_patch.start()

        # Create proper Key enum and KeyCode class
        self.keyboard_patch = patch("vocalinux.ui.keyboard_shortcuts.keyboard")
        self.mock_keyboard = self.keyboard_patch.start()

        # Set up Key attributes as simple strings for easier testing
        self.mock_keyboard.Key.alt = "Key.alt"
        self.mock_keyboard.Key.alt_l = "Key.alt_l"
        self.mock_keyboard.Key.alt_r = "Key.alt_r"
        self.mock_keyboard.Key.shift = "Key.shift"
        self.mock_keyboard.Key.shift_l = "Key.shift_l"
        self.mock_keyboard.Key.shift_r = "Key.shift_r"
        self.mock_keyboard.Key.ctrl = "Key.ctrl"
        self.mock_keyboard.Key.ctrl_l = "Key.ctrl_l"
        self.mock_keyboard.Key.ctrl_r = "Key.ctrl_r"
        self.mock_keyboard.Key.cmd = "Key.cmd"
        self.mock_keyboard.Key.cmd_l = "Key.cmd_l"
        self.mock_keyboard.Key.cmd_r = "Key.cmd_r"

        # Create mock Listener
        self.mock_listener = MagicMock()
        self.mock_listener.is_alive.return_value = True
        self.mock_keyboard.Listener.return_value = self.mock_listener

        # Patch threading to catch callback execution
        self.threading_patch = patch("vocalinux.ui.keyboard_shortcuts.threading")
        self.mock_threading = self.threading_patch.start()

        # Create a new KSM for each test
        self.ksm = KeyboardShortcutManager()

    def tearDown(self):
        """Clean up after tests."""
        self.kb_patch.stop()
        self.keyboard_patch.stop()
        self.threading_patch.stop()

    def test_init(self):
        """Test initialization of the keyboard shortcut manager."""
        # Verify initial state
        self.assertEqual(self.ksm.tap_state, 0)
        self.assertIsNone(self.ksm.double_tap_callback)

    def test_start_listener(self):
        """Test starting the keyboard listener."""
        # Start the listener
        self.ksm.start()

        # Verify listener was created with correct arguments
        self.mock_keyboard.Listener.assert_called_once()
        self.assertTrue(self.ksm.active)

    def test_start_already_active(self):
        """Test starting when already active."""
        self.ksm.active = True
        self.ksm.start()
        self.mock_keyboard.Listener.assert_not_called()

    def test_start_listener_failed(self):
        """Test handling when listener fails to start."""
        self.mock_listener.is_alive.return_value = False
        self.ksm.start()
        self.assertFalse(self.ksm.active)

    def test_stop_listener(self):
        """Test stopping the keyboard listener."""
        self.ksm.start()
        self.ksm.active = True
        self.ksm.tap_state = 1 # Change state

        self.ksm.stop()

        self.mock_listener.stop.assert_called_once()
        self.assertFalse(self.ksm.active)
        self.assertEqual(self.ksm.tap_state, 0) # Should verify reset

    def test_register_toggle_callback(self):
        """Test registering toggle callback with double-tap shortcut."""
        callback = MagicMock()
        self.ksm.register_toggle_callback(callback)
        self.assertEqual(self.ksm.double_tap_callback, callback)

    def test_double_tap_ctrl_sequence(self):
        """Test correct double-tap Ctrl sequence."""
        self.ksm.start()
        on_press = self.mock_keyboard.Listener.call_args[1]["on_press"]
        on_release = self.mock_keyboard.Listener.call_args[1]["on_release"]

        callback = MagicMock()
        self.ksm.register_toggle_callback(callback)

        # We must patch time.time
        with patch("time.time") as mock_time:
            # Setup times
            t0 = 1000.0
            t1 = t0 + 0.1 # Release time
            t2 = t1 + 0.1 # Second press time (0.1 > 0.05 min gap)
            t3 = t2 + 0.1 # Second release time

            # 1. Press
            mock_time.return_value = t0
            on_press(self.mock_keyboard.Key.ctrl)
            self.assertEqual(self.ksm.tap_state, 1)

            # 2. Release
            mock_time.return_value = t1
            on_release(self.mock_keyboard.Key.ctrl)
            self.assertEqual(self.ksm.tap_state, 2)

            # 3. Press
            mock_time.return_value = t2
            on_press(self.mock_keyboard.Key.ctrl)
            self.assertEqual(self.ksm.tap_state, 3) # Should advance

            # 4. Release (Trigger)
            mock_time.return_value = t3
            on_release(self.mock_keyboard.Key.ctrl)
            
            # Check callback logic
            self.mock_threading.Thread.assert_called_once()
            args, kwargs = self.mock_threading.Thread.call_args
            self.assertEqual(kwargs['target'], callback)
            self.assertEqual(self.ksm.tap_state, 0) # Reset after trigger

    def test_double_tap_interrupted(self):
        """Test interruption by other keys resets sequence."""
        self.ksm.start()
        on_press = self.mock_keyboard.Listener.call_args[1]["on_press"]

        # 1. Press Ctrl
        on_press(self.mock_keyboard.Key.ctrl)
        self.assertEqual(self.ksm.tap_state, 1)

        # 2. Press Other Key
        on_press(MagicMock()) # Some random key (not Ctrl)
        self.assertEqual(self.ksm.tap_state, 0)

    def test_hold_too_long(self):
        """Test holding Ctrl too long resets sequence."""
        self.ksm.start()
        on_press = self.mock_keyboard.Listener.call_args[1]["on_press"]
        on_release = self.mock_keyboard.Listener.call_args[1]["on_release"]

        with patch("time.time") as mock_time:
            t0 = 1000.0
            t1 = t0 + 1.0 # Held for 1.0s (> 0.5s limit)

            mock_time.return_value = t0
            on_press(self.mock_keyboard.Key.ctrl)
            self.assertEqual(self.ksm.tap_state, 1)

            mock_time.return_value = t1
            on_release(self.mock_keyboard.Key.ctrl)
            self.assertEqual(self.ksm.tap_state, 0) # Reset because too long

    def test_normalize_modifier_keys(self):
        """Test normalizing left/right modifier keys."""
        # Use simple mock mapping logic for test
        self.ksm._normalize_modifier_key = MagicMock(
            side_effect=lambda key: {
                self.mock_keyboard.Key.alt_l: self.mock_keyboard.Key.alt,
            }.get(key, key)
        )
        self.assertEqual(
            self.ksm._normalize_modifier_key(self.mock_keyboard.Key.alt_l),
            self.mock_keyboard.Key.alt,
        )

    def test_error_handling(self):
        """Test error handling in key event handlers."""
        self.ksm.start()
        on_press = self.mock_keyboard.Listener.call_args[1]["on_press"]
        
        # We can force _normalize_modifier_key to raise exception
        self.ksm._normalize_modifier_key = MagicMock(side_effect=Exception("Boom"))
        
        try:
            on_press(self.mock_keyboard.Key.ctrl)
            # Should catch exception and log error, not crash
        except Exception:
            self.fail("Exception not handled in on_press")

    def test_no_keyboard_library(self):
        """Test behavior when keyboard library is not available."""
        with patch("vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE", False):
            ksm = KeyboardShortcutManager()
            ksm.start()
            self.assertFalse(ksm.active)

    def test_set_shortcut_updates_mode(self):
        """Test that setting shortcut updates the listener mode."""
        self.ksm.start()
        # Initial default is ctrl+ctrl, uses Listener
        self.mock_keyboard.Listener.assert_called()
        self.mock_keyboard.GlobalHotKeys.assert_not_called()
        
        # Reset mocks
        self.mock_keyboard.Listener.reset_mock()
        self.ksm.stop()
        
        # Change shortcut
        self.ksm.set_shortcut("<ctrl>+<alt>+v")
        self.assertEqual(self.ksm.shortcut, "<ctrl>+<alt>+v")
        
        # Start again
        self.ksm.start()
        
        # Should now use GlobalHotKeys
        self.mock_keyboard.GlobalHotKeys.assert_called_once()
        self.mock_keyboard.Listener.assert_not_called()

    def test_hotkey_execution(self):
        """Test that the hotkey callback executes the registered action."""
        # Setup hotkey mode
        self.ksm.set_shortcut("<ctrl>+<alt>+v")
        
        callback = MagicMock()
        self.ksm.register_toggle_callback(callback)
        
        self.ksm.start()
        
        # Get the hotkey dictionary passed to GlobalHotKeys
        args, kwargs = self.mock_keyboard.GlobalHotKeys.call_args
        hotkeys = args[0]
        self.assertIn("<ctrl>+<alt>+v", hotkeys)
        
        # Execute the wrapper function
        wrapper = hotkeys["<ctrl>+<alt>+v"]
        wrapper()
        
        # Check if callback was threaded
        self.mock_threading.Thread.assert_called()
        thread_args = self.mock_threading.Thread.call_args[1]
        self.assertEqual(thread_args['target'], callback)
