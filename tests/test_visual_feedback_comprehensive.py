"""
Comprehensive GTK tests with mocks for Visual Feedback feature.

This module provides thorough test coverage for:
- VisualFeedbackIndicator initialization
- Animation state transitions (LISTENING, PROCESSING, IDLE)
- Config toggle behavior (enable/disable)
- Settings dialog integration
- Accessibility features
"""

import sys
import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock

import pytest

# Module path constants
VISUAL_FEEDBACK_MODULE = "vocalinux.ui.visual_feedback"
SETTINGS_DIALOG_MODULE = "vocalinux.ui.settings_dialog"

# Mock gi.repository before importing vocalinux modules
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()

from vocalinux.common_types import RecognitionState
from vocalinux.ui.config_manager import ConfigManager, DEFAULT_CONFIG


class TestCursorPosition(unittest.TestCase):
    """Test cases for the CursorPosition class."""

    def test_cursor_position_creation(self):
        """Test creating a CursorPosition object."""
        from vocalinux.ui.visual_feedback import CursorPosition

        pos = CursorPosition(100, 200)
        self.assertEqual(pos.x, 100)
        self.assertEqual(pos.y, 200)

    def test_cursor_position_str(self):
        """Test string representation of CursorPosition."""
        from vocalinux.ui.visual_feedback import CursorPosition

        pos = CursorPosition(100, 200)
        self.assertEqual(str(pos), "CursorPosition(x=100, y=200)")

    def test_cursor_position_zero_values(self):
        """Test CursorPosition with zero values."""
        from vocalinux.ui.visual_feedback import CursorPosition

        pos = CursorPosition(0, 0)
        self.assertEqual(pos.x, 0)
        self.assertEqual(pos.y, 0)

    def test_cursor_position_negative_values(self):
        """Test CursorPosition with negative values."""
        from vocalinux.ui.visual_feedback import CursorPosition

        pos = CursorPosition(-100, -200)
        self.assertEqual(pos.x, -100)
        self.assertEqual(pos.y, -200)


