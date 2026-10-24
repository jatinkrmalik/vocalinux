"""Settings must not publish load-time fields into a superseded initializer."""

import sys
import threading
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from test_reconfigure_worker_handoff import _make_manager

from vocalinux.speech_recognition import recognition_manager as rm


def _track_deferred_workers(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> list[threading.Thread]:
    workers: list[threading.Thread] = []
    for method_name in ("_resume_after_reload", "_unload_after_reload"):
        original = getattr(manager, method_name)

        def run(*args: object, target: Callable[..., None] = original) -> None:
            workers.append(threading.current_thread())
            target(*args)

        monkeypatch.setattr(manager, method_name, run)
    return workers


def _gate_whispercpp_initializer(
    manager: rm.SpeechRecognitionManager,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[threading.Event, threading.Event, list[tuple[str, str]]]:
    entered, release = threading.Event(), threading.Event()
    loads: list[tuple[str, str]] = []
    checkpoint = tmp_path / "ggml-tiny.bin"
    checkpoint.write_bytes(b"model")

    def preload() -> None:
        entered.set()
        assert release.wait(3)

    def load_whispercpp(path: str) -> None:
        loads.append(("whisper_cpp", manager.model_size))
        manager.model = ("whisper_cpp", manager.model_size)
        manager._model_initialized = True

    def create_parakeet(**kwargs: object) -> tuple[str, str]:
        loads.append(("parakeet", manager.model_size))
        return ("parakeet", manager.model_size)

    monkeypatch.setattr(rm, "_preload_pywhispercpp_shared_libraries", preload)
    monkeypatch.setitem(sys.modules, "pywhispercpp.model", SimpleNamespace(Model=Mock()))
    monkeypatch.setitem(
        sys.modules,
        "sherpa_onnx",
        SimpleNamespace(OfflineRecognizer=SimpleNamespace(from_transducer=create_parakeet)),
    )
    monkeypatch.setattr(rm, "get_model_path", lambda size: str(checkpoint))
    monkeypatch.setattr(manager, "_whispercpp_model_is_verified", lambda path: True)
    monkeypatch.setattr(manager, "_load_whispercpp_model", load_whispercpp)
    monkeypatch.setattr(rm.parakeet, "is_model_downloaded", lambda size: True)
    monkeypatch.setattr(manager, "_parakeet_model_is_verified", lambda *args: True)
    return entered, release, loads


def test_superseded_resume_cannot_replace_the_requested_parakeet_model(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manager = _make_manager(monkeypatch)
    entered, release, loads = _gate_whispercpp_initializer(manager, monkeypatch, tmp_path)
    workers = _track_deferred_workers(manager, monkeypatch)
    waiting = threading.Event()
    errors: list[Exception] = []
    original_wait = manager._wait_for_model_settings_handoff

    def wait() -> None:
        waiting.set()
        original_wait()

    def reconfigure() -> None:
        try:
            manager.reconfigure(engine="parakeet", model_size="v2-english", force_download=False)
        except Exception as error:
            errors.append(error)

    monkeypatch.setattr(manager, "_wait_for_model_settings_handoff", wait)
    # Enter the production deferred path, then block the real whisper.cpp
    # initializer immediately before its model-name validation.
    manager._model_lock.acquire()
    try:
        manager.reinitialize_after_resume(auto_resume=True)
    finally:
        manager._model_lock.release()
    assert entered.wait(1)
    settings_worker = threading.Thread(target=reconfigure)
    settings_worker.start()
    try:
        assert waiting.wait(1)
        assert (manager.engine, manager.model_size) == ("whisper_cpp", "small")
    finally:
        release.set()
        settings_worker.join(2)
        for worker in workers:
            worker.join(2)
    assert not settings_worker.is_alive()
    assert all(not worker.is_alive() for worker in workers)
    assert errors == []
    assert loads == [("whisper_cpp", "small"), ("parakeet", "v2-english")]
    assert (manager.engine, manager.model_size) == ("parakeet", "v2-english")
    assert manager.model == ("parakeet", "v2-english")
    assert manager.model_ready
    assert not manager.is_auto_paused


def test_cancel_during_initial_handoff_does_not_restore_active_initializer_fields(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manager = _make_manager(monkeypatch, model_size="obsolete")
    entered, release, _loads = _gate_whispercpp_initializer(manager, monkeypatch, tmp_path)
    waiting, loading, release_load = threading.Event(), threading.Event(), threading.Event()
    errors: list[Exception] = []
    original_wait = manager._wait_for_model_settings_handoff
    original_load = manager._load_whispercpp_model

    def wait() -> None:
        waiting.set()
        original_wait()

    def load(path: str) -> None:
        loading.set()
        assert release_load.wait(3)
        original_load(path)

    def reconfigure() -> None:
        try:
            manager.reconfigure(engine="parakeet", model_size="v2-english", force_download=False)
        except Exception as error:
            errors.append(error)

    monkeypatch.setattr(manager, "_wait_for_model_settings_handoff", wait)
    monkeypatch.setattr(manager, "_load_whispercpp_model", load)
    initializer = threading.Thread(target=manager.reinitialize_after_resume)
    initializer.start()
    assert entered.wait(1)
    assert manager.try_begin_download()
    settings_worker = threading.Thread(target=reconfigure)
    settings_worker.start()
    try:
        assert waiting.wait(1)
        release.set()
        assert loading.wait(1)
        # This write is the real old initializer's invalid-model fallback.
        assert manager.model_size == "tiny"
        manager.cancel_download()
        settings_worker.join(0.5)
        assert not settings_worker.is_alive()
        assert len(errors) == 1
        assert str(errors[0]) == "Download cancelled"
        assert (manager.engine, manager.model_size) == ("whisper_cpp", "tiny")
        assert initializer.is_alive()
    finally:
        release.set()
        release_load.set()
        settings_worker.join(2)
        initializer.join(2)
        manager.end_download()
    assert not initializer.is_alive()
    assert manager.model == ("whisper_cpp", "tiny")


def test_settings_releases_initial_handoff_lock_before_network_prefetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _make_manager(monkeypatch)
    prefetched: list[tuple[str, str]] = []

    def download() -> None:
        assert manager._model_lock.acquire(blocking=False)
        try:
            prefetched.append((manager.engine, manager.model_size))
        finally:
            manager._model_lock.release()

    def initialize() -> None:
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    monkeypatch.setattr(manager, "_download_selected_model_if_missing", download)
    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    manager.reconfigure(model_size="medium")
    assert prefetched == [("whisper_cpp", "medium")]
    assert manager.model == ("whisper_cpp", "medium")


def test_resume_queued_before_settings_cannot_initialize_after_its_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager = _make_manager(monkeypatch)
    workers = _track_deferred_workers(manager, monkeypatch)
    waiting = threading.Event()
    loads: list[tuple[str, str]] = []
    errors: list[Exception] = []
    original_wait = manager._wait_for_model_settings_handoff

    def wait() -> None:
        waiting.set()
        original_wait()

    def initialize() -> None:
        loads.append((manager.engine, manager.model_size))
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    def reconfigure() -> None:
        try:
            manager.reconfigure(engine="parakeet", model_size="v2-english", force_download=False)
        except Exception as error:
            errors.append(error)

    monkeypatch.setattr(manager, "_wait_for_model_settings_handoff", wait)
    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    monkeypatch.setattr(
        manager, "_init_whispercpp", lambda: pytest.fail("stale resume initialized")
    )
    manager._model_lock.acquire()
    settings_worker = threading.Thread(target=reconfigure)
    try:
        manager.reinitialize_after_resume(auto_resume=True)
        settings_worker.start()
        assert waiting.wait(1)
    finally:
        manager._model_lock.release()
        settings_worker.join(2)
        for worker in workers:
            worker.join(2)
    assert errors == []
    assert not settings_worker.is_alive()
    assert all(not worker.is_alive() for worker in workers)
    assert loads == [("parakeet", "v2-english")]
    assert manager.model == ("parakeet", "v2-english")


def test_auto_pause_after_settings_reservation_still_owns_the_unload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manager = _make_manager(monkeypatch)
    entered, release, loads = _gate_whispercpp_initializer(manager, monkeypatch, tmp_path)
    workers = _track_deferred_workers(manager, monkeypatch)
    waiting = threading.Event()
    errors: list[Exception] = []
    original_wait = manager._wait_for_model_settings_handoff

    def wait() -> None:
        waiting.set()
        original_wait()

    def reconfigure() -> None:
        try:
            manager.reconfigure(engine="parakeet", model_size="v2-english", force_download=False)
        except Exception as error:
            errors.append(error)

    monkeypatch.setattr(manager, "_wait_for_model_settings_handoff", wait)
    manager._model_lock.acquire()
    try:
        manager.reinitialize_after_resume(auto_resume=True)
    finally:
        manager._model_lock.release()
    assert entered.wait(1)
    settings_worker = threading.Thread(target=reconfigure)
    settings_worker.start()
    try:
        assert waiting.wait(1)
        manager.unload_model(reason="auto_pause")
        assert manager.is_auto_paused
    finally:
        release.set()
        settings_worker.join(2)
        for worker in workers:
            worker.join(2)
    assert errors == []
    assert not settings_worker.is_alive()
    assert all(not worker.is_alive() for worker in workers)
    assert loads == [("whisper_cpp", "small")]
    assert (manager.engine, manager.model_size) == ("parakeet", "v2-english")
    assert manager.model is None
    assert not manager.model_ready
    assert manager.is_auto_paused
    assert not manager._auto_resume_pending
