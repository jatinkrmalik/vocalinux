"""Capture recovery must honor stop and leave failed dictation restartable."""

import sys
import threading
from collections.abc import Generator
from typing import Callable
from unittest.mock import Mock

import pytest

from vocalinux.audio import capture
from vocalinux.common_types import RecognitionState
from vocalinux.speech_recognition import recognition_manager as rm


@pytest.fixture
def manager(monkeypatch: pytest.MonkeyPatch) -> Generator[rm.SpeechRecognitionManager, None, None]:
    monkeypatch.setattr(rm.SpeechRecognitionManager, "_init_vosk", lambda self: None)
    monkeypatch.setattr(rm, "load_silero_vad", lambda: None)
    monkeypatch.setitem(sys.modules, "numpy", sys._vocalinux_real_numpy)
    for name in ("play_start_sound", "play_stop_sound", "play_error_sound", "_show_notification"):
        monkeypatch.setattr(rm, name, Mock())
    instance = rm.SpeechRecognitionManager(engine="vosk")
    instance.model = object()
    instance._model_initialized = True
    instance._reconnection_delay = 0
    instance.stop_sound_guard_ms = 0
    yield instance
    instance._session.cancel.set()
    if instance.should_record:
        instance.stop_recognition()
    for worker in (instance.audio_thread, instance.recognition_thread):
        if worker is not None:
            worker.join(2)
            assert not worker.is_alive()


@pytest.fixture
def source(manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch) -> Mock:
    source = Mock(
        requires_pyaudio=False,
        sample_rate=16000,
        channels=1,
        audio=None,
        resolved_device_name="Webcam (hw:1,0)",
        last_error=None,
    )
    source.reopen.return_value = False
    monkeypatch.setattr(manager, "_new_capture_source", lambda: source)
    manager.should_record = True
    manager.state = RecognitionState.LISTENING
    return source


@pytest.mark.parametrize("entry", ["open", "read_chunk"])
def test_stop_after_failure_prevents_recovery_and_error_reporting(
    manager: rm.SpeechRecognitionManager, source: Mock, entry: str
) -> None:
    def fail_after_stop(*_args: object, **_kwargs: object) -> None:
        manager.stop_recognition()
        raise capture.CaptureStalledError("stopped device")

    getattr(source, entry).side_effect = fail_after_stop
    manager._record_audio()
    source.reopen.assert_not_called()
    source.close.assert_called_once()
    rm.play_error_sound.assert_not_called()
    rm._show_notification.assert_not_called()
    assert manager.state == RecognitionState.IDLE


