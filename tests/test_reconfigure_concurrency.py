"""Concurrent hot settings must follow the model transaction that owns resources."""

import threading
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from test_model_missing_offer import _load
from test_reconfigure_worker_handoff import _make_manager


@pytest.fixture
def settings_module():
    yield from _load("vocalinux.ui.settings_dialog")


@pytest.fixture
def tray_module(settings_module):
    yield from _load("vocalinux.ui.tray_indicator")


@pytest.mark.parametrize(
    ("phase", "failure"),
    [
        ("prefetch", None),
        ("prefetch", "download"),
        ("prefetch", "initialize"),
        ("model_lock", None),
        ("model_lock", "initialize"),
        ("initialize", None),
        ("initialize", "initialize"),
    ],
)
def test_accepted_hot_settings_survive_model_success_or_rollback(
    monkeypatch, settings_module, phase, failure
):
    manager = _make_manager(monkeypatch, engine="vosk")
    entered, release = threading.Event(), threading.Event()
    errors = []
    initializations = []
    original_wait = manager._wait_for_model_settings_handoff
    previous_model = manager.model

    def download():
        if phase == "prefetch":
            entered.set()
            assert release.wait(3)
        if failure == "download":
            raise OSError("network failed")

    def wait_for_handoff():
        if phase == "model_lock":
            entered.set()
        original_wait()

    def initialize():
        initializations.append((manager.engine, manager.model_size))
        if manager.engine == "whisper_cpp":
            if phase == "initialize":
                entered.set()
                assert release.wait(3)
            if failure == "initialize":
                raise RuntimeError("new model failed")
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    def apply_model():
        try:
            manager.reconfigure(engine="whisper_cpp", model_size="medium")
        except Exception as error:
            errors.append(error)

    monkeypatch.setattr(manager, "_download_selected_model_if_missing", download)
    monkeypatch.setattr(manager, "_wait_for_model_settings_handoff", wait_for_handoff)
    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    if phase == "model_lock":
        manager._model_lock.acquire()
    worker = threading.Thread(target=apply_model)
    worker.start()
    try:
        assert entered.wait(1)
        request = manager._model_request
        done = manager._reconfigure_done
        dialog = Mock(speech_engine=manager, _initializing=False, _applying_settings=False)
        started = time.monotonic()
        settings_module.SettingsDialog._on_voice_commands_toggled(dialog, None, False)
        settings_module.SettingsDialog._on_voice_commands_toggled(dialog, None, True)
        manager.reconfigure(vad_sensitivity=9, silence_timeout=0.1, stop_sound_guard_ms=120)
        assert time.monotonic() - started < 0.3
        assert manager._model_request is request
        assert manager._reconfigure_request is request
        assert manager._reconfigure_done is done
        assert not done.is_set()
        assert not manager.start_recognition()
        dialog.config_manager.set.assert_called_with(
            "speech_recognition", "voice_commands_enabled", True
        )
    finally:
        release.set()
        if phase == "model_lock":
            manager._model_lock.release()
        worker.join(2)
    assert not worker.is_alive()
    assert bool(errors) == (failure is not None)
    expected = ("vosk", "small") if failure else ("whisper_cpp", "medium")
    assert (manager.engine, manager.model_size) == expected
    assert manager.model == expected
    if failure == "download":
        assert manager.model is previous_model
        assert initializations == []
    assert manager.model_ready
    assert not manager._prefetching_model
    assert manager._reconfigure_request is None
    assert manager._reconfigure_done.is_set()
    assert manager._voice_commands_preference is True
    assert manager._voice_commands_enabled is True
    assert manager.vad_sensitivity == 5
    assert manager.silence_timeout == 0.5
    assert manager.stop_sound_guard_ms == 120
    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    assert manager.start_recognition()
    manager.stop_recognition()


@pytest.mark.parametrize("settings", [{"engine": "whisper"}, {"language": "de"}])
def test_another_model_or_language_change_rejects_before_replacing_active_owner(
    monkeypatch, settings
):
    manager = _make_manager(monkeypatch)
    entered, release = threading.Event(), threading.Event()
    errors = []

    def download():
        entered.set()
        assert release.wait(3)

    def initialize():
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    def apply_model():
        try:
            manager.reconfigure(model_size="medium")
        except Exception as error:
            errors.append(error)

    monkeypatch.setattr(manager, "_download_selected_model_if_missing", download)
    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    worker = threading.Thread(target=apply_model)
    worker.start()
    try:
        assert entered.wait(1)
        owner = manager._model_request
        previous = manager._snapshot_reconfigure_state()
        started = time.monotonic()
        with pytest.raises(RuntimeError, match="already changing"):
            manager.reconfigure(**settings)
        assert time.monotonic() - started < 0.3
        assert manager._model_request is owner
        assert manager._reconfigure_request is owner
        assert manager._snapshot_reconfigure_state() == previous
    finally:
        release.set()
        worker.join(2)
    assert not worker.is_alive()
    assert errors == []
    assert manager.model == (manager.engine, manager.model_size) == ("whisper_cpp", "medium")
    assert not manager._prefetching_model


