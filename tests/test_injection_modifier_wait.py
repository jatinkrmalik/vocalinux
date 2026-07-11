"""Tests for deferring Wayland injection until shortcut modifiers are released.

Regression coverage for intermittent "nothing pasted" failures: when a
modifier-based toggle/PTT shortcut (e.g. Alt+R) is still held as injection
fires, the simulated Ctrl+V becomes Ctrl+Alt+V and nothing pastes.
"""

import types
from unittest.mock import MagicMock, patch

import pytest

from vocalinux.text_injection.text_injector import TextInjector


def _bare_injector():
    """A TextInjector instance without running the heavy __init__."""
    return TextInjector.__new__(TextInjector)


def _fake_evdev(devices):
    """Build a fake ``evdev`` module for _held_modifier_keycodes tests.

    devices: list of ``(active_keys, has_ev_key, raises)`` describing each
    device that list_devices() reports.
    """
    ecodes = types.SimpleNamespace(EV_KEY=1)

    class FakeDevice:
        def __init__(self, active, has_ev_key):
            self._active = active
            self._caps = {ecodes.EV_KEY: []} if has_ev_key else {}
            self.closed = False

        def capabilities(self):
            return self._caps

        def active_keys(self):
            return self._active

        def close(self):
            self.closed = True

    paths = [f"/dev/input/event{i}" for i in range(len(devices))]
    built = {}
    for path, (active, has_ev_key, raises) in zip(paths, devices):
        built[path] = (FakeDevice(active, has_ev_key), raises)

    mod = types.ModuleType("evdev")
    mod.ecodes = ecodes
    mod.list_devices = lambda: list(paths)

    def input_device(path):
        device, raises = built[path]
        if raises:
            raise raises
        return device

    mod.InputDevice = input_device
    return mod


class TestWaitForModifiersReleased:
    def test_returns_immediately_when_no_modifier_held(self):
        inj = _bare_injector()
        with (
            patch.object(inj, "_held_modifier_keycodes", return_value=set()) as held,
            patch("time.sleep") as sleep,
        ):
            inj._wait_for_modifiers_released()
        assert held.call_count == 1  # checked once, cleared, no polling loop
        sleep.assert_not_called()

    def test_waits_until_modifier_released(self):
        inj = _bare_injector()
        # Held for the first two checks, then released.
        states = [{56}, {56}, set()]
        with (
            patch.object(inj, "_held_modifier_keycodes", side_effect=states) as held,
            patch("time.sleep"),
        ):
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
        with patch.object(inj, "_held_modifier_keycodes", return_value={56}), patch("time.sleep"):
            inj._wait_for_modifiers_released()  # should return within the timeout


class TestWaylandInjectionWaitsFirst:
    def test_clipboard_paste_path_waits_before_pasting(self):
        inj = _bare_injector()
        inj.wayland_tool = "ydotool"
        calls = []
        with (
            patch.object(
                inj, "_wait_for_modifiers_released", side_effect=lambda: calls.append("wait")
            ),
            patch.object(
                inj,
                "_inject_via_clipboard_paste",
                side_effect=lambda text: calls.append("paste") or True,
            ),
        ):
            inj._inject_with_wayland_tool("hello")
        # The modifier wait must happen before the paste chord is sent.
        assert calls == ["wait", "paste"]

    def test_wtype_path_waits_before_typing(self):
        inj = _bare_injector()
        inj.wayland_tool = "wtype"
        calls = []
        with (
            patch.object(
                inj, "_wait_for_modifiers_released", side_effect=lambda: calls.append("wait")
            ),
            patch("subprocess.run", side_effect=lambda *a, **k: calls.append("run") or MagicMock()),
        ):
            inj._inject_with_wayland_tool("hello")
        assert calls[0] == "wait"
        assert "run" in calls


