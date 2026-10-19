"""Deterministic shutdown races without microphone hardware or model loading."""

import importlib
import queue
import sys
import threading
import time
from collections.abc import Generator, Iterator
from contextlib import contextmanager, nullcontext
from pathlib import Path
from types import ModuleType
from typing import Callable
from unittest.mock import MagicMock, Mock

import pytest

from vocalinux.auto_pause_monitor import AutoPauseMonitor
from vocalinux.common_types import RecognitionState
from vocalinux.speech_recognition import recognition_manager as rm


@pytest.fixture
def manager(monkeypatch: pytest.MonkeyPatch) -> Generator[rm.SpeechRecognitionManager, None, None]:
    """Use real threads, mocked engines and short, independently adjustable budgets."""
    monkeypatch.setattr(rm.SpeechRecognitionManager, "_init_vosk", lambda self: None)
    monkeypatch.setattr(rm, "load_silero_vad", lambda: None)
    monkeypatch.setitem(sys.modules, "numpy", sys._vocalinux_real_numpy)
    for name in ("play_start_sound", "play_stop_sound", "play_error_sound"):
        monkeypatch.setattr(rm, name, Mock())
    monkeypatch.setattr(rm, "_CAPTURE_JOIN_SECONDS", 0.02)
    monkeypatch.setattr(rm, "_RECOGNITION_JOIN_SECONDS", 0.02)
    monkeypatch.setattr(rm, "_RECOGNITION_FINAL_JOIN_SECONDS", 0.02)
    monkeypatch.setattr(rm, "_FINAL_BUFFER_SECONDS", 0.02)
    # Restore this patch before the autouse notification patch exits.
    with monkeypatch.context() as patcher:
        patcher.setattr(rm, "_show_notification", Mock())
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
    if operation == "unload_model":
        settings = {"reason": "manual"}
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


