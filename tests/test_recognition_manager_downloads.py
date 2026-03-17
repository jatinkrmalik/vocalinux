"""
Coverage boost tests targeting major gaps in recognition_manager and ibus_engine.

Key focus areas:
- Model download methods with progress tracking
- Audio reconnection logic
- IBus engine utility functions
"""

import importlib.util
import os
import sys
import sysconfig
import time
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Mock GI imports before importing any vocalinux modules that use gi.
# On CI, real gi/IBus packages are installed; without mocks, importing
# ibus_engine would connect to a real IBus daemon and hang.
if "gi" not in sys.modules:
    sys.modules["gi"] = MagicMock()
if "gi.repository" not in sys.modules:
    sys.modules["gi.repository"] = MagicMock()

from vocalinux.speech_recognition.recognition_manager import (
    SpeechRecognitionManager,
)


def _load_stdlib_module(module_name: str):
    """Load a real stdlib module even if sys.modules was polluted by test mocks.

    Handles both single-file modules (e.g. ``zipfile.py``) and package modules
    (e.g. ``zipfile/`` directory with ``__init__.py``) which can vary across
    Python versions (``zipfile`` became a package in Python 3.13).
    """
    stdlib_path = sysconfig.get_path("stdlib")

    # Try single-file module first, then package (directory with __init__.py)
    module_file = os.path.join(stdlib_path, f"{module_name}.py")
    package_init = os.path.join(stdlib_path, module_name, "__init__.py")

    if os.path.isfile(module_file):
        module_path = module_file
    elif os.path.isfile(package_init):
        module_path = package_init
    else:
        raise FileNotFoundError(
            f"Cannot find stdlib module '{module_name}' at {module_file} or {package_init}"
        )

    spec = importlib.util.spec_from_file_location(f"_stdlib_{module_name}", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


REAL_ZIPFILE = _load_stdlib_module("zipfile")


def _make_manager(engine="whisper_cpp", **kw):
    """Create a SpeechRecognitionManager with mocked initialization."""
    with patch.object(SpeechRecognitionManager, "_init_vosk"):
        with patch.object(SpeechRecognitionManager, "_init_whisper"):
            with patch.object(SpeechRecognitionManager, "_init_whispercpp"):
                mgr = SpeechRecognitionManager(
                    engine=engine, model_size="small", language="en-us", defer_download=True, **kw
                )
                # Ensure vosk_model_map is set (normally done in _init_vosk)
                if not hasattr(mgr, "vosk_model_map"):
                    mgr.vosk_model_map = {
                        "small": "model-en-us-0.22-lgraph",
                        "medium": "vosk-model-en-us-0.22",
                        "large": "vosk-model-en-us-0.22-lgraph",
                    }
                return mgr


@pytest.fixture(autouse=True)
def cleanup_sys_modules():
    """Cleanup sys.modules after each test - full snapshot/restore."""
    # Take a complete snapshot of sys.modules before the test
    saved_modules = dict(sys.modules)

    yield

    # Restore sys.modules to exact pre-test state
    added_keys = set(sys.modules.keys()) - set(saved_modules.keys())
    for key in added_keys:
        del sys.modules[key]
    for key, value in saved_modules.items():
        if key not in sys.modules or sys.modules[key] is not value:
            sys.modules[key] = value


class TestDownloadWhispercppModel:
    """Test _download_whispercpp_model() with runtime import mocking."""

    def test_download_whispercpp_success_basic(self, tmp_path):
        """Test successful whisper.cpp model download."""
        manager = _make_manager(engine="whisper_cpp")
        model_file = str(tmp_path / "ggml-small.bin")

        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "1000"}
        mock_response.iter_content.return_value = [b"x" * 500, b"y" * 500]
        mock_requests.get.return_value = mock_response
        mock_requests.exceptions.RequestException = Exception

        with patch.dict("sys.modules", {"requests": mock_requests}):
            with patch(
                "vocalinux.speech_recognition.recognition_manager.get_model_path",
                return_value=model_file,
            ):
                manager._download_whispercpp_model()

        assert os.path.exists(model_file)
        assert os.path.getsize(model_file) == 1000

    def test_download_whispercpp_progress_callback(self, tmp_path):
        """Test progress callback is invoked during download."""
        manager = _make_manager(engine="whisper_cpp")
        progress_calls = []

        def track_progress(progress, speed, status):
            progress_calls.append((progress, speed, status))

        manager._download_progress_callback = track_progress
        model_file = str(tmp_path / "ggml-small.bin")

        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {"content-length": "1000"}
        mock_response.iter_content.return_value = [b"x" * 500, b"y" * 500]
        mock_requests.get.return_value = mock_response
        mock_requests.exceptions.RequestException = Exception

        with patch.dict("sys.modules", {"requests": mock_requests}):
            with patch(
                "vocalinux.speech_recognition.recognition_manager.get_model_path",
                return_value=model_file,
            ):
                with patch("time.time", side_effect=[0, 0.2, 0.4, 0.6]):
                    manager._download_whispercpp_model()

        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert call_args is not None
        assert len(call_args[0]) > 0 or "url" in call_args[1]
        assert len(progress_calls) >= 1

    def test_download_whispercpp_no_content_length(self, tmp_path):
        """Test download when content-length header is missing."""
        manager = _make_manager(engine="whisper_cpp")
        model_file = str(tmp_path / "ggml-small.bin")

        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {}  # No content-length
        mock_response.iter_content.return_value = [b"x" * 500, b"y" * 500]
        mock_requests.get.return_value = mock_response
        mock_requests.exceptions.RequestException = Exception

        with patch.dict("sys.modules", {"requests": mock_requests}):
            with patch(
                "vocalinux.speech_recognition.recognition_manager.get_model_path",
                return_value=model_file,
            ):
                manager._download_whispercpp_model()

        assert os.path.exists(model_file)

    def test_download_whispercpp_request_error(self, tmp_path):
        """Test download request error handling."""
        manager = _make_manager(engine="whisper_cpp")
        model_file = str(tmp_path / "ggml-small.bin")

        mock_requests = MagicMock()
        mock_error = Exception("Network error")
        mock_requests.get.side_effect = mock_error
        mock_requests.exceptions.RequestException = Exception

        with patch.dict("sys.modules", {"requests": mock_requests}):
            with patch(
                "vocalinux.speech_recognition.recognition_manager.get_model_path",
                return_value=model_file,
            ):
                with pytest.raises(RuntimeError, match="Failed to download"):
                    manager._download_whispercpp_model()


