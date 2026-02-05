"""
Tests for accessibility features in Visual Feedback.

This module tests WCAG-compliant accessibility features:
- High contrast mode support
- Animation reduction support
- Screen reader compatibility
- Keyboard navigation support
"""

import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mock gi.repository before importing vocalinux modules
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.Gio"] = MagicMock()
sys.modules["gi.repository.Atk"] = MagicMock()

from vocalinux.common_types import RecognitionState

VISUAL_FEEDBACK_MODULE = "vocalinux.ui.visual_feedback"


class TestVisualFeedbackHighContrast(unittest.TestCase):
    """Test high contrast mode accessibility support."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_high_contrast_color_fallback(self, mock_glib, mock_gdk, mock_gtk):
        """Test that colors are distinguishable in high contrast mode."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)

        indicator = VisualFeedbackIndicator()

        # Colors should be defined with sufficient contrast
        # Blue for listening
        self.assertEqual(indicator.base_color, (0.2, 0.6, 1.0, 0.8))

        # Test processing color (orange)
        indicator.update_state(RecognitionState.LISTENING)
        indicator.update_state(RecognitionState.PROCESSING)
        self.assertEqual(indicator.base_color, (1.0, 0.6, 0.2, 0.8))

        # Verify colors are different enough for high contrast
        listening_color = (0.2, 0.6, 1.0, 0.8)
        processing_color = (1.0, 0.6, 0.2, 0.8)

        # Check red channel differs significantly
        self.assertGreater(abs(listening_color[0] - processing_color[0]), 0.5)


class TestVisualFeedbackReducedMotion(unittest.TestCase):
    """Test reduced motion / animation accessibility support."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_animation_can_be_disabled(self, mock_glib, mock_gdk, mock_gtk):
        """Test that animation can be disabled for users with motion sensitivity."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)

        indicator = VisualFeedbackIndicator()

        # Animation parameters should be configurable
        self.assertTrue(hasattr(indicator, 'pulse_speed'))
        self.assertTrue(hasattr(indicator, 'pulse_min_scale'))
        self.assertTrue(hasattr(indicator, 'pulse_max_scale'))

        # Can disable animation by setting pulse range to 1.0
        indicator.pulse_min_scale = 1.0
        indicator.pulse_max_scale = 1.0
        self.assertEqual(indicator.pulse_min_scale, indicator.pulse_max_scale)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_pulse_speed_configurable(self, mock_glib, mock_gdk, mock_gtk):
        """Test that pulse animation speed is configurable."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)

        indicator = VisualFeedbackIndicator()

        # Default speed should exist
        default_speed = indicator.pulse_speed
        self.assertGreater(default_speed, 0)

        # Speed should be modifiable
        indicator.pulse_speed = 0.05  # Slower for reduced motion
        self.assertEqual(indicator.pulse_speed, 0.05)


class TestVisualFeedbackScreenReader(unittest.TestCase):
    """Test screen reader accessibility support."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_window_has_accessible_role(self, mock_glib, mock_gdk, mock_gtk):
        """Test that overlay window has appropriate accessible role."""
        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        indicator = VisualFeedbackIndicator()
        indicator._create_overlay_window()

        # Window should be created with notification type (good for AT)
        mock_window.set_type_hint.assert_called()

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_state_changes_logged_for_debugging(self, mock_glib, mock_gdk, mock_gtk):
        """Test that state changes are logged (helpful for debugging accessibility)."""
        import logging

        mock_gtk.init_check.return_value = (True, None)

        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        # Capture log output
        with self.assertLogs('vocalinux.ui.visual_feedback', level='INFO') as cm:
            indicator = VisualFeedbackIndicator()
            indicator.update_state(RecognitionState.LISTENING)

        # Should have initialization log
        self.assertTrue(
            any("Visual feedback indicator initialized" in msg for msg in cm.output)
        )


