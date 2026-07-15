"""Tests for layout-aware shortcut main-key resolution (issue #513).

Capture stores character tokens (GDK keyval "a"); Wayland/evdev previously
mapped letters to fixed US KEY_* positions. These tests drive the real shipped
helpers with an AZERTY (or XKB-built) map so Alt+A resolves to the physical key
that types A, not US KEY_A.
"""

from __future__ import annotations

import threading
import types

import pytest

from vocalinux.ui.keyboard_backends.layout_key_map import (
    build_char_to_evdev_map,
    resolve_token_to_evdev_code,
)

evdev_backend = pytest.importorskip("vocalinux.ui.keyboard_backends.evdev_backend")


# French AZERTY (base) letter positions as Linux/evdev keycodes.
# Built from XKB layout=fr level-0: character "a" is on KEY_Q (16), "q" on KEY_A (30).
# Values match libxkbcommon / kernel input codes.
AZERTY_FR_LETTER_TO_EVDEV = {
    "a": 16,  # KEY_Q
    "z": 17,  # KEY_W
    "e": 18,  # KEY_E
    "r": 19,  # KEY_R
    "t": 20,  # KEY_T
    "y": 21,  # KEY_Y
    "u": 22,  # KEY_U
    "i": 23,  # KEY_I
    "o": 24,  # KEY_O
    "p": 25,  # KEY_P
    "q": 30,  # KEY_A
    "s": 31,  # KEY_S
    "d": 32,  # KEY_D
    "f": 33,  # KEY_F
    "g": 34,  # KEY_G
    "h": 35,  # KEY_H
    "j": 36,  # KEY_J
    "k": 37,  # KEY_K
    "l": 38,  # KEY_L
    "m": 39,  # KEY_SEMICOLON (AZERTY M position)
    "w": 44,  # KEY_Z
    "x": 45,  # KEY_X
    "c": 46,  # KEY_C
    "v": 47,  # KEY_V
    "b": 48,  # KEY_B
    "n": 49,  # KEY_N
}


@pytest.mark.skipif(not evdev_backend.EVDEV_AVAILABLE, reason="evdev not available")
class TestResolveTokenToEvdevCode:
    def test_us_fallback_letter_is_key_named(self):
        from evdev import ecodes

        code = resolve_token_to_evdev_code(
            "a",
            evdev_backend._NAMED_EVDEV_KEYS,
            ecodes,
            char_to_evdev=None,
        )
        assert code == ecodes.KEY_A

    def test_azerty_letter_a_is_key_q_not_key_a(self):
        from evdev import ecodes

        code = resolve_token_to_evdev_code(
            "a",
            evdev_backend._NAMED_EVDEV_KEYS,
            ecodes,
            char_to_evdev=AZERTY_FR_LETTER_TO_EVDEV,
        )
        assert code == AZERTY_FR_LETTER_TO_EVDEV["a"]
        assert code == ecodes.KEY_Q
        assert code != ecodes.KEY_A

    def test_azerty_letter_q_is_key_a(self):
        from evdev import ecodes

        code = resolve_token_to_evdev_code(
            "q",
            evdev_backend._NAMED_EVDEV_KEYS,
            ecodes,
            char_to_evdev=AZERTY_FR_LETTER_TO_EVDEV,
        )
        assert code == ecodes.KEY_A

    def test_named_keys_ignore_layout_map(self):
        from evdev import ecodes

        code = resolve_token_to_evdev_code(
            "space",
            evdev_backend._NAMED_EVDEV_KEYS,
            ecodes,
            char_to_evdev=AZERTY_FR_LETTER_TO_EVDEV,
        )
        assert code == ecodes.KEY_SPACE

    def test_function_keys_ignore_layout_map(self):
        from evdev import ecodes

        code = resolve_token_to_evdev_code(
            "f5",
            evdev_backend._NAMED_EVDEV_KEYS,
            ecodes,
            char_to_evdev=AZERTY_FR_LETTER_TO_EVDEV,
        )
        assert code == ecodes.KEY_F5


