"""Deterministic shutdown races without microphone hardware or model loading."""

import queue
import sys
import threading
import time
from collections.abc import Generator
from typing import Callable
from unittest.mock import Mock

import pytest

from vocalinux.common_types import RecognitionState
from vocalinux.speech_recognition import recognition_manager as rm


@pytest.fixture
def manager(monkeypatch: pytest.MonkeyPatch) -> Generator[rm.SpeechRecognitionManager, None, None]:
    """Use real threads, mocked engines and short, independently adjustable budgets."""
    monkeypatch.setattr(rm.SpeechRecognitionManager, "_init_vosk", lambda self: None)
    monkeypatch.setattr(rm, "load_silero_vad", lambda: None)
    monkeypatch.setitem(sys.modules, "numpy", sys._vocalinux_real_numpy)
    for name in ("play_start_sound", "play_stop_sound", "play_error_sound", "_show_notification"):
        monkeypatch.setattr(rm, name, Mock())
    monkeypatch.setattr(rm, "_CAPTURE_JOIN_SECONDS", 0.02)
    monkeypatch.setattr(rm, "_RECOGNITION_JOIN_SECONDS", 0.02)
    monkeypatch.setattr(rm, "_RECOGNITION_FINAL_JOIN_SECONDS", 0.02)
    monkeypatch.setattr(rm, "_FINAL_BUFFER_SECONDS", 0.02)
    instance = rm.SpeechRecognitionManager(engine="vosk")
    instance.model = object()
    instance._model_initialized = True
    instance.stop_sound_guard_ms = 0
    yield instance
    instance._session.cancel.set()
    instance.should_record = False
    instance._capture_finished.set()
    instance._signal_recognition_stop()
    for worker in (instance.audio_thread, instance.recognition_thread):
        if worker is not None:
            worker.join(2)
            assert not worker.is_alive()


