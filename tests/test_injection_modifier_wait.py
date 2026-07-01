"""Tests for deferring Wayland injection until shortcut modifiers are released.

Regression coverage for intermittent "nothing pasted" failures: when a
modifier-based toggle/PTT shortcut (e.g. Alt+R) is still held as injection
fires, the simulated Ctrl+V becomes Ctrl+Alt+V and nothing pastes.
"""

from unittest.mock import MagicMock, patch

from vocalinux.text_injection.text_injector import TextInjector


def _bare_injector():
    """A TextInjector instance without running the heavy __init__."""
    return TextInjector.__new__(TextInjector)


class TestWaitForModifiersReleased:
    def test_returns_immediately_when_no_modifier_held(self):
        inj = _bare_injector()
        with patch.object(inj, "_held_modifier_keycodes", return_value=set()) as held, patch(
            "time.sleep"
        ) as sleep:
            inj._wait_for_modifiers_released()
        assert held.call_count == 1  # checked once, cleared, no polling loop
        sleep.assert_not_called()

    def test_waits_until_modifier_released(self):
        inj = _bare_injector()
        # Held for the first two checks, then released.
        states = [{56}, {56}, set()]
        with patch.object(
            inj, "_held_modifier_keycodes", side_effect=states
        ) as held, patch("time.sleep"):
            inj._wait_for_modifiers_released()
        assert held.call_count == 3

    def test_disabled_via_env(self, monkeypatch):
        inj = _bare_injector()
        monkeypatch.setenv("VOCALINUX_INJECT_MODIFIER_WAIT", "0")
        with patch.object(inj, "_held_modifier_keycodes") as held:
            inj._wait_for_modifiers_released()
        held.assert_not_called()

    def test_gives_up_after_timeout(self, monkeypatch):
        inj = _bare_injector()
        monkeypatch.setenv("VOCALINUX_INJECT_MODIFIER_WAIT", "0.05")
        # Always held -> must still return (best-effort) rather than hang.
        with patch.object(inj, "_held_modifier_keycodes", return_value={56}), patch(
            "time.sleep"
        ):
            inj._wait_for_modifiers_released()  # should return within the timeout


class TestWaylandInjectionWaitsFirst:
    def test_clipboard_paste_path_waits_before_pasting(self):
        inj = _bare_injector()
        inj.wayland_tool = "ydotool"
        calls = []
        with patch.object(
            inj, "_wait_for_modifiers_released", side_effect=lambda: calls.append("wait")
        ), patch.object(
            inj,
            "_inject_via_clipboard_paste",
            side_effect=lambda text: calls.append("paste") or True,
        ):
            inj._inject_with_wayland_tool("hello")
        # The modifier wait must happen before the paste chord is sent.
        assert calls == ["wait", "paste"]

    def test_wtype_path_waits_before_typing(self):
        inj = _bare_injector()
        inj.wayland_tool = "wtype"
        calls = []
        with patch.object(
            inj, "_wait_for_modifiers_released", side_effect=lambda: calls.append("wait")
        ), patch("subprocess.run", side_effect=lambda *a, **k: calls.append("run") or MagicMock()):
            inj._inject_with_wayland_tool("hello")
        assert calls[0] == "wait"
        assert "run" in calls
