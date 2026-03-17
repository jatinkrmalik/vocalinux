"""
Tests for keyboard backends __init__.py module.

This module tests:
- DesktopEnvironment.detect() for all cases (wayland, x11, unknown, fallback env vars)
- create_backend() for all branches (preferred evdev, preferred pynput, unknown preferred,
  wayland auto, x11 auto, no backends)
- Mocking EVDEV_AVAILABLE, PYNPUT_AVAILABLE, and backend classes
"""

import os
import pytest
from unittest.mock import MagicMock, patch, Mock
import sys

# Import the module under test
import vocalinux.ui.keyboard_backends as kb_module
from vocalinux.ui.keyboard_backends import (
    DesktopEnvironment,
    create_backend,
    EVDEV_AVAILABLE,
    PYNPUT_AVAILABLE,
)


class TestDesktopEnvironmentDetect:
    """Test DesktopEnvironment.detect() method."""

    def test_detect_xdg_session_type_wayland(self):
        """Test detection of Wayland via XDG_SESSION_TYPE."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=False):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.WAYLAND

    def test_detect_xdg_session_type_x11(self):
        """Test detection of X11 via XDG_SESSION_TYPE."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=False):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.X11

    def test_detect_xdg_session_type_case_insensitive(self):
        """Test that XDG_SESSION_TYPE detection is case-insensitive."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "WAYLAND"}, clear=False):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.WAYLAND

    def test_detect_xdg_session_type_mixed_case(self):
        """Test that XDG_SESSION_TYPE detection handles mixed case."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "Wayland"}, clear=False):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.WAYLAND

    def test_detect_wayland_display_env_var(self):
        """Test detection of Wayland via WAYLAND_DISPLAY env var (fallback)."""
        env = {
            "WAYLAND_DISPLAY": "wayland-0",
        }
        with patch.dict(os.environ, env, clear=True):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.WAYLAND

    def test_detect_display_env_var(self):
        """Test detection of X11 via DISPLAY env var (fallback)."""
        env = {
            "DISPLAY": ":0",
        }
        with patch.dict(os.environ, env, clear=True):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.X11

    def test_detect_wayland_display_priority_over_display(self):
        """Test that WAYLAND_DISPLAY takes priority over DISPLAY."""
        env = {
            "WAYLAND_DISPLAY": "wayland-0",
            "DISPLAY": ":0",
        }
        with patch.dict(os.environ, env, clear=True):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.WAYLAND

    def test_detect_xdg_session_type_priority_over_env_vars(self):
        """Test that XDG_SESSION_TYPE takes priority over WAYLAND_DISPLAY/DISPLAY."""
        env = {
            "XDG_SESSION_TYPE": "x11",
            "WAYLAND_DISPLAY": "wayland-0",
        }
        with patch.dict(os.environ, env, clear=True):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.X11

    def test_detect_unknown_no_env_vars(self):
        """Test detection returns unknown when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.UNKNOWN

    def test_detect_unknown_xdg_session_type_unknown(self):
        """Test detection returns unknown for unknown XDG_SESSION_TYPE."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "unknown_session"}, clear=True):
            result = DesktopEnvironment.detect()
            assert result == DesktopEnvironment.UNKNOWN

    def test_constants_defined(self):
        """Test that DesktopEnvironment constants are defined."""
        assert DesktopEnvironment.X11 == "x11"
        assert DesktopEnvironment.WAYLAND == "wayland"
        assert DesktopEnvironment.UNKNOWN == "unknown"


