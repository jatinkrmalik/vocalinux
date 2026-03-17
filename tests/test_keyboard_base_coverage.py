"""
Tests for keyboard backend base class and helper functions.

This module tests the base.py module including:
- parse_shortcut() function and error cases
- get_shortcut_display_name() function
- KeyboardBackend abstract class
"""

import pytest
from unittest.mock import MagicMock

from vocalinux.ui.keyboard_backends.base import (
    DEFAULT_SHORTCUT,
    DEFAULT_SHORTCUT_MODE,
    SHORTCUT_DISPLAY_NAMES,
    SHORTCUT_MODE_DISPLAY_NAMES,
    SHORTCUT_MODES,
    SUPPORTED_SHORTCUTS,
    KeyboardBackend,
    get_shortcut_display_name,
    parse_shortcut,
)


class TestParseShortcut:
    """Test the parse_shortcut() function."""

    def test_parse_shortcut_ctrl_either_side(self):
        """Test parsing ctrl+ctrl (either side)."""
        result = parse_shortcut("ctrl+ctrl")
        assert result == "ctrl"

    def test_parse_shortcut_alt_either_side(self):
        """Test parsing alt+alt (either side)."""
        result = parse_shortcut("alt+alt")
        assert result == "alt"

    def test_parse_shortcut_shift_either_side(self):
        """Test parsing shift+shift (either side)."""
        result = parse_shortcut("shift+shift")
        assert result == "shift"

    def test_parse_shortcut_left_ctrl(self):
        """Test parsing left_ctrl+left_ctrl."""
        result = parse_shortcut("left_ctrl+left_ctrl")
        assert result == "left_ctrl"

    def test_parse_shortcut_right_alt(self):
        """Test parsing right_alt+right_alt."""
        result = parse_shortcut("right_alt+right_alt")
        assert result == "right_alt"

    def test_parse_shortcut_left_shift(self):
        """Test parsing left_shift+left_shift."""
        result = parse_shortcut("left_shift+left_shift")
        assert result == "left_shift"

    def test_parse_shortcut_case_insensitive(self):
        """Test that parse_shortcut is case insensitive."""
        result = parse_shortcut("CTRL+CTRL")
        assert result == "ctrl"

    def test_parse_shortcut_with_whitespace(self):
        """Test that parse_shortcut handles whitespace."""
        result = parse_shortcut("  ctrl+ctrl  ")
        assert result == "ctrl"

    def test_parse_shortcut_invalid_shortcut(self):
        """Test that parse_shortcut raises ValueError for invalid shortcut."""
        with pytest.raises(ValueError) as excinfo:
            parse_shortcut("invalid_shortcut")
        assert "Unsupported shortcut" in str(excinfo.value)
        assert "invalid_shortcut" in str(excinfo.value)

    def test_parse_shortcut_empty_string(self):
        """Test that parse_shortcut raises ValueError for empty string."""
        with pytest.raises(ValueError):
            parse_shortcut("")

    def test_parse_shortcut_partial_match(self):
        """Test that parse_shortcut doesn't accept partial matches."""
        with pytest.raises(ValueError):
            parse_shortcut("ctrl")

    def test_parse_shortcut_all_supported(self):
        """Test that all supported shortcuts can be parsed."""
        for shortcut_key in SUPPORTED_SHORTCUTS.keys():
            result = parse_shortcut(shortcut_key)
            assert result == SUPPORTED_SHORTCUTS[shortcut_key]