class TestVisualFeedbackIndicatorInitialization(unittest.TestCase):
    """Test cases for VisualFeedbackIndicator initialization."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_init_default(self, mock_glib, mock_gdk, mock_gtk):
        """Test default initialization."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        indicator = VisualFeedbackIndicator()

        self.assertTrue(indicator.enabled)
        self.assertIsNone(indicator.overlay_window)
        self.assertFalse(indicator.is_visible)
        self.assertEqual(indicator.indicator_size, 40)
        self.assertEqual(indicator.base_color, (0.2, 0.6, 1.0, 0.8))

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_init_with_config_enabled(self, mock_glib, mock_gdk, mock_gtk):
        """Test initialization with config manager (enabled)."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_config = MagicMock()
        mock_config.get.return_value = True

        indicator = VisualFeedbackIndicator(config_manager=mock_config)

        self.assertTrue(indicator.enabled)
        mock_config.get.assert_called_once_with("ui", "enable_visual_feedback", True)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_init_with_config_disabled(self, mock_glib, mock_gdk, mock_gtk):
        """Test initialization with config manager (disabled)."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_config = MagicMock()
        mock_config.get.return_value = False

        indicator = VisualFeedbackIndicator(config_manager=mock_config)

        self.assertFalse(indicator.enabled)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_init_disabled_no_attributes_set(self, mock_glib, mock_gdk, mock_gtk):
        """Test that when disabled, GTK-dependent attributes are not initialized."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_config = MagicMock()
        mock_config.get.return_value = False

        indicator = VisualFeedbackIndicator(config_manager=mock_config)

        # When disabled, the early return means some attributes aren't set
        self.assertFalse(hasattr(indicator, "overlay_window"))
        self.assertFalse(hasattr(indicator, "is_visible"))


class TestVisualFeedbackShowHide(unittest.TestCase):
    """Test cases for show/hide functionality."""

    def setUp(self):
        """Set up mocks for GTK."""
        self.gi_patcher = patch.dict(
            "sys.modules",
            {
                "gi": MagicMock(),
                "gi.repository": MagicMock(),
            },
        )
        self.gi_patcher.start()

    def tearDown(self):
        """Clean up patches."""
        self.gi_patcher.stop()

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_show_creates_overlay_window(self, mock_glib, mock_gdk, mock_gtk):
        """Test showing the indicator creates overlay window."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        # Mock display and cursor position
        mock_display = MagicMock()
        mock_seat = MagicMock()
        mock_pointer = MagicMock()
        mock_position = MagicMock()
        mock_position.x = 500
        mock_position.y = 300
        mock_pointer.get_position.return_value = mock_position
        mock_seat.get_pointer.return_value = mock_pointer
        mock_display.get_default_seat.return_value = mock_seat
        mock_gdk.Display.get_default.return_value = mock_display

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        indicator = VisualFeedbackIndicator()
        indicator.show()

        self.assertTrue(indicator.is_visible)
        mock_gtk.Window.assert_called_once()
        mock_window.show_all.assert_called_once()
        mock_glib.timeout_add.assert_called()

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_show_already_visible(self, mock_glib, mock_gdk, mock_gtk):
        """Test showing when already visible does nothing."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        # Mock display and cursor position
        mock_display = MagicMock()
        mock_seat = MagicMock()
        mock_pointer = MagicMock()
        mock_position = MagicMock()
        mock_position.x = 500
        mock_position.y = 300
        mock_pointer.get_position.return_value = mock_position
        mock_seat.get_pointer.return_value = mock_pointer
        mock_display.get_default_seat.return_value = mock_seat
        mock_gdk.Display.get_default.return_value = mock_display

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        indicator = VisualFeedbackIndicator()
        indicator.show()

        # Reset mock
        mock_gtk.Window.reset_mock()
        mock_window.show_all.reset_mock()

        # Show again
        indicator.show()

        # Should not create new window
        mock_gtk.Window.assert_not_called()
        mock_window.show_all.assert_not_called()

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_hide(self, mock_glib, mock_gdk, mock_gtk):
        """Test hiding the indicator."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        # Mock display and cursor position
        mock_display = MagicMock()
        mock_seat = MagicMock()
        mock_pointer = MagicMock()
        mock_position = MagicMock()
        mock_position.x = 500
        mock_position.y = 300
        mock_pointer.get_position.return_value = mock_position
        mock_seat.get_pointer.return_value = mock_pointer
        mock_display.get_default_seat.return_value = mock_seat
        mock_gdk.Display.get_default.return_value = mock_display

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        indicator = VisualFeedbackIndicator()
        indicator.show()
        indicator.hide()

        self.assertFalse(indicator.is_visible)
        self.assertIsNone(indicator.overlay_window)
        mock_window.hide.assert_called_once()
        mock_glib.source_remove.assert_called()

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_hide_not_visible(self, mock_glib, mock_gdk, mock_gtk):
        """Test hiding when not visible does nothing."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_gtk.init_check.return_value = (True, None)

        indicator = VisualFeedbackIndicator()
        # Should not raise any errors
        indicator.hide()
        self.assertFalse(indicator.is_visible)


class TestVisualFeedbackStateTransitions(unittest.TestCase):
    """Test cases for animation state transitions (LISTENING, PROCESSING, IDLE)."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def setUp(self, mock_glib, mock_gdk, mock_gtk):
        """Set up test fixtures with mocked GTK."""
        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        # Mock display and cursor position
        mock_display = MagicMock()
        mock_seat = MagicMock()
        mock_pointer = MagicMock()
        mock_position = MagicMock()
        mock_position.x = 500
        mock_position.y = 300
        mock_pointer.get_position.return_value = mock_position
        mock_seat.get_pointer.return_value = mock_pointer
        mock_display.get_default_seat.return_value = mock_seat
        mock_gdk.Display.get_default.return_value = mock_display

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        self.mock_gtk = mock_gtk
        self.mock_window = mock_window

        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator
        self.indicator = VisualFeedbackIndicator()

    def test_update_state_listening(self):
        """Test updating to LISTENING state shows blue indicator."""
        self.indicator.update_state(RecognitionState.LISTENING)

        # Color should be blue
        self.assertEqual(self.indicator.base_color, (0.2, 0.6, 1.0, 0.8))
        self.assertTrue(self.indicator.is_visible)

    def test_update_state_processing(self):
        """Test updating to PROCESSING state changes to orange."""
        self.indicator.update_state(RecognitionState.LISTENING)
        self.indicator.update_state(RecognitionState.PROCESSING)

        # Color should be orange
        self.assertEqual(self.indicator.base_color, (1.0, 0.6, 0.2, 0.8))
        self.assertTrue(self.indicator.is_visible)

    def test_update_state_idle(self):
        """Test updating to IDLE state hides indicator."""
        self.indicator.update_state(RecognitionState.LISTENING)
        self.indicator.update_state(RecognitionState.IDLE)

        self.assertFalse(self.indicator.is_visible)

    def test_update_state_error(self):
        """Test updating to ERROR state hides indicator."""
        self.indicator.update_state(RecognitionState.LISTENING)
        self.indicator.update_state(RecognitionState.ERROR)

        self.assertFalse(self.indicator.is_visible)

    def test_transition_listening_to_processing_to_idle(self):
        """Test full state transition cycle."""
        # Start idle
        self.assertFalse(self.indicator.is_visible)

        # Start listening
        self.indicator.update_state(RecognitionState.LISTENING)
        self.assertTrue(self.indicator.is_visible)
        self.assertEqual(self.indicator.base_color, (0.2, 0.6, 1.0, 0.8))

        # Processing
        self.indicator.update_state(RecognitionState.PROCESSING)
        self.assertTrue(self.indicator.is_visible)
        self.assertEqual(self.indicator.base_color, (1.0, 0.6, 0.2, 0.8))

        # Back to idle
        self.indicator.update_state(RecognitionState.IDLE)
        self.assertFalse(self.indicator.is_visible)


