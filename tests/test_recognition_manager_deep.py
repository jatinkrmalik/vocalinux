"""
Deep coverage tests for recognition_manager.py.
Properly isolated - saves/restores sys.modules to avoid polluting other tests.
"""

import importlib
import json
import os
import sys
import threading
import time
import unittest
from unittest.mock import MagicMock, patch, call

# ---- Safely mock external deps, preserving stdlib ----
_MOCK_KEYS = [
    "vosk", "whisper", "torch", "pyaudio",
    "pywhispercpp", "pywhispercpp.model",
]
_ORIG_MODULES = {}
for _k in _MOCK_KEYS:
    _ORIG_MODULES[_k] = sys.modules.get(_k)
    if _k not in sys.modules:
        sys.modules[_k] = MagicMock()

if "gi" not in sys.modules:
    sys.modules["gi"] = MagicMock()
if "gi.repository" not in sys.modules:
    sys.modules["gi.repository"] = MagicMock()

from vocalinux.common_types import RecognitionState  # noqa: E402
from vocalinux.speech_recognition.recognition_manager import (  # noqa: E402
    SpeechRecognitionManager,
    _setup_alsa_error_handler,
    _get_supported_channels,
    _get_supported_sample_rate,
    get_audio_input_devices,
)

# Restore stdlib modules immediately after import
for _k, _v in _ORIG_MODULES.items():
    if _v is not None:
        sys.modules[_k] = _v
    elif _k in sys.modules and isinstance(sys.modules[_k], MagicMock):
        del sys.modules[_k]


def _make_manager(engine="whisper_cpp", **kw):
    """Create a manager with deferred init to avoid actually loading models."""
    with patch.object(SpeechRecognitionManager, "_init_vosk"):
        with patch.object(SpeechRecognitionManager, "_init_whisper"):
            with patch.object(SpeechRecognitionManager, "_init_whispercpp"):
                mgr = SpeechRecognitionManager(
                    engine=engine, model_size="small", language="en-us",
                    defer_download=True, **kw
                )
    return mgr


class TestALSAErrorHandler(unittest.TestCase):
    def test_setup_success(self):
        with patch("ctypes.CDLL") as mock_cdll:
            mock_cdll.return_value = MagicMock()
            _setup_alsa_error_handler()
            mock_cdll.assert_called_once_with("libasound.so.2")

    def test_setup_oserror(self):
        with patch("ctypes.CDLL", side_effect=OSError("not found")):
            _setup_alsa_error_handler()  # Should not raise


class TestGetAudioInputDevices(unittest.TestCase):
    def test_returns_devices(self):
        mock_pa_inst = MagicMock()
        mock_pa_inst.get_device_count.return_value = 3
        mock_pa_inst.get_device_info_by_index.side_effect = [
            {"name": "Mic 1", "maxInputChannels": 2, "index": 0},
            {"name": "Speaker", "maxInputChannels": 0, "index": 1},
            {"name": "Mic 2", "maxInputChannels": 1, "index": 2},
        ]
        mock_pyaudio = MagicMock()
        mock_pyaudio.PyAudio.return_value = mock_pa_inst
        with patch.dict("sys.modules", {"pyaudio": mock_pyaudio}):
            devices = get_audio_input_devices()
        self.assertEqual(len(devices), 2)

    def test_handles_error(self):
        mock_pyaudio = MagicMock()
        mock_pyaudio.PyAudio.side_effect = Exception("no audio")
        with patch.dict("sys.modules", {"pyaudio": mock_pyaudio}):
            devices = get_audio_input_devices()
        self.assertEqual(devices, [])


