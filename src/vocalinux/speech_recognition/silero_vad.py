"""
Silero VAD wrapper for Vocalinux.

Provides neural-network-based Voice Activity Detection using the Silero VAD
ONNX model. Falls back gracefully when onnxruntime is unavailable.
"""

import logging
import os

import numpy as np

logger = logging.getLogger(__name__)

# Path to the bundled ONNX model
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "data", "silero_vad.onnx")

# Silero VAD expects 512 samples per chunk at 16kHz (32ms)
SILERO_CHUNK_SIZE = 512
SILERO_SAMPLE_RATE = 16000

# Context window size (prepended to each chunk for cross-chunk continuity)
_CONTEXT_SIZE = 64


class SileroVAD:
    """Silero VAD wrapper using ONNX Runtime inference.

    Not thread-safe — process() and reset() mutate internal LSTM state.
    Currently only called from the recording thread in _record_audio().
    """

    def __init__(self):
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        opts.log_severity_level = 3  # suppress ort warnings
        self._session = ort.InferenceSession(
            _MODEL_PATH, sess_options=opts, providers=["CPUExecutionProvider"]
        )
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, _CONTEXT_SIZE), dtype=np.float32)
        self._sr = np.array(SILERO_SAMPLE_RATE, dtype=np.int64)
        logger.info("Silero VAD model loaded")

    def reset(self):
        """Reset internal LSTM state and context (call between utterances)."""
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, _CONTEXT_SIZE), dtype=np.float32)

    def process(self, audio_int16: np.ndarray) -> float:
        """Return speech probability for a 512-sample int16 chunk.

        Args:
            audio_int16: numpy array of int16 PCM samples, length 512.

        Returns:
            Speech probability in [0, 1].

        Raises:
            ValueError: If audio_int16 length is not SILERO_CHUNK_SIZE.
        """
        if len(audio_int16) != SILERO_CHUNK_SIZE:
            raise ValueError(f"Expected {SILERO_CHUNK_SIZE} samples, got {len(audio_int16)}")
        # Normalize int16 → float32 [-1, 1]
        audio_f32 = audio_int16.astype(np.float32) / 32768.0
        audio_f32 = audio_f32.reshape(1, -1)

        # Prepend context from previous chunk (64 samples) for cross-chunk continuity
        input_with_context = np.concatenate([self._context, audio_f32], axis=1)
        self._context = audio_f32[:, -_CONTEXT_SIZE:]

        output, self._state = self._session.run(
            None, {"input": input_with_context, "sr": self._sr, "state": self._state}
        )
        return float(output[0][0])


def load_silero_vad():
    """Try to load Silero VAD, return None on failure."""
    try:
        vad = SileroVAD()
        return vad
    except Exception as e:
        # Catches ImportError (missing onnxruntime), FileNotFoundError,
        # onnxruntime.capi.onnxruntime_pybind11_state.NoSuchFile (missing model),
        # and RuntimeError (corrupted model / ONNX errors).
        logger.warning(f"Silero VAD unavailable, falling back to amplitude VAD: {e}")
        return None