class TestGetShortcutDisplayName:
    """Test the get_shortcut_display_name() function."""

    def test_get_display_name_ctrl_no_mode(self):
        """Test getting display name for ctrl without mode."""
        result = get_shortcut_display_name("ctrl+ctrl")
        assert result == "Ctrl (either side)"

    def test_get_display_name_alt_no_mode(self):
        """Test getting display name for alt without mode."""
        result = get_shortcut_display_name("alt+alt")
        assert result == "Alt (either side)"

    def test_get_display_name_shift_no_mode(self):
        """Test getting display name for shift without mode."""
        result = get_shortcut_display_name("shift+shift")
        assert result == "Shift (either side)"

    def test_get_display_name_left_ctrl_no_mode(self):
        """Test getting display name for left_ctrl without mode."""
        result = get_shortcut_display_name("left_ctrl+left_ctrl")
        assert result == "Left Ctrl"

    def test_get_display_name_right_alt_no_mode(self):
        """Test getting display name for right_alt without mode."""
        result = get_shortcut_display_name("right_alt+right_alt")
        assert result == "Right Alt"

    def test_get_display_name_ctrl_toggle_mode(self):
        """Test getting display name for ctrl with toggle mode."""
        result = get_shortcut_display_name("ctrl+ctrl", mode="toggle")
        assert result == "Double-tap Ctrl"

    def test_get_display_name_ctrl_push_to_talk_mode(self):
        """Test getting display name for ctrl with push_to_talk mode."""
        result = get_shortcut_display_name("ctrl+ctrl", mode="push_to_talk")
        assert result == "Hold Ctrl"

    def test_get_display_name_alt_toggle_mode(self):
        """Test getting display name for alt with toggle mode."""
        result = get_shortcut_display_name("alt+alt", mode="toggle")
        assert result == "Double-tap Alt"

    def test_get_display_name_left_ctrl_toggle(self):
        """Test getting display name for left_ctrl with toggle mode."""
        result = get_shortcut_display_name("left_ctrl+left_ctrl", mode="toggle")
        assert result == "Double-tap Left Ctrl"

    def test_get_display_name_left_ctrl_push_to_talk(self):
        """Test getting display name for left_ctrl with push_to_talk mode."""
        result = get_shortcut_display_name("left_ctrl+left_ctrl", mode="push_to_talk")
        assert result == "Hold Left Ctrl"

    def test_get_display_name_unknown_shortcut(self):
        """Test getting display name for unknown shortcut (returns the shortcut itself)."""
        result = get_shortcut_display_name("unknown+unknown")
        assert result == "unknown+unknown"

    def test_get_display_name_unknown_mode(self):
        """Test getting display name with unknown mode (falls back to base name)."""
        result = get_shortcut_display_name("ctrl+ctrl", mode="unknown_mode")
        assert result == "Ctrl (either side)"

    def test_get_display_name_all_supported_shortcuts_no_mode(self):
        """Test that all supported shortcuts have display names."""
        for shortcut_key in SUPPORTED_SHORTCUTS.keys():
            result = get_shortcut_display_name(shortcut_key)
            assert result  # Should not be empty
            assert isinstance(result, str)

    def test_get_display_name_all_shortcuts_with_toggle_mode(self):
        """Test all shortcuts with toggle mode."""
        for shortcut_key in SUPPORTED_SHORTCUTS.keys():
            result = get_shortcut_display_name(shortcut_key, mode="toggle")
            assert result  # Should not be empty
            assert isinstance(result, str)

    def test_get_display_name_all_shortcuts_with_push_to_talk_mode(self):
        """Test all shortcuts with push_to_talk mode."""
        for shortcut_key in SUPPORTED_SHORTCUTS.keys():
            result = get_shortcut_display_name(shortcut_key, mode="push_to_talk")
            assert result  # Should not be empty
            assert isinstance(result, str)


class ConcreteKeyboardBackend(KeyboardBackend):
    """Concrete implementation of KeyboardBackend for testing."""

    def start(self) -> bool:
        """Start the backend."""
        return True

    def stop(self) -> None:
        """Stop the backend."""
        pass

    def is_available(self) -> bool:
        """Check if available."""
        return True

    def get_permission_hint(self):
        """Get permission hint."""
        return None


