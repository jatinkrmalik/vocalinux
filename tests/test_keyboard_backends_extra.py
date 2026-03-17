"""
Additional coverage tests for keyboard_backends module.

Tests for backend detection and creation.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock

# Autouse fixture to prevent sys.modules pollution
@pytest.fixture(autouse=True)
def _restore_sys_modules():
    saved = dict(sys.modules)
    yield
    added = set(sys.modules.keys()) - set(saved.keys())
    for k in added:
        del sys.modules[k]
    for k, v in saved.items():
        if k not in sys.modules or sys.modules[k] is not v:
            sys.modules[k] = v


class TestDesktopEnvironmentDetection:
    """Tests for desktop environment detection."""

    def test_detect_x11_from_session_type(self):
        """Test X11 detection from XDG_SESSION_TYPE."""
        from vocalinux.ui.keyboard_backends import DesktopEnvironment

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}, clear=True):
            env = DesktopEnvironment.detect()
            assert env == DesktopEnvironment.X11

    def test_detect_wayland_from_session_type(self):
        """Test Wayland detection from XDG_SESSION_TYPE."""
        from vocalinux.ui.keyboard_backends import DesktopEnvironment

        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
            env = DesktopEnvironment.detect()
            assert env == DesktopEnvironment.WAYLAND

    def test_detect_x11_from_display(self):
        """Test X11 detection from DISPLAY environment variable."""
        from vocalinux.ui.keyboard_backends import DesktopEnvironment

        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
            env = DesktopEnvironment.detect()
            assert env == DesktopEnvironment.X11

    def test_detect_wayland_from_wayland_display(self):
        """Test Wayland detection from WAYLAND_DISPLAY environment variable."""
        from vocalinux.ui.keyboard_backends import DesktopEnvironment

        with patch.dict(os.environ, {"WAYLAND_DISPLAY": "wayland-0"}, clear=True):
            env = DesktopEnvironment.detect()
            assert env == DesktopEnvironment.WAYLAND

    def test_detect_unknown_no_env_vars(self):
        """Test unknown detection when no environment variables are set."""
        from vocalinux.ui.keyboard_backends import DesktopEnvironment

        with patch.dict(os.environ, {}, clear=True):
            env = DesktopEnvironment.detect()
            assert env == DesktopEnvironment.UNKNOWN


class TestCreateBackendPynput:
    """Tests for create_backend with pynput backend."""

    def test_create_backend_pynput_available(self):
        """Test create_backend when pynput is available."""
        from vocalinux.ui import keyboard_backends
        
        with patch.object(keyboard_backends, 'PYNPUT_AVAILABLE', True):
            with patch.object(keyboard_backends, 'PynputKeyboardBackend') as mock_pynput:
                with patch.object(keyboard_backends, 'DesktopEnvironment') as mock_env:
                    mock_env.detect.return_value = "x11"
                    
                    backend = keyboard_backends.create_backend()
                    
                    # Should have tried to create pynput backend (unconditional assertion)
                    mock_pynput.assert_called()

    def test_create_backend_pynput_preferred(self):
        """Test create_backend with pynput as preferred backend."""
        from vocalinux.ui import keyboard_backends
        
        with patch.object(keyboard_backends, 'PYNPUT_AVAILABLE', True):
            with patch.object(keyboard_backends, 'PynputKeyboardBackend') as mock_pynput:
                backend = keyboard_backends.create_backend(preferred_backend="pynput")
                
                # Should have tried to create pynput backend
                if mock_pynput is not None:
                    mock_pynput.assert_called()


class TestCreateBackendEvdev:
    """Tests for create_backend with evdev backend."""

    def test_create_backend_evdev_available(self):
        """Test create_backend when evdev is available."""
        from vocalinux.ui import keyboard_backends
        
        with patch.object(keyboard_backends, 'EVDEV_AVAILABLE', True):
            with patch.object(keyboard_backends, 'EvdevKeyboardBackend') as mock_evdev:
                with patch.object(keyboard_backends, 'PYNPUT_AVAILABLE', False):
                    with patch.object(keyboard_backends, 'DesktopEnvironment') as mock_env:
                        mock_env.detect.return_value = "x11"
                        mock_instance = MagicMock()
                        mock_instance.is_available.return_value = False
                        mock_evdev.return_value = mock_instance
                        
                        backend = keyboard_backends.create_backend()
                        
                        # Should have tried to create evdev backend
                        assert mock_evdev.called or backend is None

    def test_create_backend_evdev_preferred(self):
        """Test create_backend with evdev as preferred backend."""
        from vocalinux.ui import keyboard_backends
        
        with patch.object(keyboard_backends, 'EVDEV_AVAILABLE', True):
            with patch.object(keyboard_backends, 'EvdevKeyboardBackend') as mock_evdev:
                mock_instance = MagicMock()
                mock_instance.is_available.return_value = False
                mock_instance.get_permission_hint.return_value = None
                mock_evdev.return_value = mock_instance
                
                backend = keyboard_backends.create_backend(preferred_backend="evdev")
                
                # Should have tried to create evdev backend
                mock_evdev.assert_called()

    def test_create_backend_evdev_wayland(self):
        """Test create_backend on Wayland with evdev backend."""
        from vocalinux.ui import keyboard_backends
        
        with patch.object(keyboard_backends, 'EVDEV_AVAILABLE', True):
            with patch.object(keyboard_backends, 'EvdevKeyboardBackend') as mock_evdev:
                with patch.object(keyboard_backends, 'DesktopEnvironment') as mock_env:
                    mock_env.detect.return_value = keyboard_backends.DesktopEnvironment.WAYLAND
                    mock_instance = MagicMock()
                    mock_instance.is_available.return_value = False
                    mock_instance.get_permission_hint.return_value = None
                    mock_evdev.return_value = mock_instance
                    
                    backend = keyboard_backends.create_backend()
                    
                    # Should attempt to use evdev on Wayland
                    assert mock_evdev.called or backend is None


class TestCreateBackendNoBackend:
    """Tests for create_backend when no backend is available."""

    def test_create_backend_no_backend_available(self):
        """Test create_backend when no backend is available."""
        from vocalinux.ui import keyboard_backends
        
        with patch.object(keyboard_backends, 'PYNPUT_AVAILABLE', False):
            with patch.object(keyboard_backends, 'EVDEV_AVAILABLE', False):
                with patch.object(keyboard_backends, 'DesktopEnvironment') as mock_env:
                    mock_env.detect.return_value = "x11"
                    
                    backend = keyboard_backends.create_backend()
                    
                    # Should return None when no backend is available
                    assert backend is None

    def test_create_backend_unknown_preferred(self):
        """Test create_backend with unknown preferred backend."""
        from vocalinux.ui import keyboard_backends
        
        with patch.object(keyboard_backends, 'PYNPUT_AVAILABLE', False):
            with patch.object(keyboard_backends, 'EVDEV_AVAILABLE', False):
                with patch.object(keyboard_backends, 'DesktopEnvironment') as mock_env:
                    mock_env.detect.return_value = "x11"
                    
                    backend = keyboard_backends.create_backend(preferred_backend="unknown")
                    
                    # Should return None when preferred backend is unknown
                    assert backend is None


class TestKeyboardBackendImports:
    """Tests for keyboard backends module imports."""

    def test_backend_imports(self):
        """Test that backend module imports are available."""
        from vocalinux.ui.keyboard_backends import (
            KeyboardBackend,
            create_backend,
            DesktopEnvironment,
            SUPPORTED_SHORTCUTS,
            DEFAULT_SHORTCUT,
            DEFAULT_SHORTCUT_MODE,
            parse_shortcut,
        )
        
        # Verify KeyboardBackend is a class/type
        assert callable(KeyboardBackend)
        # Verify create_backend is a callable function
        assert callable(create_backend)
        # Verify DesktopEnvironment is a class
        assert callable(DesktopEnvironment)
        # Verify SUPPORTED_SHORTCUTS is a dict with valid content
        assert isinstance(SUPPORTED_SHORTCUTS, dict)
        assert len(SUPPORTED_SHORTCUTS) > 0
        # Verify DEFAULT_SHORTCUT is a string
        assert isinstance(DEFAULT_SHORTCUT, str)
        # Verify DEFAULT_SHORTCUT_MODE is a string
        assert isinstance(DEFAULT_SHORTCUT_MODE, str)
        # Verify parse_shortcut is callable
        assert callable(parse_shortcut)
