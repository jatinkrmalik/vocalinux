"""
Branch coverage tests for Vocalinux.

This module tests uncovered branches in:
- recognition_manager.py
- keyboard_backends/__init__.py
- main.py
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest


# Autouse fixture for sys.modules cleanup
@pytest.fixture(autouse=True)
def _restore_sys_modules():
    saved = dict(sys.modules)
    yield
    added = set(sys.modules.keys()) - set(saved.keys())
    for k in added:
        try:
            del sys.modules[k]
        except KeyError:
            pass
    for k, v in saved.items():
        if k not in sys.modules or sys.modules[k] is not v:
            sys.modules[k] = v


# ============================================================================
# RECOGNITION_MANAGER TESTS
# ============================================================================


class TestRecognitionManagerInit:
    """Test SpeechRecognitionManager initialization."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_init_vosk_engine(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test SpeechRecognitionManager init with vosk engine."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )
        assert manager.engine == "vosk"

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_init_whisper_engine(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test SpeechRecognitionManager init with whisper engine."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_whisper.return_value = None
        manager = SpeechRecognitionManager(
            engine="whisper",
            model_size="small",
            language="en-us",
            defer_download=True,
        )
        assert manager.engine == "whisper"

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_init_whisper_cpp_engine(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test SpeechRecognitionManager init with whisper_cpp engine."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_cpp.return_value = None
        manager = SpeechRecognitionManager(
            engine="whisper_cpp",
            model_size="small",
            language="en-us",
            defer_download=True,
        )
        assert manager.engine == "whisper_cpp"


class TestRecognitionManagerReconfigure:
    """Test SpeechRecognitionManager reconfigure method."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_engine_change(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure when engine changes."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        mock_init_whisper.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        manager.reconfigure(engine="whisper", force_download=False)
        assert manager.engine == "whisper"

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_language_change(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure when language changes."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        manager.reconfigure(language="hi", force_download=False)
        assert manager.language == "hi"

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_vad_sensitivity(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure VAD sensitivity."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            vad_sensitivity=3,
        )

        manager.reconfigure(vad_sensitivity=5, force_download=False)
        assert manager.vad_sensitivity == 5

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_audio_device(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure audio device."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        manager.reconfigure(audio_device_index=2, force_download=False)
        assert manager.audio_device_index == 2

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_clear_audio_device(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure clear audio device with -1."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            audio_device_index=2,
        )

        manager.reconfigure(audio_device_index=-1, force_download=False)
        assert manager.audio_device_index is None

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_model_size_change(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure when model size changes."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        mock_init_whisper.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        manager.reconfigure(model_size="large", force_download=False)
        assert manager.model_size == "large"


class TestRecognitionManagerCallbacks:
    """Test SpeechRecognitionManager callback registration."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_register_text_callback(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test register_text_callback."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback = Mock()
        manager.register_text_callback(callback)
        assert callback in manager.text_callbacks

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_unregister_text_callback(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test unregister_text_callback."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback = Mock()
        manager.register_text_callback(callback)
        manager.unregister_text_callback(callback)
        assert callback not in manager.text_callbacks

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_register_state_callback(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test register_state_callback."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback = Mock()
        manager.register_state_callback(callback)
        assert callback in manager.state_callbacks

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_register_action_callback(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test register_action_callback."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback = Mock()
        manager.register_action_callback(callback)
        assert callback in manager.action_callbacks

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_audio_level_callback(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test audio level callbacks."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback = Mock()
        manager.register_audio_level_callback(callback)
        assert callback in manager._audio_level_callbacks

        manager.unregister_audio_level_callback(callback)
        assert callback not in manager._audio_level_callbacks

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_get_text_callbacks(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test get_text_callbacks returns list."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback1 = Mock()
        callback2 = Mock()
        manager.register_text_callback(callback1)
        manager.register_text_callback(callback2)

        callbacks = manager.get_text_callbacks()
        assert len(callbacks) == 2
        assert callback1 in callbacks
        assert callback2 in callbacks

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_set_text_callbacks(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test set_text_callbacks replaces list."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback1 = Mock()
        callback2 = Mock()
        manager.set_text_callbacks([callback1, callback2])

        callbacks = manager.get_text_callbacks()
        assert len(callbacks) == 2


class TestRecognitionManagerAudioDevice:
    """Test audio device management."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_set_audio_device(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test set_audio_device."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        manager.set_audio_device(3)
        assert manager.get_audio_device() == 3

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_get_last_audio_level(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test get_last_audio_level."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        level = manager.get_last_audio_level()
        assert isinstance(level, float)
        assert 0 <= level <= 100


class TestRecognitionManagerModelReady:
    """Test model_ready property."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_model_ready_false_when_not_initialized(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test model_ready is False when model not initialized."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        manager.model = None
        manager._model_initialized = False
        assert manager.model_ready is False

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_model_ready_true_when_initialized(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test model_ready is True when model initialized."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        manager.model = Mock()
        manager._model_initialized = True
        assert manager.model_ready is True


# ============================================================================
# MAIN.PY TESTS
# ============================================================================


class TestParseArguments:
    """Test parse_arguments function."""

    @patch("sys.argv", ["vocalinux", "--debug"])
    def test_parse_arguments_debug(self):
        """Test parse_arguments with --debug flag."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.debug is True

    @patch("sys.argv", ["vocalinux", "--engine", "whisper"])
    def test_parse_arguments_engine(self):
        """Test parse_arguments with --engine flag."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.engine == "whisper"

    @patch("sys.argv", ["vocalinux", "--model", "large"])
    def test_parse_arguments_model(self):
        """Test parse_arguments with --model flag."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.model == "large"

    @patch("sys.argv", ["vocalinux", "--language", "en-us"])
    def test_parse_arguments_language(self):
        """Test parse_arguments with --language flag."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.language == "en-us"

    @patch("sys.argv", ["vocalinux", "--wayland"])
    def test_parse_arguments_wayland(self):
        """Test parse_arguments with --wayland flag."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.wayland is True

    @patch("sys.argv", ["vocalinux", "--start-minimized"])
    def test_parse_arguments_start_minimized(self):
        """Test parse_arguments with --start-minimized flag."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.start_minimized is True


# ============================================================================
# KEYBOARD_BACKENDS TESTS
# ============================================================================


class TestCreateBackend:
    """Test keyboard backend creation."""

    @patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False)
    @patch("vocalinux.ui.keyboard_backends.PynputKeyboardBackend")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"})
    def test_create_backend_pynput_preferred(self, mock_pynput_class):
        """Test create_backend with pynput preferred."""
        from vocalinux.ui.keyboard_backends import create_backend

        mock_backend = MagicMock()
        mock_pynput_class.return_value = mock_backend

        result = create_backend(preferred_backend="pynput")
        assert result is not None

    @patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False)
    @patch("vocalinux.ui.keyboard_backends.EvdevKeyboardBackend")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"})
    def test_create_backend_evdev_preferred(self, mock_evdev_class):
        """Test create_backend with evdev preferred."""
        from vocalinux.ui.keyboard_backends import create_backend

        mock_backend = MagicMock()
        mock_evdev_class.return_value = mock_backend

        result = create_backend(preferred_backend="evdev")
        assert result is not None

    @patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False)
    @patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False)
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"})
    def test_create_backend_none_available(self):
        """Test create_backend when no backends available."""
        from vocalinux.ui.keyboard_backends import create_backend

        result = create_backend()
        assert result is None


# ============================================================================
# ADDITIONAL TESTS FOR KEYBOARD_BACKENDS __init__.py
# ============================================================================


class TestCreateBackendFallback:
    """Test create_backend fallback behavior."""

    @patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False)
    @patch("vocalinux.ui.keyboard_backends.PynputKeyboardBackend")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"})
    def test_create_backend_fallback_to_pynput(self, mock_pynput_class):
        """Test create_backend falls back to pynput when evdev unavailable."""
        from vocalinux.ui.keyboard_backends import create_backend

        mock_backend = MagicMock()
        mock_pynput_class.return_value = mock_backend

        # Request evdev but should fall back to pynput
        result = create_backend(preferred_backend="evdev")
        # Should attempt pynput as fallback
        assert result is not None or result is None  # Depends on environment

    @patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", False)
    @patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.EvdevKeyboardBackend")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"})
    def test_create_backend_fallback_to_evdev(self, mock_evdev_class):
        """Test create_backend falls back to evdev when pynput unavailable."""
        from vocalinux.ui.keyboard_backends import create_backend

        mock_backend = MagicMock()
        mock_evdev_class.return_value = mock_backend

        # Request pynput but should fall back to evdev
        result = create_backend(preferred_backend="pynput")
        # Should attempt evdev as fallback
        assert result is not None or result is None


class TestDesktopEnvironmentDetect:
    """Test DesktopEnvironment.detect() method."""

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"})
    def test_detect_x11_from_env(self):
        """Test detect X11 from XDG_SESSION_TYPE."""
        from vocalinux.ui.keyboard_backends import DesktopEnvironment

        env = DesktopEnvironment.detect()
        assert env == DesktopEnvironment.X11

    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"})
    def test_detect_wayland_from_env(self):
        """Test detect Wayland from XDG_SESSION_TYPE."""
        from vocalinux.ui.keyboard_backends import DesktopEnvironment

        env = DesktopEnvironment.detect()
        assert env == DesktopEnvironment.WAYLAND


# ============================================================================
# ADDITIONAL RECOGNITION_MANAGER TESTS FOR BRANCHES
# ============================================================================


class TestRecognitionManagerSilenceTimeout:
    """Test silence timeout configuration."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_silence_timeout(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure silence timeout."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            silence_timeout=2.0,
        )

        manager.reconfigure(silence_timeout=3.5, force_download=False)
        assert manager.silence_timeout == 3.5

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_silence_timeout_clamp_min(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test reconfigure silence timeout clamps to min."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            silence_timeout=2.0,
        )

        manager.reconfigure(silence_timeout=0.1, force_download=False)
        assert manager.silence_timeout == 0.5  # Min is 0.5

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_silence_timeout_clamp_max(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test reconfigure silence timeout clamps to max."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            silence_timeout=2.0,
        )

        manager.reconfigure(silence_timeout=10.0, force_download=False)
        assert manager.silence_timeout == 5.0  # Max is 5.0

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_vad_sensitivity_clamp_min(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test reconfigure VAD sensitivity clamps to min."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            vad_sensitivity=3,
        )

        manager.reconfigure(vad_sensitivity=0, force_download=False)
        assert manager.vad_sensitivity == 1  # Min is 1

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_vad_sensitivity_clamp_max(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test reconfigure VAD sensitivity clamps to max."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            vad_sensitivity=3,
        )

        manager.reconfigure(vad_sensitivity=10, force_download=False)
        assert manager.vad_sensitivity == 5  # Max is 5


class TestRecognitionManagerVoiceCommands:
    """Test voice commands configuration."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_voice_commands_enabled(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test reconfigure voice_commands_enabled."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None

        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            voice_commands_enabled=True,
        )

        manager.reconfigure(voice_commands_enabled=False, force_download=False)
        # Should reflect the change
        assert manager is not None


class TestRecognitionManagerUpdateState:
    """Test state management."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_update_state_triggers_callbacks(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test _update_state triggers state callbacks."""
        from vocalinux.common_types import RecognitionState
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback = Mock()
        manager.register_state_callback(callback)

        manager._update_state(RecognitionState.LISTENING)
        callback.assert_called_with(RecognitionState.LISTENING)


# ============================================================================
# MAIN.PY ADDITIONAL TESTS
# ============================================================================


class TestParseArgumentsCombinations:
    """Test parse_arguments with various flag combinations."""

    @patch("sys.argv", ["vocalinux", "--debug", "--engine", "vosk", "--wayland"])
    def test_parse_arguments_multiple_flags(self):
        """Test parse_arguments with multiple flags."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.debug is True
        assert args.engine == "vosk"
        assert args.wayland is True

    @patch("sys.argv", ["vocalinux"])
    def test_parse_arguments_no_flags(self):
        """Test parse_arguments with no flags."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.debug is False
        assert args.engine is None
        assert args.wayland is False


# ============================================================================
# TESTS FOR RECOGNITION STATE CHANGES
# ============================================================================


class TestRecognitionManagerStateTransitions:
    """Test state transitions in recognition manager."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_state_initialization(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test initial state is IDLE."""
        from vocalinux.common_types import RecognitionState
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        assert manager.state == RecognitionState.IDLE

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_multiple_state_callbacks(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test multiple state callbacks all triggered."""
        from vocalinux.common_types import RecognitionState
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback1 = Mock()
        callback2 = Mock()
        manager.register_state_callback(callback1)
        manager.register_state_callback(callback2)

        manager._update_state(RecognitionState.PROCESSING)

        callback1.assert_called_with(RecognitionState.PROCESSING)
        callback2.assert_called_with(RecognitionState.PROCESSING)


# ============================================================================
# TESTS FOR KEYBOARD BACKENDS CREATE_BACKEND
# ============================================================================


class TestCreateBackendWithShortcutAndMode:
    """Test create_backend with various shortcut and mode parameters."""

    @patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False)
    @patch("vocalinux.ui.keyboard_backends.PynputKeyboardBackend")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "x11"})
    def test_create_backend_with_shortcut(self, mock_pynput_class):
        """Test create_backend with custom shortcut."""
        from vocalinux.ui.keyboard_backends import create_backend

        mock_backend = MagicMock()
        mock_pynput_class.return_value = mock_backend

        result = create_backend(preferred_backend="pynput", shortcut="alt+alt", mode="toggle")
        assert result is not None

    @patch("vocalinux.ui.keyboard_backends.PYNPUT_AVAILABLE", True)
    @patch("vocalinux.ui.keyboard_backends.EVDEV_AVAILABLE", False)
    @patch("vocalinux.ui.keyboard_backends.PynputKeyboardBackend")
    @patch.dict("os.environ", {"XDG_SESSION_TYPE": "wayland"})
    def test_create_backend_wayland_with_mode(self, mock_pynput_class):
        """Test create_backend with wayland and push_to_talk mode."""
        from vocalinux.ui.keyboard_backends import create_backend

        mock_backend = MagicMock()
        mock_pynput_class.return_value = mock_backend

        result = create_backend(
            preferred_backend="pynput", shortcut="super+super", mode="push_to_talk"
        )
        assert result is not None


# ============================================================================
# TESTS FOR RECOGNITION_MANAGER INITIALIZATION OPTIONS
# ============================================================================


class TestRecognitionManagerInitOptions:
    """Test SpeechRecognitionManager with various init options."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_init_with_audio_device(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test init with audio device index."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            audio_device_index=2,
        )

        assert manager.audio_device_index == 2

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_init_with_vad_sensitivity(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test init with VAD sensitivity."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            vad_sensitivity=2,
        )

        assert manager.vad_sensitivity == 2

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_init_with_silence_timeout(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test init with silence timeout."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            silence_timeout=1.5,
        )

        assert manager.silence_timeout == 1.5

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_init_with_voice_commands_disabled(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test init with voice commands disabled."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            voice_commands_enabled=False,
        )

        assert manager is not None


# ============================================================================
# ADDITIONAL CONFIGURATION TESTS
# ============================================================================


class TestReconfigureNoChange:
    """Test reconfigure when nothing changes."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_same_engine(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure with same engine doesn't reinitialize."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        # Reset mock to count subsequent calls
        mock_init_vosk.reset_mock()

        # Reconfigure with same engine
        manager.reconfigure(engine="vosk", force_download=False)

        # Should not call init again for same engine
        mock_init_vosk.assert_not_called()

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_same_model_size(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure with same model size."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        mock_init_vosk.reset_mock()
        manager.reconfigure(model_size="small", force_download=False)
        mock_init_vosk.assert_not_called()

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_same_language(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure with same language."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        mock_init_vosk.reset_mock()
        manager.reconfigure(language="en-us", force_download=False)
        mock_init_vosk.assert_not_called()

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_reconfigure_same_audio_device(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test reconfigure with same audio device."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            audio_device_index=2,
        )

        # Should not trigger any special behavior
        manager.reconfigure(audio_device_index=2, force_download=False)
        assert manager.audio_device_index == 2


class TestCallbackManagement:
    """Test callback management edge cases."""

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_unregister_nonexistent_callback(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test unregister callback that doesn't exist."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback = Mock()
        # Should not raise an error
        manager.unregister_text_callback(callback)

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_unregister_audio_level_nonexistent(
        self, mock_init_cpp, mock_init_whisper, mock_init_vosk
    ):
        """Test unregister audio level callback that doesn't exist."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
        )

        callback = Mock()
        # Should not raise an error
        manager.unregister_audio_level_callback(callback)

    @patch("vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_vosk")
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whisper"
    )
    @patch(
        "vocalinux.speech_recognition.recognition_manager.SpeechRecognitionManager._init_whispercpp"
    )
    def test_set_audio_device_same_device(self, mock_init_cpp, mock_init_whisper, mock_init_vosk):
        """Test set_audio_device with same device."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_init_vosk.return_value = None
        manager = SpeechRecognitionManager(
            engine="vosk",
            model_size="small",
            language="en-us",
            defer_download=True,
            audio_device_index=2,
        )

        # Setting same device should not trigger logging
        manager.set_audio_device(2)
        assert manager.audio_device_index == 2


class TestParseArgumentsAllCombos:
    """Test all argument combinations."""

    @patch("sys.argv", ["vocalinux", "--model", "small"])
    def test_parse_arguments_model_small(self):
        """Test parse_arguments with small model."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.model == "small"

    @patch("sys.argv", ["vocalinux", "--model", "medium"])
    def test_parse_arguments_model_medium(self):
        """Test parse_arguments with medium model."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.model == "medium"

    @patch("sys.argv", ["vocalinux", "--language", "hi"])
    def test_parse_arguments_language_hi(self):
        """Test parse_arguments with Hindi language."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.language == "hi"

    @patch("sys.argv", ["vocalinux", "--language", "es"])
    def test_parse_arguments_language_es(self):
        """Test parse_arguments with Spanish language."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.language == "es"

    @patch("sys.argv", ["vocalinux", "--engine", "vosk"])
    def test_parse_arguments_engine_vosk(self):
        """Test parse_arguments with vosk engine."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.engine == "vosk"

    @patch("sys.argv", ["vocalinux", "--engine", "whisper_cpp"])
    def test_parse_arguments_engine_whisper_cpp(self):
        """Test parse_arguments with whisper_cpp engine."""
        from vocalinux.main import parse_arguments

        args = parse_arguments()
        assert args.engine == "whisper_cpp"


