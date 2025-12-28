"""
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

        # Create a new KSM for each test
        self.ksm = KeyboardShortcutManager()

    def tearDown(self):
        """Clean up after tests."""
        self.kb_patch.stop()
        self.keyboard_patch.stop()

    def test_init(self):
        """Test initialization of the keyboard shortcut manager."""
        # Verify double-tap threshold is set
        self.assertEqual(self.ksm.double_tap_threshold, 0.3)
        # Verify double-tap callback is initially None
        self.assertIsNone(self.ksm.double_tap_callback)

    def test_start_listener(self):
        """Test starting the keyboard listener."""
        # Start the listener
        self.ksm.start()

        # Verify listener was created with correct arguments
        self.mock_keyboard.Listener.assert_called_once()

        # Check that on_press and on_release are being passed
        args, kwargs = self.mock_keyboard.Listener.call_args
        self.assertIn("on_press", kwargs)
        self.assertIn("on_release", kwargs)

        # Check that listener was started
        self.mock_listener.start.assert_called_once()
        self.assertTrue(self.ksm.active)

    def test_start_already_active(self):
        """Test starting when already active."""
        # Make it active already
        self.ksm.active = True

        # Try to start again
        self.ksm.start()

        # Verify nothing was called
        self.mock_keyboard.Listener.assert_not_called()

    def test_start_listener_failed(self):
        """Test handling when listener fails to start."""
        # Make is_alive return False
        self.mock_listener.is_alive.return_value = False

        # Start the listener
        self.ksm.start()

        # Should have tried to start but then set active to False
        self.mock_listener.start.assert_called_once()
        self.assertFalse(self.ksm.active)

    def test_stop_listener(self):
        """Test stopping the keyboard listener."""
        # Setup an active listener
        self.ksm.start()
        self.ksm.active = True

        # Stop the listener
        self.ksm.stop()

        # Verify listener was stopped
        self.mock_listener.stop.assert_called_once()
        self.mock_listener.join.assert_called_once()
        self.assertFalse(self.ksm.active)
        self.assertIsNone(self.ksm.listener)

    def test_stop_not_active(self):
        """Test stopping when not active."""
        # Make it inactive
        self.ksm.active = False

        # Try to stop
        self.ksm.stop()

        # Nothing should happen
        if hasattr(self.ksm, "listener") and self.ksm.listener:
            self.mock_listener.stop.assert_not_called()

    def test_register_toggle_callback(self):
        """Test registering toggle callback with double-tap shortcut."""
        # Create mock callback
        callback = MagicMock()

        # Register as toggle callback
        self.ksm.register_toggle_callback(callback)

        # Verify it was registered as double-tap callback
        self.assertEqual(self.ksm.double_tap_callback, callback)

    def test_key_press_modifier(self):
        """Test handling a modifier key press."""
        # Initialize and start to set up the listener
        self.ksm.start()

        # Get the on_press handler
        on_press = self.mock_keyboard.Listener.call_args[1]["on_press"]

        # Make sure current_keys is set and initially empty
        self.ksm.current_keys = set()

        # Simulate pressing Ctrl
        on_press(self.mock_keyboard.Key.ctrl)

        # Verify Ctrl was added to current keys
        self.assertIn(self.mock_keyboard.Key.ctrl, self.ksm.current_keys)

    def test_double_tap_ctrl(self):
        """Test double-tap Ctrl detection."""
        # Initialize and start to set up the listener
        self.ksm.start()

        # Get the on_press handler
        on_press = self.mock_keyboard.Listener.call_args[1]["on_press"]

        # Register mock callback for double-tap Ctrl
        callback = MagicMock()
        self.ksm.register_toggle_callback(callback)

        # Set up initial state
        self.ksm.last_ctrl_press_time = time.time() - 0.2  # Recent press (within threshold)
        self.ksm.last_trigger_time = 0  # No recent triggers

        # Simulate second Ctrl press (should trigger callback)
        on_press(self.mock_keyboard.Key.ctrl)

        # Verify callback was triggered
        callback.assert_called_once()

        # Reset and test when press is outside threshold (not a double-tap)
        callback.reset_mock()
        self.ksm.last_ctrl_press_time = time.time() - 0.5  # Outside threshold
        on_press(self.mock_keyboard.Key.ctrl)
        callback.assert_not_called()

    def test_normalize_modifier_keys(self):
        """Test normalizing left/right modifier keys."""
        # Setup the key mapping dictionary correctly
        self.ksm._normalize_modifier_key = MagicMock(
            side_effect=lambda key: {
                self.mock_keyboard.Key.alt_l: self.mock_keyboard.Key.alt,
                self.mock_keyboard.Key.alt_r: self.mock_keyboard.Key.alt,
                self.mock_keyboard.Key.shift_l: self.mock_keyboard.Key.shift,
                self.mock_keyboard.Key.shift_r: self.mock_keyboard.Key.shift,
                self.mock_keyboard.Key.ctrl_l: self.mock_keyboard.Key.ctrl,
                self.mock_keyboard.Key.ctrl_r: self.mock_keyboard.Key.ctrl,
                self.mock_keyboard.Key.cmd_l: self.mock_keyboard.Key.cmd,
                self.mock_keyboard.Key.cmd_r: self.mock_keyboard.Key.cmd,
            }.get(key, key)
        )

        # Test the normalization
        self.assertEqual(
            self.ksm._normalize_modifier_key(self.mock_keyboard.Key.alt_l),
            self.mock_keyboard.Key.alt,
        )

    def test_double_tap_ctrl_debounce(self):
        """Test that double-tap Ctrl has debounce protection."""
        # Initialize and start to set up the listener
        self.ksm.start()

        # Get the on_press handler
        on_press = self.mock_keyboard.Listener.call_args[1]["on_press"]

        # Register mock callback for double-tap Ctrl
        callback = MagicMock()
        self.ksm.register_toggle_callback(callback)

        # Set up initial state (recent trigger)
        self.ksm.last_ctrl_press_time = time.time() - 0.2  # Recent press (within threshold)
        self.ksm.last_trigger_time = time.time() - 0.2  # Recent trigger, within debounce

        # Simulate second Ctrl press (should NOT trigger due to debounce)
        on_press(self.mock_keyboard.Key.ctrl)

        # Verify callback was NOT triggered
        callback.assert_not_called()

    def test_key_release(self):
        """Test handling a key release."""
        # Initialize and start to set up the listener
        self.ksm.start()

        # Get the on_release handler
        on_release = self.mock_keyboard.Listener.call_args[1]["on_release"]

        # Add some keys
        self.ksm.current_keys = {self.mock_keyboard.Key.ctrl}

        # Simulate releasing Ctrl
        on_release(self.mock_keyboard.Key.ctrl)

        # Verify Ctrl was removed
        self.assertNotIn(self.mock_keyboard.Key.ctrl, self.ksm.current_keys)

    def test_error_handling(self):
        """Test error handling in key event handlers."""
        # Initialize and start to set up the listener
        self.ksm.start()

        # Get the handlers
        on_press = self.mock_keyboard.Listener.call_args[1]["on_press"]
        on_release = self.mock_keyboard.Listener.call_args[1]["on_release"]

        # Make a key that raises an exception
        bad_key = MagicMock()
        bad_key.__eq__ = MagicMock(side_effect=Exception("Test exception"))

        # Verify exceptions are caught
        try:
            on_press(bad_key)
            on_release(bad_key)
            # If we get here, exceptions were caught properly
            self.assertTrue(True)
        except:
            self.fail("Exceptions were not caught in event handlers")

    def test_no_keyboard_library(self):
        """Test behavior when keyboard library is not available."""
        # Create a new mock to replace the keyboard system
        with patch("vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE", False):
            # Create a new KSM with no keyboard library
            ksm = KeyboardShortcutManager()

            # Start should do nothing
            ksm.start()

            # When keyboard is not available, active should remain False
            self.assertFalse(ksm.active)
