"""Regression test: switching shortcut mode must use the saved shortcut.

A custom shortcut (e.g. "alt+r") is stored in config but leaves the preset
combo pointing at a default/previous preset. When the user toggles between
Toggle and Push-to-Talk, the live listener must be restarted on the *saved*
shortcut, not the stale preset shown in the combo. (Codex P2 on PR #493.)

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
