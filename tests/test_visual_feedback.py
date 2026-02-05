"""
Tests for visual feedback indicator functionality.

These tests mock the GTK/GI modules to allow testing without a display server.
The tests focus on the business logic of the VisualFeedbackIndicator class.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest

# Create mock modules for GTK/GI BEFORE importing anything
mock_gi = MagicMock()
mock_gi.require_version = MagicMock()

mock_gtk = MagicMock()
mock_glib = MagicMock()
mock_gdk = MagicMock()

# Create mock for gi.repository
mock_gi_repository = MagicMock()
mock_gi_repository.Gtk = mock_gtk
mock_gi_repository.GLib = mock_glib
mock_gi_repository.Gdk = mock_gdk

# Inject mocks into sys.modules BEFORE any imports
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = mock_gi_repository


class TestVisualFeedbackIndicator(unittest.TestCase):
    """Test cases for the visual feedback indicator."""

    @classmethod
    def setUpClass(cls):
        """Set up class fixtures."""
        # Ensure mocks are in place for the entire test class
        sys.modules["gi"] = mock_gi
        sys.modules["gi.repository"] = mock_gi_repository

    def setUp(self):
        """Set up test environment before each test."""
        # Reset all GTK mocks to avoid test pollution
        mock_gtk.reset_mock()
        mock_glib.reset_mock()
        mock_gdk.reset_mock()

        # Configure GTK.init_check to return success
        mock_gtk.init_check.return_value = (True, [])

        # Clear any cached imports of visual_feedback
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Import RecognitionState
        from vocalinux.common_types import RecognitionState

        self.RecognitionState = RecognitionState

        # Patch GTK_AVAILABLE to True and WAYLAND_SESSION to False for tests
        # (simulating X11 environment where visual feedback works)
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

                self.VisualFeedbackIndicator = VisualFeedbackIndicator

    def tearDown(self):
        """Clean up test environment after each test."""
        pass

    def test_initialization(self):
        """Test initialization of the visual feedback indicator."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                self.assertIsNone(indicator.overlay_window)
                self.assertIsNone(indicator.current_cursor_pos)
                self.assertFalse(indicator.is_visible)
                self.assertEqual(indicator.animation_phase, 0)
                self.assertIsNone(indicator.animation_timeout_id)
                self.assertIsNone(indicator.position_update_timeout_id)

    def test_initialization_without_gtk(self):
        """Test initialization without GTK available."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", False):
            # Re-import to get the class with GTK_AVAILABLE=False
            modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
            for mod in modules_to_remove:
                del sys.modules[mod]

            from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

            indicator = VisualFeedbackIndicator()
            # When GTK is not available, the __init__ returns early before setting attributes
            # The indicator should still be created, but show/hide should do nothing
            # Since the code returns early, overlay_window may or may not exist depending on
            # how the mock handles GTK_AVAILABLE check in __init__
            # What matters is that operations don't fail
            indicator.show()  # Should not raise
            indicator.hide()  # Should not raise
            indicator.cleanup()  # Should not raise

    def test_update_state_listening(self):
        """Test update_state for LISTENING state."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()

                with patch.object(indicator, "show") as mock_show:
                    indicator.update_state(self.RecognitionState.LISTENING)
                    mock_show.assert_called_once()
                    # Check color changed to blue
                    self.assertEqual(indicator.base_color, (0.2, 0.6, 1.0, 0.8))

    def test_update_state_processing(self):
        """Test update_state for PROCESSING state."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                indicator.overlay_window = MagicMock()

                indicator.update_state(self.RecognitionState.PROCESSING)
                # Check color changed to orange
                self.assertEqual(indicator.base_color, (1.0, 0.6, 0.2, 0.8))
                indicator.overlay_window.queue_draw.assert_called_once()

    def test_update_state_idle(self):
        """Test update_state for IDLE state."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()

                with patch.object(indicator, "hide") as mock_hide:
                    indicator.update_state(self.RecognitionState.IDLE)
                    mock_hide.assert_called_once()

    def test_update_state_error(self):
        """Test update_state for ERROR state."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()

                with patch.object(indicator, "hide") as mock_hide:
                    indicator.update_state(self.RecognitionState.ERROR)
                    mock_hide.assert_called_once()

    def test_show_creates_overlay_window(self):
        """Test show method creates overlay window."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()

                with patch.object(indicator, "_create_overlay_window") as mock_create:
                    with patch.object(indicator, "_get_cursor_position") as mock_get_pos:
                        mock_get_pos.return_value = MagicMock(x=100, y=100)
                        indicator.overlay_window = MagicMock()

                        with patch("vocalinux.ui.visual_feedback.GLib") as mock_glib_local:
                            indicator.show()
                            mock_create.assert_called_once()

    def test_show_when_already_visible(self):
        """Test show method does nothing when already visible."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                indicator.is_visible = True

                with patch.object(indicator, "_create_overlay_window") as mock_create:
                    indicator.show()
                    mock_create.assert_not_called()

    def test_hide_stops_animation(self):
        """Test hide method stops animation timeouts."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                indicator.is_visible = True
                indicator.animation_timeout_id = 123
                indicator.position_update_timeout_id = 456
                indicator.overlay_window = MagicMock()

                with patch("vocalinux.ui.visual_feedback.GLib") as mock_glib_local:
                    indicator.hide()

                    self.assertEqual(mock_glib_local.source_remove.call_count, 2)
                    mock_glib_local.source_remove.assert_any_call(123)
                    mock_glib_local.source_remove.assert_any_call(456)
                    self.assertFalse(indicator.is_visible)
                    self.assertIsNone(indicator.animation_timeout_id)
                    self.assertIsNone(indicator.position_update_timeout_id)

    def test_hide_when_not_visible(self):
        """Test hide method does nothing when not visible."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                indicator.is_visible = False

                with patch("vocalinux.ui.visual_feedback.GLib") as mock_glib_local:
                    indicator.hide()
                    mock_glib_local.source_remove.assert_not_called()

    def test_cleanup(self):
        """Test cleanup method."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()

                with patch.object(indicator, "hide") as mock_hide:
                    indicator.cleanup()
                    mock_hide.assert_called_once()

    def test_animate_continues_when_visible(self):
        """Test _animate returns True to continue when visible."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                indicator.is_visible = True
                indicator.overlay_window = MagicMock()

                result = indicator._animate()

                self.assertTrue(result)
                indicator.overlay_window.queue_draw.assert_called_once()

    def test_animate_stops_when_not_visible(self):
        """Test _animate returns False to stop when not visible."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                indicator.is_visible = False

                result = indicator._animate()

                self.assertFalse(result)

    def test_update_position_returns_false_when_not_visible(self):
        """Test _update_position returns False when not visible."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                indicator.is_visible = False

                result = indicator._update_position()

                self.assertFalse(result)

    def test_update_position_returns_true_when_visible(self):
        """Test _update_position returns True to continue when visible."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                indicator.is_visible = True
                indicator.overlay_window = MagicMock()

                with patch.object(indicator, "_get_cursor_position") as mock_get_pos:
                    mock_get_pos.return_value = MagicMock(x=100, y=100)

                    result = indicator._update_position()

                    self.assertTrue(result)

    def test_update_position_moves_window_on_position_change(self):
        """Test _update_position moves window when cursor position changes."""
        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", False):
                indicator = self.VisualFeedbackIndicator()
                indicator.is_visible = True
                indicator.overlay_window = MagicMock()
                indicator.last_cursor_position = None

                with patch.object(indicator, "_get_cursor_position") as mock_get_pos:
                    mock_cursor = MagicMock()
                    mock_cursor.x = 200
                    mock_cursor.y = 300
                    mock_get_pos.return_value = mock_cursor

                    indicator._update_position()

                    # Window should be moved to center indicator on cursor
                    expected_x = 200 - indicator.indicator_size
                    expected_y = 300 - indicator.indicator_size
                    indicator.overlay_window.move.assert_called_once_with(expected_x, expected_y)

    def test_cursor_position_class(self):
        """Test CursorPosition class."""
        from vocalinux.ui.visual_feedback import CursorPosition

        pos = CursorPosition(100, 200)
        self.assertEqual(pos.x, 100)
        self.assertEqual(pos.y, 200)
        self.assertEqual(str(pos), "CursorPosition(x=100, y=200)")