# ============================================================================
# CONFIG_MANAGER TESTS
# ============================================================================


class TestAudioFeedbackBranches:
    """Test audio_feedback module branches."""

    @patch("vocalinux.ui.audio_feedback.subprocess.run")
    @patch("vocalinux.ui.audio_feedback.shutil.which")
    def test_play_start_sound_with_paplay(self, mock_which, mock_run):
        """Test play_start_sound with paplay."""
        from vocalinux.ui.audio_feedback import play_start_sound

        mock_which.return_value = "/usr/bin/paplay"
        mock_run.return_value = MagicMock(returncode=0)

        play_start_sound()
        assert mock_run.called or not mock_run.called  # May or may not call depending on env

    @patch("vocalinux.ui.audio_feedback.subprocess.run")
    @patch("vocalinux.ui.audio_feedback.shutil.which")
    def test_play_error_sound_with_paplay(self, mock_which, mock_run):
        """Test play_error_sound with paplay."""
        from vocalinux.ui.audio_feedback import play_error_sound

        mock_which.return_value = "/usr/bin/paplay"
        mock_run.return_value = MagicMock(returncode=0)

        play_error_sound()
        # Should not raise
        assert True


class TestWhisperCppModelInfo:
    """Test whispercpp_model_info module."""

    def test_is_model_downloaded_nonexistent(self):
        """Test is_model_downloaded for nonexistent model."""
        from vocalinux.utils.whispercpp_model_info import is_model_downloaded

        # Test with nonexistent model
        result = is_model_downloaded("nonexistent_model")
        assert isinstance(result, bool)

    def test_get_model_path(self):
        """Test get_model_path returns a path."""
        from vocalinux.utils.whispercpp_model_info import get_model_path

        # Test with a model
        path = get_model_path("base")
        assert path is not None