class TestKeyboardBackend:
    """Test the KeyboardBackend abstract base class."""

    def test_init_default_values(self):
        """Test backend initialization with default values."""
        backend = ConcreteKeyboardBackend()
        assert backend.shortcut == DEFAULT_SHORTCUT
        assert backend.mode == DEFAULT_SHORTCUT_MODE
        assert backend.active is False
        assert backend.double_tap_callback is None
        assert backend.key_press_callback is None
        assert backend.key_release_callback is None

    def test_init_custom_shortcut_and_mode(self):
        """Test backend initialization with custom shortcut and mode."""
        backend = ConcreteKeyboardBackend(shortcut="alt+alt", mode="push_to_talk")
        assert backend.shortcut == "alt+alt"
        assert backend.mode == "push_to_talk"

    def test_shortcut_property(self):
        """Test shortcut property is read-only."""
        backend = ConcreteKeyboardBackend(shortcut="ctrl+ctrl")
        assert backend.shortcut == "ctrl+ctrl"

    def test_mode_property(self):
        """Test mode property is read-only."""
        backend = ConcreteKeyboardBackend(mode="toggle")
        assert backend.mode == "toggle"

    def test_modifier_key_property(self):
        """Test modifier_key property."""
        backend = ConcreteKeyboardBackend(shortcut="alt+alt")
        assert backend.modifier_key == "alt"

    def test_modifier_key_left_ctrl(self):
        """Test modifier_key for left_ctrl shortcut."""
        backend = ConcreteKeyboardBackend(shortcut="left_ctrl+left_ctrl")
        assert backend.modifier_key == "left_ctrl"

    def test_set_mode_valid(self):
        """Test setting a valid mode."""
        backend = ConcreteKeyboardBackend()
        backend.set_mode("push_to_talk")
        assert backend.mode == "push_to_talk"

    def test_set_mode_toggle(self):
        """Test setting mode to toggle."""
        backend = ConcreteKeyboardBackend(mode="push_to_talk")
        backend.set_mode("toggle")
        assert backend.mode == "toggle"

    def test_set_mode_invalid(self):
        """Test setting an invalid mode raises ValueError."""
        backend = ConcreteKeyboardBackend()
        with pytest.raises(ValueError) as excinfo:
            backend.set_mode("invalid_mode")
        assert "Invalid mode" in str(excinfo.value)

    def test_set_shortcut_ctrl(self):
        """Test setting shortcut to ctrl+ctrl."""
        backend = ConcreteKeyboardBackend(shortcut="alt+alt")
        backend.set_shortcut("ctrl+ctrl")
        assert backend.shortcut == "ctrl+ctrl"
        assert backend.modifier_key == "ctrl"

    def test_set_shortcut_left_shift(self):
        """Test setting shortcut to left_shift+left_shift."""
        backend = ConcreteKeyboardBackend()
        backend.set_shortcut("left_shift+left_shift")
        assert backend.shortcut == "left_shift+left_shift"
        assert backend.modifier_key == "left_shift"

    def test_set_shortcut_invalid(self):
        """Test setting an invalid shortcut raises ValueError."""
        backend = ConcreteKeyboardBackend()
        with pytest.raises(ValueError):
            backend.set_shortcut("invalid+invalid")

    def test_register_toggle_callback(self):
        """Test registering a toggle callback."""
        backend = ConcreteKeyboardBackend()
        callback = MagicMock()
        backend.register_toggle_callback(callback)
        assert backend.double_tap_callback == callback

    def test_register_toggle_callback_none(self):
        """Test unregistering toggle callback by passing None."""
        backend = ConcreteKeyboardBackend()
        callback = MagicMock()
        backend.register_toggle_callback(callback)
        backend.register_toggle_callback(None)
        assert backend.double_tap_callback is None

    def test_register_press_callback(self):
        """Test registering a press callback."""
        backend = ConcreteKeyboardBackend()
        callback = MagicMock()
        backend.register_press_callback(callback)
        assert backend.key_press_callback == callback

    def test_register_press_callback_none(self):
        """Test unregistering press callback by passing None."""
        backend = ConcreteKeyboardBackend()
        callback = MagicMock()
        backend.register_press_callback(callback)
        backend.register_press_callback(None)
        assert backend.key_press_callback is None

    def test_register_release_callback(self):
        """Test registering a release callback."""
        backend = ConcreteKeyboardBackend()
        callback = MagicMock()
        backend.register_release_callback(callback)
        assert backend.key_release_callback == callback

    def test_register_release_callback_none(self):
        """Test unregistering release callback by passing None."""
        backend = ConcreteKeyboardBackend()
        callback = MagicMock()
        backend.register_release_callback(callback)
        backend.register_release_callback(None)
        assert backend.key_release_callback is None

    def test_multiple_callbacks_independent(self):
        """Test that multiple callbacks can be registered independently."""
        backend = ConcreteKeyboardBackend()
        toggle_cb = MagicMock()
        press_cb = MagicMock()
        release_cb = MagicMock()

        backend.register_toggle_callback(toggle_cb)
        backend.register_press_callback(press_cb)
        backend.register_release_callback(release_cb)

        assert backend.double_tap_callback == toggle_cb
        assert backend.key_press_callback == press_cb
        assert backend.key_release_callback == release_cb

    def test_start_method(self):
        """Test that start() method can be called."""
        backend = ConcreteKeyboardBackend()
        result = backend.start()
        assert result is True

    def test_stop_method(self):
        """Test that stop() method can be called."""
        backend = ConcreteKeyboardBackend()
        backend.stop()  # Should not raise

    def test_is_available_method(self):
        """Test that is_available() method returns bool."""
        backend = ConcreteKeyboardBackend()
        result = backend.is_available()
        assert isinstance(result, bool)

    def test_get_permission_hint_method(self):
        """Test that get_permission_hint() method returns Optional[str]."""
        backend = ConcreteKeyboardBackend()
        result = backend.get_permission_hint()
        assert result is None or isinstance(result, str)

    def test_active_flag_management(self):
        """Test that active flag is properly managed."""
        backend = ConcreteKeyboardBackend()
        assert backend.active is False
        backend.active = True
        assert backend.active is True
        backend.active = False
        assert backend.active is False