class TestHeldModifierKeycodes:
    def test_returns_only_modifier_codes(self):
        inj = _bare_injector()
        # event0: Alt (56) + 'a' (30) held; event1: nothing.
        fake = _fake_evdev([([56, 30], True, None), ([], True, None)])
        with patch.dict("sys.modules", {"evdev": fake}):
            held = inj._held_modifier_keycodes()
        assert held == {56}  # 'a' (30) is not a modifier and is excluded

    def test_unions_across_devices_split_keyboard(self):
        inj = _bare_injector()
        # Left half holds Ctrl (29), right half holds Shift (42).
        fake = _fake_evdev([([29], True, None), ([42], True, None)])
        with patch.dict("sys.modules", {"evdev": fake}):
            held = inj._held_modifier_keycodes()
        assert held == {29, 42}

    def test_skips_non_keyboard_devices(self):
        inj = _bare_injector()
        # A device without EV_KEY (e.g. a mouse) must be ignored.
        fake = _fake_evdev([([56], False, None)])
        with patch.dict("sys.modules", {"evdev": fake}):
            held = inj._held_modifier_keycodes()
        assert held == set()

    def test_skips_unopenable_devices(self):
        inj = _bare_injector()
        fake = _fake_evdev([([56], True, PermissionError("denied"))])
        with patch.dict("sys.modules", {"evdev": fake}):
            held = inj._held_modifier_keycodes()
        assert held == set()

    def test_no_evdev_returns_empty(self):
        inj = _bare_injector()
        # Simulate evdev not installed.
        with patch.dict("sys.modules", {"evdev": None}):
            held = inj._held_modifier_keycodes()
        assert held == set()

    def test_wait_polls_real_reader(self, monkeypatch):
        # Exercise _wait_for_modifiers_released against the real reader: held
        # once, then clear.
        inj = _bare_injector()
        states = [_fake_evdev([([56], True, None)]), _fake_evdev([([], True, None)])]
        calls = {"n": 0}

        def held():
            mod = states[min(calls["n"], len(states) - 1)]
            calls["n"] += 1
            with patch.dict("sys.modules", {"evdev": mod}):
                return TextInjector._held_modifier_keycodes(inj)

        monkeypatch.setattr(inj, "_held_modifier_keycodes", held)
        with patch("time.sleep"):
            inj._wait_for_modifiers_released()
        assert calls["n"] >= 2


class TestHeldModifierKeycodesErrorPaths:
    def test_list_devices_failure_returns_empty(self):
        inj = _bare_injector()
        mod = types.ModuleType("evdev")
        mod.ecodes = types.SimpleNamespace(EV_KEY=1)

        def boom():
            raise RuntimeError("enumeration failed")

        mod.list_devices = boom
        with patch.dict("sys.modules", {"evdev": mod}):
            assert inj._held_modifier_keycodes() == set()

    def test_device_read_oserror_is_skipped(self):
        inj = _bare_injector()
        mod = types.ModuleType("evdev")
        mod.ecodes = types.SimpleNamespace(EV_KEY=1)

        class RaisingDevice:
            def capabilities(self):
                return {1: []}

            def active_keys(self):
                raise OSError("device went away mid-read")

            def close(self):
                pass

        mod.list_devices = lambda: ["/dev/input/event0"]
        mod.InputDevice = lambda path: RaisingDevice()
        with patch.dict("sys.modules", {"evdev": mod}):
            assert inj._held_modifier_keycodes() == set()


class TestInjectionModifierWaitSeconds:
    @pytest.mark.parametrize("raw,expected", [("2.5", 2.5), ("0", 0.0), ("0.5", 0.5)])
    def test_valid_values(self, raw, expected, monkeypatch):
        inj = _bare_injector()
        monkeypatch.setenv("VOCALINUX_INJECT_MODIFIER_WAIT", raw)
        assert inj._injection_modifier_wait_seconds() == expected

    @pytest.mark.parametrize("raw", ["inf", "-inf", "nan", "Infinity", "NaN"])
    def test_non_finite_falls_back_to_default(self, raw, monkeypatch):
        inj = _bare_injector()
        monkeypatch.setenv("VOCALINUX_INJECT_MODIFIER_WAIT", raw)
        assert inj._injection_modifier_wait_seconds() == 1.0

    def test_non_numeric_falls_back_to_default(self, monkeypatch):
        inj = _bare_injector()
        monkeypatch.setenv("VOCALINUX_INJECT_MODIFIER_WAIT", "abc")
        assert inj._injection_modifier_wait_seconds() == 1.0

    def test_unset_uses_default(self, monkeypatch):
        inj = _bare_injector()
        monkeypatch.delenv("VOCALINUX_INJECT_MODIFIER_WAIT", raising=False)
        assert inj._injection_modifier_wait_seconds() == 1.0

    def test_inf_does_not_block_forever(self, monkeypatch):
        # Regression: with 'inf', the wait must still terminate (bounded by the
        # finite default) instead of looping forever while a modifier is held.
        inj = _bare_injector()
        monkeypatch.setenv("VOCALINUX_INJECT_MODIFIER_WAIT", "inf")
        # Simulate the clock crossing the finite default deadline in a few steps.
        clock = iter([0.0, 0.5, 1.5])
        monkeypatch.setattr("time.monotonic", lambda: next(clock, 2.0))
        with patch.object(inj, "_held_modifier_keycodes", return_value={56}), patch("time.sleep"):
            inj._wait_for_modifiers_released()  # must return, not hang