def test_tray_download_announces_the_new_model_after_a_concurrent_voice_toggle(
    monkeypatch, settings_module, tray_module
):
    manager = _make_manager(monkeypatch)
    entered, release = threading.Event(), threading.Event()

    def download():
        entered.set()
        assert release.wait(3)

    def initialize():
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    monkeypatch.setattr(manager, "_download_selected_model_if_missing", download)
    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    monkeypatch.setattr(tray_module, "_idle_once", lambda fn, *args: fn(*args))
    notifications = Mock()
    monkeypatch.setattr(tray_module, "notifications", notifications)
    tray = Mock(speech_engine=manager)
    assert manager.try_begin_download()
    recommendation = SimpleNamespace(model_id="medium", display_name="Medium")
    worker = threading.Thread(
        target=tray_module.TrayIndicator._run_recommended_model_download,
        args=(tray, "whisper_cpp", recommendation, object()),
    )
    worker.start()
    try:
        assert entered.wait(1)
        dialog = Mock(speech_engine=manager, _initializing=False, _applying_settings=False)
        settings_module.SettingsDialog._on_voice_commands_toggled(dialog, None, True)
    finally:
        release.set()
        worker.join(2)
    assert not worker.is_alive()
    assert manager.model == ("whisper_cpp", "medium")
    assert manager._voice_commands_preference is True
    assert not manager._prefetching_model
    assert not manager.download_in_progress
    tray.config_manager.set_model_size_for_engine.assert_called_once_with("whisper_cpp", "medium")
    tray.config_manager.save_config.assert_called_once_with()
    assert notifications.notify.call_args.args[0] == "Speech model ready"


def test_hot_toggle_during_idle_cleanup_keeps_lazy_recovery_available(monkeypatch, settings_module):
    manager = _make_manager(monkeypatch, engine="faster_whisper")
    entered, release = threading.Event(), threading.Event()
    manager._faster_whisper_engine = Mock()

    def cleanup():
        entered.set()
        assert release.wait(3)

    def initialize():
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    manager._faster_whisper_engine.cleanup.side_effect = cleanup
    monkeypatch.setattr(manager, "_init_faster_whisper", initialize)
    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    worker = threading.Thread(target=manager.unload_model, kwargs={"reason": "idle_keepalive"})
    worker.start()
    try:
        assert entered.wait(1)
        assert not manager.model_ready
        assert manager.is_idle_unloaded
        dialog = Mock(speech_engine=manager, _initializing=False, _applying_settings=False)
        settings_module.SettingsDialog._on_voice_commands_toggled(dialog, None, True)
    finally:
        release.set()
        worker.join(2)
    assert not worker.is_alive()
    assert manager.is_idle_unloaded
    assert manager.start_recognition()
    assert manager.model_ready
    manager.stop_recognition()