class TestCreateBackendPreferred:
    """Test create_backend() with preferred backend specified."""

    def test_create_backend_preferred_evdev_available_and_usable(self):
        """Test preferred evdev backend when available and usable."""
        mock_evdev_backend = MagicMock()
        mock_evdev_backend.is_available.return_value = True

        with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True):
            with patch(
                "vocalinux.ui.keyboard_backends.EvdevKeyboardBackend",
                return_value=mock_evdev_backend,
            ):
                result = create_backend(preferred_backend="evdev")
                assert result == mock_evdev_backend
                mock_evdev_backend.is_available.assert_called_once()

    def test_create_backend_preferred_evdev_not_available(self):
        """Test preferred evdev backend when module not available."""
        with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
                result = create_backend(preferred_backend="evdev")
                assert result is None

    def test_create_backend_preferred_evdev_available_but_not_usable(self):
        """Test preferred evdev backend when available but not usable."""
        mock_evdev_backend = MagicMock()
        mock_evdev_backend.is_available.return_value = False
        mock_evdev_backend.get_permission_hint.return_value = "Permission denied"

        with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True):
            with patch(
                "vocalinux.ui.keyboard_backends.EvdevKeyboardBackend",
                return_value=mock_evdev_backend,
            ):
                with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
                    result = create_backend(preferred_backend="evdev")
                    assert result is None

    def test_create_backend_preferred_pynput_available(self):
        """Test preferred pynput backend when available."""
        mock_pynput_backend = MagicMock()

        with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True):
            with patch(
                "vocalinux.ui.keyboard_backends.PynputKeyboardBackend",
                return_value=mock_pynput_backend,
            ):
                result = create_backend(preferred_backend="pynput")
                assert result == mock_pynput_backend

    def test_create_backend_preferred_pynput_not_available(self):
        """Test preferred pynput backend when not available."""
        with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
            with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False):
                result = create_backend(preferred_backend="pynput")
                assert result is None

    def test_create_backend_preferred_unknown_backend(self):
        """Test create_backend with unknown preferred backend."""
        with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
                result = create_backend(preferred_backend="unknown_backend")
                assert result is None

    def test_create_backend_preferred_with_custom_shortcut(self):
        """Test that shortcut parameter is passed to backend."""
        mock_pynput_backend = MagicMock()

        with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True):
            with patch(
                "vocalinux.ui.keyboard_backends.PynputKeyboardBackend",
                return_value=mock_pynput_backend,
            ) as mock_constructor:
                result = create_backend(
                    preferred_backend="pynput", shortcut="alt+alt", mode="push_to_talk"
                )
                mock_constructor.assert_called_once_with(shortcut="alt+alt", mode="push_to_talk")
                assert result == mock_pynput_backend

    def test_create_backend_preferred_with_custom_mode(self):
        """Test that mode parameter is passed to backend."""
        mock_evdev_backend = MagicMock()
        mock_evdev_backend.is_available.return_value = True

        with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True):
            with patch(
                "vocalinux.ui.keyboard_backends.EvdevKeyboardBackend",
                return_value=mock_evdev_backend,
            ) as mock_constructor:
                result = create_backend(preferred_backend="evdev", mode="push_to_talk")
                mock_constructor.assert_called_once()
                call_kwargs = mock_constructor.call_args[1]
                assert call_kwargs["mode"] == "push_to_talk"