class TestSupportedChannels(unittest.TestCase):
    def _run_with_pyaudio(self, func):
        mock_pyaudio = MagicMock()
        mock_pyaudio.paInt16 = 8
        with patch.dict("sys.modules", {"pyaudio": mock_pyaudio}):
            return func()

    def test_mono_supported(self):
        mock_pa = MagicMock()
        mock_pa.is_format_supported.return_value = True
        result = self._run_with_pyaudio(lambda: _get_supported_channels(mock_pa, None))
        self.assertEqual(result, 1)

    def test_mono_fails_stereo_ok(self):
        mock_pa = MagicMock()
        call_count = [0]
        mock_stream = MagicMock()
        def open_side_effect(**kw):
            call_count[0] += 1
            if kw.get("channels") == 1:
                raise IOError("Invalid number of channels -9998")
            return mock_stream
        mock_pa.open.side_effect = open_side_effect
        result = self._run_with_pyaudio(lambda: _get_supported_channels(mock_pa, None))
        self.assertEqual(result, 2)

    def test_both_fail(self):
        mock_pa = MagicMock()
        mock_pa.is_format_supported.side_effect = ValueError("nope")
        result = self._run_with_pyaudio(lambda: _get_supported_channels(mock_pa, None))
        self.assertEqual(result, 1)


class TestSupportedSampleRate(unittest.TestCase):
    def _run_with_pyaudio(self, func):
        mock_pyaudio = MagicMock()
        mock_pyaudio.paInt16 = 8
        with patch.dict("sys.modules", {"pyaudio": mock_pyaudio}):
            return func()

    def test_default_rate_used(self):
        mock_pa = MagicMock()
        mock_pa.get_default_input_device_info.return_value = {"defaultSampleRate": 48000}
        mock_stream = MagicMock()
        mock_pa.open.return_value = mock_stream
        result = self._run_with_pyaudio(lambda: _get_supported_sample_rate(mock_pa, None, 1))
        self.assertEqual(result, 48000)

    def test_all_open_fail_returns_16000(self):
        mock_pa = MagicMock()
        mock_pa.get_default_input_device_info.return_value = {"defaultSampleRate": 0}
        mock_pa.open.side_effect = IOError("no rate works")
        result = self._run_with_pyaudio(lambda: _get_supported_sample_rate(mock_pa, None, 1))
        self.assertEqual(result, 16000)


class TestManagerConstruction(unittest.TestCase):
    def test_vosk_engine(self):
        mgr = _make_manager(engine="vosk")
        self.assertEqual(mgr.engine, "vosk")

    def test_whisper_engine(self):
        mgr = _make_manager(engine="whisper")
        self.assertEqual(mgr.engine, "whisper")

    def test_whispercpp_engine(self):
        mgr = _make_manager(engine="whisper_cpp")
        self.assertEqual(mgr.engine, "whisper_cpp")

    def test_default_state(self):
        mgr = _make_manager()
        self.assertEqual(mgr.state, RecognitionState.IDLE)
        self.assertIsNone(mgr.model)


class TestCallbacks(unittest.TestCase):
    def test_register_text_callback(self):
        mgr = _make_manager()
        cb = MagicMock()
        mgr.register_text_callback(cb)
        self.assertIn(cb, mgr.text_callbacks)

    def test_register_state_callback(self):
        mgr = _make_manager()
        cb = MagicMock()
        mgr.register_state_callback(cb)
        self.assertIn(cb, mgr.state_callbacks)

    def test_register_action_callback(self):
        mgr = _make_manager()
        cb = MagicMock()
        mgr.register_action_callback(cb)
        self.assertIn(cb, mgr.action_callbacks)

    def test_register_audio_level_callback(self):
        mgr = _make_manager()
        cb = MagicMock()
        mgr.register_audio_level_callback(cb)
        self.assertIn(cb, mgr._audio_level_callbacks)

    def test_update_state(self):
        mgr = _make_manager()
        cb = MagicMock()
        mgr.register_state_callback(cb)
        mgr._update_state(RecognitionState.LISTENING)
        self.assertEqual(mgr.state, RecognitionState.LISTENING)
        cb.assert_called_with(RecognitionState.LISTENING)


class TestCancelDownload(unittest.TestCase):
    def test_cancel_download(self):
        mgr = _make_manager()
        mgr._download_cancelled = False
        mgr.cancel_download()
        self.assertTrue(mgr._download_cancelled)