@pytest.mark.parametrize("failure", [None, "download", "initialize"])
def test_staged_vad_controls_survive_owner_rollback_and_snapshot_save(
    monkeypatch, settings_module, failure
):
    manager = _make_manager(monkeypatch, engine="vosk")
    entered, release = threading.Event(), threading.Event()
    errors = []
    saved = {"engine": "vosk", "model_size": "small", "vad_sensitivity": 3, "silence_timeout": 1.2}

    def download():
        if failure != "initialize":
            entered.set()
            assert release.wait(3)
        if failure == "download":
            raise OSError("download failed")

    def initialize():
        if manager.engine == "whisper_cpp" and failure == "initialize":
            entered.set()
            assert release.wait(3)
            raise RuntimeError("model failed")
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    owner = Mock(speech_engine=manager)
    owner._save_selected_settings.side_effect = lambda settings: saved.update(settings)
    owner_settings = {
        "engine": "whisper_cpp",
        "model_size": "medium",
        "vad_sensitivity": 2,
        "silence_timeout": 1.1,
    }

    def apply_model():
        try:
            settings_module.SettingsDialog._apply_settings_internal(
                owner, owner_settings, raise_errors=True
            )
        except Exception as error:
            errors.append(error)

    monkeypatch.setattr(manager, "_download_selected_model_if_missing", download)
    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    monkeypatch.setattr(
        settings_module, "_undownloaded_model_info", lambda *_args: {"size_mb": 100}
    )
    worker = threading.Thread(target=apply_model)
    worker.start()
    try:
        assert entered.wait(1)
        request = manager._model_request
        staged = Mock(
            speech_engine=manager,
            language="en-us",
            _initializing=False,
            _applying_settings=False,
            _test_active=False,
            _populating_models=False,
            _simple_driving=False,
        )
        staged.get_selected_settings.return_value = {
            "engine": "whisper_cpp",
            "model_size": "large",
            "vad_sensitivity": 5,
            "silence_timeout": 0.8,
        }
        staged._save_selected_settings.side_effect = lambda settings: saved.update(settings)
        started = time.monotonic()
        settings_module.SettingsDialog._auto_apply_settings(staged)
        assert time.monotonic() - started < 0.3
        assert manager._model_request is request
        assert saved["vad_sensitivity"] == 5
        assert saved["silence_timeout"] == 0.8
        assert manager._cancel_buffered_session.is_set() is False
        # Returning a control to the owner's in-flight value must replace its
        # earlier queued edit too; live state alone cannot detect this change.
        staged.get_selected_settings.return_value["vad_sensitivity"] = 2
        settings_module.SettingsDialog._auto_apply_settings(staged)
        assert saved["vad_sensitivity"] == 2
    finally:
        release.set()
        worker.join(2)
    assert not worker.is_alive()
    assert bool(errors) == (failure is not None)
    expected = ("vosk", "small") if failure else ("whisper_cpp", "medium")
    assert (manager.engine, manager.model_size) == expected
    assert manager.model == expected
    assert (saved["engine"], saved["model_size"]) == expected
    assert saved["vad_sensitivity"] == manager.vad_sensitivity == 2
    assert saved["silence_timeout"] == manager.silence_timeout == 0.8
    assert manager.model_ready
    assert not manager._prefetching_model


@pytest.mark.parametrize("change", [False, True])
def test_settings_with_a_resident_model_settles_idle_unloaded_flag(monkeypatch, change):
    manager = _make_manager(monkeypatch)
    manager.unload_model(reason="idle_keepalive")
    assert manager.is_idle_unloaded

    def initialize():
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    manager.reconfigure(
        model_size="medium" if change else None, force_reinit=True, force_download=False
    )
    assert manager.model_ready
    assert not manager.is_idle_unloaded


def test_staged_vad_edit_at_owner_save_boundary_remains_the_latest_saved_value(
    monkeypatch, settings_module
):
    manager = _make_manager(monkeypatch, engine="vosk")
    saving, release_save = threading.Event(), threading.Event()
    staging, staged_done = threading.Event(), threading.Event()
    saved = {}
    errors = []

    def initialize():
        manager.model = (manager.engine, manager.model_size)
        manager._model_initialized = True

    def save_owner(settings):
        saving.set()
        assert release_save.wait(3)
        saved.update(settings)

    owner = Mock(speech_engine=manager)
    owner._save_selected_settings.side_effect = save_owner
    staged = Mock(
        speech_engine=manager,
        language="en-us",
        _initializing=False,
        _applying_settings=False,
        _test_active=False,
        _populating_models=False,
        _simple_driving=False,
    )

    def staged_settings():
        staging.set()
        return {
            "engine": "whisper_cpp",
            "model_size": "large",
            "vad_sensitivity": 5,
            "silence_timeout": 2.3,
        }

    staged.get_selected_settings.side_effect = staged_settings
    staged._save_selected_settings.side_effect = lambda settings: saved.update(settings)

    def apply_model():
        try:
            settings_module.SettingsDialog._apply_settings_internal(
                owner,
                {"engine": "whisper_cpp", "model_size": "medium", "vad_sensitivity": 3},
                raise_errors=True,
            )
        except Exception as error:
            errors.append(error)

    def apply_staged():
        try:
            settings_module.SettingsDialog._auto_apply_settings(staged)
        except Exception as error:
            errors.append(error)
        finally:
            staged_done.set()

    monkeypatch.setattr(manager, "_download_selected_model_if_missing", lambda: None)
    monkeypatch.setattr(manager, "_init_selected_engine", initialize)
    monkeypatch.setattr(
        settings_module, "_undownloaded_model_info", lambda *_args: {"size_mb": 100}
    )
    owner_worker = threading.Thread(target=apply_model)
    staged_worker = threading.Thread(target=apply_staged)
    owner_worker.start()
    try:
        assert saving.wait(1)
        staged_worker.start()
        assert staging.wait(1)
        # Without persistence serialization this lets the newer staged save
        # finish first, exposing the older owner's subsequent overwrite.
        staged_done.wait(0.1)
    finally:
        release_save.set()
        owner_worker.join(2)
        if staged_worker.ident is not None:
            staged_worker.join(2)
    assert not owner_worker.is_alive()
    assert not staged_worker.is_alive()
    assert errors == []
    assert saved["vad_sensitivity"] == manager.vad_sensitivity == 5
    assert saved["silence_timeout"] == manager.silence_timeout == 2.3