def test_stop_interrupts_backoff_before_reopen(
    manager: rm.SpeechRecognitionManager, source: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager._capture_source = source
    manager._reconnection_delay = 60
    entered = threading.Event()
    wait = manager._session.cancel.wait
    results = []

    def backoff(seconds: float) -> bool:
        entered.set()
        return wait(seconds)

    monkeypatch.setattr(manager._session.cancel, "wait", backoff)
    worker = threading.Thread(
        target=lambda: results.append(
            manager._attempt_audio_reconnection(None, should_continue=lambda: manager.should_record)
        )
    )
    worker.start()
    try:
        assert entered.wait(1)
        manager.stop_recognition()
    finally:
        manager._session.cancel.set()
        worker.join(1)
    assert not worker.is_alive()
    assert results == [False]
    source.reopen.assert_not_called()


def test_cancellation_after_backoff_prevents_reopen(
    manager: rm.SpeechRecognitionManager, source: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager._capture_source = source

    def backoff(_seconds: float) -> bool:
        manager.should_record = False
        return False

    monkeypatch.setattr(manager._session.cancel, "wait", backoff)
    assert not manager._attempt_audio_reconnection(
        None, should_continue=lambda: manager.should_record
    )
    source.reopen.assert_not_called()


def test_cancellation_after_validation_prevents_capture_state_publication(
    manager: rm.SpeechRecognitionManager, source: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager._capture_source = source
    sync = Mock()
    monkeypatch.setattr(manager, "_sync_capture_state", sync)

    def reopen(_audio: object, should_continue: Callable[[], bool]) -> bool:
        assert should_continue()
        manager.should_record = False
        return True

    source.reopen.side_effect = reopen
    assert not manager._attempt_audio_reconnection(
        None, should_continue=lambda: manager.should_record
    )
    sync.assert_not_called()


@pytest.mark.parametrize("entry", ["open", "read_chunk"])
def test_only_one_stall_recovery_and_original_device_is_reported(
    manager: rm.SpeechRecognitionManager, source: Mock, caplog: pytest.LogCaptureFixture, entry: str
) -> None:
    errors = iter(
        [capture.CaptureStalledError("first stall"), capture.CaptureStalledError("again")]
    )
    states = []
    closed_on = []
    timeline = []
    manager.state_callbacks.append(states.append)

    def read(**_kwargs: object) -> bytes:
        manager._last_audio_error_time = 0  # Exercise the limit, not the time throttle.
        raise next(errors)

    if entry == "open":

        def fail_open(_audio: object) -> None:
            raise next(errors)

        source.open.side_effect = fail_open
    source.read_chunk.side_effect = read
    source.reopen.return_value = True

    def close() -> None:
        closed_on.append(threading.current_thread())
        timeline.append("closed")

    source.close.side_effect = close
    rm.play_error_sound.side_effect = lambda: timeline.append("error cue")
    manager._record_audio()
    assert timeline == ["closed", "error cue"]
    source.reopen.assert_called_once()
    assert closed_on == [threading.current_thread()]
    rm.play_error_sound.assert_called_once()
    rm.play_stop_sound.assert_not_called()
    rm._show_notification.assert_called_once()
    notification = rm._show_notification.call_args.args
    assert notification[0] == "Microphone Stalled"
    assert "Webcam (hw:1,0)" in notification[1] and "Settings" in notification[1]
    assert any(
        record.levelname == "ERROR"
        and "first stall" in record.message
        and "Webcam (hw:1,0)" in record.message
        for record in caplog.records
    )
    assert RecognitionState.ERROR in states
    assert states[-1] == RecognitionState.IDLE
    assert not manager.should_record


@pytest.mark.parametrize("initial_stall", [False, True])
def test_validation_stall_preserves_cause_and_resolved_device(
    manager: rm.SpeechRecognitionManager,
    monkeypatch: pytest.MonkeyPatch,
    initial_stall: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    source = capture.PortAudioCaptureSource()
    audio = Mock()
    audio.get_device_count.return_value = 0
    audio.get_default_input_device_info.return_value = {"index": 9, "name": "Original microphone"}
    first_stream = Mock()
    stream = Mock()
    monkeypatch.setitem(sys.modules, "pyaudio", Mock(PyAudio=lambda: audio, paInt16=8))
    monkeypatch.setattr(manager, "_new_capture_source", lambda: source)
    monkeypatch.setattr(
        capture,
        "_open_capture_stream",
        Mock(side_effect=[(1, 16000, first_stream), (1, 16000, stream)]),
    )
    first_error = (
        capture.CaptureStalledError("original stall") if initial_stall else OSError("lost")
    )
    validation_error = capture.CaptureStalledError("validation stall")

    def read(**_kwargs: object) -> bytes:
        audio.get_default_input_device_info.return_value = {"index": 5, "name": "Changed default"}
        raise first_error

    def validate(*_args: object, **_kwargs: object) -> bytes:
        raise validation_error

    monkeypatch.setattr(source, "read_chunk", read)
    monkeypatch.setattr(capture, "_read_frames_bounded", validate)
    manager.should_record = True
    manager.state = RecognitionState.LISTENING
    manager._record_audio()
    assert manager._session.stall_error is (first_error if initial_stall else validation_error)
    assert source.last_error is validation_error
    first_stream.close.assert_called_once()
    audio.terminate.assert_called_once()
    assert "Original microphone" in rm._show_notification.call_args.args[1]
    assert "original stall" in caplog.text if initial_stall else "validation stall" in caplog.text
    assert manager.state == RecognitionState.IDLE
    stream.close.assert_called_once()


def test_real_validation_honors_stop_without_error_cue(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = capture.PortAudioCaptureSource()
    stream = Mock()
    audio = Mock()
    audio.get_default_input_device_info.return_value = {"name": "Microphone"}
    monkeypatch.setitem(sys.modules, "pyaudio", Mock(PyAudio=lambda: audio, paInt16=8))
    monkeypatch.setattr(source, "open", lambda _audio: None)
    monkeypatch.setattr(
        source, "read_chunk", Mock(side_effect=capture.CaptureStalledError("stalled"))
    )
    monkeypatch.setattr(manager, "_new_capture_source", lambda: source)
    monkeypatch.setattr(capture, "_open_capture_stream", lambda *_args: (1, 16000, stream))

    def validate(*_args: object, should_continue: Callable[[], bool]) -> bytes:
        assert should_continue()
        manager.stop_recognition()
        assert not should_continue()
        return b"validation data"

    monkeypatch.setattr(capture, "_read_frames_bounded", validate)
    manager.should_record = True
    manager.state = RecognitionState.LISTENING
    manager._record_audio()
    rm.play_error_sound.assert_not_called()
    rm._show_notification.assert_not_called()
    stream.close.assert_called_once()
    assert manager.state == RecognitionState.IDLE


def test_failed_buffered_reload_reports_once_and_subsequent_dictation_succeeds(
    manager: rm.SpeechRecognitionManager, source: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager.should_record = False
    manager.state = RecognitionState.IDLE
    manager._idle_unloaded = True
    manager._model_initialized = False
    manager.buffer_during_reload = True
    loading = threading.Event()
    release = threading.Event()
    failed = threading.Event()
    source.read_chunk.side_effect = capture.CaptureStalledError("stalled")

    def load() -> None:
        loading.set()
        assert release.wait(2)
        manager._model_initialized = True

    monkeypatch.setattr(manager, "_init_selected_engine", load)
    manager.state_callbacks.append(
        lambda state: failed.set() if state == RecognitionState.ERROR else None
    )
    assert manager.start_recognition()
    try:
        assert loading.wait(1) and failed.wait(1)
    finally:
        release.set()
        manager.audio_thread.join(2)
        manager.recognition_thread.join(2)
    assert manager.state == RecognitionState.IDLE
    assert not manager._buffered_reload_session
    rm.play_error_sound.assert_called_once()
    rm._show_notification.assert_called_once()

    source.read_chunk.side_effect = None
    source.read_chunk.return_value = b"\xe8\x03" * 1024
    transcribed = []
    monkeypatch.setattr(
        manager, "_process_audio_buffer", lambda audio, language: transcribed.append(audio)
    )
    manager._audio_level_callbacks.append(lambda _level: manager.stop_recognition())
    assert manager.start_recognition()
    manager.audio_thread.join(2)
    manager.recognition_thread.join(2)
    assert manager.state == RecognitionState.IDLE
    assert len(transcribed) == 1


@pytest.mark.parametrize("reconnecting", [False, True])
def test_stop_during_audio_initialization_keeps_teardown_owned(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch, reconnecting: bool
) -> None:
    source = capture.PortAudioCaptureSource()
    audio = Mock()
    open_stream = Mock()
    monkeypatch.setattr(source, "open", open_stream)
    monkeypatch.setattr(source, "reopen", open_stream)
    monkeypatch.setattr(manager, "_new_capture_source", lambda: source)
    manager.should_record = True
    manager.state = RecognitionState.LISTENING

    def create_audio() -> Mock:
        manager.stop_recognition()
        return audio

    monkeypatch.setitem(sys.modules, "pyaudio", Mock(PyAudio=create_audio))
    if reconnecting:
        manager._capture_source = source
        assert not manager._attempt_audio_reconnection(None)
        source.close()  # The caller remains responsible for owner-thread teardown.
    else:
        manager._record_audio()
    open_stream.assert_not_called()
    audio.terminate.assert_called_once()
    rm.play_error_sound.assert_not_called()


def test_successful_reopen_updates_identity_for_a_later_stall(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = capture.PortAudioCaptureSource()
    audio = Mock()
    audio.get_device_count.return_value = 0
    audio.get_default_input_device_info.return_value = {"index": 2, "name": "Old microphone"}
    monkeypatch.setitem(sys.modules, "pyaudio", Mock(PyAudio=lambda: audio, paInt16=8))
    monkeypatch.setattr(manager, "_new_capture_source", lambda: source)
    streams = [Mock(), Mock(), Mock()]
    monkeypatch.setattr(
        capture,
        "_open_capture_stream",
        Mock(side_effect=[(1, 16000, stream) for stream in streams]),
    )
    monkeypatch.setattr(
        capture,
        "_read_frames_bounded",
        Mock(side_effect=[b"valid samples", OSError("validation failed")]),
    )
    failures = iter([OSError("old device lost"), capture.CaptureStalledError("new device stalled")])

    def read(**_kwargs: object) -> bytes:
        audio.get_default_input_device_info.return_value = {"index": 7, "name": "New microphone"}
        manager._last_audio_error_time = 0
        raise next(failures)

    monkeypatch.setattr(source, "read_chunk", read)
    manager.should_record = True
    manager.state = RecognitionState.LISTENING
    manager._record_audio()
    notification = rm._show_notification.call_args.args[1]
    assert "New microphone" in notification
    assert "Old microphone" not in notification
    assert source.resolved_device_name == "New microphone"
    assert str(manager._session.stall_error) == "new device stalled"
    assert manager.state == RecognitionState.IDLE
    for stream in streams:
        stream.close.assert_called_once()
    audio.terminate.assert_called_once()