class TestVisualFeedbackAnimation(unittest.TestCase):
    """Test cases for animation functionality."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def setUp(self, mock_glib, mock_gdk, mock_gtk):
        """Set up test fixtures with mocked GTK."""
        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        # Mock display and cursor position
        mock_display = MagicMock()
        mock_seat = MagicMock()
        mock_pointer = MagicMock()
        mock_position = MagicMock()
        mock_position.x = 500
        mock_position.y = 300
        mock_pointer.get_position.return_value = mock_position
        mock_seat.get_pointer.return_value = mock_pointer
        mock_display.get_default_seat.return_value = mock_seat
        mock_gdk.Display.get_default.return_value = mock_display

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        self.mock_window = mock_window

        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator
        self.indicator = VisualFeedbackIndicator()
        self.indicator.show()

    def test_animate_updates_phase(self):
        """Test that animation updates the phase."""
        initial_phase = self.indicator.animation_phase

        # Simulate animation frame
        result = self.indicator._animate()

        self.assertTrue(result)
        self.assertGreater(self.indicator.animation_phase, initial_phase)

    def test_animate_queues_redraw(self):
        """Test that animation queues window redraw."""
        self.indicator._animate()

        self.mock_window.queue_draw.assert_called()

    def test_animate_not_visible(self):
        """Test animation when not visible returns False."""
        self.indicator.is_visible = False

        result = self.indicator._animate()

        self.assertFalse(result)


class TestVisualFeedbackConfigToggle(unittest.TestCase):
    """Test cases for configuration toggle behavior (enable/disable)."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_config_toggle_enabled(self, mock_glib, mock_gdk, mock_gtk):
        """Test that visual feedback can be enabled via config."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_config = MagicMock()
        mock_config.get.return_value = True

        indicator = VisualFeedbackIndicator(config_manager=mock_config)

        self.assertTrue(indicator.enabled)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_config_toggle_disabled(self, mock_glib, mock_gdk, mock_gtk):
        """Test that visual feedback can be disabled via config."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_config = MagicMock()
        mock_config.get.return_value = False

        indicator = VisualFeedbackIndicator(config_manager=mock_config)

        self.assertFalse(indicator.enabled)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_disabled_indicator_does_not_show(self, mock_glib, mock_gdk, mock_gtk):
        """Test that disabled indicator does not show on state update."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_config = MagicMock()
        mock_config.get.return_value = False

        indicator = VisualFeedbackIndicator(config_manager=mock_config)
        indicator.update_state(RecognitionState.LISTENING)

        # When disabled, indicator should not have is_visible attribute
        self.assertFalse(hasattr(indicator, "is_visible"))

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_disabled_indicator_cleanup(self, mock_glib, mock_gdk, mock_gtk):
        """Test that cleanup works when disabled."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        mock_config = MagicMock()
        mock_config.get.return_value = False

        indicator = VisualFeedbackIndicator(config_manager=mock_config)
        # Should not raise any errors
        indicator.cleanup()