class TestCreateBackendAutoDetect:
    """Test create_backend() with auto-detection based on desktop environment."""

    def test_create_backend_wayland_evdev_available_and_usable(self):
        """Test Wayland environment auto-selects evdev when available."""
        mock_evdev_backend = MagicMock()
        mock_evdev_backend.is_available.return_value = True

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True):
                with patch(
                    "vocalinux.ui.keyboard_backends.EvdevKeyboardBackend",
                    return_value=mock_evdev_backend,
                ):
                    with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
                        result = create_backend()
                        assert result == mock_evdev_backend

    def test_create_backend_wayland_evdev_not_available(self):
        """Test Wayland returns None when evdev not available."""
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False):
                with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
                    result = create_backend()
                    assert result is None

    def test_create_backend_wayland_evdev_available_but_not_usable(self):
        """Test Wayland returns None when evdev not usable."""
        mock_evdev_backend = MagicMock()
        mock_evdev_backend.is_available.return_value = False
        mock_evdev_backend.get_permission_hint.return_value = "Permission denied"

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True):
                with patch(
                    "vocalinux.ui.keyboard_backends.EvdevKeyboardBackend",
                    return_value=mock_evdev_backend,
                ):
                    result = create_backend()
                    assert result is None

    def test_create_backend_x11_pynput_available(self):
        """Test X11 environment auto-selects pynput."""
        mock_pynput_backend = MagicMock()

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True):
                with patch(
                    "vocalinux.ui.keyboard_backends.PynputKeyboardBackend",
                    return_value=mock_pynput_backend,
                ):
                    result = create_backend()
                    assert result == mock_pynput_backend

    def test_create_backend_x11_pynput_not_available_evdev_available(self):
        """Test X11 falls back to evdev when pynput not available."""
        mock_evdev_backend = MagicMock()
        mock_evdev_backend.is_available.return_value = True

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
                with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True):
                    with patch(
                        "vocalinux.ui.keyboard_backends.EvdevKeyboardBackend",
                        return_value=mock_evdev_backend,
                    ):
                        result = create_backend()
                        assert result == mock_evdev_backend

    def test_create_backend_unknown_env_pynput_available(self):
        """Test unknown environment defaults to pynput."""
        mock_pynput_backend = MagicMock()

        with patch.dict(os.environ, {}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True):
                with patch(
                    "vocalinux.ui.keyboard_backends.PynputKeyboardBackend",
                    return_value=mock_pynput_backend,
                ):
                    result = create_backend()
                    assert result == mock_pynput_backend

    def test_create_backend_unknown_env_no_backends(self):
        """Test unknown environment returns None when no backends available."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
                with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False):
                    result = create_backend()
                    assert result is None

    def test_create_backend_no_backends_available(self):
        """Test create_backend returns None when no backends available at all."""
        with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
            with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False):
                result = create_backend()
                assert result is None

    def test_create_backend_with_custom_parameters(self):
        """Test that custom parameters are passed to auto-selected backend."""
        mock_pynput_backend = MagicMock()

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True):
                with patch(
                    "vocalinux.ui.keyboard_backends.PynputKeyboardBackend",
                    return_value=mock_pynput_backend,
                ) as mock_constructor:
                    result = create_backend(shortcut="alt+alt", mode="push_to_talk")
                    mock_constructor.assert_called_once_with(
                        shortcut="alt+alt", mode="push_to_talk"
                    )

    def test_create_backend_default_parameters(self):
        """Test that default parameters are used when not specified."""
        mock_pynput_backend = MagicMock()

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True):
                with patch(
                    "vocalinux.ui.keyboard_backends.PynputKeyboardBackend",
                    return_value=mock_pynput_backend,
                ) as mock_constructor:
                    result = create_backend()
                    # Check that the constructor was called with some default shortcut/mode
                    mock_constructor.assert_called_once()
                    call_kwargs = mock_constructor.call_args[1]
                    # Shortcut and mode should be passed as defaults
                    assert "shortcut" in call_kwargs
                    assert "mode" in call_kwargs


class TestCreateBackendFallback:
    """Test create_backend() fallback scenarios."""

    def test_create_backend_pynput_not_available_evdev_available_not_usable(self):
        """Test fallback to evdev when pynput unavailable and evdev not usable."""
        mock_evdev_backend = MagicMock()
        mock_evdev_backend.is_available.return_value = False
        mock_evdev_backend.get_permission_hint.return_value = "Permission denied"

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
                with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True):
                    with patch(
                        "vocalinux.ui.keyboard_backends.EvdevKeyboardBackend",
                        return_value=mock_evdev_backend,
                    ):
                        result = create_backend()
                        assert result is None

    def test_create_backend_wayland_preferred_pynput_fails_evdev_available(self):
        """Test that preferred pynput on Wayland fails and then tries evdev."""
        # When preferred_backend is pynput and Wayland is detected,
        # if pynput is not available, it falls back to auto-detection which tries evdev
        mock_evdev_backend = MagicMock()
        mock_evdev_backend.is_available.return_value = True

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
            with patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False):
                with patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True):
                    with patch(
                        "vocalinux.ui.keyboard_backends.EvdevKeyboardBackend",
                        return_value=mock_evdev_backend,
                    ):
                        result = create_backend(preferred_backend="pynput")
                        # Falls back to auto-detection which selects evdev on Wayland
                        assert result == mock_evdev_backend