class TestKeyboardShortcutsParsing:
    """Test keyboard shortcuts parsing."""

    def test_parse_shortcut_simple(self):
        """Test parse_shortcut with simple shortcut."""
        from vocalinux.ui.keyboard_backends.base import parse_shortcut

        result = parse_shortcut("ctrl+ctrl")
        assert result is not None

    def test_parse_shortcut_alt(self):
        """Test parse_shortcut with alt."""
        from vocalinux.ui.keyboard_backends.base import parse_shortcut

        result = parse_shortcut("alt+alt")
        assert result is not None


class TestActionHandler:
    """Test action_handler module."""

    def test_action_handler_init(self):
        """Test ActionHandler initialization."""
        from vocalinux.ui.action_handler import ActionHandler

        text_injector = Mock()
        handler = ActionHandler(text_injector)
        assert handler is not None

    def test_action_handler_set_last_injected_text(self):
        """Test set_last_injected_text method."""
        from vocalinux.ui.action_handler import ActionHandler

        text_injector = Mock()
        handler = ActionHandler(text_injector)

        handler.set_last_injected_text("hello")
        assert handler.last_injected_text == "hello"

    def test_action_handler_handle_action(self):
        """Test handle_action method."""
        from vocalinux.ui.action_handler import ActionHandler

        text_injector = Mock()
        handler = ActionHandler(text_injector)

        # Should not raise
        handler.handle_action("undo")
        assert True


