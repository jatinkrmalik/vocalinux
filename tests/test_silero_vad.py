"""
Tests for Silero VAD wrapper (silero_vad.py).

Covers:
- SileroVAD.process() return type and validation
- SileroVAD.reset() state clearing
- load_silero_vad() success and graceful fallback
- Sensitivity-to-threshold mapping
"""

import sys
from unittest.mock import MagicMock, patch  # noqa: E402

# Earlier test modules (test_recognition_manager_core.py etc.) install
# `sys.modules["numpy"] = MagicMock()` at module load and don't restore it.
# Drop the NumPy module family only when the top-level reference is mocked; a
# mocked top-level package with real cached submodules can break NumPy reloads.
if isinstance(sys.modules.get("numpy"), MagicMock):
    for _module_name in list(sys.modules):
        if _module_name == "numpy" or _module_name.startswith("numpy."):
            sys.modules.pop(_module_name, None)

import numpy as np  # noqa: E402
import pytest  # noqa: E402

from vocalinux.speech_recognition import silero_vad as _sv_mod  # noqa: E402
from vocalinux.speech_recognition.silero_vad import (  # noqa: E402
    _CONTEXT_SIZE,
    SILERO_CHUNK_SIZE,
    SILERO_SAMPLE_RATE,
    SileroVAD,
    is_silero_available,
    load_silero_vad,
)

# silero_vad imported numpy when first loaded (likely with a mocked numpy
# reference). Point its module-level `np` at the real numpy so SileroVAD
# methods use real array operations.
_sv_mod.np = np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_session(prob=0.05):
    """Create a mock ONNX InferenceSession mimicking Silero VAD output."""
    session = MagicMock()
    state = np.zeros((2, 1, 128), dtype=np.float32)
    session.run.return_value = ([[prob]], state)
    return session


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSileroVADProcess:
    """Test the process() method."""

    def test_returns_float(self):
        vad = SileroVAD.__new__(SileroVAD)
        vad._session = _make_mock_session()
        vad._state = np.zeros((2, 1, 128), dtype=np.float32)
        vad._context = np.zeros((1, _CONTEXT_SIZE), dtype=np.float32)
        vad._sr = np.array(SILERO_SAMPLE_RATE, dtype=np.int64)

        chunk = np.zeros(SILERO_CHUNK_SIZE, dtype=np.int16)
        prob = vad.process(chunk)
        assert isinstance(prob, float)

    def test_prob_from_session(self):
        vad = SileroVAD.__new__(SileroVAD)
        vad._session = _make_mock_session(prob=0.42)
        vad._state = np.zeros((2, 1, 128), dtype=np.float32)
        vad._context = np.zeros((1, _CONTEXT_SIZE), dtype=np.float32)
        vad._sr = np.array(SILERO_SAMPLE_RATE, dtype=np.int64)

        chunk = np.zeros(SILERO_CHUNK_SIZE, dtype=np.int16)
        prob = vad.process(chunk)
        assert abs(prob - 0.42) < 1e-6

    def test_session_receives_correct_input_shape(self):
        """Session should receive (1, 512+64) float32 input."""
        session = _make_mock_session()
        vad = SileroVAD.__new__(SileroVAD)
        vad._session = session
        vad._state = np.zeros((2, 1, 128), dtype=np.float32)
        vad._context = np.zeros((1, _CONTEXT_SIZE), dtype=np.float32)
        vad._sr = np.array(SILERO_SAMPLE_RATE, dtype=np.int64)

        chunk = np.zeros(SILERO_CHUNK_SIZE, dtype=np.int16)
        vad.process(chunk)

        call_kwargs = session.run.call_args
        input_tensor = call_kwargs[1]["input"] if call_kwargs[1] else call_kwargs[0][1]["input"]
        assert input_tensor.shape == (1, SILERO_CHUNK_SIZE + _CONTEXT_SIZE)
        assert input_tensor.dtype == np.float32

    def test_wrong_length_raises_value_error(self):
        vad = SileroVAD.__new__(SileroVAD)
        vad._session = _make_mock_session()
        vad._state = np.zeros((2, 1, 128), dtype=np.float32)
        vad._context = np.zeros((1, _CONTEXT_SIZE), dtype=np.float32)
        vad._sr = np.array(SILERO_SAMPLE_RATE, dtype=np.int64)

        with pytest.raises(ValueError, match="Expected 512"):
            vad.process(np.zeros(256, dtype=np.int16))
        with pytest.raises(ValueError, match="Expected 512"):
            vad.process(np.zeros(1024, dtype=np.int16))

    def test_context_updated_after_process(self):
        """Context should contain last 64 samples of the processed chunk."""
        vad = SileroVAD.__new__(SileroVAD)
        vad._session = _make_mock_session()
        vad._state = np.zeros((2, 1, 128), dtype=np.float32)
        vad._context = np.zeros((1, _CONTEXT_SIZE), dtype=np.float32)
        vad._sr = np.array(SILERO_SAMPLE_RATE, dtype=np.int64)

        chunk = np.arange(SILERO_CHUNK_SIZE, dtype=np.int16)
        vad.process(chunk)

        expected = chunk[-_CONTEXT_SIZE:].astype(np.float32) / 32768.0
        assert np.allclose(vad._context[0], expected)


