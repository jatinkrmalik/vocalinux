"""Tests for the shortcut-capture keyname mapping in the settings dialog.

Covers the pure `_gdk_keyname_to_token` helper that turns a GDK key-symbol name
(from the "Record shortcut" capture) into a canonical main-key token. The GTK
dialog itself can't be instantiated under the mocked-GTK test harness, but this
module-level helper is pure and directly testable.
"""

import pytest

from vocalinux.ui.settings_dialog import _gdk_keyname_to_token


@pytest.mark.parametrize(
    "name,expected",
    [
        ("r", "r"),
        ("A", "a"),  # capture may report a shifted/upper name
        ("5", "5"),
        ("F5", "f5"),
        ("f12", "f12"),
        ("space", "space"),
        ("Return", "enter"),
        ("Escape", "esc"),
        ("Page_Up", "pageup"),
        ("comma", "comma"),
        ("bracketleft", "leftbracket"),
    ],
)
def test_maps_known_keys(name, expected):
    assert _gdk_keyname_to_token(name) == expected


@pytest.mark.parametrize("name", ["Control_L", "Alt_R", "Shift_L", "Super_L", "", None, "F25"])
def test_rejects_modifiers_and_unknown(name):
    # Modifiers, empty/None, and out-of-range function keys are not main keys.
    assert _gdk_keyname_to_token(name) is None