class TestDownloadVoskModel:
    """Test _download_vosk_model() with runtime import mocking."""

    def test_download_vosk_progress_callback(self, tmp_path):
        """Test progress callback during Vosk download."""
        manager = _make_manager(engine="vosk")
        progress_calls = []

        def track_progress(progress, speed, status):
            progress_calls.append((progress, speed, status))

        manager._download_progress_callback = track_progress

        zip_data = BytesIO()
        with REAL_ZIPFILE.ZipFile(zip_data, "w") as zf:
            zf.writestr("model-en-us-0.22-lgraph/am/model.pkl", "x" * 5000)
        zip_bytes = zip_data.getvalue()

        mock_requests = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {"content-length": str(len(zip_bytes))}
        mock_response.iter_content.return_value = [zip_bytes]
        mock_requests.get.return_value = mock_response
        mock_requests.exceptions.RequestException = Exception

        with patch.dict("sys.modules", {"requests": mock_requests}):
            with patch(
                "vocalinux.speech_recognition.recognition_manager.MODELS_DIR", str(tmp_path)
            ):
                with patch("time.time", side_effect=[0, 0.2, 0.4, 0.6]):
                    manager._download_vosk_model()

        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert call_args is not None
        assert len(call_args[0]) > 0 or "url" in call_args[1]
        assert len(progress_calls) >= 1

    def test_download_vosk_request_error(self, tmp_path):
        """Test Vosk download request error handling."""
        manager = _make_manager(engine="vosk")

        mock_requests = MagicMock()
        mock_error = Exception("Network error")
        mock_requests.get.side_effect = mock_error
        mock_requests.exceptions.RequestException = Exception

        with patch.dict("sys.modules", {"requests": mock_requests}):
            with patch(
                "vocalinux.speech_recognition.recognition_manager.MODELS_DIR", str(tmp_path)
            ):
                with pytest.raises(RuntimeError, match="Failed to download"):
                    manager._download_vosk_model()


