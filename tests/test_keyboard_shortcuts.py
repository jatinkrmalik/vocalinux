"""
Tests for keyboard shortcut management.
"""

import os
import threading
import time
import unittest
from unittest.mock import DEFAULT, MagicMock, patch

# Set up environment variables for testing
os.environ["VOCALINUX_ENV"] = "testing"

# Create mocks before importing anything
mock_keyboard = MagicMock()
mock_keyboard.Key = MagicMock()
mock_keyboard.Key.ctrl = "Key.ctrl"
mock_keyboard.Key.ctrl_l = "Key.ctrl_l"
mock_keyboard.Key.ctrl_r = "Key.ctrl_r"

mock_listener = MagicMock()
mock_listener.is_alive.return_value = True
mock_keyboard.Listener = MagicMock(return_value=mock_listener)

mock_environment = MagicMock()
mock_environment.is_feature_available = MagicMock(return_value=True)

# Patch before importing
with patch.dict(
    "sys.modules", {"pynput": MagicMock(), "pynput.keyboard": mock_keyboard}
), patch("vocalinux.utils.environment.environment", mock_environment):
    from vocalinux.ui.keyboard_shortcuts import (
        FEATURE_KEYBOARD,
        KEYBOARD_AVAILABLE,
        KeyboardShortcutManager,
    )