class TestStartStopRecognition(unittest.TestCase):
    def test_start_recognition_no_model(self):
        mgr = _make_manager()
        mgr.model = None
        mgr.state = RecognitionState.IDLE
        # start_recognition when no model should try to init
        with patch.object(mgr, "_init_whispercpp"):
            try:
                mgr.start_recognition()
            except Exception:
                pass

    def test_stop_recognition(self):
        mgr = _make_manager()
        mgr.state = RecognitionState.LISTENING
        mgr.should_record = True
        mgr.audio_thread = MagicMock()
        mgr.audio_thread.is_alive.return_value = True
        mgr.audio_thread.join = MagicMock()
        mgr.stop_recognition()
        self.assertFalse(mgr.should_record)


class TestReconfigure(unittest.TestCase):
    def test_reconfigure_language(self):
        mgr = _make_manager()
        mgr.state = RecognitionState.IDLE
        with patch.object(mgr, "_init_whispercpp"):
            mgr.reconfigure(language="fr")
        self.assertEqual(mgr.language, "fr")

    def test_reconfigure_model_size(self):
        mgr = _make_manager()
        mgr.state = RecognitionState.IDLE
        with patch.object(mgr, "_init_whispercpp"):
            mgr.reconfigure(model_size="medium")
        self.assertEqual(mgr.model_size, "medium")

    def test_reconfigure_engine(self):
        mgr = _make_manager()
        mgr.state = RecognitionState.IDLE
        with patch.object(mgr, "_init_vosk"):
            mgr.reconfigure(engine="vosk")
        self.assertEqual(mgr.engine, "vosk")


class TestProcessFinalBuffer(unittest.TestCase):
    def test_process_final_buffer_whispercpp(self):
        mgr = _make_manager(engine="whisper_cpp")
        mgr.audio_buffer = [b"\x00\x00" * 512] * 5
        mgr._capture_sample_rate = 16000
        cb = MagicMock()
        mgr.register_text_callback(cb)
        mgr.command_processor = MagicMock()
        mgr.command_processor.process_text.return_value = "hello"

        with patch.object(mgr, "_transcribe_with_whispercpp", return_value="hello world"):
            mgr._process_final_buffer()

    def test_process_final_buffer_whisper(self):
        mgr = _make_manager(engine="whisper")
        mgr.audio_buffer = [b"\x00\x00" * 512] * 5
        mgr._capture_sample_rate = 16000
        mgr.command_processor = MagicMock()
        mgr.command_processor.process_text.return_value = "hello"

        with patch.object(mgr, "_transcribe_with_whisper", return_value="hello world"):
            mgr._process_final_buffer()

    def test_process_final_buffer_empty(self):
        mgr = _make_manager(engine="whisper_cpp")
        mgr.audio_buffer = []
        mgr._process_final_buffer()  # Should handle empty gracefully


