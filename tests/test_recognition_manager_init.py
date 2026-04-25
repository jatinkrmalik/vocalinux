"""
Additional coverage tests for recognition_manager.py module.

Tests for uncovered initialization paths, error handling, and edge cases.
"""

import os
import sys
from unittest.mock import MagicMock, Mock, mock_open, patch

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


def _make_manager(engine="whisper_cpp", **kw):
    """Helper to create SpeechRecognitionManager with init methods patched."""
    from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

    with patch.object(SpeechRecognitionManager, "_init_vosk"):
        with patch.object(SpeechRecognitionManager, "_init_whisper"):
            with patch.object(SpeechRecognitionManager, "_init_whispercpp"):
                return SpeechRecognitionManager(
                    engine=engine, model_size="small", language="en-us", defer_download=True, **kw
                )


class TestSpeechRecognitionManagerInit:
    """Tests for SpeechRecognitionManager initialization."""

    def test_manager_init_whisper_cpp_engine(self):
        """Test manager initialization with whisper_cpp engine."""
        manager = _make_manager(engine="whisper_cpp")
        assert manager.engine == "whisper_cpp"
        assert manager.model_size == "small"
        assert manager.language == "en-us"

    def test_manager_init_vosk_engine(self):
        """Test manager initialization with vosk engine."""
        manager = _make_manager(engine="vosk")
        assert manager.engine == "vosk"

    def test_manager_init_whisper_engine(self):
        """Test manager initialization with whisper engine."""
        manager = _make_manager(engine="whisper")
        assert manager.engine == "whisper"

    def test_manager_init_with_audio_device_index(self):
        """Test manager initialization with audio device index."""
        manager = _make_manager(audio_device_index=2)
        assert manager.audio_device_index == 2

    def test_manager_init_with_vad_sensitivity(self):
        """Test manager initialization with VAD sensitivity."""
        manager = _make_manager(vad_sensitivity=5)
        assert manager.vad_sensitivity == 5

    def test_manager_init_with_silence_timeout(self):
        """Test manager initialization with silence timeout."""
        manager = _make_manager(silence_timeout=3.0)
        assert manager.silence_timeout == 3.0

    def test_manager_init_with_voice_commands_enabled(self):
        """Test manager initialization with voice commands enabled."""
        manager = _make_manager(voice_commands_enabled=True)
        # Just verify manager initializes without error
        assert manager is not None

    def test_manager_init_with_gpu_selection(self):
        """Test manager initialization stores requested GPU selection."""
        manager = _make_manager(gpu_name="NVIDIA RTX 4090", gpu_backend="cuda")
        assert manager.requested_gpu_name == "NVIDIA RTX 4090"
        assert manager.preferred_gpu_backend == "cuda"

    def test_manager_init_with_download_progress_callback(self):
        """Test manager initialization with download progress callback."""
        callback = MagicMock()
        manager = _make_manager(download_progress_callback=callback)
        # Just verify manager initializes without error
        assert manager is not None

    def test_restore_managed_gpu_environment_restores_original_values(self):
        manager = _make_manager(engine="whisper_cpp")

        with patch.dict(os.environ, {"GGML_VULKAN": "9"}, clear=False):
            manager._set_managed_env("GGML_VULKAN", "1")
            manager._set_managed_env("GGML_CUDA", "0")

            assert os.environ["GGML_VULKAN"] == "1"
            assert os.environ["GGML_CUDA"] == "0"

            manager._restore_managed_gpu_environment()

            assert os.environ["GGML_VULKAN"] == "9"
            assert "GGML_CUDA" not in os.environ
            assert manager._managed_gpu_env_keys == set()

    def test_remember_env_original_keeps_first_seen_value(self):
        manager = _make_manager(engine="whisper_cpp")

        with patch.dict(os.environ, {"GGML_VULKAN": "7"}, clear=False):
            manager._remember_env_original("GGML_VULKAN")
            os.environ["GGML_VULKAN"] = "8"
            manager._remember_env_original("GGML_VULKAN")

        assert manager._gpu_env_originals["GGML_VULKAN"] == "7"

    def test_resolve_requested_gpu_returns_none_when_unconfigured(self):
        manager = _make_manager(engine="whisper_cpp")
        manager.selected_gpu_name = "Old GPU"
        manager.selected_gpu_backend = "cuda"
        manager.selected_gpu_index = 2

        assert manager._resolve_requested_gpu() is None
        assert manager.selected_gpu_name is None
        assert manager.selected_gpu_backend is None
        assert manager.selected_gpu_index is None

    def test_resolve_requested_gpu_updates_selected_fields(self):
        manager = _make_manager(
            engine="whisper_cpp",
            gpu_name="RTX 4090",
            gpu_backend="cuda",
        )

        with patch(
            "vocalinux.utils.whispercpp_model_info.resolve_gpu_selection",
            return_value=("cuda", 1, "NVIDIA RTX 4090"),
        ) as mock_resolve:
            assert manager._resolve_requested_gpu(["cuda"]) == (
                "cuda",
                1,
                "NVIDIA RTX 4090",
            )

        mock_resolve.assert_called_once_with(
            "RTX 4090",
            allowed_backends=["cuda"],
            preferred_backend="cuda",
        )
        assert manager.selected_gpu_backend == "cuda"
        assert manager.selected_gpu_index == 1
        assert manager.selected_gpu_name == "NVIDIA RTX 4090"

    def test_apply_whispercpp_gpu_selection_for_vulkan(self):
        manager = _make_manager(engine="whisper_cpp")

        with patch.dict(os.environ, {}, clear=True):
            manager._apply_whispercpp_gpu_selection(("vulkan", 3, "Intel Arc A770"))

            assert os.environ["GGML_VK_VISIBLE_DEVICES"] == "3"
            assert os.environ["GGML_VULKAN"] == "1"
            assert os.environ["GGML_CUDA"] == "0"

    def test_apply_whispercpp_gpu_selection_for_cuda(self):
        manager = _make_manager(engine="whisper_cpp")

        with patch.dict(os.environ, {}, clear=True):
            manager._apply_whispercpp_gpu_selection(("cuda", 1, "NVIDIA Tesla P40"))

            assert os.environ["CUDA_VISIBLE_DEVICES"] == "1"
            assert os.environ["GGML_VULKAN"] == "0"
            assert os.environ["GGML_CUDA"] == "1"

    def test_apply_whispercpp_gpu_selection_rejects_unknown_backend(self):
        manager = _make_manager(engine="whisper_cpp")

        with pytest.raises(ValueError, match="Unsupported GPU backend selection"):
            manager._apply_whispercpp_gpu_selection(("metal", 0, "Apple GPU"))

    def test_handle_gpu_fallback_clears_selection_and_forces_cpu(self):
        manager = _make_manager(engine="whisper_cpp")
        manager.selected_gpu_name = "Intel Arc A770"
        manager.selected_gpu_backend = "vulkan"
        manager.selected_gpu_index = 0

        mock_model_ctor = MagicMock(return_value="cpu-model")
        mock_module = MagicMock(Model=mock_model_ctor)

        with (
            patch.dict(sys.modules, {"pywhispercpp.model": mock_module}),
            patch(
                "vocalinux.speech_recognition.recognition_manager._show_notification"
            ) as mock_notify,
            patch.dict(os.environ, {}, clear=True),
        ):
            backend = manager._handle_gpu_fallback(
                RuntimeError("16-bit storage not supported"),
                "/tmp/model.bin",
                4,
                "cpu",
            )

            assert os.environ["GGML_VULKAN"] == "0"
            assert os.environ["GGML_CUDA"] == "0"

        assert backend == "cpu"
        assert manager.model == "cpu-model"
        assert manager.selected_gpu_name is None
        assert manager.selected_gpu_backend is None
        assert manager.selected_gpu_index is None
        mock_notify.assert_called_once()

    def test_init_whisper_uses_requested_cuda_gpu(self):
        manager = _make_manager(engine="whisper", gpu_name="RTX 4090", gpu_backend="cuda")
        manager.model_size = "tiny"

        mock_whisper = MagicMock()
        mock_model = MagicMock()
        mock_whisper.load_model.return_value = mock_model
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 2

        with (
            patch.dict("sys.modules", {"whisper": mock_whisper, "torch": mock_torch}),
            patch("os.makedirs"),
            patch("os.path.exists", return_value=True),
            patch(
                "vocalinux.utils.whispercpp_model_info.resolve_gpu_selection",
                return_value=("cuda", 1, "NVIDIA RTX 4090"),
            ),
        ):
            manager._init_whisper()

        _, kwargs = mock_whisper.load_model.call_args
        assert kwargs["device"] == "cuda:1"
        assert manager.selected_gpu_backend == "cuda"
        assert manager.selected_gpu_index == 1
        assert manager.selected_gpu_name == "NVIDIA RTX 4090"

    def test_init_whisper_tracks_auto_selected_cuda_gpu(self):
        manager = _make_manager(engine="whisper")
        manager.model_size = "tiny"

        mock_whisper = MagicMock()
        mock_whisper.load_model.return_value = MagicMock()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.current_device.return_value = 0
        mock_torch.cuda.get_device_name.return_value = "NVIDIA Tesla P40"

        with (
            patch.dict("sys.modules", {"whisper": mock_whisper, "torch": mock_torch}),
            patch("os.makedirs"),
            patch("os.path.exists", return_value=True),
        ):
            manager._init_whisper()

        assert manager.selected_gpu_backend == "cuda"
        assert manager.selected_gpu_index == 0
        assert manager.selected_gpu_name == "NVIDIA Tesla P40"

    def test_init_whisper_raises_when_requested_cuda_is_unavailable(self):
        manager = _make_manager(engine="whisper", gpu_name="RTX 4090", gpu_backend="cuda")
        manager.model_size = "tiny"

        mock_whisper = MagicMock()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        with (
            patch.dict("sys.modules", {"whisper": mock_whisper, "torch": mock_torch}),
            patch("os.makedirs"),
            patch("os.path.exists", return_value=True),
            patch(
                "vocalinux.utils.whispercpp_model_info.resolve_gpu_selection",
                return_value=("cuda", 1, "NVIDIA RTX 4090"),
            ),
        ):
            with pytest.raises(RuntimeError, match="CUDA is unavailable"):
                manager._init_whisper()

        assert manager.state.name == "ERROR"

    def test_init_whisper_raises_when_requested_cuda_index_is_out_of_range(self):
        manager = _make_manager(engine="whisper", gpu_name="RTX 4090", gpu_backend="cuda")
        manager.model_size = "tiny"

        mock_whisper = MagicMock()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1

        with (
            patch.dict("sys.modules", {"whisper": mock_whisper, "torch": mock_torch}),
            patch("os.makedirs"),
            patch("os.path.exists", return_value=True),
            patch(
                "vocalinux.utils.whispercpp_model_info.resolve_gpu_selection",
                return_value=("cuda", 3, "NVIDIA RTX 4090"),
            ),
        ):
            with pytest.raises(RuntimeError, match="only 1 CUDA device"):
                manager._init_whisper()

    def test_init_whisper_clears_selected_gpu_when_using_cpu(self):
        manager = _make_manager(engine="whisper")
        manager.model_size = "tiny"
        manager.selected_gpu_name = "Old GPU"
        manager.selected_gpu_backend = "cuda"
        manager.selected_gpu_index = 5

        mock_whisper = MagicMock()
        mock_whisper.load_model.return_value = MagicMock()
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False

        with (
            patch.dict("sys.modules", {"whisper": mock_whisper, "torch": mock_torch}),
            patch("os.makedirs"),
            patch("os.path.exists", return_value=True),
        ):
            manager._init_whisper()

        assert manager.selected_gpu_name is None
        assert manager.selected_gpu_backend is None
        assert manager.selected_gpu_index is None

    def test_load_whispercpp_model_tracks_detected_backend_without_request(self):
        manager = _make_manager(engine="whisper_cpp")
        mock_model_ctor = MagicMock(return_value="gpu-model")
        mock_pywhispercpp = MagicMock(Model=mock_model_ctor)
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.total = 8 * 1024 * 1024 * 1024

        with (
            patch.dict(
                "sys.modules",
                {"pywhispercpp.model": mock_pywhispercpp, "psutil": mock_psutil},
            ),
            patch.object(manager, "_resolve_requested_gpu", return_value=None),
            patch.object(manager, "_restore_managed_gpu_environment") as mock_restore,
            patch(
                "vocalinux.utils.whispercpp_model_info.detect_compute_backend",
                return_value=("vulkan", "Intel Arc A770"),
            ),
            patch(
                "vocalinux.utils.whispercpp_model_info.get_backend_display_name",
                return_value="Vulkan",
            ),
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=100 * 1024 * 1024),
            patch("multiprocessing.cpu_count", return_value=4),
            patch("time.time", side_effect=[100.0, 101.5]),
        ):
            manager._load_whispercpp_model("/tmp/mock.bin")

        mock_restore.assert_called_once()
        assert manager.model == "gpu-model"
        assert manager.selected_gpu_backend == "vulkan"
        assert manager.selected_gpu_index is None
        assert manager.selected_gpu_name == "Intel Arc A770"

    def test_load_whispercpp_model_clears_selected_gpu_for_cpu_auto_backend(self):
        manager = _make_manager(engine="whisper_cpp")
        manager.selected_gpu_name = "Old GPU"
        manager.selected_gpu_backend = "cuda"
        manager.selected_gpu_index = 1
        mock_model_ctor = MagicMock(return_value="cpu-model")
        mock_pywhispercpp = MagicMock(Model=mock_model_ctor)
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.total = 8 * 1024 * 1024 * 1024

        with (
            patch.dict(
                "sys.modules",
                {"pywhispercpp.model": mock_pywhispercpp, "psutil": mock_psutil},
            ),
            patch.object(manager, "_resolve_requested_gpu", return_value=None),
            patch.object(manager, "_restore_managed_gpu_environment"),
            patch(
                "vocalinux.utils.whispercpp_model_info.detect_compute_backend",
                return_value=("cpu", "CPU"),
            ),
            patch(
                "vocalinux.utils.whispercpp_model_info.get_backend_display_name",
                return_value="CPU",
            ),
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=100 * 1024 * 1024),
            patch("multiprocessing.cpu_count", return_value=4),
            patch("time.time", side_effect=[200.0, 200.5]),
        ):
            manager._load_whispercpp_model("/tmp/mock.bin")

        assert manager.selected_gpu_name is None
        assert manager.selected_gpu_backend is None
        assert manager.selected_gpu_index is None

    def test_load_whispercpp_model_applies_requested_gpu_selection(self):
        manager = _make_manager(engine="whisper_cpp", gpu_name="Tesla P40", gpu_backend="cuda")
        mock_model_ctor = MagicMock(return_value="gpu-model")
        mock_pywhispercpp = MagicMock(Model=mock_model_ctor)
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.total = 8 * 1024 * 1024 * 1024

        with (
            patch.dict(
                "sys.modules",
                {"pywhispercpp.model": mock_pywhispercpp, "psutil": mock_psutil},
            ),
            patch.object(
                manager, "_resolve_requested_gpu", return_value=("cuda", 1, "NVIDIA Tesla P40")
            ),
            patch.object(manager, "_apply_whispercpp_gpu_selection") as mock_apply,
            patch(
                "vocalinux.utils.whispercpp_model_info.detect_compute_backend",
                return_value=("cuda", "NVIDIA Tesla P40"),
            ),
            patch(
                "vocalinux.utils.whispercpp_model_info.get_backend_display_name",
                return_value="CUDA",
            ),
            patch(
                "vocalinux.utils.whispercpp_model_info.get_whispercpp_compiled_backends",
                return_value={"cpu", "cuda"},
            ),
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=100 * 1024 * 1024),
            patch("multiprocessing.cpu_count", return_value=4),
            patch("time.time", side_effect=[300.0, 300.2]),
        ):
            manager._load_whispercpp_model("/tmp/mock.bin")

        mock_apply.assert_called_once_with(("cuda", 1, "NVIDIA Tesla P40"))
        assert manager.selected_gpu_backend == "cuda"
        assert manager.selected_gpu_index == 1
        assert manager.selected_gpu_name == "NVIDIA Tesla P40"

    def test_load_whispercpp_model_rejects_requested_backend_missing_from_build(self):
        manager = _make_manager(engine="whisper_cpp", gpu_name="Tesla P40", gpu_backend="cuda")
        mock_pywhispercpp = MagicMock(Model=MagicMock(return_value="gpu-model"))
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.total = 8 * 1024 * 1024 * 1024

        with (
            patch.dict(
                "sys.modules",
                {"pywhispercpp.model": mock_pywhispercpp, "psutil": mock_psutil},
            ),
            patch.object(manager, "_resolve_requested_gpu", return_value=("cuda", 0, "Tesla P40")),
            patch(
                "vocalinux.utils.whispercpp_model_info.get_whispercpp_compiled_backends",
                return_value={"cpu", "vulkan"},
            ),
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=100 * 1024 * 1024),
        ):
            with pytest.raises(RuntimeError, match="does not support the requested CUDA backend"):
                manager._load_whispercpp_model("/tmp/mock.bin")

    def test_handle_gpu_fallback_reraises_unrelated_runtime_error(self):
        manager = _make_manager(engine="whisper_cpp")

        with patch.dict(sys.modules, {"pywhispercpp.model": MagicMock()}):
            with pytest.raises(RuntimeError, match="some other failure"):
                manager._handle_gpu_fallback(
                    RuntimeError("some other failure"), "/tmp/model.bin", 4, "cpu"
                )


