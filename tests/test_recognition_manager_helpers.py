"""Tests for standalone helper functions in recognition_manager.py."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest


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


# Ensure external deps are mocked
_MOCK_KEYS = ["vosk", "whisper", "torch", "pyaudio", "pywhispercpp", "pywhispercpp.model"]
_ORIG = {}
for _k in _MOCK_KEYS:
    _ORIG[_k] = sys.modules.get(_k)
    if _k not in sys.modules:
        sys.modules[_k] = MagicMock()
if "gi" not in sys.modules:
    sys.modules["gi"] = MagicMock()
if "gi.repository" not in sys.modules:
    sys.modules["gi.repository"] = MagicMock()

from vocalinux.speech_recognition.recognition_manager import (
    SpeechRecognitionManager,
    _filter_non_speech,
    _get_system_model_paths,
    _show_notification,
)
from vocalinux.speech_recognition.recognition_manager import (  # noqa: E402
    test_audio_input as _test_audio_input,
)

# Restore immediately
for _k, _v in _ORIG.items():
    if _v is not None:
        sys.modules[_k] = _v
    elif _k in sys.modules and isinstance(sys.modules[_k], MagicMock):
        del sys.modules[_k]


class TestFilterNonSpeech(unittest.TestCase):
    """Test _filter_non_speech function."""

    def test_empty_string(self):
        self.assertEqual(_filter_non_speech(""), "")

    def test_whitespace_only(self):
        self.assertEqual(_filter_non_speech("   "), "")

    def test_normal_text(self):
        result = _filter_non_speech("Hello world, this is a test.")
        self.assertEqual(result, "Hello world, this is a test.")

    def test_low_speech_content(self):
        # Text with mostly non-alphanumeric characters
        result = _filter_non_speech("♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪")
        self.assertEqual(result, "")

    def test_known_hallucination_patterns(self):
        # Test that actual speech passes through the filter
        result = _filter_non_speech("Thank you for watching!")
        # This is actual speech content, should pass through
        self.assertIn("Thank", result)

    def test_mixed_content(self):
        # Test that normal speech content is preserved
        result = _filter_non_speech("Hello, how are you?")
        # Normal speech should be preserved
        self.assertIn("Hello", result)
        self.assertIn("how", result)
        self.assertIn("are", result)
        self.assertIn("you", result)


class TestShowNotification(unittest.TestCase):
    """Test _show_notification function."""

    def test_show_notification_success(self):
        with patch("subprocess.Popen") as mock_popen:
            _show_notification("Test Title", "Test Message")
            mock_popen.assert_called_once()

    def test_show_notification_custom_icon(self):
        with patch("subprocess.Popen") as mock_popen:
            _show_notification("Title", "Message", icon="dialog-information")
            mock_popen.assert_called_once()

    def test_show_notification_error(self):
        with patch("subprocess.Popen", side_effect=Exception("no notify-send")):
            # Should not raise
            _show_notification("Title", "Message")


class TestGetSystemModelPaths(unittest.TestCase):
    """Test _get_system_model_paths function."""

    def test_default_paths(self):
        with patch.dict(os.environ, {"XDG_DATA_DIRS": "/usr/local/share:/usr/share"}):
            paths = _get_system_model_paths()
            self.assertIsInstance(paths, list)
            self.assertGreater(len(paths), 0)

    def test_custom_xdg_dirs(self):
        with patch.dict(os.environ, {"XDG_DATA_DIRS": "/custom/share"}):
            paths = _get_system_model_paths()
            self.assertTrue(any("/custom/share" in p for p in paths))

    def test_empty_xdg_dirs(self):
        with patch.dict(os.environ, {"XDG_DATA_DIRS": ""}):
            paths = _get_system_model_paths()
            self.assertIsInstance(paths, list)

    def test_fedora_paths(self):
        mock_os_release = 'NAME="Fedora Linux"\nID=fedora\n'
        with patch.dict(os.environ, {"XDG_DATA_DIRS": "/usr/share"}):
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__ = lambda s: s
                mock_open.return_value.__exit__ = MagicMock(return_value=False)
                mock_open.return_value.read.return_value = mock_os_release
                paths = _get_system_model_paths()
                self.assertIsInstance(paths, list)

    def test_os_release_not_found(self):
        with patch.dict(os.environ, {"XDG_DATA_DIRS": "/usr/share"}):
            with patch("builtins.open", side_effect=FileNotFoundError()):
                paths = _get_system_model_paths()
                self.assertIsInstance(paths, list)


class TestTestAudioInput(unittest.TestCase):
    """Test test_audio_input function."""

    def test_basic_audio_test(self):
        mock_pa_mod = MagicMock()
        mock_pa_inst = MagicMock()
        mock_pa_mod.PyAudio.return_value = mock_pa_inst
        mock_pa_mod.paInt16 = 8

        mock_pa_inst.get_default_input_device_info.return_value = {
            "name": "Test Mic",
            "index": 0,
            "defaultSampleRate": 16000,
        }

        mock_stream = MagicMock()
        mock_pa_inst.open.return_value = mock_stream
        mock_stream.read.return_value = b"\x00\xf4" * 1024

        mock_np = MagicMock()
        mock_np.int16 = "int16"
        mock_np.frombuffer.return_value = MagicMock()
        mock_np.abs.return_value = [500] * 1024
        mock_np.array.return_value = MagicMock()
        mock_np.max.return_value = 500.0
        mock_np.mean.return_value = 250.0

        with patch.dict("sys.modules", {"pyaudio": mock_pa_mod, "numpy": mock_np}):
            result = _test_audio_input()
        self.assertIsInstance(result, dict)

    def test_audio_input_import_error(self):
        # When pyaudio is not available
        with patch.dict("sys.modules", {"pyaudio": None}):
            try:
                result = _test_audio_input()
                self.assertIn("error", result)
            except ImportError:
                pass  # Expected if module is None

    def test_audio_input_with_index(self):
        mock_pa_mod = MagicMock()
        mock_pa_inst = MagicMock()
        mock_pa_mod.PyAudio.return_value = mock_pa_inst
        mock_pa_mod.paInt16 = 8

        mock_pa_inst.get_device_info_by_index.return_value = {
            "name": "USB Mic",
            "index": 1,
            "defaultSampleRate": 44100,
        }

        mock_stream = MagicMock()
        mock_pa_inst.open.return_value = mock_stream
        mock_stream.read.return_value = b"\x00" * 2048

        mock_np = MagicMock()
        mock_np.int16 = "int16"
        mock_np.frombuffer.return_value = MagicMock()
        mock_np.abs.return_value = [0, 0, 0]
        mock_np.array.return_value = MagicMock()
        mock_np.max.return_value = 0.0
        mock_np.mean.return_value = 0.0

        with patch.dict("sys.modules", {"pyaudio": mock_pa_mod, "numpy": mock_np}):
            result = _test_audio_input(device_index=1)
        self.assertIsInstance(result, dict)

    def test_audio_input_open_error(self):
        mock_pa_mod = MagicMock()
        mock_pa_inst = MagicMock()
        mock_pa_mod.PyAudio.return_value = mock_pa_inst
        mock_pa_mod.paInt16 = 8

        mock_pa_inst.get_default_input_device_info.return_value = {
            "name": "Mic",
            "index": 0,
            "defaultSampleRate": 16000,
        }
        mock_pa_inst.open.side_effect = IOError("Cannot open stream")

        with patch.dict("sys.modules", {"pyaudio": mock_pa_mod}):
            result = _test_audio_input()
        self.assertIn("error", result)

    def test_audio_input_info_error(self):
        mock_pa_mod = MagicMock()
        mock_pa_inst = MagicMock()
        mock_pa_mod.PyAudio.return_value = mock_pa_inst
        mock_pa_mod.paInt16 = 8
        mock_pa_inst.get_default_input_device_info.side_effect = IOError("No device")

        with patch.dict("sys.modules", {"pyaudio": mock_pa_mod}):
            result = _test_audio_input()
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