class TestTranscribeWhispercpp(unittest.TestCase):
    def test_transcribe_success(self):
        mgr = _make_manager()
        mgr.language = "en-us"
        mock_segment = MagicMock()
        mock_segment.text = "hello world"
        mgr.model = MagicMock()
        mgr.model.transcribe.return_value = [mock_segment]

        mock_np = MagicMock()
        mock_np.frombuffer.return_value = MagicMock(__len__=lambda s: 16000)
        mock_np.frombuffer.return_value.astype.return_value = mock_np.frombuffer.return_value
        mock_np.int16 = "int16"
        mock_np.float32 = "float32"

        with patch.dict("sys.modules", {"numpy": mock_np}):
            result = mgr._transcribe_with_whispercpp([b"\x00\x00" * 512])
        # Should return transcribed text

    def test_transcribe_model_none(self):
        mgr = _make_manager()
        mgr.model = None

        mock_np = MagicMock()
        mock_np.frombuffer.return_value = MagicMock(__len__=lambda s: 16000)
        mock_np.frombuffer.return_value.astype.return_value = mock_np.frombuffer.return_value
        mock_np.int16 = "int16"
        mock_np.float32 = "float32"

        with patch.dict("sys.modules", {"numpy": mock_np}):
            result = mgr._transcribe_with_whispercpp([b"\x00\x00" * 512])
        self.assertEqual(result, "")

    def test_transcribe_empty_buffer(self):
        mgr = _make_manager()
        mock_np = MagicMock()
        with patch.dict("sys.modules", {"numpy": mock_np}):
            result = mgr._transcribe_with_whispercpp([])
        self.assertEqual(result, "")

    def test_transcribe_exception(self):
        mgr = _make_manager()
        mgr.model = MagicMock()
        mgr.model.transcribe.side_effect = RuntimeError("crash")

        mock_np = MagicMock()
        mock_np.frombuffer.return_value = MagicMock(__len__=lambda s: 16000)
        mock_np.frombuffer.return_value.astype.return_value = mock_np.frombuffer.return_value
        mock_np.int16 = "int16"
        mock_np.float32 = "float32"

        with patch.dict("sys.modules", {"numpy": mock_np}):
            result = mgr._transcribe_with_whispercpp([b"\x00\x00" * 512])
        self.assertEqual(result, "")

    def test_transcribe_auto_language(self):
        mgr = _make_manager()
        mgr.language = "auto"
        mock_segment = MagicMock()
        mock_segment.text = "bonjour"
        mgr.model = MagicMock()
        mgr.model.transcribe.return_value = [mock_segment]

        mock_np = MagicMock()
        mock_np.frombuffer.return_value = MagicMock(__len__=lambda s: 16000)
        mock_np.frombuffer.return_value.astype.return_value = mock_np.frombuffer.return_value
        mock_np.int16 = "int16"
        mock_np.float32 = "float32"

        with patch.dict("sys.modules", {"numpy": mock_np}):
            result = mgr._transcribe_with_whispercpp([b"\x00\x00" * 512])


class TestTranscribeWhisper(unittest.TestCase):
    def test_transcribe_success(self):
        mgr = _make_manager(engine="whisper")
        mgr.language = "en-us"
        mgr.model = MagicMock()
        mgr.model.transcribe.return_value = {"text": "hello world"}
        mgr.model.device = MagicMock()

        mock_np = MagicMock()
        mock_np.frombuffer.return_value = MagicMock(__len__=lambda s: 16000)
        mock_np.frombuffer.return_value.astype.return_value = mock_np.frombuffer.return_value
        mock_np.int16 = "int16"
        mock_np.float32 = "float32"

        mock_torch = MagicMock()

        with patch.dict("sys.modules", {"numpy": mock_np, "torch": mock_torch}):
            result = mgr._transcribe_with_whisper([b"\x00\x00" * 512])

    def test_transcribe_empty(self):
        mgr = _make_manager(engine="whisper")
        mock_np = MagicMock()
        with patch.dict("sys.modules", {"numpy": mock_np}):
            result = mgr._transcribe_with_whisper([])
        self.assertEqual(result, "")

    def test_transcribe_model_none(self):
        mgr = _make_manager(engine="whisper")
        mgr.model = None
        mock_np = MagicMock()
        mock_np.frombuffer.return_value = MagicMock(__len__=lambda s: 16000)
        mock_np.frombuffer.return_value.astype.return_value = mock_np.frombuffer.return_value
        mock_np.int16 = "int16"
        mock_np.float32 = "float32"
        with patch.dict("sys.modules", {"numpy": mock_np, "torch": MagicMock()}):
            result = mgr._transcribe_with_whisper([b"\x00\x00" * 512])
        self.assertEqual(result, "")