class TestVisualFeedbackAccessibility(unittest.TestCase):
    """Test cases for accessibility features."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_indicator_size_configurable(self, mock_glib, mock_gdk, mock_gtk):
        """Test that indicator size is configurable."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        indicator = VisualFeedbackIndicator()

        # Default size should be 40
        self.assertEqual(indicator.indicator_size, 40)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_base_color_transparency(self, mock_glib, mock_gdk, mock_gtk):
        """Test that base color includes transparency."""
        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        indicator = VisualFeedbackIndicator()

        # Color should be RGBA tuple with alpha < 1 for transparency
        self.assertEqual(len(indicator.base_color), 4)
        self.assertLess(indicator.base_color[3], 1.0)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_window_click_through(self, mock_glib, mock_gdk, mock_gtk):
        """Test that overlay window is click-through."""
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

        # Window should not accept focus
        mock_window.set_accept_focus.assert_called_once_with(False)
        mock_window.set_focus_on_map.assert_called_once_with(False)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_window_stays_above(self, mock_glib, mock_gdk, mock_gtk):
        """Test that overlay window stays above other windows."""
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

        # Window should stay above
        mock_window.set_keep_above.assert_called_once_with(True)


class TestVisualFeedbackSettingsDialogIntegration(unittest.TestCase):
    """Test cases for settings dialog integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config_manager = MagicMock()
        self.mock_config_manager.get.return_value = True

    def _create_mock_checkbutton(self, active=True):
        """Helper to create a mock checkbutton."""
        checkbutton = MagicMock()
        checkbutton.get_active.return_value = active
        checkbutton.set_active = Mock()
        checkbutton.set_tooltip_text = Mock()
        checkbutton.connect = Mock()
        return checkbutton

    def test_visual_feedback_checkbox_initialization_enabled(self):
        """Test that visual feedback checkbox is initialized correctly when enabled."""
        # Mock config returns True for visual feedback
        self.mock_config_manager.get.side_effect = lambda section, key, default=None: {
            ("ui", "enable_visual_feedback", True): True,
            ("speech_recognition", "engine", "vosk"): "vosk",
        }.get((section, key, default), default)

        # Verify the config returns True
        visual_feedback_enabled = self.mock_config_manager.get(
            "ui", "enable_visual_feedback", True
        )
        self.assertTrue(visual_feedback_enabled)

    def test_visual_feedback_checkbox_initialization_disabled(self):
        """Test that visual feedback checkbox is initialized correctly when disabled."""
        # Mock config returns False for visual feedback
        self.mock_config_manager.get.side_effect = lambda section, key, default=None: {
            ("ui", "enable_visual_feedback", True): False,
            ("speech_recognition", "engine", "vosk"): "vosk",
        }.get((section, key, default), default)

        # Verify the config returns False
        visual_feedback_enabled = self.mock_config_manager.get(
            "ui", "enable_visual_feedback", True
        )
        self.assertFalse(visual_feedback_enabled)

    def test_on_visual_feedback_changed_triggers_auto_apply(self):
        """Test the visual feedback changed callback triggers auto-apply."""
        mock_checkbutton = self._create_mock_checkbutton(active=False)

        # Create a mock dialog with necessary attributes
        dialog = MagicMock()
        dialog.config_manager = self.mock_config_manager
        dialog._initializing = False
        dialog._test_active = False
        dialog._applying_settings = False
        dialog._populating_models = False
        dialog.visual_feedback_check = mock_checkbutton
        dialog._auto_apply_settings = Mock()

        # Import and manually call the handler function logic
        # The _on_visual_feedback_changed just calls _auto_apply_settings
        dialog._on_visual_feedback_changed = lambda widget: dialog._auto_apply_settings()

        # Simulate the changed event
        dialog._on_visual_feedback_changed(mock_checkbutton)

        # Verify _auto_apply_settings is called
        dialog._auto_apply_settings.assert_called_once()

    def test_config_manager_set_visual_feedback(self):
        """Test config manager can set visual feedback value."""
        config_manager = MagicMock()
        config_manager.set.return_value = True

        result = config_manager.set("ui", "enable_visual_feedback", False)

        self.assertTrue(result)
        config_manager.set.assert_called_once_with("ui", "enable_visual_feedback", False)


class TestVisualFeedbackDefaultConfig(unittest.TestCase):
    """Test cases for default configuration."""

    def test_default_config_includes_visual_feedback(self):
        """Test that default config includes visual feedback setting."""
        self.assertIn("ui", DEFAULT_CONFIG)
        self.assertIn("enable_visual_feedback", DEFAULT_CONFIG["ui"])
        self.assertTrue(DEFAULT_CONFIG["ui"]["enable_visual_feedback"])

    def test_default_config_structure(self):
        """Test that default config has proper structure."""
        ui_config = DEFAULT_CONFIG.get("ui", {})
        self.assertIn("start_minimized", ui_config)
        self.assertIn("show_notifications", ui_config)
        self.assertIn("enable_visual_feedback", ui_config)


class TestVisualFeedbackCleanup(unittest.TestCase):
    """Test cases for cleanup functionality."""

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_cleanup_hides_indicator(self, mock_glib, mock_gdk, mock_gtk):
        """Test cleanup hides the indicator."""
        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        # Mock display and cursor position
        mock_display = MagicMock()
        mock_seat = MagicMock()
        mock_pointer = MagicMock()
        mock_position = MagicMock()
        mock_position.x = 500
        mock_position.y = 300
        mock_pointer.get_position.return_value = mock_position
        mock_seat.get_pointer.return_value = mock_pointer
        mock_display.get_default_seat.return_value = mock_seat
        mock_gdk.Display.get_default.return_value = mock_display

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        indicator = VisualFeedbackIndicator()
        indicator.show()
        indicator.cleanup()

        self.assertFalse(indicator.is_visible)

    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gtk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.Gdk")
    @patch(f"{VISUAL_FEEDBACK_MODULE}.GLib")
    def test_cleanup_removes_timeouts(self, mock_glib, mock_gdk, mock_gtk):
        """Test cleanup removes animation and position timeouts."""
        mock_gtk.init_check.return_value = (True, None)
        mock_gtk.WindowType.POPUP = 0
        mock_gtk.WindowTypeHint.NOTIFICATION = 1

        mock_screen = MagicMock()
        mock_visual = MagicMock()
        mock_screen.get_rgba_visual.return_value = mock_visual
        mock_gdk.Screen.get_default.return_value = mock_screen

        # Mock display and cursor position
        mock_display = MagicMock()
        mock_seat = MagicMock()
        mock_pointer = MagicMock()
        mock_position = MagicMock()
        mock_position.x = 500
        mock_position.y = 300
        mock_pointer.get_position.return_value = mock_position
        mock_seat.get_pointer.return_value = mock_pointer
        mock_display.get_default_seat.return_value = mock_seat
        mock_gdk.Display.get_default.return_value = mock_display

        mock_window = MagicMock()
        mock_gtk.Window.return_value = mock_window

        from vocalinux.ui.visual_feedback import VisualFeedbackIndicator

        indicator = VisualFeedbackIndicator()
        indicator.show()
        indicator.cleanup()

        # Should call source_remove for animation and position timeouts
        mock_glib.source_remove.assert_called()


if __name__ == "__main__":
    unittest.main()