def test_blocked_read_leaves_lock_available_and_preserves_final_speech(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    entered = threading.Event()
    closed_on = []
    transcribed = []
    source = Mock(requires_pyaudio=False, sample_rate=16000, channels=1, audio=None)

    def read(should_continue: Callable[[], bool]) -> bytes:
        entered.set()
        assert manager._session.cancel.wait(2)
        assert not should_continue()
        return b"late samples"

    source.read_chunk.side_effect = read
    source.close.side_effect = lambda: closed_on.append(threading.current_thread())
    monkeypatch.setattr(manager, "_new_capture_source", lambda: source)
    monkeypatch.setattr(
        manager, "_process_audio_buffer", lambda audio, language: transcribed.append(audio)
    )
    monkeypatch.setattr(rm, "_RECOGNITION_JOIN_SECONDS", 1)
    assert manager.start_recognition()
    assert entered.wait(1)
    try:
        assert manager._buffer_lock.acquire(timeout=0.1)
        try:
            manager.audio_buffer = [b"final word"]
            manager._recording_segment_has_speech = True
        finally:
            manager._buffer_lock.release()
        manager.stop_recognition()
        assert transcribed == [[b"final word"]]
        assert closed_on == [manager.audio_thread]
        rm.play_stop_sound.assert_called_once()
        assert manager.audio_buffer == []
        assert manager.state == RecognitionState.IDLE
    finally:
        manager._session.cancel.set()


def test_final_lock_timeout_drops_segment_and_allows_restart(
    manager: rm.SpeechRecognitionManager,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    manager.state = RecognitionState.LISTENING
    manager.should_record = True
    manager.audio_buffer = [b"unavailable tail"]
    manager._recording_segment_has_speech = True
    with manager._buffer_lock:
        started = time.monotonic()
        manager.stop_recognition()
        assert time.monotonic() - started < 0.5
    assert "dropping final segment" in caplog.text
    assert manager._segment_queue.get_nowait() is None
    assert manager.state == RecognitionState.IDLE
    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    assert manager.start_recognition()
    assert manager.audio_buffer == []


def test_stuck_capture_suppresses_cue_and_blocks_reuse_until_owner_exits(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    entered = threading.Event()
    release = threading.Event()

    def capture() -> None:
        entered.set()
        assert release.wait(2)

    monkeypatch.setattr(manager, "_record_audio", capture)
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    assert manager.start_recognition()
    assert entered.wait(1)
    old_capture = manager.audio_thread
    try:
        manager.stop_recognition()
        assert manager.state == RecognitionState.IDLE
        rm.play_stop_sound.assert_not_called()
        assert not manager.start_recognition()
    finally:
        release.set()
        old_capture.join(1)
    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    assert manager.start_recognition()


def test_concurrent_and_reentrant_stops_handoff_only_once(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager.state = RecognitionState.LISTENING
    manager.should_record = True
    manager.audio_buffer = [b"one final segment"]
    manager._recording_segment_has_speech = True
    entered = threading.Event()
    release = threading.Event()
    waiting = threading.Event()
    stop = manager._stop_session
    wait = manager._session.stop_complete.wait

    def elected(session: rm._CaptureSession) -> None:
        entered.set()
        assert release.wait(2)
        stop(session)

    def waiter(timeout: float) -> bool:
        waiting.set()
        return wait(timeout)

    monkeypatch.setattr(manager, "_stop_session", elected)
    monkeypatch.setattr(manager._session.stop_complete, "wait", waiter)
    manager.state_callbacks.append(lambda state: manager.stop_recognition())
    owner = threading.Thread(target=manager.stop_recognition)
    follower = threading.Thread(target=manager.stop_recognition)
    try:
        owner.start()
        assert entered.wait(1)
        follower.start()
        assert waiting.wait(1)
    finally:
        release.set()
        owner.join(1)
        if follower.ident is not None:
            follower.join(1)
    assert not owner.is_alive() and not follower.is_alive()
    queued = []
    while not manager._segment_queue.empty():
        item = manager._segment_queue.get_nowait()
        if item is not None:
            queued.append(item[0])
    assert queued == [[b"one final segment"]]
    rm.play_stop_sound.assert_called_once()
    assert manager._session.stop_complete.is_set()


@pytest.mark.parametrize("worker_name", ["audio_thread", "recognition_thread"])
def test_worker_can_stop_itself(manager: rm.SpeechRecognitionManager, worker_name: str) -> None:
    manager.state = RecognitionState.LISTENING
    manager.should_record = True
    worker = threading.Thread(target=manager.stop_recognition)
    setattr(manager, worker_name, worker)
    worker.start()
    worker.join(1)
    assert not worker.is_alive()
    assert manager.state == RecognitionState.IDLE


@pytest.mark.parametrize("operation", ["unload_model", "reinitialize_after_resume", "reconfigure"])
def test_reload_callers_report_timeout_before_engine_handoff(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch, operation: str
) -> None:
    manager.buffer_during_reload = True
    manager._idle_unloaded = True
    manager._model_initialized = False
    original_model = manager.model
    original_timeout = manager.silence_timeout
    settings = {"silence_timeout": 1.25} if operation == "reconfigure" else {}
    loading = threading.Event()
    release = threading.Event()

    def load() -> None:
        loading.set()
        assert release.wait(2)
        manager._model_initialized = True

    monkeypatch.setattr(manager, "_init_selected_engine", load)
    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    assert manager.start_recognition()
    assert loading.wait(1)
    try:
        started = time.monotonic()
        with pytest.raises(TimeoutError, match="still loading"):
            getattr(manager, operation)(**settings)
        assert time.monotonic() - started < 0.5
        assert manager.model is original_model
        assert manager.silence_timeout == original_timeout
        assert manager._buffered_reload_session
        assert manager._cancel_buffered_session.is_set()
        assert not manager.start_recognition()
    finally:
        release.set()
        manager.recognition_thread.join(1)
    assert not manager._buffered_reload_session
    assert manager.state == RecognitionState.IDLE
    if operation == "reconfigure":
        manager.reconfigure(**settings)
        assert manager.silence_timeout == 1.25
    assert manager.start_recognition()


def test_late_recognizer_keeps_its_queue_and_cannot_change_next_session(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    decoding = threading.Event()
    release = threading.Event()
    attempts = []

    def decode(audio: list[bytes], language: str) -> None:
        attempts.append(audio)
        decoding.set()
        assert release.wait(2)
        manager._update_state(RecognitionState.ERROR)
        manager.release_playback_duck()

    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    monkeypatch.setattr(manager, "_process_audio_buffer", decode)
    assert manager.start_recognition()
    manager._segment_queue.put_nowait(([b"old speech"], "en"))
    assert decoding.wait(1)
    old_worker = manager.recognition_thread
    old_session = manager._session
    try:
        manager.stop_recognition()
        monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
        assert manager.start_recognition()
        assert manager._session is not old_session
        new_queue = manager._segment_queue
        new_queue.put_nowait(([b"new speech"], "en"))
        restore = Mock()
        monkeypatch.setattr(manager._playback_duck, "restore", restore)
    finally:
        release.set()
        old_worker.join(1)
    assert not old_worker.is_alive()
    assert manager.state == RecognitionState.LISTENING
    assert manager.should_record
    assert new_queue.get_nowait() == ([b"new speech"], "en")
    with pytest.raises(queue.Empty):
        new_queue.get_nowait()
    assert attempts == [[b"old speech"]]
    restore.assert_not_called()


def test_healthy_stop_adds_no_polling_delay(manager: rm.SpeechRecognitionManager) -> None:
    manager.state = RecognitionState.LISTENING
    manager.should_record = True
    started = time.monotonic()
    manager.stop_recognition()
    assert time.monotonic() - started < 0.05
    assert manager.state == RecognitionState.IDLE


def test_stop_from_start_callback_does_not_launch_capture(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    capture = Mock()
    monkeypatch.setattr(manager, "_record_audio", capture)
    manager.state_callbacks.append(
        lambda state: manager.stop_recognition() if state == RecognitionState.LISTENING else None
    )
    assert not manager.start_recognition()
    capture.assert_not_called()
    assert not manager.should_record
    assert manager.state == RecognitionState.IDLE


def test_final_handoff_waits_for_vad_without_publishing_after_timeout(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    vad_entered = threading.Event()
    release = threading.Event()
    source = Mock(requires_pyaudio=False, sample_rate=16000, channels=1, audio=None)
    source.read_chunk.return_value = b"\x01\x00" * 1024
    vad = Mock()

    def process(_chunk: object) -> float:
        vad_entered.set()
        assert release.wait(2)
        return 0.99

    vad.process.side_effect = process
    manager._silero_vad = vad
    monkeypatch.setattr(manager, "_new_capture_source", lambda: source)
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    assert manager.start_recognition()
    assert vad_entered.wait(1)
    try:
        assert not manager._buffer_lock.acquire(blocking=False)
        manager.stop_recognition()
        assert manager._session.stop_complete.is_set()
    finally:
        release.set()
        manager.audio_thread.join(1)
    assert not manager._recording_segment_has_speech
    assert manager._segment_queue.get_nowait() is None
    assert manager._segment_queue.get_nowait() is None
    with pytest.raises(queue.Empty):
        manager._segment_queue.get_nowait()


@pytest.mark.parametrize("hook", ["state", "cue"])
def test_reentrant_restart_cannot_be_overwritten_by_original_start(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch, hook: str
) -> None:
    captured_sessions = []
    restarted = []
    reentered = False

    def capture() -> None:
        captured_sessions.append(manager._worker_session.session)

    def restart() -> None:
        nonlocal reentered
        if reentered:
            return
        reentered = True
        manager.stop_recognition()
        restarted.append(manager.start_recognition())

    monkeypatch.setattr(manager, "_record_audio", capture)
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    if hook == "state":
        manager.state_callbacks.append(
            lambda state: restart() if state == RecognitionState.LISTENING else None
        )
    else:
        monkeypatch.setattr(rm, "play_start_sound", restart)
    assert not manager.start_recognition()
    manager.audio_thread.join(1)
    manager.recognition_thread.join(1)
    assert restarted == [True]
    assert captured_sessions == [manager._session]
    assert manager.should_record
    assert manager.state == RecognitionState.LISTENING
