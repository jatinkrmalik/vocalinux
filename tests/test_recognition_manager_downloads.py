"""
Coverage boost tests targeting major gaps in recognition_manager and ibus_engine.

Key focus areas:
- Model download methods with progress tracking
- Audio reconnection logic
- IBus engine utility functions
"""

import os
import sys
import time
import zipfile as REAL_ZIPFILE  # Capture real zipfile before any test mocks it
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


class MockRequestException(Exception):
    pass


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


def _mock_requests(chunks):
    mock_requests = MagicMock()
    response = mock_requests.get.return_value
    response.headers = {"content-length": "10"}
    response.iter_content.return_value = chunks
    mock_requests.exceptions.RequestException = MockRequestException
    return mock_requests


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

    def test_unknown_model_is_rejected(self):
        manager = _make_manager(engine="whisper_cpp")
        manager.model_size = "missing"

        with pytest.raises(ValueError, match="Unknown whisper.cpp model size"):
            manager._download_whispercpp_model()


class TestDownloadCleanup:
    def test_cancelled_download_removes_partial_file(self, tmp_path):
        manager = _make_manager()
        destination = tmp_path / "model.bin"

        def chunks():
            yield b"partial"
            manager._download_cancelled = True
            yield b"cancel"

        with patch.dict(
            "sys.modules", {"requests": _mock_requests(chunks()), "zipfile": REAL_ZIPFILE}
        ):
            with pytest.raises(RuntimeError, match="cancelled"):
                manager._download_with_progress("https://example.test/model", str(destination))

        assert not Path(f"{destination}.tmp").exists()

    def test_stream_error_removes_partial_file(self, tmp_path):
        manager = _make_manager()
        destination = tmp_path / "model.bin"

        def chunks():
            yield b"partial"
            raise MockRequestException("network interrupted")

        with patch.dict(
            "sys.modules", {"requests": _mock_requests(chunks()), "zipfile": REAL_ZIPFILE}
        ):
            with pytest.raises(RuntimeError, match="Failed to download"):
                manager._download_with_progress("https://example.test/model", str(destination))

        assert not Path(f"{destination}.tmp").exists()

    def test_corrupt_zip_is_removed(self, tmp_path):
        manager = _make_manager()
        archive = tmp_path / "model.zip"

        with patch.dict(
            "sys.modules",
            {"requests": _mock_requests([b"not a zip"]), "zipfile": REAL_ZIPFILE},
        ):
            with pytest.raises(RuntimeError, match="corrupted"):
                manager._download_with_progress(
                    "https://example.test/model.zip",
                    str(archive),
                    extract_zip=True,
                    extract_dir=str(tmp_path),
                )

        assert not archive.exists()


class TestDownloadVoskModel:
    """Test _download_vosk_model() with runtime import mocking."""

    def test_download_vosk_progress_callback(self, tmp_path):
        """Test progress callback during Vosk download."""
        manager = _make_manager(engine="vosk")
        progress_calls = []

        def track_progress(progress, speed, status):
            progress_calls.append((progress, speed, status))

        manager._download_progress_callback = track_progress
        (tmp_path / "model-en-us-0.22-lgraph" / "am").mkdir(parents=True)

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

    def test_attempt_audio_reconnection_falls_back_to_default_resolver(self):
        """Test reconnection falls back when saved device name/index cannot resolve."""
        manager = _make_manager(engine="whisper_cpp", audio_device_name="Missing Mic")

        mock_pyaudio_mod = MagicMock()
        mock_pyaudio_mod.paInt16 = 8
        mock_stream = MagicMock()
        mock_stream.read.return_value = b"\x00" * 1024
        mock_audio_instance = MagicMock()
        mock_audio_instance.get_default_input_device_info.return_value = {"index": 0}
        mock_audio_instance.open.return_value = mock_stream

        with (
            patch.dict("sys.modules", {"pyaudio": mock_pyaudio_mod}),
            patch("time.sleep"),
            patch(
                "vocalinux.speech_recognition.recognition_manager._resolve_device_by_name",
                return_value=None,
            ) as mock_resolve_name,
            patch(
                "vocalinux.speech_recognition.recognition_manager._resolve_valid_input_device",
                return_value=1,
            ) as mock_resolve_default,
            patch(
                "vocalinux.speech_recognition.recognition_manager._get_supported_channels",
                return_value=1,
            ),
            patch(
                "vocalinux.speech_recognition.recognition_manager._get_supported_sample_rate",
                return_value=16000,
            ),
        ):
            result = manager._attempt_audio_reconnection(mock_audio_instance)

        assert result is True
        assert manager._audio_stream == mock_stream
        mock_resolve_name.assert_called_once_with(mock_audio_instance, "Missing Mic", None)
        mock_resolve_default.assert_called_once_with(mock_audio_instance, None)

    def test_attempt_audio_reconnection_no_resolved_device(self):
        """Test reconnection fails when no resolver finds an input device."""
        manager = _make_manager(engine="whisper_cpp", audio_device_name="Missing Mic")

        mock_pyaudio_mod = MagicMock()
        mock_audio_instance = MagicMock()

        with (
            patch.dict("sys.modules", {"pyaudio": mock_pyaudio_mod}),
            patch("time.sleep"),
            patch(
                "vocalinux.speech_recognition.recognition_manager._resolve_device_by_name",
                return_value=None,
            ),
            patch(
                "vocalinux.speech_recognition.recognition_manager._resolve_valid_input_device",
                return_value=None,
            ),
        ):
            result = manager._attempt_audio_reconnection(mock_audio_instance)

        assert result is False
        mock_audio_instance.open.assert_not_called()

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