class TestGetAudioInputDevices:
    """Tests for get_audio_input_devices function."""

    def test_get_audio_input_devices_success(self):
        """Test getting audio input devices successfully."""
        from vocalinux.speech_recognition.recognition_manager import get_audio_input_devices

        mock_audio = MagicMock()
        mock_audio.get_device_count.return_value = 2
        mock_audio.get_default_input_device_info.return_value = {"index": 0}
        mock_audio.get_device_info_by_index.side_effect = [
            {"name": "Device 0", "maxInputChannels": 2, "index": 0},
            {"name": "Device 1", "maxInputChannels": 2, "index": 1},
        ]

        with patch.dict(
            "sys.modules", {"pyaudio": MagicMock(PyAudio=MagicMock(return_value=mock_audio))}
        ):
            devices = get_audio_input_devices()
            assert len(devices) == 2
            assert devices[0][0] == 0  # device index
            assert devices[0][2] is True  # is_default
            assert devices[1][2] is False

    def test_get_audio_input_devices_no_default(self):
        """Test getting devices when no default input device exists."""
        from vocalinux.speech_recognition.recognition_manager import get_audio_input_devices

        mock_audio = MagicMock()
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_default_input_device_info.side_effect = IOError("No default device")
        mock_audio.get_device_info_by_index.return_value = {
            "name": "Device 0",
            "maxInputChannels": 2,
            "index": 0,
        }

        with patch.dict(
            "sys.modules", {"pyaudio": MagicMock(PyAudio=MagicMock(return_value=mock_audio))}
        ):
            devices = get_audio_input_devices()
            assert len(devices) == 1
            assert devices[0][2] is False  # not default

    def test_get_audio_input_devices_skip_input_only(self):
        """Test that devices with 0 input channels are skipped."""
        from vocalinux.speech_recognition.recognition_manager import get_audio_input_devices

        mock_audio = MagicMock()
        mock_audio.get_device_count.return_value = 2
        mock_audio.get_default_input_device_info.return_value = {"index": 0}
        mock_audio.get_device_info_by_index.side_effect = [
            {"name": "Output Device", "maxInputChannels": 0, "index": 0},  # output only
            {"name": "Input Device", "maxInputChannels": 2, "index": 1},  # input capable
        ]

        with patch.dict(
            "sys.modules", {"pyaudio": MagicMock(PyAudio=MagicMock(return_value=mock_audio))}
        ):
            devices = get_audio_input_devices()
            assert len(devices) == 1
            assert devices[0][1] == "Input Device"

    def test_get_audio_input_devices_device_error(self):
        """Test handling of device enumeration errors."""
        from vocalinux.speech_recognition.recognition_manager import get_audio_input_devices

        mock_audio = MagicMock()
        mock_audio.get_device_count.return_value = 2
        mock_audio.get_default_input_device_info.return_value = {"index": 0}
        mock_audio.get_device_info_by_index.side_effect = [
            IOError("Device error"),  # First device has error
            {"name": "Device 1", "maxInputChannels": 2, "index": 1},
        ]

        with patch.dict(
            "sys.modules", {"pyaudio": MagicMock(PyAudio=MagicMock(return_value=mock_audio))}
        ):
            devices = get_audio_input_devices()
            assert len(devices) == 1
            assert devices[0][1] == "Device 1"

    def test_get_audio_input_devices_pyaudio_not_installed(self):
        """Test handling when pyaudio is not installed."""
        from vocalinux.speech_recognition.recognition_manager import get_audio_input_devices

        with patch.dict("sys.modules", {"pyaudio": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module named 'pyaudio'")):
                devices = get_audio_input_devices()
                assert devices == []

    def test_get_audio_input_devices_generic_exception(self):
        """Test handling of OS-level audio errors during device enumeration."""
        from vocalinux.speech_recognition.recognition_manager import get_audio_input_devices

        mock_pyaudio = MagicMock()
        mock_pyaudio.PyAudio.side_effect = OSError("Audio subsystem error")
        with patch.dict("sys.modules", {"pyaudio": mock_pyaudio}):
            devices = get_audio_input_devices()
            assert devices == []


class TestGetSupportedChannels:
    """Tests for _get_supported_channels function."""

    def test_get_supported_channels_mono(self):
        """Test that mono (1 channel) is detected as supported."""
        from vocalinux.speech_recognition.recognition_manager import _get_supported_channels

        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream

        # First call (mono) succeeds
        mock_audio.open.side_effect = [mock_stream, IOError("2 channels not supported")]

        with patch.dict(
            "sys.modules",
            {"pyaudio": MagicMock(paInt16=16, PyAudio=MagicMock(return_value=mock_audio))},
        ):
            channels = _get_supported_channels(mock_audio, None)
            assert channels == 1

    def test_get_supported_channels_stereo_fallback(self):
        """Test fallback to stereo if mono fails."""
        from vocalinux.speech_recognition.recognition_manager import _get_supported_channels

        mock_audio = MagicMock()
        mock_stream = MagicMock()

        def open_side_effect(**kwargs):
            if kwargs.get("channels") == 1:
                raise IOError("-9998 invalid number of channels")
            return mock_stream

        mock_audio.open.side_effect = open_side_effect
        mock_audio.get_default_input_device_info.return_value = {"defaultSampleRate": 48000}

        with patch.dict(
            "sys.modules",
            {"pyaudio": MagicMock(paInt16=16, PyAudio=MagicMock(return_value=mock_audio))},
        ):
            channels = _get_supported_channels(mock_audio, None)
            assert channels == 2

    def test_get_supported_channels_both_fail(self):
        """Test default to 1 channel if both mono and stereo fail."""
        from vocalinux.speech_recognition.recognition_manager import _get_supported_channels

        mock_audio = MagicMock()

        mock_audio.open.side_effect = IOError("All channel/rate probes failed")
        mock_audio.get_default_input_device_info.return_value = {"defaultSampleRate": 48000}

        with patch.dict(
            "sys.modules",
            {"pyaudio": MagicMock(paInt16=16, PyAudio=MagicMock(return_value=mock_audio))},
        ):
            channels = _get_supported_channels(mock_audio, None)
            assert channels == 1


class TestGetSupportedSampleRate:
    """Tests for _get_supported_sample_rate function."""

    def test_get_supported_sample_rate_device_default(self):
        """Test that device's default sample rate is preferred."""
        from vocalinux.speech_recognition.recognition_manager import _get_supported_sample_rate

        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.get_device_info_by_index.return_value = {"defaultSampleRate": 48000}
        mock_audio.open.return_value = mock_stream

        with patch.dict(
            "sys.modules",
            {"pyaudio": MagicMock(paInt16=16, PyAudio=MagicMock(return_value=mock_audio))},
        ):
            rate = _get_supported_sample_rate(mock_audio, 0, 1)
            assert rate == 48000

    def test_get_supported_sample_rate_fallback_to_common(self):
        """Test fallback to common sample rates."""
        from vocalinux.speech_recognition.recognition_manager import _get_supported_sample_rate

        mock_audio = MagicMock()
        mock_stream = MagicMock()
        # Device default fails, but 44100 works
        mock_audio.get_device_info_by_index.return_value = {"defaultSampleRate": 0}
        mock_audio.open.side_effect = [
            IOError("Device default failed"),
            mock_stream,  # 44100 works
        ]

        with patch.dict(
            "sys.modules",
            {"pyaudio": MagicMock(paInt16=16, PyAudio=MagicMock(return_value=mock_audio))},
        ):
            rate = _get_supported_sample_rate(mock_audio, 0, 1)
            assert rate == 44100

    def test_get_supported_sample_rate_all_fail_default(self):
        """Test default to 16000 if all rates fail."""
        from vocalinux.speech_recognition.recognition_manager import _get_supported_sample_rate

        mock_audio = MagicMock()
        mock_audio.get_device_info_by_index.return_value = {"defaultSampleRate": 0}
        # All rates fail
        mock_audio.open.side_effect = IOError("All rates failed")

        with patch.dict(
            "sys.modules",
            {"pyaudio": MagicMock(paInt16=16, PyAudio=MagicMock(return_value=mock_audio))},
        ):
            rate = _get_supported_sample_rate(mock_audio, 0, 1)
            assert rate == 16000

    def test_get_supported_sample_rate_no_device_info(self):
        """Test handling when device info cannot be retrieved."""
        from vocalinux.speech_recognition.recognition_manager import _get_supported_sample_rate

        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.get_device_info_by_index.side_effect = IOError("Cannot get device info")
        mock_audio.open.side_effect = [
            mock_stream,  # First common rate works
        ]

        with patch.dict(
            "sys.modules",
            {"pyaudio": MagicMock(paInt16=16, PyAudio=MagicMock(return_value=mock_audio))},
        ):
            rate = _get_supported_sample_rate(mock_audio, 0, 1)
            # Should try common rates and return first working one
            assert rate in [48000, 44100, 32000, 22050, 16000, 8000]


class TestManagerStateCallbacks:
    """Tests for callback registration and state management."""

    def test_register_text_callback(self):
        """Test registering text callback."""
        manager = _make_manager()
        callback = MagicMock()
        # Just verify method exists and doesn't error
        manager.register_text_callback(callback)
        assert manager is not None

    def test_register_action_callback(self):
        """Test registering action callback."""
        manager = _make_manager()
        callback = MagicMock()
        # Just verify method exists and doesn't error
        manager.register_action_callback(callback)
        assert manager is not None

    def test_register_state_callback(self):
        """Test registering state callback."""
        manager = _make_manager()
        callback = MagicMock()
        # Just verify method exists and doesn't error
        manager.register_state_callback(callback)
        assert manager is not None

    def test_manager_state_property(self):
        """Test manager state property."""
        manager = _make_manager()
        # Just verify manager has state property
        state = manager.state
        assert state is not None