class TestVisualFeedbackWithoutGTK(unittest.TestCase):
    """Test visual feedback behavior when GTK is not available."""

    def test_update_state_without_gtk(self):
        """Test update_state does nothing when GTK is not available."""
        # Clear cached imports
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", False):
            from vocalinux.common_types import RecognitionState
            from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

            indicator = VisualFeedbackIndicator()
            # Should not raise any errors
            indicator.update_state(RecognitionState.LISTENING)
            indicator.update_state(RecognitionState.PROCESSING)
            indicator.update_state(RecognitionState.IDLE)

    def test_show_without_gtk(self):
        """Test show does nothing when GTK is not available."""
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", False):
            from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

            indicator = VisualFeedbackIndicator()
            # Should not raise any errors
            indicator.show()

    def test_hide_without_gtk(self):
        """Test hide does nothing when GTK is not available."""
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", False):
            from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

            indicator = VisualFeedbackIndicator()
            # Should not raise any errors
            indicator.hide()

    def test_cleanup_without_gtk(self):
        """Test cleanup works when GTK is not available."""
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", False):
            from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

            indicator = VisualFeedbackIndicator()
            # Should not raise any errors
            indicator.cleanup()


class TestVisualFeedbackOnWayland(unittest.TestCase):
    """Test visual feedback behavior on Wayland sessions."""

    def test_indicator_disabled_on_wayland(self):
        """Test indicator is disabled when running on Wayland."""
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", True):
                from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

                indicator = VisualFeedbackIndicator()
                # Indicator should be disabled on Wayland
                self.assertFalse(indicator._enabled)

    def test_show_does_nothing_on_wayland(self):
        """Test show does nothing on Wayland."""
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", True):
                from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

                indicator = VisualFeedbackIndicator()
                # Should not raise any errors
                indicator.show()
                # No overlay window should be created
                self.assertFalse(hasattr(indicator, "overlay_window"))

    def test_hide_does_nothing_on_wayland(self):
        """Test hide does nothing on Wayland."""
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", True):
                from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

                indicator = VisualFeedbackIndicator()
                # Should not raise any errors
                indicator.hide()

    def test_update_state_does_nothing_on_wayland(self):
        """Test update_state does nothing on Wayland."""
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", True):
                from vocalinux.common_types import RecognitionState
                from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

                indicator = VisualFeedbackIndicator()
                # Should not raise any errors
                indicator.update_state(RecognitionState.LISTENING)
                indicator.update_state(RecognitionState.PROCESSING)
                indicator.update_state(RecognitionState.IDLE)

    def test_cleanup_works_on_wayland(self):
        """Test cleanup works on Wayland."""
        modules_to_remove = [k for k in list(sys.modules.keys()) if "visual_feedback" in k]
        for mod in modules_to_remove:
            del sys.modules[mod]

        with patch("vocalinux.ui.visual_feedback.GTK_AVAILABLE", True):
            with patch("vocalinux.ui.visual_feedback.WAYLAND_SESSION", True):
                from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

                indicator = VisualFeedbackIndicator()
                # Should not raise any errors
                indicator.cleanup()


if __name__ == "__main__":
    unittest.main()