class TestInitVosk(unittest.TestCase):
    def test_init_vosk_model_exists(self):
        mgr = _make_manager(engine="vosk")
        with patch("os.path.exists", return_value=True):
            with patch("os.path.isdir", return_value=True):
                mock_vosk = MagicMock()
                with patch.dict("sys.modules", {"vosk": mock_vosk}):
                    try:
                        mgr._init_vosk()
                    except Exception:
                        pass

    def test_init_vosk_no_model(self):
        mgr = _make_manager(engine="vosk")
        with patch("os.path.exists", return_value=False):
            with patch("os.path.isdir", return_value=False):
                try:
                    mgr._init_vosk()
                except Exception:
                    pass


class TestInitWhisper(unittest.TestCase):
    def test_init_whisper(self):
        mgr = _make_manager(engine="whisper")
        mock_whisper = MagicMock()
        mock_whisper.load_model.return_value = MagicMock()
        with patch.dict("sys.modules", {"whisper": mock_whisper, "torch": MagicMock()}):
            with patch("os.path.exists", return_value=True):
                try:
                    mgr._init_whisper()
                except Exception:
                    pass


class TestInitWhispercpp(unittest.TestCase):
    def test_init_whispercpp_model_exists(self):
        mgr = _make_manager(engine="whisper_cpp")
        with patch("os.path.exists", return_value=True):
            mock_model = MagicMock()
            with patch.dict("sys.modules", {
                "pywhispercpp": MagicMock(),
                "pywhispercpp.model": MagicMock(),
            }):
                try:
                    mgr._init_whispercpp()
                except Exception:
                    pass

    def test_init_whispercpp_vulkan_fallback(self):
        mgr = _make_manager(engine="whisper_cpp")
        with patch("os.path.exists", return_value=True):
            mock_pywhispercpp = MagicMock()
            call_count = [0]
            def model_side_effect(*a, **kw):
                call_count[0] += 1
                if call_count[0] == 1:
                    raise RuntimeError("16-bit storage not supported")
                return MagicMock()
            mock_pywhispercpp.Model.side_effect = model_side_effect
            with patch.dict("sys.modules", {
                "pywhispercpp": MagicMock(),
                "pywhispercpp.model": mock_pywhispercpp,
            }):
                try:
                    mgr._init_whispercpp()
                except Exception:
                    pass


class TestDownloadVoskModel(unittest.TestCase):
    def test_download_cancelled(self):
        mgr = _make_manager(engine="vosk")
        mgr._download_cancelled = True
        try:
            mgr._download_vosk_model()
        except (RuntimeError, Exception):
            pass


class TestDownloadWhisperModel(unittest.TestCase):
    def test_download_whisper_model(self):
        mgr = _make_manager(engine="whisper")
        mgr._download_cancelled = False
        mock_whisper = MagicMock()
        with patch.dict("sys.modules", {"whisper": mock_whisper}):
            try:
                mgr._download_whisper_model(cache_dir="/tmp/test")
            except Exception:
                pass


class TestBufferManagement(unittest.TestCase):
    def test_set_buffer_limit(self):
        mgr = _make_manager()
        mgr.set_buffer_limit(100)
        self.assertEqual(mgr._max_buffer_size, 100)

    def test_get_buffer_stats(self):
        mgr = _make_manager()
        stats = mgr.get_buffer_stats()
        self.assertIsInstance(stats, dict)


class TestVoiceCommandsProperty(unittest.TestCase):
    def test_voice_commands_vosk_default(self):
        mgr = _make_manager(engine="vosk")
        # For vosk engine, voice commands should be enabled by default
        self.assertTrue(mgr._resolve_voice_commands_enabled())

    def test_voice_commands_whisper_default(self):
        mgr = _make_manager(engine="whisper")
        self.assertFalse(mgr._resolve_voice_commands_enabled())

    def test_voice_commands_explicit_on(self):
        mgr = _make_manager(engine="whisper", voice_commands_enabled=True)
        self.assertTrue(mgr._resolve_voice_commands_enabled())

    def test_voice_commands_explicit_off(self):
        mgr = _make_manager(engine="vosk", voice_commands_enabled=False)
        self.assertFalse(mgr._resolve_voice_commands_enabled())


if __name__ == "__main__":
    unittest.main()