class TestKeyboardShortcuts(unittest.TestCase):
    """Test cases for keyboard shortcuts."""

    def setUp(self):
        """Set up test environment."""
        # Reset all mocks
        mock_keyboard.reset_mock()
        mock_listener.reset_mock()
        mock_environment.reset_mock()

        # Patch environment and keyboard availability
        patches = {
            "vocalinux.ui.keyboard_shortcuts.environment": mock_environment,
            "vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE": True,
            "vocalinux.ui.keyboard_shortcuts.keyboard": mock_keyboard,
        }

        self.patches = {key: patch(key, new=value) for key, value in patches.items()}

        # Start all patches
        self.mocks = {key: patcher.start() for key, patcher in self.patches.items()}

        # Set up environment mock to enable keyboard features
        mock_environment.is_feature_available.return_value = True

        # Create a new instance with keyboard features enabled
        self.ksm = KeyboardShortcutManager()
        self.ksm._keyboard_available = True

        # Store mock_listener for tests
        self.mock_listener = mock_listener

        # Make sure is_alive returns True by default
        self.mock_listener.is_alive.return_value = True

    def tearDown(self):
        """Clean up after tests."""
        # Stop all patches
        for patcher in self.patches.values():
            patcher.stop()

        # Stop the listener if it's running
        if self.ksm and hasattr(self.ksm, "listener") and self.ksm.listener:
            self.ksm.stop()

    def test_initialization(self):
        """Test initialization of the KeyboardShortcutManager."""
        # Create a fresh instance with no patches to test actual initialization
        with patch("vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE", True):
            ksm = KeyboardShortcutManager()
            # Verify initial state is correct
            self.assertIsNone(ksm.listener)
            self.assertFalse(ksm.active)
            self.assertEqual(ksm.last_trigger_time, 0)
            self.assertEqual(ksm.last_ctrl_press_time, 0)
            self.assertIsNone(ksm.double_tap_callback)
            self.assertTrue(ksm.keyboard_available)

    def test_register_toggle_callback(self):
        """Test registering a toggle callback."""
        # Create a test callback
        callback = MagicMock()

        # Register it
        self.ksm.register_toggle_callback(callback)

        # Verify it was assigned
        self.assertEqual(self.ksm.double_tap_callback, callback)

    def test_unregister_toggle_callback(self):
        """Test unregistering a toggle callback."""
        # We don't have an explicit unregister method in the implementation
        # but let's test setting the callback to None
        callback = MagicMock()
        self.ksm.register_toggle_callback(callback)

        # Verify it was registered
        self.assertEqual(self.ksm.double_tap_callback, callback)

        # Register a different callback (which replaces the previous one)
        callback2 = MagicMock()
        self.ksm.register_toggle_callback(callback2)

        # Verify old callback was replaced
        self.assertEqual(self.ksm.double_tap_callback, callback2)
        self.assertNotEqual(self.ksm.double_tap_callback, callback)

    def test_start_listener(self):
        """Test starting the keyboard listener."""
        # Start the listener
        self.ksm.start()

        # Verify Listener was created with the correct parameters
        mock_keyboard.Listener.assert_called_once()
        # Verify the correct callbacks were passed
        kwargs = mock_keyboard.Listener.call_args[1]
        self.assertEqual(kwargs.get("on_press"), self.ksm._on_press)
        self.assertEqual(kwargs.get("on_release"), self.ksm._on_release)

        # Verify listener.start was called
        self.mock_listener.start.assert_called_once()

        # Verify active flag was set
        self.assertTrue(self.ksm.active)

    def test_start_listener_when_unavailable(self):
        """Test starting when keyboard features aren't available."""
        # Set keyboard as unavailable
        with patch("vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE", False):
            # Create a new instance with keyboard unavailable
            ksm = KeyboardShortcutManager()

            # Explicitly set keyboard_available to false to override earlier patches
            ksm.keyboard_available = False

            # Reset mocks
            mock_keyboard.Listener.reset_mock()
            self.mock_listener.start.reset_mock()

            # Try to start
            ksm.start()

            # Verify no listener was created
            mock_keyboard.Listener.assert_not_called()
            self.mock_listener.start.assert_not_called()
            self.assertFalse(ksm.active)

    def test_start_listener_failed(self):
        """Test handling when listener fails to start."""
        # Set listener.is_alive to return False to simulate failed start
        self.mock_listener.is_alive.return_value = False

        # Start the listener
        self.ksm.start()

        # Verify Listener was created and started
        mock_keyboard.Listener.assert_called_once()
        self.mock_listener.start.assert_called_once()

        # But active should be False since the listener didn't start
        self.assertFalse(self.ksm.active)

    def test_stop_listener(self):
        """Test stopping the keyboard listener."""
        # First start the listener
        self.ksm.start()
        self.assertTrue(self.ksm.active)

        # Then stop it
        self.ksm.stop()

        # Verify it was stopped
        self.mock_listener.stop.assert_called_once()
        self.mock_listener.join.assert_called_once()

        # Verify state was updated
        self.assertFalse(self.ksm.active)
        self.assertIsNone(self.ksm.listener)

    def test_stop_listener_when_none(self):
        """Test stopping when no listener exists."""
        # Make sure we have no listener
        self.ksm.listener = None
        self.ksm.active = False

        # Try to stop (shouldn't raise exceptions)
        self.ksm.stop()

        # Verify no interactions with mock_listener
        self.mock_listener.stop.assert_not_called()
        self.mock_listener.join.assert_not_called()

    def test_key_press_modifier(self):
        """Test handling a modifier key press."""
        # Start the listener with our mocks in place
        self.ksm.start()

        # Call _on_press directly since we're not using call_args in this test
        self.ksm._on_press("a")  # Non-modifier key
        self.assertEqual(len(self.ksm.current_keys), 0)

        # Test with Ctrl key
        prev_time = self.ksm.last_ctrl_press_time
        self.ksm._on_press(mock_keyboard.Key.ctrl)

        # Should update last_ctrl_time
        self.assertGreater(self.ksm.last_ctrl_press_time, prev_time)
        self.assertIn(mock_keyboard.Key.ctrl, self.ksm.current_keys)

    def test_double_tap_ctrl(self):
        """Test double-tap Ctrl detection."""
        # Register a callback
        callback = MagicMock()
        self.ksm.register_toggle_callback(callback)

        # Start the listener
        self.ksm.start()

        # Simulate a recent Ctrl press
        self.ksm.last_ctrl_press_time = time.time() - 0.2  # Within threshold
        self.ksm._on_press(mock_keyboard.Key.ctrl)

        # Wait briefly for the callback thread to execute
        time.sleep(0.1)

        # Verify callback was called
        callback.assert_called_once()

    def test_double_tap_ctrl_debounce(self):
        """Test debounce for double-tap Ctrl."""
        # Register a callback
        callback = MagicMock()
        self.ksm.register_toggle_callback(callback)

        # Start the listener
        self.ksm.start()

        # Set last_ctrl_time to something too old
        self.ksm.last_ctrl_press_time = time.time() - 2.0  # Beyond threshold
        self.ksm._on_press(mock_keyboard.Key.ctrl)

        # Verify callback was not triggered (this was a single press)
        callback.assert_not_called()

    def test_key_release(self):
        """Test key release handler."""
        # Start the listener
        self.ksm.start()

        # Add some keys to current_keys
        self.ksm.current_keys = {mock_keyboard.Key.ctrl, mock_keyboard.Key.shift}

        # Test with Ctrl key
        self.ksm._on_release(mock_keyboard.Key.ctrl)

        # Should have removed Ctrl from current keys
        self.assertNotIn(mock_keyboard.Key.ctrl, self.ksm.current_keys)
        self.assertIn(mock_keyboard.Key.shift, self.ksm.current_keys)

    def test_error_handling(self):
        """Test error handling in key event handlers."""

        # Create a problematic callback that raises an exception
        def problematic_callback():
            raise Exception("Test exception")

        # Register it
        self.ksm.register_toggle_callback(problematic_callback)
        self.ksm.start()

        # Simulate a double-tap Ctrl (should handle the exception gracefully)
        self.ksm.last_ctrl_press_time = time.time() - 0.2  # Within threshold

        # This should not raise an exception
        self.ksm._on_press(mock_keyboard.Key.ctrl)

        # Wait for the thread to execute
        time.sleep(0.1)

        # Also test error handling in release
        with patch.object(
            self.ksm, "_normalize_modifier_key", side_effect=Exception("Test exception")
        ):
            # This should not raise an exception
            self.ksm._on_release(mock_keyboard.Key.ctrl)

    def test_feature_detection(self):
        """Test proper detection of keyboard features."""
        # Test with feature available
        with patch(
            "vocalinux.ui.keyboard_shortcuts.environment.is_feature_available",
            return_value=True,
        ):
            with patch("vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE", True):
                ksm = KeyboardShortcutManager()
                # Verify the keyboard_available property returns True
                self.assertTrue(ksm.keyboard_available)

        # Test with feature unavailable
        with patch(
            "vocalinux.ui.keyboard_shortcuts.environment.is_feature_available",
            return_value=False,
        ):
            with patch("vocalinux.ui.keyboard_shortcuts.KEYBOARD_AVAILABLE", False):
                ksm = KeyboardShortcutManager()
                # Verify the keyboard_available property returns False
                self.assertFalse(ksm.keyboard_available)
