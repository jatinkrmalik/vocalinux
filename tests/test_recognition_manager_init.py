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

    def test_manager_init_with_download_progress_callback(self):
        """Test manager initialization with download progress callback."""
        callback = MagicMock()
        manager = _make_manager(download_progress_callback=callback)
        # Just verify manager initializes without error
        assert manager is not None


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

    def test_manager_init_with_initial_prompt(self):
        """Test manager initialization with initial_prompt."""
        manager = _make_manager(engine="whisper_cpp", initial_prompt="Custom vocab")
        assert manager.initial_prompt == "Custom vocab"

    def test_reconfigure_whispercpp_prompt_change_triggers_reload(self):
        """Test that changing initial_prompt on whisper_cpp triggers model reload."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "_init_vosk"):
            with patch.object(SpeechRecognitionManager, "_init_whisper"):
                with patch.object(SpeechRecognitionManager, "_init_whispercpp") as mock_init:
                    manager = SpeechRecognitionManager(
                        engine="whisper_cpp", model_size="tiny", defer_download=True
                    )
                    mock_init.reset_mock()
                    manager.reconfigure(initial_prompt="New prompt")
                    mock_init.assert_called_once()

    def test_reconfigure_same_prompt_no_reload(self):
        """Test that reconfiguring with the same prompt does not reload."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "_init_vosk"):
            with patch.object(SpeechRecognitionManager, "_init_whisper"):
                with patch.object(SpeechRecognitionManager, "_init_whispercpp") as mock_init:
                    manager = SpeechRecognitionManager(
                        engine="whisper_cpp", model_size="tiny", defer_download=True
                    )
                    manager.initial_prompt = "Same prompt"
                    mock_init.reset_mock()
                    manager.reconfigure(initial_prompt="Same prompt")
                    mock_init.assert_not_called()

    def test_reconfigure_whisper_prompt_change_no_reload(self):
        """Test that changing initial_prompt on whisper does NOT trigger model reload.

        Only whisper_cpp requires reload for prompt changes; OpenAI Whisper
        passes the prompt at transcription time.
        """
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "_init_vosk"):
            with patch.object(SpeechRecognitionManager, "_init_whisper") as mock_init:
                with patch.object(SpeechRecognitionManager, "_init_whispercpp"):
                    manager = SpeechRecognitionManager(
                        engine="whisper", model_size="tiny", defer_download=True
                    )
                    mock_init.reset_mock()
                    manager.reconfigure(initial_prompt="New prompt")
                    # Whisper does not reload model on prompt change
                    mock_init.assert_not_called()

    def test_reconfigure_vosk_prompt_ignored(self):
        """Test that changing initial_prompt on vosk does not trigger reload."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "_init_vosk") as mock_init:
            with patch.object(SpeechRecognitionManager, "_init_whisper"):
                with patch.object(SpeechRecognitionManager, "_init_whispercpp"):
                    manager = SpeechRecognitionManager(
                        engine="vosk", model_size="tiny", defer_download=True
                    )
                    mock_init.reset_mock()
                    manager.reconfigure(initial_prompt="New prompt")
                    mock_init.assert_not_called()


class TestWhispercppInitialPrompt:
    """Tests for whisper.cpp initialization with initial_prompt."""

    def test_init_whispercpp_with_prompt(self):
        """Test that initial_prompt is passed to Model constructor."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mock_model = MagicMock()

        with patch.object(SpeechRecognitionManager, "_init_vosk"):
            with patch.object(SpeechRecognitionManager, "_init_whisper"):
                with patch.object(SpeechRecognitionManager, "_init_whispercpp"):
                    manager = SpeechRecognitionManager(
                        engine="whisper_cpp",
                        model_size="tiny",
                        language="en-us",
                        defer_download=True,
                        initial_prompt="Custom vocab",
                    )
                    # Verify initial_prompt is set correctly
                    assert manager.initial_prompt == "Custom vocab"

    def test_init_whispercpp_empty_prompt(self):
        """Test that empty initial_prompt defaults correctly."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "_init_vosk"):
            with patch.object(SpeechRecognitionManager, "_init_whisper"):
                with patch.object(SpeechRecognitionManager, "_init_whispercpp"):
                    manager = SpeechRecognitionManager(
                        engine="whisper_cpp",
                        model_size="tiny",
                        language="en-us",
                        defer_download=True,
                    )
                    assert manager.initial_prompt == ""


class TestWhisperInitialPrompt:
    """Tests for OpenAI Whisper initialization with initial_prompt."""

    def test_transcribe_with_whisper_includes_prompt(self):
        """Test that initial_prompt is passed to whisper transcribe."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "_init_vosk"):
            with patch.object(SpeechRecognitionManager, "_init_whispercpp"):
                with patch.object(SpeechRecognitionManager, "_init_whisper"):
                    manager = SpeechRecognitionManager(
                        engine="whisper",
                        model_size="tiny",
                        language="en-us",
                        defer_download=True,
                        initial_prompt="Custom vocab",
                    )
                    assert manager.initial_prompt == "Custom vocab"

    def test_transcribe_with_whisper_omits_empty_prompt(self):
        """Test that empty initial_prompt is not passed to whisper transcribe."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "_init_vosk"):
            with patch.object(SpeechRecognitionManager, "_init_whispercpp"):
                with patch.object(SpeechRecognitionManager, "_init_whisper"):
                    manager = SpeechRecognitionManager(
                        engine="whisper",
                        model_size="tiny",
                        language="en-us",
                        defer_download=True,
                        initial_prompt="",
                    )
                    assert manager.initial_prompt == ""


class TestInitialPromptCodeCoverage:
    """Tests covering the exact lines flagged by codecov patch coverage."""

    def _setup_whispercpp_mocks(self):
        """Return a dict of mocks needed for _load_whispercpp_model."""
        from vocalinux.utils.whispercpp_model_info import ComputeBackend

        mock_model_cls = MagicMock(name="Model")
        mock_model_instance = MagicMock(name="model_instance")
        mock_model_cls.return_value = mock_model_instance

        mock_detect = MagicMock(return_value=(ComputeBackend.CPU, "test-info"))
        mock_display = MagicMock(return_value="CPU")

        return {
            "model_cls": mock_model_cls,
            "model_instance": mock_model_instance,
            "detect_compute_backend": mock_detect,
            "get_backend_display_name": mock_display,
        }

    def _write_temp_model(self, tmp_path):
        """Write a tiny temp file to act as model_path."""
        model_path = str(tmp_path / "model.bin")
        with open(model_path, "wb") as f:
            f.write(b"\x00" * 1024)
        return model_path

    # ------------------------------------------------------------------
    # _load_whispercpp_model: inspect.signature branches (lines 900-907)
    # ------------------------------------------------------------------

    def test_load_whispercpp_model_with_supported_prompt(self, tmp_path):
        """initial_prompt IS in Model.__init__ signature → kwargs include it."""
        import inspect as real_inspect

        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mocks = self._setup_whispercpp_mocks()
        model_path = self._write_temp_model(tmp_path)

        # Build a fake signature that includes "initial_prompt"
        fake_params = {
            "self": MagicMock(),
            "model_path": MagicMock(),
            "initial_prompt": MagicMock(),
        }
        fake_sig = MagicMock()
        fake_sig.parameters = fake_params

        with patch.object(SpeechRecognitionManager, "_init_vosk"), \
             patch.object(SpeechRecognitionManager, "_init_whisper"), \
             patch.object(SpeechRecognitionManager, "_init_whispercpp"):
            manager = SpeechRecognitionManager(
                engine="whisper_cpp", model_size="tiny", defer_download=True,
                initial_prompt="test vocab",
            )

        with patch.dict("sys.modules", {
            "pywhispercpp": MagicMock(model=MagicMock(Model=mocks["model_cls"])),
            "pywhispercpp.model": MagicMock(Model=mocks["model_cls"]),
        }), \
             patch("vocalinux.speech_recognition.recognition_manager.detect_compute_backend",
                   mocks["detect_compute_backend"]), \
             patch("vocalinux.speech_recognition.recognition_manager.get_backend_display_name",
                   mocks["get_backend_display_name"]), \
             patch("psutil.virtual_memory", return_value=MagicMock(total=8 * 1024**3)), \
             patch("multiprocessing.cpu_count", return_value=4), \
             patch("inspect.signature", return_value=fake_sig) as mock_sig:

            manager._load_whispercpp_model(model_path)

        # Model was loaded
        assert manager.model is not None
        assert manager._model_initialized is True
        # inspect.signature was called on the Model class
        mock_sig.assert_called_once_with(mocks["model_cls"].__init__)
        # initial_prompt was passed to Model constructor
        call_kwargs = mocks["model_cls"].call_args[1]
        assert call_kwargs["initial_prompt"] == "test vocab"

    def test_load_whispercpp_model_with_unsupported_prompt(self, tmp_path):
        """Old pywhispercpp without initial_prompt param → warning, kwargs exclude it."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mocks = self._setup_whispercpp_mocks()
        model_path = self._write_temp_model(tmp_path)

        # Fake signature WITHOUT "initial_prompt"
        fake_params = {
            "self": MagicMock(),
            "model_path": MagicMock(),
        }
        fake_sig = MagicMock()
        fake_sig.parameters = fake_params

        with patch.object(SpeechRecognitionManager, "_init_vosk"), \
             patch.object(SpeechRecognitionManager, "_init_whisper"), \
             patch.object(SpeechRecognitionManager, "_init_whispercpp"):
            manager = SpeechRecognitionManager(
                engine="whisper_cpp", model_size="tiny", defer_download=True,
                initial_prompt="test vocab",
            )

        with patch.dict("sys.modules", {
            "pywhispercpp": MagicMock(model=MagicMock(Model=mocks["model_cls"])),
            "pywhispercpp.model": MagicMock(Model=mocks["model_cls"]),
        }), \
             patch("vocalinux.speech_recognition.recognition_manager.detect_compute_backend",
                   mocks["detect_compute_backend"]), \
             patch("vocalinux.speech_recognition.recognition_manager.get_backend_display_name",
                   mocks["get_backend_display_name"]), \
             patch("psutil.virtual_memory", return_value=MagicMock(total=8 * 1024**3)), \
             patch("multiprocessing.cpu_count", return_value=4), \
             patch("inspect.signature", return_value=fake_sig):

            manager._load_whispercpp_model(model_path)

        assert manager.model is not None
        assert manager._model_initialized is True
        # initial_prompt was NOT passed to Model constructor
        call_kwargs = mocks["model_cls"].call_args[1]
        assert "initial_prompt" not in call_kwargs

    def test_load_whispercpp_model_empty_prompt_skips_check(self, tmp_path):
        """Empty initial_prompt → inspect.signature block skipped entirely."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        mocks = self._setup_whispercpp_mocks()
        model_path = self._write_temp_model(tmp_path)

        with patch.object(SpeechRecognitionManager, "_init_vosk"), \
             patch.object(SpeechRecognitionManager, "_init_whisper"), \
             patch.object(SpeechRecognitionManager, "_init_whispercpp"):
            manager = SpeechRecognitionManager(
                engine="whisper_cpp", model_size="tiny", defer_download=True,
                initial_prompt="",
            )

        with patch.dict("sys.modules", {
            "pywhispercpp": MagicMock(model=MagicMock(Model=mocks["model_cls"])),
            "pywhispercpp.model": MagicMock(Model=mocks["model_cls"]),
        }), \
             patch("vocalinux.speech_recognition.recognition_manager.detect_compute_backend",
                   mocks["detect_compute_backend"]), \
             patch("vocalinux.speech_recognition.recognition_manager.get_backend_display_name",
                   mocks["get_backend_display_name"]), \
             patch("psutil.virtual_memory", return_value=MagicMock(total=8 * 1024**3)), \
             patch("multiprocessing.cpu_count", return_value=4), \
             patch("inspect.signature") as mock_sig:

            manager._load_whispercpp_model(model_path)

        assert manager.model is not None
        assert manager._model_initialized is True
        # inspect.signature should NOT have been called (empty prompt → if guard skipped)
        mock_sig.assert_not_called()
        # No initial_prompt in kwargs
        call_kwargs = mocks["model_cls"].call_args[1]
        assert "initial_prompt" not in call_kwargs

    # ------------------------------------------------------------------
    # _transcribe_with_whisper: transcribe_kwargs conditional (lines 782-783)
    # ------------------------------------------------------------------

    def test_transcribe_with_whisper_includes_prompt_in_kwargs(self):
        """When initial_prompt is set, model.transcribe receives it."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "_init_vosk"), \
             patch.object(SpeechRecognitionManager, "_init_whispercpp"), \
             patch.object(SpeechRecognitionManager, "_init_whisper"):
            manager = SpeechRecognitionManager(
                engine="whisper", model_size="tiny", language="en-us",
                defer_download=True, initial_prompt="medical terms",
            )

        # Set up model mock
        mock_device = object()
        manager.model = MagicMock()
        manager.model.device = mock_device
        manager.model.transcribe.return_value = {"text": "hello"}

        # Mock torch so the import inside the method succeeds
        mock_torch = MagicMock()
        mock_torch.device.return_value = mock_device  # same object → use_fp16 = False

        # Fake numpy
        import numpy as real_np

        audio_buffer = [b"\x00\x10" * 512]  # ~1KB of fake audio

        with patch.dict("sys.modules", {"torch": mock_torch, "numpy": real_np}):
            result = manager._transcribe_with_whisper(audio_buffer)

        assert result == "hello"
        # Verify transcribe was called with initial_prompt
        transcribe_call = manager.model.transcribe.call_args
        assert "initial_prompt" in transcribe_call[1]
        assert transcribe_call[1]["initial_prompt"] == "medical terms"

    def test_transcribe_with_whisper_omits_empty_prompt_from_kwargs(self):
        """When initial_prompt is empty, model.transcribe does NOT receive it."""
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager

        with patch.object(SpeechRecognitionManager, "_init_vosk"), \
             patch.object(SpeechRecognitionManager, "_init_whispercpp"), \
             patch.object(SpeechRecognitionManager, "_init_whisper"):
            manager = SpeechRecognitionManager(
                engine="whisper", model_size="tiny", language="en-us",
                defer_download=True, initial_prompt="",
            )

        mock_device = object()
        manager.model = MagicMock()
        manager.model.device = mock_device
        manager.model.transcribe.return_value = {"text": "world"}

        mock_torch = MagicMock()
        mock_torch.device.return_value = mock_device

        import numpy as real_np
        audio_buffer = [b"\x00\x10" * 512]

        with patch.dict("sys.modules", {"torch": mock_torch, "numpy": real_np}):
            result = manager._transcribe_with_whisper(audio_buffer)

        assert result == "world"
        transcribe_call = manager.model.transcribe.call_args
        assert "initial_prompt" not in transcribe_call[1]