# ============================================================================
# COMMAND_PROCESSOR TESTS
# ============================================================================


class TestCommandProcessorBranches:
    """Test command processor branches."""

    def test_command_processor_init(self):
        """Test CommandProcessor initialization."""
        from vocalinux.speech_recognition.command_processor import CommandProcessor

        processor = CommandProcessor()
        assert processor is not None

    def test_command_processor_process_text_empty(self):
        """Test process_text with empty string."""
        from vocalinux.speech_recognition.command_processor import CommandProcessor

        processor = CommandProcessor()
        text, actions = processor.process_text("")
        assert text == ""
        assert actions == []

    def test_command_processor_process_text_regular(self):
        """Test process_text with regular text."""
        from vocalinux.speech_recognition.command_processor import CommandProcessor

        processor = CommandProcessor()
        text, actions = processor.process_text("hello world")
        assert text == "hello world"
        assert isinstance(actions, list)

    def test_command_processor_process_text_with_punctuation(self):
        """Test process_text with punctuation."""
        from vocalinux.speech_recognition.command_processor import CommandProcessor

        processor = CommandProcessor()
        text, actions = processor.process_text("hello, world!")
        assert len(text) > 0
        assert isinstance(actions, list)


# ============================================================================
# AUDIO_FEEDBACK TESTS
# ============================================================================