@pytest.mark.skipif(not evdev_backend.EVDEV_AVAILABLE, reason="evdev not available")
class TestEvdevCodeForKeyLayoutAware:
    def test_explicit_azerty_map_for_token_a(self):
        from evdev import ecodes

        # Stored shortcut token "a" (as settings capture would store Alt+A)
        # must resolve to KEY_Q under AZERTY, not KEY_A.
        code = evdev_backend.evdev_code_for_key("a", char_to_evdev=AZERTY_FR_LETTER_TO_EVDEV)
        assert code == ecodes.KEY_Q
        assert code != ecodes.KEY_A

    def test_use_active_layout_false_keeps_us_key_a(self):
        from evdev import ecodes

        code = evdev_backend.evdev_code_for_key("a", use_active_layout=False)
        assert code == ecodes.KEY_A

    def test_us_qwerty_r_unchanged_with_azerty_map(self):
        from evdev import ecodes

        # R is in the same physical place on AZERTY and QWERTY.
        assert (
            evdev_backend.evdev_code_for_key("r", char_to_evdev=AZERTY_FR_LETTER_TO_EVDEV)
            == ecodes.KEY_R
        )


@pytest.mark.skipif(not evdev_backend.EVDEV_AVAILABLE, reason="evdev not available")
class TestEvdevComboAzertyAltA:
    """Shipped combo path: stored alt+a + AZERTY map fires on physical KEY_Q."""

    def _event(self, code, value):
        return types.SimpleNamespace(code=code, value=value, type=1)

    def _backend_with_azerty(self, monkeypatch, shortcut="alt+a", mode="toggle"):
        """Build a real EvdevKeyboardBackend that resolves letters via AZERTY.

        Only layout detection is replaced; ``evdev_code_for_key`` /
        ``_resolve_combo_targets`` / combo matching stay on the shipped path.
        """
        monkeypatch.setattr(
            evdev_backend,
            "get_active_char_to_evdev_map",
            lambda: AZERTY_FR_LETTER_TO_EVDEV,
        )
        return evdev_backend.EvdevKeyboardBackend(shortcut=shortcut, mode=mode)

    def test_resolve_combo_targets_maps_a_to_key_q(self, monkeypatch):
        from evdev import ecodes

        backend = self._backend_with_azerty(monkeypatch, "alt+a")
        assert backend._combo_main_code == ecodes.KEY_Q
        assert backend._combo_main_code != ecodes.KEY_A

    def test_alt_a_fires_on_physical_azerty_a_key(self, monkeypatch):
        from evdev import ecodes

        from vocalinux.ui.keyboard_backends.evdev_backend import KEY_LEFTALT

        # Config stays character-semantic: "alt+a" (settings capture / #513).
        backend = self._backend_with_azerty(monkeypatch, "alt+a", "toggle")
        fired = threading.Event()
        backend.register_toggle_callback(fired.set)

        # Physical AZERTY "A" key is KEY_Q; with Alt held this must trigger.
        backend._handle_key_event(self._event(KEY_LEFTALT, 1), None)
        backend._handle_key_event(self._event(ecodes.KEY_Q, 1), None)
        assert fired.wait(1.0)

    def test_alt_a_does_not_fire_on_us_key_a_under_azerty(self, monkeypatch):
        from evdev import ecodes

        from vocalinux.ui.keyboard_backends.evdev_backend import KEY_LEFTALT

        backend = self._backend_with_azerty(monkeypatch, "alt+a", "toggle")
        fired = threading.Event()
        backend.register_toggle_callback(fired.set)

        # KEY_A is the key labeled Q on AZERTY; must NOT fire for stored alt+a.
        backend._handle_key_event(self._event(KEY_LEFTALT, 1), None)
        backend._handle_key_event(self._event(ecodes.KEY_A, 1), None)
        assert not fired.wait(0.2)


class TestBuildCharMapFromXkb:
    def test_french_azerty_a_maps_to_key_q(self):
        char_map = build_char_to_evdev_map("fr")
        if char_map is None:
            pytest.skip("libxkbcommon or XKB data not available")
        from evdev import ecodes

        assert char_map["a"] == ecodes.KEY_Q
        assert char_map["q"] == ecodes.KEY_A
        # Sanity: R stays put.
        assert char_map["r"] == ecodes.KEY_R

    def test_us_layout_letters_match_key_names(self):
        char_map = build_char_to_evdev_map("us")
        if char_map is None:
            pytest.skip("libxkbcommon or XKB data not available")
        from evdev import ecodes

        assert char_map["a"] == ecodes.KEY_A
        assert char_map["q"] == ecodes.KEY_Q
