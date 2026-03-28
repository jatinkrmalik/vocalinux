"""
Tests for Silero VAD wrapper (silero_vad.py).

Covers:
- SileroVAD.process() return type and validation
- SileroVAD.reset() state clearing
- load_silero_vad() success and graceful fallback
- Sensitivity-to-threshold mapping
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from vocalinux.speech_recognition.silero_vad import (
    _CONTEXT_SIZE,
    SILERO_CHUNK_SIZE,
    SILERO_SAMPLE_RATE,
    SileroVAD,
    load_silero_vad,
)

# Detect if numpy was replaced by a MagicMock (upstream test modules do this).
# When numpy is mocked, tests that need real array operations are skipped.
_numpy_is_real = isinstance(getattr(np, "__version__", None), str)
_skip_if_numpy_mocked = pytest.mark.skipif(
    not _numpy_is_real, reason="numpy is mocked by another test module"
)


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


@_skip_if_numpy_mocked
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
        assert prob == pytest.approx(0.42)

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


@_skip_if_numpy_mocked
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
