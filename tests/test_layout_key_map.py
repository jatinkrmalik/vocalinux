"""Layout-aware combo main-key resolution (issue #513)."""

from __future__ import annotations

import threading
import types

import pytest

from vocalinux.ui.keyboard_backends.layout_key_map import build_char_to_evdev_map

evdev_backend = pytest.importorskip("vocalinux.ui.keyboard_backends.evdev_backend")

# Minimal AZERTY fr positions used by #513 (a/q swap; r unchanged).
AZERTY = {"a": 16, "q": 30, "r": 19}  # KEY_Q, KEY_A, KEY_R


@pytest.mark.skipif(not evdev_backend.EVDEV_AVAILABLE, reason="evdev not available")
class TestAzertyCombo:
    def _event(self, code, value):
        return types.SimpleNamespace(code=code, value=value, type=1)

    def _backend(self, monkeypatch, shortcut="alt+a"):
        monkeypatch.setattr(evdev_backend, "get_active_char_to_evdev_map", lambda: AZERTY)
        return evdev_backend.EvdevKeyboardBackend(shortcut=shortcut, mode="toggle")

    def test_alt_a_resolves_to_key_q(self, monkeypatch):
        from evdev import ecodes

        backend = self._backend(monkeypatch)
        assert backend._combo_main_code == ecodes.KEY_Q
        assert backend._combo_main_code != ecodes.KEY_A

    def test_alt_a_fires_on_physical_a(self, monkeypatch):
        from evdev import ecodes

        from vocalinux.ui.keyboard_backends.evdev_backend import KEY_LEFTALT

        backend = self._backend(monkeypatch)
        fired = threading.Event()
        backend.register_toggle_callback(fired.set)
        backend._handle_key_event(self._event(KEY_LEFTALT, 1), None)
        backend._handle_key_event(self._event(ecodes.KEY_Q, 1), None)
        assert fired.wait(1.0)

    def test_alt_a_does_not_fire_on_key_a(self, monkeypatch):
        from evdev import ecodes

        from vocalinux.ui.keyboard_backends.evdev_backend import KEY_LEFTALT

        backend = self._backend(monkeypatch)
        fired = threading.Event()
        backend.register_toggle_callback(fired.set)
        backend._handle_key_event(self._event(KEY_LEFTALT, 1), None)
        backend._handle_key_event(self._event(ecodes.KEY_A, 1), None)
        assert not fired.wait(0.2)


def test_xkb_fr_a_is_key_q():
    char_map = build_char_to_evdev_map("fr")
    if char_map is None:
        pytest.skip("libxkbcommon or XKB data not available")
    from evdev import ecodes

    assert char_map["a"] == ecodes.KEY_Q
    assert char_map["q"] == ecodes.KEY_A
