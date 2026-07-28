"""Tests for speech-engine display name helpers."""

from vocalinux.ui.settings_dialog import (
    ENGINE_DISPLAY_NAMES,
    _engine_display_name,
    _engine_from_display,
)


def test_whisper_cpp_display_name():
    assert ENGINE_DISPLAY_NAMES["whisper_cpp"] == "whisper.cpp"
    assert _engine_display_name("whisper_cpp") == "whisper.cpp"
    assert _engine_from_display("whisper.cpp") == "whisper_cpp"


def test_engine_display_roundtrip():
    for engine_id in ENGINE_DISPLAY_NAMES:
        assert _engine_from_display(_engine_display_name(engine_id)) == engine_id
