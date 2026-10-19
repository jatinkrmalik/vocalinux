"""System Default must follow a sound-server PCM instead of substituted ALSA hardware."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from vocalinux.audio import capture


def device(index: int, name: str, channels: int = 1, host_api: int = 0) -> dict:
    """Build realistic PortAudio enumeration metadata without probing hardware."""
    return {
        "index": index,
        "name": name,
        "maxInputChannels": channels,
        "hostApi": host_api,
        "defaultSampleRate": 16000,
    }


@pytest.fixture
def audio(monkeypatch: pytest.MonkeyPatch) -> Mock:
    devices = [device(0, "Webcam (hw:1,0)"), device(1, "pulse", 32)]
    audio = Mock()
    audio.get_default_input_device_info.return_value = devices[0]
    audio.get_host_api_info_by_index.return_value = {"type": 8, "name": "ALSA"}
    audio.get_device_count.return_value = len(devices)
    audio.get_device_info_by_index.side_effect = lambda index: devices[index]
    audio.open.return_value.get_read_available.return_value = 1024
    audio.open.return_value.read.return_value = b"\x00\x01" * 1024
    monkeypatch.setitem(sys.modules, "pyaudio", SimpleNamespace(PyAudio=lambda: audio, paInt16=8))
    monkeypatch.setitem(sys.modules, "numpy", sys._vocalinux_real_numpy)
    return audio


@pytest.mark.parametrize("name", ["default", "pulse", "pipewire", "DeepFilterNet", "default: Mic"])
def test_valid_defaults_stay_implicit(audio: Mock, name: str) -> None:
    audio.get_default_input_device_info.return_value = device(0, name)
    assert capture._resolve_system_default(audio) is None
    audio.open.assert_not_called()


@pytest.mark.parametrize("host_type", [1, 2, 12, 16])
def test_other_host_apis_keep_their_default(audio: Mock, host_type: int) -> None:
    audio.get_host_api_info_by_index.return_value = {"type": host_type}
    assert capture._resolve_system_default(audio) is None
    audio.get_device_count.assert_not_called()


def test_hardware_default_prefers_input_pulse_without_probing(audio: Mock) -> None:
    assert capture._resolve_system_default(audio) == 1
    audio.open.assert_not_called()
    audio.is_format_supported.assert_not_called()


@pytest.mark.parametrize(
    "candidate",
    [
        device(1, "pulse", 0),
        device(1, "pulse.monitor"),
        device(1, "pipewire"),
        device(1, "pulse", 1, host_api=1),
        device(1, "speech-dispatcher-dummy"),
    ],
)
def test_ineligible_pcm_warns_with_actual_hardware(
    audio: Mock, candidate: dict, caplog: pytest.LogCaptureFixture
) -> None:
    audio.get_device_info_by_index.side_effect = lambda index: (
        device(0, "Webcam (hw:1,0)") if index == 0 else candidate
    )
    assert capture._resolve_system_default(audio) is None
    assert "Webcam (hw:1,0)" in caplog.text and "no input-capable pulse PCM" in caplog.text
    audio.open.assert_not_called()


def test_unavailable_pcm_warns_and_keeps_implicit_fallback(
    audio: Mock, caplog: pytest.LogCaptureFixture
) -> None:
    def info(index: int) -> dict:
        if index == 1:
            raise OSError("device unavailable")
        return device(0, "Webcam (hw:1,0)")

    audio.get_device_info_by_index.side_effect = info
    assert capture._resolve_system_default(audio) is None
    assert "Webcam (hw:1,0)" in caplog.text


@pytest.mark.parametrize("endpoint", ["open", "reopen", "settings"])
def test_all_opening_paths_select_pulse_once(audio: Mock, endpoint: str) -> None:
    source = capture.PortAudioCaptureSource()
    try:
        if endpoint == "open":
            source.open(audio)
            assert source.resolved_device_name == "pulse"
        elif endpoint == "reopen":
            assert source.reopen(audio)
            assert source.resolved_device_name == "pulse"
        else:
            result = capture.test_audio_input(duration=0.1)
            assert result["success"]
            assert result["device_name"] == "pulse" and result["device_index"] == 1
        audio.open.assert_called_once()
        assert audio.open.call_args.kwargs["input_device_index"] == 1
        audio.get_host_api_info_by_index.assert_called_once_with(0)
    finally:
        if endpoint != "settings":
            source.close()


@pytest.mark.parametrize("endpoint", ["open", "reopen", "settings"])
def test_explicit_hardware_is_preserved(audio: Mock, endpoint: str) -> None:
    source = capture.PortAudioCaptureSource(device_index=0)
    try:
        if endpoint == "open":
            source.open(audio)
        elif endpoint == "reopen":
            assert source.reopen(audio)
        else:
            assert capture.test_audio_input(device_index=0, duration=0.1)["success"]
        assert audio.open.call_args.kwargs["input_device_index"] == 0
        audio.get_host_api_info_by_index.assert_not_called()
    finally:
        if endpoint != "settings":
            source.close()


@pytest.mark.parametrize("endpoint", ["open", "reopen", "settings"])
def test_empty_enumeration_never_opens_an_explicit_index(audio: Mock, endpoint: str) -> None:
    audio.get_device_count.return_value = 0
    source = capture.PortAudioCaptureSource()
    try:
        if endpoint == "open":
            source.open(audio)
        elif endpoint == "reopen":
            assert source.reopen(audio)
        else:
            assert capture.test_audio_input(duration=0.1)["success"]
        assert "input_device_index" not in audio.open.call_args.kwargs
    finally:
        if endpoint != "settings":
            source.close()


@pytest.mark.parametrize("endpoint", ["open", "reopen", "settings"])
def test_selected_pulse_failure_never_switches_to_hardware(audio: Mock, endpoint: str) -> None:
    audio.open.side_effect = OSError("pulse cannot open")
    source = capture.PortAudioCaptureSource()
    try:
        if endpoint == "open":
            with pytest.raises(OSError, match="pulse cannot open"):
                source.open(audio)
        elif endpoint == "reopen":
            assert not source.reopen(audio)
            assert "pulse cannot open" in str(source.last_error)
        else:
            result = capture.test_audio_input(duration=0.1)
            assert not result["success"] and "pulse cannot open" in result["error"]
        assert audio.open.call_count > 1  # Negotiation plus the final plain open.
        assert all(call.kwargs.get("input_device_index") == 1 for call in audio.open.call_args_list)
        audio.get_host_api_info_by_index.assert_called_once_with(0)
    finally:
        if endpoint != "settings":
            source.close()


@pytest.mark.parametrize("endpoint", ["open", "reopen", "settings"])
def test_no_safe_pcm_reports_the_actual_implicit_fallback(
    audio: Mock, endpoint: str, caplog: pytest.LogCaptureFixture
) -> None:
    audio.get_device_count.return_value = 1
    source = capture.PortAudioCaptureSource()
    try:
        if endpoint == "open":
            source.open(audio)
            assert source.resolved_device_name == "Webcam (hw:1,0)"
        elif endpoint == "reopen":
            assert source.reopen(audio)
            assert source.resolved_device_name == "Webcam (hw:1,0)"
        else:
            result = capture.test_audio_input(duration=0.1)
            assert result["success"] and result["device_name"] == "Webcam (hw:1,0)"
        assert "Webcam (hw:1,0)" in caplog.text
        assert "no input-capable pulse PCM" in caplog.text
        audio.open.assert_called_once()
        assert "input_device_index" not in audio.open.call_args.kwargs
    finally:
        if endpoint != "settings":
            source.close()


@pytest.mark.parametrize("endpoint", ["open", "reopen", "settings"])
def test_final_plain_open_retains_selected_pcm_when_host_default_changes(
    audio: Mock, monkeypatch: pytest.MonkeyPatch, endpoint: str
) -> None:
    def negotiate(_audio: object, index: int | None) -> tuple[int, int, None]:
        assert index == 1
        audio.get_default_input_device_info.return_value = device(1, "pulse", 32)
        return 1, 16000, None

    monkeypatch.setattr(capture, "_open_capture_stream", negotiate)
    source = capture.PortAudioCaptureSource()
    try:
        if endpoint == "open":
            source.open(audio)
        elif endpoint == "reopen":
            assert source.reopen(audio)
        else:
            assert capture.test_audio_input(duration=0.1)["success"]
        audio.open.assert_called_once()
        assert audio.open.call_args.kwargs["input_device_index"] == 1
    finally:
        if endpoint != "settings":
            source.close()


def test_unknown_host_api_keeps_the_host_default(audio: Mock) -> None:
    audio.get_host_api_info_by_index.side_effect = OSError("host metadata unavailable")
    assert capture._resolve_system_default(audio) is None
    audio.open.assert_not_called()