@pytest.mark.parametrize("control", ["voice_commands", "staged_vad"])
@pytest.mark.parametrize("buffer_during_reload", [False, True])
def test_hot_settings_handlers_keep_native_idle_reload_responsive(
    monkeypatch, tmp_path, settings_module, control, buffer_during_reload
):
    """Real GTK handlers return while either kind of idle reload still owns native work."""
    from vocalinux.ui import config_manager

    monkeypatch.setattr(config_manager, "CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr(config_manager, "CONFIG_FILE", str(tmp_path / "config.json"))
    config = config_manager.ConfigManager()
    config.update_speech_recognition_settings(
        {"engine": "vosk", "model_size": "small", "language": "en-us"}
    )
    manager = _make_manager(monkeypatch, engine="vosk")
    manager.buffer_during_reload = buffer_during_reload
    manager.unload_model(reason="idle_keepalive")
    loading, release, returned = threading.Event(), threading.Event(), threading.Event()
    errors = []
    started = []
    loaded_model = object()

    def initialize():
        loading.set()
        assert release.wait(3)
        manager.model = loaded_model
        manager._model_initialized = True

    monkeypatch.setattr(manager, "_init_vosk", initialize)
    monkeypatch.setattr(manager, "_record_audio", lambda: None)
    monkeypatch.setattr(manager, "_perform_recognition", lambda: None)
    monkeypatch.setattr(
        settings_module, "_undownloaded_model_info", lambda *_args: {"size_mb": 100}
    )
    dialog = Mock(
        speech_engine=manager,
        config_manager=config,
        language="en-us",
        _initializing=False,
        _applying_settings=False,
        _test_active=False,
        _populating_models=False,
        _simple_driving=False,
    )
    dialog.get_selected_settings.return_value = {
        "engine": "whisper_cpp",
        "model_size": "large",
        "vad_sensitivity": 5,
        "silence_timeout": 2.3,
    }
    dialog._save_selected_settings = settings_module.SettingsDialog._save_selected_settings.__get__(
        dialog
    )

    def start():
        try:
            started.append(manager.start_recognition())
        except Exception as error:
            errors.append(error)

    def edit():
        try:
            if control == "voice_commands":
                settings_module.SettingsDialog._on_voice_commands_toggled(dialog, None, True)
            else:
                settings_module.SettingsDialog._auto_apply_settings(dialog)
        except Exception as error:
            errors.append(error)
        finally:
            returned.set()

    starter, editor = threading.Thread(target=start), threading.Thread(target=edit)
    starter.start()
    try:
        assert loading.wait(1)
        request = manager._model_request
        session = manager._session
        editor.start()
        assert returned.wait(0.5)
        assert not release.is_set()
        assert manager._model_request is request
        assert manager._session is session
        assert not manager._cancel_buffered_session.is_set()
        if control == "voice_commands":
            assert manager._voice_commands_preference is True
            assert config.get("speech_recognition", "voice_commands_enabled") is True
        else:
            assert (
                manager.vad_sensitivity == config.get("speech_recognition", "vad_sensitivity") == 5
            )
            assert (
                manager.silence_timeout
                == config.get("speech_recognition", "silence_timeout")
                == 2.3
            )
            assert config.get("speech_recognition", "engine") == "vosk"
    finally:
        release.set()
        starter.join(2)
        if editor.ident is not None:
            editor.join(2)
        if manager.recognition_thread is not None:
            manager.recognition_thread.join(2)
        manager.stop_recognition()
    assert not starter.is_alive()
    assert not editor.is_alive()
    assert errors == []
    assert started == [True]
    assert manager.model is loaded_model