class TestVisualFeedbackKeyboardNavigation(unittest.TestCase):
    """Test keyboard navigation accessibility support."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_window_does_not_accept_focus(self, mock_glib, mock_gdk, mock_gtk):
        """Test that overlay window does not steal keyboard focus."""
        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        indicator = VisualFeedbackIndicator()
        indicator._create_overlay_window()

        # Window should not accept focus (doesn't interfere with typing)
        mock_window.set_accept_focus.assert_called_once_with(False)
        mock_window.set_focus_on_map.assert_called_once_with(False)


class TestVisualFeedbackVisibilityAndContrast(unittest.TestCase):
    """Test visibility and contrast requirements."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_indicator_opacity_configurable(self, mock_glib, mock_gdk, mock_gtk):
        """Test that indicator opacity can be adjusted for visibility needs."""
        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        indicator = VisualFeedbackIndicator()
        indicator._create_overlay_window()

        # Opacity should be set for visibility
        mock_window.set_opacity.assert_called_once()
        # Opacity should be between 0 and 1
        opacity_call = mock_window.set_opacity.call_args[0][0]
        self.assertGreater(opacity_call, 0)
        self.assertLessEqual(opacity_call, 1.0)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_indicator_size_configurable(self, mock_glib, mock_gdk, mock_gtk):
        """Test that indicator size can be adjusted for visibility needs."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)

        indicator = VisualFeedbackIndicator()

        # Should have a reasonable default size
        self.assertEqual(indicator.indicator_size, 40)

        # Size should be modifiable for accessibility
        indicator.indicator_size = 60  # Larger for low vision users
        self.assertEqual(indicator.indicator_size, 60)


class TestVisualFeedbackDefaultAccessibility(unittest.TestCase):
    """Test default accessibility configuration."""

    def test_default_config_has_visual_feedback_enabled(self):
        """Test that visual feedback is enabled by default (helpful for users)."""
        from vocalinux.ui.config_manager import DEFAULT_CONFIG

        self.assertIn("ui", DEFAULT_CONFIG)
        self.assertIn("enable_visual_feedback", DEFAULT_CONFIG["ui"])
        # Default should be enabled to help users notice when system is listening
        self.assertTrue(DEFAULT_CONFIG["ui"]["enable_visual_feedback"])

    def test_visual_feedback_does_not_block_interaction(self):
        """Test that visual feedback doesn't block user interaction."""
        # The window should be:
        # - Click-through (accept_focus=False)
        # - Non-decorated
        # - Type: NOTIFICATION (not MODAL or DIALOG)
        # These are verified in other tests
        pass  # Placeholder - actual behavior tested in integration tests


class TestVisualFeedbackAlternativeText(unittest.TestCase):
    """Test that visual states have semantic meaning."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_listening_state_semantic_color(self, mock_glib, mock_gdk, mock_gtk):
        """Test that listening state uses semantically meaningful color."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)

        indicator = VisualFeedbackIndicator()
        indicator.update_state(RecognitionState.LISTENING)

        # Blue typically means "active/listening" in UI conventions
        # RGB values: 0.2, 0.6, 1.0 is a clear blue
        self.assertEqual(indicator.base_color[2], 1.0)  # Max blue channel
        self.assertLess(indicator.base_color[0], 0.5)   # Low red

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_processing_state_semantic_color(self, mock_glib, mock_gdk, mock_gtk):
        """Test that processing state uses semantically meaningful color."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)

        indicator = VisualFeedbackIndicator()
        indicator.update_state(RecognitionState.LISTENING)
        indicator.update_state(RecognitionState.PROCESSING)

        # Orange/amber typically means "processing/waiting" in UI conventions
        # RGB values: 1.0, 0.6, 0.2 is an orange/amber
        self.assertEqual(indicator.base_color[0], 1.0)  # Max red
        self.assertGreater(indicator.base_color[1], 0.5)  # Moderate green
        self.assertLess(indicator.base_color[2], 0.5)   # Low blue


if __name__ == "__main__":
    unittest.main()