class TestAudioReconnection:
    """Test audio reconnection logic."""

    def test_attempt_audio_reconnection_success(self):
        """Test successful audio reconnection."""
        manager = _make_manager(engine="whisper_cpp")

        mock_pyaudio_mod = MagicMock()
        mock_pyaudio_mod.paInt16 = 8
        mock_stream = MagicMock()
        mock_stream.read.return_value = b"\x00" * 1024
        mock_audio_instance = MagicMock()
        mock_audio_instance.open.return_value = mock_stream

        with patch.dict("sys.modules", {"pyaudio": mock_pyaudio_mod}):
            with patch("time.sleep"):
                result = manager._attempt_audio_reconnection(mock_audio_instance)

        assert result is True
        assert manager._audio_stream == mock_stream

    def test_attempt_audio_reconnection_max_attempts(self):
        """Test reconnection stops after max attempts."""
        manager = _make_manager(engine="whisper_cpp")
        manager._reconnection_attempts = manager._max_reconnection_attempts

        mock_audio_instance = MagicMock()

        with patch.dict("sys.modules", {"pyaudio": MagicMock()}):
            result = manager._attempt_audio_reconnection(mock_audio_instance)

        assert result is False

    def test_attempt_audio_reconnection_open_failure(self):
        """Test reconnection when stream open fails."""
        manager = _make_manager(engine="whisper_cpp")

        mock_pyaudio_mod = MagicMock()
        mock_pyaudio_mod.paInt16 = 8
        mock_audio_instance = MagicMock()
        mock_audio_instance.open.side_effect = IOError("Cannot open stream")

        with patch.dict("sys.modules", {"pyaudio": mock_pyaudio_mod}):
            with patch("time.sleep"):
                result = manager._attempt_audio_reconnection(mock_audio_instance)

        assert result is False

    def test_attempt_audio_reconnection_exponential_backoff(self):
        """Test exponential backoff in reconnection attempts."""
        manager = _make_manager(engine="whisper_cpp")
        manager._reconnection_delay = 0.1

        mock_pyaudio_mod = MagicMock()
        mock_pyaudio_mod.paInt16 = 8
        mock_stream = MagicMock()
        mock_stream.read.return_value = b"\x00" * 1024
        mock_audio_instance = MagicMock()
        mock_audio_instance.open.return_value = mock_stream

        sleep_durations = []

        def track_sleep(duration):
            sleep_durations.append(duration)

        with patch.dict("sys.modules", {"pyaudio": mock_pyaudio_mod}):
            with patch("time.sleep", side_effect=track_sleep):
                manager._reconnection_attempts = 0
                manager._attempt_audio_reconnection(mock_audio_instance)
                first_delay = sleep_durations[-1]

                manager._reconnection_attempts = 1
                manager._attempt_audio_reconnection(mock_audio_instance)
                second_delay = sleep_durations[-1]

        assert second_delay > first_delay
        assert second_delay == first_delay * 2


class TestIBusEngineUtilities:
    """Test ibus_engine utility functions."""

    def test_is_ibus_available(self):
        """Test is_ibus_available() function."""
        from vocalinux.text_injection.ibus_engine import is_ibus_available

        result = is_ibus_available()
        assert isinstance(result, bool)

    def test_is_ibus_daemon_running(self):
        """Test daemon detection when not running."""
        from vocalinux.text_injection.ibus_engine import is_ibus_daemon_running

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            result = is_ibus_daemon_running()
            assert result is False

    def test_is_ibus_daemon_running_success(self):
        """Test daemon detection when running."""
        from vocalinux.text_injection.ibus_engine import is_ibus_daemon_running

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
