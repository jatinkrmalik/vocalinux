"""
Layout-aware mapping from character key tokens to Linux/evdev keycodes.

Settings capture stores character-semantic tokens (GDK keyval names, e.g. "a").
evdev listens for physical KEY_* codes. On non-US layouts those diverge: French
AZERTY types "a" on KEY_Q. This module builds char→evdev maps from XKB (via
libxkbcommon) so combo matching uses the same physical key the user pressed.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from ctypes import CDLL, POINTER, Structure, byref, c_char_p, c_int, c_uint32, c_void_p
from functools import lru_cache
from typing import Mapping, Optional, Tuple

logger = logging.getLogger(__name__)

# X11/xkbcommon keycodes are offset from Linux/evdev codes by this amount.
_XKB_EVDEV_OFFSET = 8

# Lazy libxkbcommon handle; None means "not tried", False means "unavailable".
_xkb_lib: object = None


class _XkbRuleNames(Structure):
    _fields_ = [
        ("rules", c_char_p),
        ("model", c_char_p),
        ("layout", c_char_p),
        ("variant", c_char_p),
        ("options", c_char_p),
    ]


def _load_xkbcommon():
    """Return a CDLL for libxkbcommon, or False if unavailable."""
    global _xkb_lib
    if _xkb_lib is not None:
        return _xkb_lib
    try:
        lib = CDLL("libxkbcommon.so.0")
        lib.xkb_context_new.argtypes = [c_int]
        lib.xkb_context_new.restype = c_void_p
        lib.xkb_keymap_new_from_names.argtypes = [c_void_p, POINTER(_XkbRuleNames), c_int]
        lib.xkb_keymap_new_from_names.restype = c_void_p
        lib.xkb_keymap_min_keycode.argtypes = [c_void_p]
        lib.xkb_keymap_min_keycode.restype = c_uint32
        lib.xkb_keymap_max_keycode.argtypes = [c_void_p]
        lib.xkb_keymap_max_keycode.restype = c_uint32
        lib.xkb_keymap_num_layouts_for_key.argtypes = [c_void_p, c_uint32]
        lib.xkb_keymap_num_layouts_for_key.restype = c_uint32
        lib.xkb_keymap_num_levels_for_key.argtypes = [c_void_p, c_uint32, c_uint32]
        lib.xkb_keymap_num_levels_for_key.restype = c_uint32
        lib.xkb_keymap_key_get_syms_by_level.argtypes = [
            c_void_p,
            c_uint32,
            c_uint32,
            c_uint32,
            POINTER(POINTER(c_uint32)),
        ]
        lib.xkb_keymap_key_get_syms_by_level.restype = c_int
        lib.xkb_keysym_to_utf32.argtypes = [c_uint32]
        lib.xkb_keysym_to_utf32.restype = c_uint32
        lib.xkb_keymap_unref.argtypes = [c_void_p]
        lib.xkb_context_unref.argtypes = [c_void_p]
        _xkb_lib = lib
    except OSError as e:
        logger.debug("libxkbcommon not available: %s", e)
        _xkb_lib = False
    return _xkb_lib


def build_char_to_evdev_map(
    layout: str,
    variant: str = "",
) -> Optional[dict[str, int]]:
    """
    Build a mapping of lowercase characters → Linux/evdev keycodes for an XKB layout.

    Uses unshifted (level 0) keysyms on the first layout group. First key that
    produces a given character wins (matches typical "base letter" positions).

    Returns:
        dict mapping single-character strings to evdev codes, or None if the
        layout cannot be loaded (missing libxkbcommon / invalid layout).
    """
    if not layout:
        return None
    lib = _load_xkbcommon()
    if not lib:
        return None

    ctx = lib.xkb_context_new(0)
    if not ctx:
        return None

    names = _XkbRuleNames(
        None,
        None,
        layout.encode("utf-8"),
        variant.encode("utf-8") if variant else None,
        None,
    )
    keymap = lib.xkb_keymap_new_from_names(ctx, byref(names), 0)
    if not keymap:
        lib.xkb_context_unref(ctx)
        logger.debug("Could not load XKB keymap for layout=%r variant=%r", layout, variant)
        return None

    char_map: dict[str, int] = {}
    try:
        min_kc = lib.xkb_keymap_min_keycode(keymap)
        max_kc = lib.xkb_keymap_max_keycode(keymap)
        for xkb_code in range(min_kc, max_kc + 1):
            if lib.xkb_keymap_num_layouts_for_key(keymap, xkb_code) == 0:
                continue
            if lib.xkb_keymap_num_levels_for_key(keymap, xkb_code, 0) == 0:
                continue
            syms_ptr = POINTER(c_uint32)()
            n_syms = lib.xkb_keymap_key_get_syms_by_level(keymap, xkb_code, 0, 0, byref(syms_ptr))
            if n_syms <= 0:
                continue
            utf32 = lib.xkb_keysym_to_utf32(syms_ptr[0])
            # Printable BMP/plane-0 only; skip controls and non-characters.
            if utf32 < 32 or utf32 > 0x10FFFF:
                continue
            try:
                ch = chr(utf32)
            except ValueError:
                continue
            if len(ch) != 1:
                continue
            # Prefer lowercase letter slots; keep first mapping for each char.
            key = ch.lower() if ch.isalpha() else ch
            if key not in char_map:
                char_map[key] = int(xkb_code) - _XKB_EVDEV_OFFSET
    finally:
        lib.xkb_keymap_unref(keymap)
        lib.xkb_context_unref(ctx)

    return char_map or None


def detect_active_xkb_layout() -> Tuple[str, str]:
    """
    Best-effort detection of the active XKB layout and variant.

    Order: GNOME gsettings (works on Wayland), setxkbmap (X11), localectl.
    Returns ("", "") when nothing useful is found.
    """
    layout, variant = _detect_gnome_layout()
    if layout:
        return layout, variant

    layout, variant = _detect_setxkbmap_layout()
    if layout:
        return layout, variant

    layout, variant = _detect_localectl_layout()
    if layout:
        return layout, variant

    return "", ""


def _detect_gnome_layout() -> Tuple[str, str]:
    """Read current source from org.gnome.desktop.input-sources when available."""
    try:
        # Prefer mru-sources[0] (most recently used = current) over sources[0].
        for key in ("mru-sources", "sources"):
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.input-sources", key],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                continue
            parsed = _parse_gnome_sources(result.stdout.strip())
            if parsed:
                return parsed
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug("gsettings layout query failed: %s", e)
    return "", ""


def _parse_gnome_sources(raw: str) -> Optional[Tuple[str, str]]:
    """
    Parse gsettings sources output like:
      [('xkb', 'us'), ('xkb', 'fr')]
      [('xkb', 'fr+azerty'), ('ibus', 'anthy')]
    """
    # First xkb entry wins (current / first configured).
    match = re.search(r"\(\s*'xkb'\s*,\s*'([^']+)'\s*\)", raw)
    if not match:
        return None
    source_id = match.group(1)
    layout, _, variant = source_id.partition("+")
    return layout, variant


def _detect_setxkbmap_layout() -> Tuple[str, str]:
    if os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("DISPLAY"):
        return "", ""
    try:
        result = subprocess.run(
            ["setxkbmap", "-query"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode != 0:
            return "", ""
        layout, variant = "", ""
        for line in result.stdout.splitlines():
            if line.startswith("layout:"):
                # May be comma-separated multi-layout; take the first.
                layout = line.split(":", 1)[1].strip().split(",")[0].strip()
            elif line.startswith("variant:"):
                variant = line.split(":", 1)[1].strip().split(",")[0].strip()
        return layout, variant
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug("setxkbmap layout query failed: %s", e)
        return "", ""


def _detect_localectl_layout() -> Tuple[str, str]:
    try:
        result = subprocess.run(
            ["localectl", "status"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode != 0:
            return "", ""
        layout, variant = "", ""
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("X11 Layout:"):
                layout = stripped.split(":", 1)[1].strip().split(",")[0].strip()
            elif stripped.startswith("X11 Variant:"):
                variant = stripped.split(":", 1)[1].strip().split(",")[0].strip()
                if variant in ("(unset)", "n/a", ""):
                    variant = ""
        return layout, variant
    except (OSError, subprocess.SubprocessError) as e:
        logger.debug("localectl layout query failed: %s", e)
        return "", ""


@lru_cache(maxsize=1)
def get_active_char_to_evdev_map() -> Optional[Mapping[str, int]]:
    """
    Cached char→evdev map for the currently detected keyboard layout.

    Returns None for US/empty layouts (caller should use KEY_* name fallback)
    or when libxkbcommon / layout detection is unavailable.
    """
    layout, variant = detect_active_xkb_layout()
    if not layout:
        logger.debug("No XKB layout detected; using US keycode fallback for combos")
        return None
    # US QWERTY letter positions match KEY_A, KEY_Q, … — no remap needed.
    if layout == "us" and not variant:
        logger.debug("US layout active; using KEY_* name fallback for combos")
        return None
    char_map = build_char_to_evdev_map(layout, variant)
    if char_map:
        logger.info(
            "Loaded layout-aware key map for XKB layout=%s variant=%s (%d chars)",
            layout,
            variant or "(none)",
            len(char_map),
        )
    return char_map


def clear_layout_map_cache() -> None:
    """Drop the cached active layout map (tests / layout change)."""
    get_active_char_to_evdev_map.cache_clear()


def resolve_token_to_evdev_code(
    token: str,
    named_keys: Mapping[str, str],
    ecodes_module,
    char_to_evdev: Optional[Mapping[str, int]] = None,
) -> Optional[int]:
    """
    Resolve a canonical main-key token to a Linux/evdev keycode.

    Args:
        token: Canonical token (e.g. "a", "f5", "space").
        named_keys: Map of irregular tokens → ecodes attribute names.
        ecodes_module: The ``evdev.ecodes`` module (or compatible).
        char_to_evdev: Optional layout map for single-character tokens. When
            provided, letter/digit/punctuation chars are resolved from this map
            before falling back to US ``KEY_<UPPER>`` names.

    Returns:
        evdev keycode int, or None if unresolvable.
    """
    if not token or ecodes_module is None:
        return None

    name = named_keys.get(token)
    if name is not None:
        return getattr(ecodes_module, name, None)

    if len(token) == 1:
        if char_to_evdev is not None and token in char_to_evdev:
            return char_to_evdev[token]
        if token.isalnum():
            return getattr(ecodes_module, f"KEY_{token.upper()}", None)
        return None

    if re.fullmatch(r"f\d+", token):
        return getattr(ecodes_module, f"KEY_{token.upper()}", None)

    return None