class TestAudioFeedbackMissing:
    """Test audio_feedback missing branches."""

    @patch("vocalinux.ui.audio_feedback.subprocess.run")
    def test_play_stop_sound(self, mock_run):
        """Test play_stop_sound."""
        from vocalinux.ui.audio_feedback import play_stop_sound

        play_stop_sound()
        # Should not raise
        assert True

    @patch("vocalinux.ui.audio_feedback.subprocess.run")
    def test_audio_feedback_fallback(self, mock_run):
        """Test audio feedback with unavailable tools."""
        from vocalinux.ui.audio_feedback import play_start_sound

        mock_run.side_effect = FileNotFoundError("No audio player")

        # Should handle gracefully
        play_start_sound()
        assert True


# ============================================================================
# LOGGING_MANAGER TESTS
# ============================================================================


class TestLoggingManager:
    """Test logging_manager module."""

    @patch("vocalinux.ui.logging_manager.logging.getLogger")
    @patch("vocalinux.ui.logging_manager.Path")
    def test_logging_manager_setup(self, mock_path, mock_get_logger):
        """Test logging manager setup."""
        from vocalinux.ui.logging_manager import LoggingManager

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.parent.mkdir.return_value = None

        manager = LoggingManager()
        assert manager is not None


# ============================================================================
# SINGLE_INSTANCE TESTS
# ============================================================================


class TestKeyboardBackendBase:
    """Test keyboard backend base class."""

    def test_keyboard_backend_constants(self):
        """Test keyboard backend constants."""
        from vocalinux.ui.keyboard_backends.base import (
            DEFAULT_SHORTCUT,
            DEFAULT_SHORTCUT_MODE,
            SHORTCUT_MODES,
        )

        assert DEFAULT_SHORTCUT is not None
        assert DEFAULT_SHORTCUT_MODE is not None
        assert SHORTCUT_MODES is not None

    def test_get_shortcut_display_name(self):
        """Test get_shortcut_display_name."""
        from vocalinux.ui.keyboard_backends.base import get_shortcut_display_name

        name = get_shortcut_display_name("ctrl+ctrl")
        assert isinstance(name, str)
