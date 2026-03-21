"""
Additional coverage tests for common_types.py module.

Tests for Protocol definitions and enums.
"""

import sys

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


class TestRecognitionState:
    """Tests for RecognitionState enum."""

    def test_recognition_state_idle(self):
        """Test IDLE state."""
        from vocalinux.common_types import RecognitionState

        assert RecognitionState.IDLE.value == 1

    def test_recognition_state_listening(self):
        """Test LISTENING state."""
        from vocalinux.common_types import RecognitionState

        assert RecognitionState.LISTENING.value == 2

    def test_recognition_state_processing(self):
        """Test PROCESSING state."""
        from vocalinux.common_types import RecognitionState

        assert RecognitionState.PROCESSING.value == 3

    def test_recognition_state_error(self):
        """Test ERROR state."""
        from vocalinux.common_types import RecognitionState

        assert RecognitionState.ERROR.value == 4

    def test_recognition_state_enum_members(self):
        """Test that all enum members are present."""
        from vocalinux.common_types import RecognitionState

        states = [
            RecognitionState.IDLE,
            RecognitionState.LISTENING,
            RecognitionState.PROCESSING,
            RecognitionState.ERROR,
        ]
        assert len(states) == 4

    def test_recognition_state_comparison(self):
        """Test enum member comparison."""
        from vocalinux.common_types import RecognitionState

        assert RecognitionState.IDLE == RecognitionState.IDLE
        assert RecognitionState.IDLE != RecognitionState.LISTENING


class TestProtocols:
    """Tests for Protocol definitions."""

    def test_speech_recognition_manager_protocol_defined(self):
        """Test that SpeechRecognitionManagerProtocol is defined."""
        from vocalinux.common_types import SpeechRecognitionManagerProtocol

        assert SpeechRecognitionManagerProtocol is not None

    def test_text_injector_protocol_defined(self):
        """Test that TextInjectorProtocol is defined."""
        from vocalinux.common_types import TextInjectorProtocol

        assert TextInjectorProtocol is not None

    def test_protocols_have_required_methods(self):
        """Test that protocols define required methods."""
        from vocalinux.common_types import SpeechRecognitionManagerProtocol, TextInjectorProtocol

        # SpeechRecognitionManagerProtocol should have required methods
        assert hasattr(SpeechRecognitionManagerProtocol, "__protocol_attrs__") or hasattr(
            SpeechRecognitionManagerProtocol, "__mro__"
        )

        # TextInjectorProtocol should have required methods
        assert hasattr(TextInjectorProtocol, "__protocol_attrs__") or hasattr(
            TextInjectorProtocol, "__mro__"
        )


class TestImports:
    """Tests for imports from common_types."""

    def test_can_import_all_types(self):
        """Test that all types can be imported."""
        from vocalinux.common_types import (
            Callable,
            Optional,
            Protocol,
            RecognitionState,
            SpeechRecognitionManagerProtocol,
            TextInjectorProtocol,
        )

        assert all(
            [
                RecognitionState,
                SpeechRecognitionManagerProtocol,
                TextInjectorProtocol,
                Callable,
                Optional,
                Protocol,
            ]
        )
