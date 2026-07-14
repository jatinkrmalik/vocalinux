"""Regression test: switching shortcut mode must use the saved shortcut.

Config is the source of truth for both presets and custom shortcuts. When the
user toggles between Toggle and Push-to-Talk, the live listener must restart on
the *saved* shortcut (not a stale combo selection). (Codex P2 on PR #493.)

The settings dialog can't be instantiated under the mocked-GTK test harness, so
(like test_settings_shortcuts.py) this asserts against the source of the
_on_shortcut_mode_changed method.
"""

import inspect
import re

from vocalinux.ui import settings_dialog


def _method_source(name: str) -> str:
    src = inspect.getsource(settings_dialog)
    # Grab from `def <name>(` up to the next method definition.
    match = re.search(rf"\n    def {name}\(.*?(?=\n    def )", src, re.DOTALL)
    assert match, f"could not locate method {name}"
    return match.group(0)


def test_mode_change_reads_saved_shortcut_from_config():
    body = _method_source("_on_shortcut_mode_changed")
    assert "self.config_manager.get_str(" in body
    assert '"toggle_recognition"' in body


def test_mode_change_does_not_use_stale_preset_combo():
    body = _method_source("_on_shortcut_mode_changed")
    # The stale preset combo must not drive the live mode-change apply.
    assert "self.shortcut_combo.get_active_id()" not in body


def test_mode_ui_toggle_is_combo_aware():
    # A combo (alt+r) toggles on a single press, so the toggle label must branch
    # on whether the shortcut is a combo rather than always saying "Double-tap".
    body = _method_source("_update_shortcut_ui_for_mode")
    assert "is_combo" in body
    assert "get_shortcut_display_name(" in body
    assert "self.config_manager.get_str(" in body


def test_mode_ui_double_tap_text_is_guarded_for_non_combo():
    body = _method_source("_update_shortcut_ui_for_mode")
    # The "Double-tap" wording must sit inside the non-combo branch, not fire
    # unconditionally for every toggle shortcut.
    idx_if = body.find("if is_combo:")
    # The user-facing "Double-tap this key" subtitle (not the example in a
    # comment) must sit inside the non-combo branch.
    idx_double_tap = body.find("Double-tap this key")
    assert idx_if != -1
    assert idx_double_tap > idx_if


def test_sync_ui_mutually_excludes_preset_and_custom():
    """Custom and preset UI state must not both look active at once."""
    body = _method_source("_sync_shortcut_selection_ui")
    assert '_set_shortcut_combo_active_id("__custom__")' in body
    assert 'self.custom_shortcut_entry.set_text("")' in body
    assert "self._is_preset_shortcut(shortcut)" in body


def test_preset_change_clears_custom_entry():
    body = _method_source("_on_shortcut_changed")
    # After a real preset id is chosen, clear the custom entry so users are not
    # left thinking the old custom combo is still active.
    assert 'self.custom_shortcut_entry.set_text("")' in body
    assert 'shortcut_id == "__custom__"' in body