class TestSileroVADReset:
    """Test state reset between sessions."""

    def test_reset_clears_state(self):
        vad = SileroVAD.__new__(SileroVAD)
        vad._state = np.ones((2, 1, 128), dtype=np.float32)
        vad._context = np.ones((1, _CONTEXT_SIZE), dtype=np.float32)

        vad.reset()

        assert np.allclose(vad._state, 0.0)
        assert np.allclose(vad._context, 0.0)

    def test_reset_preserves_correct_shapes(self):
        vad = SileroVAD.__new__(SileroVAD)
        vad._state = np.ones((2, 1, 128), dtype=np.float32)
        vad._context = np.ones((1, _CONTEXT_SIZE), dtype=np.float32)

        vad.reset()

        assert vad._state.shape == (2, 1, 128)
        assert vad._context.shape == (1, _CONTEXT_SIZE)


class TestSensitivityMapping:
    """Test the sensitivity -> threshold mapping used in recognition_manager."""

    @pytest.mark.parametrize(
        "sensitivity,expected_threshold",
        [
            (1, 0.800),
            (2, 0.675),
            (3, 0.550),
            (4, 0.425),
            (5, 0.300),
        ],
    )
    def test_mapping(self, sensitivity, expected_threshold):
        threshold = 0.8 - (sensitivity - 1) * 0.125
        assert abs(threshold - expected_threshold) < 1e-10


class TestConstants:
    """Test module constants."""

    def test_chunk_size(self):
        assert SILERO_CHUNK_SIZE == 512

    def test_sample_rate(self):
        assert SILERO_SAMPLE_RATE == 16000

    def test_context_size(self):
        assert _CONTEXT_SIZE == 64


class TestLoadFallback:
    """Test graceful fallback when onnxruntime is unavailable."""

    def test_load_returns_none_on_import_error(self):
        """If SileroVAD() raises ImportError, load_silero_vad returns None."""
        with patch(
            "vocalinux.speech_recognition.silero_vad.SileroVAD",
            side_effect=ImportError("no onnxruntime"),
        ):
            result = load_silero_vad()
            assert result is None

    def test_load_returns_none_on_runtime_error(self):
        """If SileroVAD() raises RuntimeError (bad model), load returns None."""
        with patch(
            "vocalinux.speech_recognition.silero_vad.SileroVAD",
            side_effect=RuntimeError("corrupted model"),
        ):
            result = load_silero_vad()
            assert result is None

    def test_load_returns_vad_on_success(self):
        """load_silero_vad() returns a SileroVAD when init succeeds."""
        mock_vad = MagicMock(spec=SileroVAD)
        with patch(
            "vocalinux.speech_recognition.silero_vad.SileroVAD",
            return_value=mock_vad,
        ):
            result = load_silero_vad()
            assert result is mock_vad


class TestIsSileroAvailable:
    """Cheap probe used by Settings UI to decide whether to show the install hint."""

    def test_returns_false_without_onnxruntime(self):
        with patch.dict(sys.modules, {"onnxruntime": None}):
            assert is_silero_available() is False

    def test_returns_false_when_model_missing(self):
        # onnxruntime importable, but model file gone
        ort_mod = MagicMock()
        with (
            patch.dict(sys.modules, {"onnxruntime": ort_mod}),
            patch(
                "vocalinux.speech_recognition.silero_vad.os.path.exists",
                return_value=False,
            ),
        ):
            assert is_silero_available() is False

    def test_returns_true_when_both_present(self):
        ort_mod = MagicMock()
        with (
            patch.dict(sys.modules, {"onnxruntime": ort_mod}),
            patch(
                "vocalinux.speech_recognition.silero_vad.os.path.exists",
                return_value=True,
            ),
        ):
            assert is_silero_available() is True