class _AutoPauseFlow:
    """Exercise production monitor/tray callbacks with gated model workers."""

    def __init__(
        self, manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The fixture isolates this import from other tests' mocked GLib modules.
        from vocalinux.ui.tray_indicator import TrayIndicator

        self.manager = manager
        self.loading = threading.Event()
        self.release_load = threading.Event()
        self.unload_started = threading.Event()
        self.release_unload = threading.Event()
        self.resume_started = threading.Event()
        self.release_resume = threading.Event()
        self.unload_threads: list[threading.Thread] = []
        self.resume_threads: list[threading.Thread] = []
        self.cleanup_during_reload: list[bool] = []
        self.resumed_model = object()
        self.backend = Mock()
        self.http_session = Mock()
        self.transcribe = Mock()
        self.reinit = Mock(side_effect=self._reinit)
        manager.buffer_during_reload = True
        manager._idle_unloaded = True
        manager._model_initialized = False
        manager._faster_whisper_engine = self.backend
        manager._http_session = self.http_session

        def load() -> None:
            self.loading.set()
            assert self.release_load.wait(3)
            manager.model = object()
            manager._model_initialized = True

        unload_after_reload = manager._unload_after_reload
        resume_after_reload = manager._resume_after_reload

        def deferred_unload(worker: threading.Thread, request: object) -> None:
            self.unload_threads.append(threading.current_thread())
            self.unload_started.set()
            assert self.release_unload.wait(3)
            unload_after_reload(worker, request)

        def deferred_resume(worker: threading.Thread, request: object) -> None:
            self.resume_threads.append(threading.current_thread())
            self.resume_started.set()
            assert self.release_resume.wait(3)
            resume_after_reload(worker, request)

        monkeypatch.setattr(manager, "_init_selected_engine", load)
        monkeypatch.setattr(manager, "_init_vosk", self.reinit)
        monkeypatch.setattr(manager, "_record_audio", lambda: None)
        monkeypatch.setattr(manager, "_unload_after_reload", deferred_unload)
        monkeypatch.setattr(manager, "_resume_after_reload", deferred_resume)
        monkeypatch.setattr(manager, "_process_audio_buffer", self.transcribe)
        self.tray = TrayIndicator.__new__(TrayIndicator)
        self.tray.speech_engine = manager
        self.tray._model_keepalive = Mock()
        self.running: set[str] = set()
        self.monitor = AutoPauseMonitor(
            get_config=lambda: (True, ["game"], 5),
            on_pause=self.tray._on_auto_pause,
            on_resume=self.tray._on_auto_resume,
            process_snapshot=lambda: self.running,
            use_glib=False,
        )
        self.tray._auto_pause_monitor = self.monitor
        self.backend.cleanup.side_effect = lambda: self.cleanup_during_reload.append(
            self.reload_worker.is_alive()
        )

    def _reinit(self) -> None:
        self.manager.model = self.resumed_model
        self.manager._model_initialized = True

    def poll(self, running: bool) -> None:
        self.running.clear()
        if running:
            self.running.add("game")
        started = time.monotonic()
        assert self.monitor.check_once() is running
        assert time.monotonic() - started < 0.5
        assert self.monitor.paused is running

    def finish_reload(self) -> None:
        self.release_load.set()
        self.reload_worker.join(1)
        assert not self.reload_worker.is_alive()
        assert not self.manager._buffered_reload_session
        assert self.manager.state == RecognitionState.IDLE
        self.transcribe.assert_not_called()

    def join(self, workers: list[threading.Thread]) -> None:
        for worker in workers:
            worker.join(1)
            assert not worker.is_alive()


@contextmanager
def _isolated_tray_import() -> Iterator[ModuleType]:
    """Restore local modules and package bindings, including newly imported dependencies."""
    saved_modules = {
        name: module
        for name, module in sys.modules.copy().items()
        if name == "vocalinux" or name.startswith("vocalinux.")
    }
    saved_packages = {
        name: (module, vars(module).copy())
        for name, module in saved_modules.items()
        if isinstance(module, ModuleType) and hasattr(module, "__path__")
    }
    try:
        # A cached tray may be bound to a different test's GLib mock.
        sys.modules.pop("vocalinux.ui.tray_indicator", None)
        yield importlib.import_module("vocalinux.ui.tray_indicator")
    finally:
        module_names = set(saved_modules) | {
            name for name in sys.modules.copy() if name.startswith("vocalinux.")
        }
        for name in module_names:
            if name in saved_modules:
                sys.modules[name] = saved_modules[name]
            else:
                sys.modules.pop(name, None)
            parent_name, _, attribute = name.rpartition(".")
            if parent_name in saved_packages:
                parent, attributes = saved_packages[parent_name]
                if attribute in attributes:
                    setattr(parent, attribute, attributes[attribute])
                else:
                    vars(parent).pop(attribute, None)


@pytest.fixture
def auto_pause_flow(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> Generator[_AutoPauseFlow, None, None]:
    with _isolated_tray_import():
        flow = _AutoPauseFlow(manager, monkeypatch)
        try:
            assert manager.start_recognition()
            flow.reload_worker = manager.recognition_thread
            assert flow.loading.wait(1)
            yield flow
        finally:
            flow.release_load.set()
            flow.release_unload.set()
            flow.release_resume.set()
            flow.join(
                [
                    worker
                    for worker in (manager.audio_thread, manager.recognition_thread)
                    if worker is not None
                ]
                + flow.unload_threads
                + flow.resume_threads
            )


@pytest.mark.parametrize("cached", [False, True])
@pytest.mark.parametrize("package_attribute", [False, True])
@pytest.mark.parametrize("fail", [False, True])
def test_tray_import_restores_modules_and_package_attributes(
    monkeypatch: pytest.MonkeyPatch, cached: bool, package_attribute: bool, fail: bool
) -> None:
    """An earlier GLib mock must not survive an isolated flow through import caching."""
    import vocalinux.ui

    tray_name = "vocalinux.ui.tray_indicator"
    settings_name = "vocalinux.ui.settings_dialog"
    # Model a cached tray and a freshly imported dependency independently of
    # their package attributes; those bindings can be absent or out of sync.
    old_tray = ModuleType(tray_name)
    old_tray.GLib = MagicMock()
    old_attribute = ModuleType(tray_name)
    if cached:
        monkeypatch.setitem(sys.modules, tray_name, old_tray)
    else:
        monkeypatch.delitem(sys.modules, tray_name, raising=False)
    monkeypatch.delitem(sys.modules, settings_name, raising=False)
    for attribute in ("tray_indicator", "settings_dialog"):
        if package_attribute:
            monkeypatch.setattr(vocalinux.ui, attribute, old_attribute, raising=False)
        else:
            monkeypatch.delattr(vocalinux.ui, attribute, raising=False)

    for _ in range(2):
        glib = MagicMock()
        monkeypatch.setattr(sys.modules["gi.repository"], "GLib", glib)
        with pytest.raises(RuntimeError, match="flow failed") if fail else nullcontext():
            with _isolated_tray_import() as tray:
                assert tray is not old_tray
                assert tray.GLib is glib
                assert vocalinux.ui.tray_indicator is tray
                assert vocalinux.ui.settings_dialog is sys.modules[settings_name]
                assert tray.TrayIndicator._reinit_keyboard_fallback(Mock()) is glib.SOURCE_REMOVE
                if fail:
                    raise RuntimeError("flow failed")

        if cached:
            assert sys.modules[tray_name] is old_tray
        else:
            assert tray_name not in sys.modules
        assert settings_name not in sys.modules
        for attribute in ("tray_indicator", "settings_dialog"):
            if package_attribute:
                assert vars(vocalinux.ui)[attribute] is old_attribute
            else:
                assert attribute not in vars(vocalinux.ui)


@pytest.mark.parametrize(
    "resume", ["after_unload", "during_reload", "during_cancel", "before_deferred_unload"]
)
def test_monitor_auto_pause_survives_reload_timeout(
    manager: rm.SpeechRecognitionManager,
    monkeypatch: pytest.MonkeyPatch,
    auto_pause_flow: _AutoPauseFlow,
    resume: str,
) -> None:
    """A single monitor resume recovers automatically, including after timeout."""
    flow = auto_pause_flow
    flow.poll(True)
    assert flow.unload_started.wait(1)
    assert flow.reload_worker.is_alive()
    assert manager.is_auto_paused
    assert not manager.is_idle_unloaded
    assert not manager.start_recognition()
    flow.backend.cleanup.assert_not_called()
    flow.http_session.close.assert_not_called()
    flow.poll(True)
    assert len(flow.unload_threads) == 1

    if resume == "during_reload":
        flow.poll(False)
        assert flow.resume_started.wait(1)
        assert manager.is_auto_paused
        assert not manager.start_recognition()
        # Allow the real deferred callback to wait for the captured worker.
        flow.release_resume.set()
    elif resume == "during_cancel":
        cancel_reload = manager._cancel_reload_recording

        def cancel_after_release() -> None:
            assert flow.reload_worker.is_alive()
            flow.release_load.set()
            cancel_reload()

        monkeypatch.setattr(manager, "_cancel_reload_recording", cancel_after_release)
        monkeypatch.setattr(rm, "_RECOGNITION_JOIN_SECONDS", 1)
        flow.poll(False)
        assert not flow.resume_started.is_set()

    flow.finish_reload()
    if resume == "after_unload":
        flow.release_unload.set()
        flow.join(flow.unload_threads)
        assert manager.model is None
        assert manager.is_auto_paused
        assert not manager.is_idle_unloaded
        assert not manager.start_recognition()
        flow.poll(True)
        assert len(flow.unload_threads) == 1
        flow.poll(False)
    elif resume == "before_deferred_unload":
        flow.poll(False)
    elif resume == "during_reload":
        flow.join(flow.resume_threads)
        # No further monitor transition or manual resume is needed.
        flow.poll(False)
        assert len(flow.resume_threads) == 1

    assert manager.model is flow.resumed_model
    assert manager.model_ready
    assert not manager.is_auto_paused
    assert not manager.is_idle_unloaded
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    assert manager.start_recognition()
    # Let the stale unload arrive after resumed dictation has started.
    flow.release_unload.set()
    flow.join(flow.unload_threads)
    assert manager.model is flow.resumed_model
    assert manager.state == RecognitionState.LISTENING
    assert manager.should_record
    flow.reinit.assert_called_once_with()
    flow.backend.cleanup.assert_called_once_with()
    flow.http_session.close.assert_called_once_with()
    assert flow.cleanup_during_reload == [False]


@pytest.mark.parametrize("supersede", ["pause", "resume"])
def test_new_monitor_transition_invalidates_deferred_resume(
    manager: rm.SpeechRecognitionManager, auto_pause_flow: _AutoPauseFlow, supersede: str
) -> None:
    flow = auto_pause_flow
    flow.poll(True)
    assert flow.unload_started.wait(1)
    flow.poll(False)
    assert flow.resume_started.wait(1)
    assert manager.is_auto_paused
    flow.unload_started.clear()
    flow.poll(True)
    assert flow.unload_started.wait(1)
    assert len(flow.unload_threads) == 2
    flow.finish_reload()

    if supersede == "resume":
        flow.poll(False)
        assert manager.model is flow.resumed_model
        assert not manager.is_auto_paused
    flow.release_resume.set()
    flow.join(flow.resume_threads)
    flow.release_unload.set()
    flow.join(flow.unload_threads)
    if supersede == "pause":
        flow.reinit.assert_not_called()
        assert manager.model is None
        assert manager.is_auto_paused
        assert not manager.start_recognition()
    else:
        flow.reinit.assert_called_once_with()
        assert manager.model is flow.resumed_model
        assert manager.model_ready
        assert not manager.is_auto_paused
    flow.backend.cleanup.assert_called_once_with()
    flow.http_session.close.assert_called_once_with()
    assert flow.cleanup_during_reload == [False]


@pytest.mark.parametrize("pending", ["unload", "resume"])
@pytest.mark.parametrize(
    "operation", ["manual", "idle_keepalive", "reconfigure", "system_resume", "suspend"]
)
def test_lifecycle_operation_invalidates_deferred_auto_pause_work(
    manager: rm.SpeechRecognitionManager,
    monkeypatch: pytest.MonkeyPatch,
    auto_pause_flow: _AutoPauseFlow,
    pending: str,
    operation: str,
) -> None:
    flow = auto_pause_flow
    flow.poll(True)
    assert flow.unload_started.wait(1)
    if pending == "resume":
        flow.poll(False)
        assert flow.resume_started.wait(1)

    started = time.monotonic()
    if operation == "suspend":
        flow.tray._on_system_suspend()
    else:
        with pytest.raises(TimeoutError, match="still loading"):
            if operation == "reconfigure":
                manager.reconfigure(silence_timeout=1.25)
            elif operation == "system_resume":
                manager.reinitialize_after_resume()
            else:
                manager.unload_model(reason=operation)
    assert time.monotonic() - started < 0.5
    assert manager.silence_timeout != 1.25
    flow.finish_reload()
    loaded_model = manager.model
    flow.release_resume.set()
    flow.release_unload.set()
    flow.join(flow.resume_threads + flow.unload_threads)
    flow.reinit.assert_not_called()
    flow.backend.cleanup.assert_not_called()
    flow.http_session.close.assert_not_called()
    assert manager.model is loaded_model
    assert manager.is_auto_paused
    if operation == "suspend":
        from vocalinux.ui import tray_indicator

        schedule = Mock()
        monkeypatch.setattr(tray_indicator.GLib, "timeout_add_seconds", schedule)
        monkeypatch.setattr(flow.tray, "_external_activation_active", lambda: True)
        flow.tray._on_system_resume()
        if pending == "unload":
            schedule.assert_not_called()
            flow.poll(False)
        else:
            schedule.assert_called_once_with(2, flow.tray._reinit_speech_after_resume)
            schedule.call_args.args[1]()
        assert not manager.is_auto_paused
        assert manager.model_ready
        flow.reinit.assert_called_once_with()


def test_new_auto_resume_supersedes_waiting_resume(
    manager: rm.SpeechRecognitionManager, auto_pause_flow: _AutoPauseFlow
) -> None:
    flow = auto_pause_flow
    flow.poll(True)
    assert flow.unload_started.wait(1)
    flow.poll(False)
    assert flow.resume_started.wait(1)
    flow.resume_started.clear()
    flow.tray._on_auto_resume()
    assert flow.resume_started.wait(1)
    assert len(flow.resume_threads) == 2
    flow.finish_reload()
    flow.release_resume.set()
    flow.join(flow.resume_threads)
    flow.release_unload.set()
    flow.join(flow.unload_threads)
    flow.reinit.assert_called_once_with()
    assert manager.model is flow.resumed_model
    assert manager.model_ready
    assert not manager.is_auto_paused


@pytest.mark.parametrize("restart", [False, True])
@pytest.mark.parametrize("new_pause", [False, True])
def test_successful_reconfigure_takes_over_deferred_resume(
    manager: rm.SpeechRecognitionManager,
    monkeypatch: pytest.MonkeyPatch,
    auto_pause_flow: _AutoPauseFlow,
    restart: bool,
    new_pause: bool,
) -> None:
    flow = auto_pause_flow
    flow.poll(True)
    assert flow.unload_started.wait(1)
    flow.poll(False)
    assert flow.resume_started.wait(1)
    flow.finish_reload()
    initializing = threading.Event()
    release_init = threading.Event()

    def initialize() -> None:
        initializing.set()
        assert release_init.wait(3)
        flow.reinit()

    monkeypatch.setattr(manager, "_init_vosk", initialize)
    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    reconfigure = threading.Thread(
        target=manager.reconfigure, kwargs={"silence_timeout": 1.25, "force_reinit": restart}
    )
    try:
        reconfigure.start()
        assert initializing.wait(1)
        if new_pause:
            flow.unload_started.clear()
            flow.poll(True)
            assert flow.unload_started.wait(1)
        release_init.set()
        flow.join([reconfigure])
        assert manager.silence_timeout == 1.25
        flow.release_resume.set()
        flow.release_unload.set()
        flow.join(flow.resume_threads + flow.unload_threads)
        flow.reinit.assert_called_once_with()
        if new_pause:
            assert manager.is_auto_paused
            assert manager.model is None
            assert not manager.start_recognition()
            flow.poll(False)
        assert manager.model is flow.resumed_model
        assert manager.model_ready
        assert not manager.is_auto_paused
        monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
        assert manager.start_recognition()
    finally:
        release_init.set()
        flow.join([reconfigure])


@pytest.mark.parametrize("operation", ["unload", "resume"])
@pytest.mark.parametrize("resource", ["model", "recognizer"])
def test_native_destruction_does_not_block_new_pause(
    manager: rm.SpeechRecognitionManager,
    auto_pause_flow: _AutoPauseFlow,
    operation: str,
    resource: str,
) -> None:
    flow = auto_pause_flow
    flow.poll(True)
    assert flow.unload_started.wait(1)
    if operation == "resume":
        flow.poll(False)
        assert flow.resume_started.wait(1)
    flow.finish_reload()
    destroying = threading.Event()
    release_destroy = threading.Event()
    pause_done = threading.Event()

    class NativeResource:
        def __del__(self) -> None:
            destroying.set()
            assert release_destroy.wait(3)

    def pause() -> None:
        flow.tray._on_auto_pause()
        pause_done.set()

    # The manager holds the only reference, so clearing it runs __del__.
    setattr(manager, resource, NativeResource())
    pausing = threading.Thread(target=pause)
    try:
        if operation == "resume":
            flow.release_resume.set()
        else:
            flow.release_unload.set()
        assert destroying.wait(1)
        flow.unload_started.clear()
        pausing.start()
        assert pause_done.wait(0.5)
        assert flow.unload_started.wait(1)
        assert manager.is_auto_paused
        assert not manager.start_recognition()
        assert not release_destroy.is_set()
    finally:
        release_destroy.set()
        if pausing.ident is not None:
            flow.join([pausing])
        flow.release_unload.set()
        flow.join(flow.resume_threads + flow.unload_threads)
    flow.reinit.assert_not_called()
    assert manager.model is None
    assert manager.is_auto_paused


@pytest.mark.parametrize("superseded", [False, True])
def test_initializer_failure_cannot_poison_newer_resume(
    manager: rm.SpeechRecognitionManager,
    monkeypatch: pytest.MonkeyPatch,
    auto_pause_flow: _AutoPauseFlow,
    tmp_path: Path,
    superseded: bool,
) -> None:
    flow = auto_pause_flow
    flow.poll(True)
    assert flow.unload_started.wait(1)
    flow.poll(False)
    assert flow.resume_started.wait(1)
    flow.finish_reload()
    first_loading = threading.Event()
    release_first = threading.Event()
    second_loading = threading.Event()
    release_second = threading.Event()
    states: list[RecognitionState] = []
    manager.state_callbacks.append(states.append)

    def load(*args: object, **kwargs: object) -> object:
        if not first_loading.is_set():
            first_loading.set()
            assert release_first.wait(3)
            raise RuntimeError("old initializer failed")
        second_loading.set()
        if superseded:
            assert release_second.wait(3)
        return flow.resumed_model

    # Exercise the engine's own error write as well as the manager's handler.
    manager.engine = "whisper"
    manager._defer_download = False
    monkeypatch.setattr(rm, "MODELS_DIR", str(tmp_path))
    monkeypatch.setattr(manager, "_download_whisper_model", Mock())
    monkeypatch.setitem(sys.modules, "whisper", Mock(load_model=load))
    torch = Mock()
    torch.cuda.is_available.return_value = False
    monkeypatch.setitem(sys.modules, "torch", torch)
    try:
        flow.release_resume.set()
        assert first_loading.wait(1)
        if superseded:
            flow.resume_started.clear()
            flow.tray._on_auto_resume()
            assert flow.resume_started.wait(1)
            assert len(flow.resume_threads) == 2
        release_first.set()
        if not superseded:
            flow.join(flow.resume_threads)
            assert manager.state == RecognitionState.ERROR
            flow.tray._on_auto_resume()
        assert second_loading.wait(1)
        if superseded:
            assert manager.state == RecognitionState.IDLE
            assert RecognitionState.ERROR not in states
        release_second.set()
        flow.join(flow.resume_threads)
        flow.release_unload.set()
        flow.join(flow.unload_threads)
        assert manager.state == RecognitionState.IDLE
        assert manager.model is flow.resumed_model
        assert manager.model_ready
        assert not manager.is_auto_paused
        monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
        assert manager.start_recognition()
    finally:
        release_first.set()
        release_second.set()


@pytest.mark.parametrize("supersede", ["pause", "resume"])
def test_transition_while_deferred_resume_initializes(
    manager: rm.SpeechRecognitionManager,
    monkeypatch: pytest.MonkeyPatch,
    auto_pause_flow: _AutoPauseFlow,
    supersede: str,
) -> None:
    """Native initialization cannot delay a new pause or publish a stale guard."""
    flow = auto_pause_flow
    flow.poll(True)
    assert flow.unload_started.wait(1)
    flow.poll(False)
    assert flow.resume_started.wait(1)
    flow.finish_reload()
    initializing = threading.Event()
    release_init = threading.Event()

    def initialize() -> None:
        initializing.set()
        assert release_init.wait(3)
        flow._reinit()

    monkeypatch.setattr(manager, "_init_vosk", initialize)
    try:
        flow.release_resume.set()
        assert initializing.wait(1)
        assert not manager._model_lock.acquire(blocking=False)
        flow.unload_started.clear()
        flow.poll(True)
        assert flow.unload_started.wait(1)
        if supersede == "resume":
            flow.resume_started.clear()
            flow.poll(False)
            assert flow.resume_started.wait(1)
        release_init.set()
        flow.join(flow.resume_threads)
        if supersede == "pause":
            assert manager.is_auto_paused
            assert not manager.start_recognition()
        else:
            assert not manager.is_auto_paused
            assert manager.model is flow.resumed_model
        flow.release_unload.set()
        flow.join(flow.unload_threads)
        if supersede == "pause":
            assert manager.model is None
            assert manager.is_auto_paused
        else:
            assert manager.model is flow.resumed_model
            assert manager.model_ready
            assert not manager.is_auto_paused
    finally:
        release_init.set()


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


def test_stale_recognizer_cannot_deliver_text_after_slow_corrections(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    correcting = threading.Event()
    release = threading.Event()
    delivered: list[str] = []

    def correct(text: str) -> str:
        correcting.set()
        assert release.wait(2)
        return text

    manager.engine = "whisper"
    manager._voice_commands_enabled = False
    manager.text_callbacks.append(delivered.append)
    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    monkeypatch.setattr(manager, "_transcribe_with_whisper", lambda audio, language: "old text")
    monkeypatch.setattr(manager, "_apply_dictionary_corrections", correct)
    assert manager.start_recognition()
    manager._segment_queue.put_nowait(([b"old speech"], "en"))
    assert correcting.wait(1)
    old_worker = manager.recognition_thread
    try:
        manager.stop_recognition()
        monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
        assert manager.start_recognition()
    finally:
        release.set()
        old_worker.join(1)
    assert not old_worker.is_alive()
    assert delivered == []
    assert manager.state == RecognitionState.LISTENING


def test_stop_stays_bounded_and_restart_waits_for_active_text_callback(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    delivering = threading.Event()
    release = threading.Event()

    def deliver(_text: str) -> None:
        delivering.set()
        assert release.wait(2)

    manager.engine = "whisper"
    manager._voice_commands_enabled = False
    manager.text_callbacks.append(deliver)
    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    monkeypatch.setattr(manager, "_transcribe_with_whisper", lambda audio, language: "old text")
    assert manager.start_recognition()
    manager._segment_queue.put_nowait(([b"old speech"], "en"))
    assert delivering.wait(1)
    old_worker = manager.recognition_thread
    try:
        started = time.monotonic()
        manager.stop_recognition()
        assert time.monotonic() - started < 0.5
        assert not manager.start_recognition()
    finally:
        release.set()
        old_worker.join(1)
    assert not old_worker.is_alive()
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    assert manager.start_recognition()


def test_failed_start_restores_one_shot_language_after_buffer_timeout(
    manager: rm.SpeechRecognitionManager, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_language = manager.language
    monkeypatch.setattr(manager, "_serving_model_supports_language_switch", lambda: True)
    monkeypatch.setattr(manager, "_can_relanguage_without_reload", lambda: True)
    with manager._buffer_lock:
        assert not manager.start_recognition_with_language("de")
    assert manager.language == original_language
    assert manager._oneshot_language_restore is None
    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    assert manager.start_recognition()
    assert manager._session_language == original_language


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
