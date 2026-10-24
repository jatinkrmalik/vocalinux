"""Resource-changing settings cannot overtake speech from the previous engine."""

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from unittest.mock import Mock

import pytest

from vocalinux.common_types import RecognitionState
from vocalinux.speech_recognition import recognition_manager as rm


def _make_manager(
    monkeypatch: pytest.MonkeyPatch, engine: str = "whisper_cpp", model_size: str = "small"
) -> rm.SpeechRecognitionManager:
    monkeypatch.setattr(rm, "load_silero_vad", lambda: None)
    for sound in ("play_start_sound", "play_stop_sound", "play_error_sound"):
        monkeypatch.setattr(rm, sound, Mock())
    with monkeypatch.context() as patcher:
        for initializer in (
            "_init_vosk",
            "_init_whisper",
            "_init_whispercpp",
            "_init_parakeet",
            "_init_faster_whisper",
            "_init_remote_api",
        ):
            patcher.setattr(rm.SpeechRecognitionManager, initializer, lambda self: None)
        manager = rm.SpeechRecognitionManager(
            engine=engine,
            model_size=model_size,
            language="en-us",
            playback_duck=Mock(enabled=Mock(return_value=False)),
        )
    manager.model = (engine, model_size)
    manager._model_initialized = True
    manager.stop_sound_guard_ms = 0
    manager._record_audio = lambda: None
    return manager


@contextmanager
def _cancelled_native_worker(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> Iterator[threading.Thread]:
    entered = threading.Event()
    release = threading.Event()

    def transcribe(*_args: object) -> str:
        with manager._model_lock:
            entered.set()
            assert release.wait(3)
        return "cancelled old speech"

    transcribers = {
        "vosk": "_transcribe_with_vosk",
        "whisper": "_transcribe_with_whisper",
        "whisper_cpp": "_transcribe_with_whispercpp",
        "parakeet": "_transcribe_with_parakeet",
        "faster_whisper": "_transcribe_with_faster_whisper",
        "remote_api": "_transcribe_remote_api_segment",
    }
    monkeypatch.setattr(manager, transcribers[manager.engine], transcribe)
    monkeypatch.setattr(rm, "_RECOGNITION_JOIN_SECONDS", 0.02)
    monkeypatch.setattr(rm, "_RECOGNITION_FINAL_JOIN_SECONDS", 0.02)
    assert manager.start_recognition()
    manager._enqueue_audio_segment([b"old speech"])
    worker = manager.recognition_thread
    assert worker is not None
    try:
        assert entered.wait(1)
        manager.stop_recognition()
        assert manager.state is RecognitionState.PROCESSING
        assert manager.cancel_transcription()
        assert manager.state is RecognitionState.IDLE
        assert worker.is_alive()
        yield worker
    finally:
        release.set()
        worker.join(2)
        assert not worker.is_alive()


def test_switching_engines_drains_final_speech_before_publishing_new_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _make_manager(monkeypatch, engine="vosk")
    processed = []
    monkeypatch.setattr(
        manager,
        "_process_audio_buffer",
        lambda audio, language: processed.append((manager.engine, manager.model, list(audio))),
    )

    def initialize() -> None:
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    assert manager.start_recognition()
    with manager._buffer_lock:
        manager.audio_buffer = [b"last spoken word"]
        manager._recording_segment_has_speech = True
    try:
        manager.reconfigure(engine="whisper_cpp", model_size="medium", force_download=False)
    finally:
        manager._session_cancel.set()
        manager._signal_recognition_stop()
        if manager.recognition_thread is not None:
            manager.recognition_thread.join(2)
    assert processed == [("vosk", ("vosk", "small"), [b"last spoken word"])]
    assert manager.engine == "whisper_cpp"
    assert manager.model == ("whisper_cpp", "medium")


@pytest.mark.parametrize("tracked_only", [False, True])
def test_cancelled_native_worker_rejects_engine_change_before_mutating_settings(
    monkeypatch: pytest.MonkeyPatch, tracked_only: bool
) -> None:
    manager = _make_manager(monkeypatch)
    initialize = Mock()
    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    with _cancelled_native_worker(manager, monkeypatch) as worker:
        if tracked_only:
            manager.recognition_thread = None
        previous = manager._snapshot_reconfigure_state()
        previous_model = manager.model
        started = time.monotonic()
        with pytest.raises(TimeoutError, match="previous transcription is still finishing"):
            manager.reconfigure(
                engine="vosk", model_size="medium", vad_sensitivity=5, force_download=False
            )
        assert time.monotonic() - started < 0.3
        assert manager._snapshot_reconfigure_state() == previous
        assert manager.model is previous_model
        assert worker.is_alive()
        initialize.assert_not_called()


@pytest.mark.parametrize(
    ("engine", "model_size", "settings"),
    [
        ("whisper_cpp", "small", {"model_size": "medium"}),
        ("whisper_cpp", "small", {"force_reinit": True}),
        ("whisper_cpp", "small", {"whispercpp_temperature": 0.4}),
        ("whisper_cpp", "small.en", {"language": "de"}),
        ("vosk", "small", {"language": "de"}),
        ("parakeet", "small", {"language": "de"}),
        ("remote_api", "small", {"remote_api_url": "https://new.example.invalid"}),
    ],
)
def test_other_resource_changes_also_wait_for_cancelled_native_workers(
    monkeypatch: pytest.MonkeyPatch, engine: str, model_size: str, settings: dict[str, Any]
) -> None:
    manager = _make_manager(monkeypatch, engine=engine, model_size=model_size)
    with _cancelled_native_worker(manager, monkeypatch):
        previous = manager._snapshot_reconfigure_state()
        with pytest.raises(TimeoutError):
            manager.reconfigure(force_download=False, **settings)
        assert manager._snapshot_reconfigure_state() == previous


@pytest.mark.parametrize(
    "settings",
    [
        {"vad_sensitivity": 4, "silence_timeout": 1.7, "voice_commands_enabled": False},
        {"language": "de"},
    ],
)
def test_nonrestarting_settings_remain_hot_with_a_cancelled_native_worker(
    monkeypatch: pytest.MonkeyPatch, settings: dict[str, Any]
) -> None:
    manager = _make_manager(monkeypatch)
    previous_model = manager.model
    with _cancelled_native_worker(manager, monkeypatch) as worker:
        started = time.monotonic()
        manager.reconfigure(force_download=False, **settings)
        assert time.monotonic() - started < 0.3
        assert worker.is_alive()
        assert manager.model is previous_model
        assert manager.engine == "whisper_cpp"
        if "language" in settings:
            assert manager.language == "de"
        else:
            assert manager.vad_sensitivity == 4
            assert manager.silence_timeout == 1.7
            assert manager._voice_commands_enabled is False
