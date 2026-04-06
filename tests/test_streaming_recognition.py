"""Tests for streaming-specific methods in SpeechRecognitionManager."""

import json
import queue
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.modules["vosk"] = MagicMock()
sys.modules["whisper"] = MagicMock()
sys.modules["requests"] = MagicMock()
sys.modules["pyaudio"] = MagicMock()
sys.modules["wave"] = MagicMock()
sys.modules["tempfile"] = MagicMock()
sys.modules["tqdm"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["zipfile"] = MagicMock()
_mock_torch = MagicMock()
_mock_torch.cuda.is_available.return_value = False
sys.modules["torch"] = _mock_torch

from conftest import mock_audio_feedback  # noqa: E402

from vocalinux.common_types import RecognitionState  # noqa: E402
from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager  # noqa: E402


def _make_manager(engine="vosk", **kwargs):
    """Create a manager with all external deps mocked out."""
    patches = [
        patch.object(SpeechRecognitionManager, "_get_vosk_model_path"),
        patch.object(SpeechRecognitionManager, "_download_vosk_model"),
        patch("os.makedirs"),
        patch("os.path.exists", return_value=True),
        patch("threading.Thread"),
    ]
    if engine == "whisper":
        patches.append(patch.object(SpeechRecognitionManager, "_init_whisper"))
    elif engine == "whisper_cpp":
        patches.append(patch.object(SpeechRecognitionManager, "_init_whispercpp"))
    started = []
    for p in patches:
        p.start()
        started.append(p)
    try:
        mgr = SpeechRecognitionManager(engine=engine, defer_download=True, **kwargs)
    finally:
        for p in reversed(started):
            p.stop()
    mock_audio_feedback.play_start_sound.reset_mock()
    mock_audio_feedback.play_stop_sound.reset_mock()
    mock_audio_feedback.play_error_sound.reset_mock()
    return mgr


# ------------------------------------------------------------------
# Streaming callback registration
# ------------------------------------------------------------------
class TestStreamingCallbackRegistration(unittest.TestCase):
    def setUp(self):
        self.mgr = _make_manager()

    def test_add_streaming_callback(self):
        cb = MagicMock()
        self.mgr.add_streaming_callback(cb)
        self.assertIn(cb, self.mgr._streaming_callbacks)

    def test_add_multiple_callbacks(self):
        cb1, cb2 = MagicMock(), MagicMock()
        self.mgr.add_streaming_callback(cb1)
        self.mgr.add_streaming_callback(cb2)
        self.assertEqual(len(self.mgr._streaming_callbacks), 2)

    def test_remove_streaming_callback(self):
        cb = MagicMock()
        self.mgr.add_streaming_callback(cb)
        self.mgr.remove_streaming_callback(cb)
        self.assertNotIn(cb, self.mgr._streaming_callbacks)

    def test_remove_nonexistent_callback_is_noop(self):
        cb = MagicMock()
        self.mgr.remove_streaming_callback(cb)
        self.assertEqual(len(self.mgr._streaming_callbacks), 0)


# ------------------------------------------------------------------
# _emit_text
# ------------------------------------------------------------------
class TestEmitText(unittest.TestCase):
    def setUp(self):
        self.mgr = _make_manager()
        self.text_cb = MagicMock()
        self.action_cb = MagicMock()
        self.mgr.text_callbacks.append(self.text_cb)
        self.mgr.action_callbacks.append(self.action_cb)

    def test_empty_string_does_nothing(self):
        self.mgr._emit_text("")
        self.text_cb.assert_not_called()

    def test_whitespace_only_does_nothing(self):
        self.mgr._emit_text("   ")
        self.text_cb.assert_not_called()

    def test_none_does_nothing(self):
        self.mgr._emit_text(None)
        self.text_cb.assert_not_called()

    def test_text_without_voice_commands(self):
        self.mgr._voice_commands_enabled = False
        self.mgr._emit_text("hello world")
        self.text_cb.assert_called_once_with("hello world")
        self.action_cb.assert_not_called()

    def test_text_with_voice_commands(self):
        self.mgr._voice_commands_enabled = True
        self.mgr.command_processor.process_text = MagicMock(return_value=("processed", ["action1"]))
        self.mgr._emit_text("raw text")
        self.mgr.command_processor.process_text.assert_called_once_with("raw text")
        self.text_cb.assert_called_once_with("processed")
        self.action_cb.assert_called_once_with("action1")

    def test_text_callback_exception_does_not_propagate(self):
        self.text_cb.side_effect = RuntimeError("boom")
        self.mgr._voice_commands_enabled = False
        self.mgr._emit_text("hello")

    def test_action_callback_exception_does_not_propagate(self):
        self.action_cb.side_effect = RuntimeError("boom")
        self.mgr._voice_commands_enabled = True
        self.mgr.command_processor.process_text = MagicMock(return_value=("ok", ["act"]))
        self.mgr._emit_text("hello")

    def test_empty_processed_text_skips_text_callbacks(self):
        self.mgr._voice_commands_enabled = True
        self.mgr.command_processor.process_text = MagicMock(return_value=("", ["action"]))
        self.mgr._emit_text("raw")
        self.text_cb.assert_not_called()
        self.action_cb.assert_called_once_with("action")


# ------------------------------------------------------------------
# _enqueue_streaming_segment
# ------------------------------------------------------------------
class TestEnqueueStreamingSegment(unittest.TestCase):
    def setUp(self):
        self.mgr = _make_manager()
        self.mgr._segment_queue = queue.Queue(maxsize=4)
        self.mgr.audio_buffer = [b"\x00" * 1024, b"\x01" * 1024, b"\x02" * 1024]

    def test_empty_buffer_does_nothing(self):
        self.mgr.audio_buffer = []
        self.mgr._enqueue_streaming_segment()
        self.assertTrue(self.mgr._segment_queue.empty())

    def test_vosk_no_overlap(self):
        self.mgr.engine = "vosk"
        self.mgr._enqueue_streaming_segment()
        seg = self.mgr._segment_queue.get_nowait()
        self.assertTrue(seg["is_streaming"])
        self.assertFalse(seg["is_final"])
        self.assertEqual(len(seg["audio"]), 3)
        self.assertEqual(seg["overlap"], [])
        self.assertEqual(self.mgr.audio_buffer, [])

    def test_whisper_with_overlap(self):
        self.mgr.engine = "whisper"
        self.mgr.streaming_overlap_ms = 200
        self.mgr._enqueue_streaming_segment()
        seg = self.mgr._segment_queue.get_nowait()
        self.assertTrue(len(seg["overlap"]) > 0)
        self.assertEqual(self.mgr.audio_buffer, seg["overlap"])

    def test_whisper_cpp_with_overlap(self):
        self.mgr.engine = "whisper_cpp"
        self.mgr.streaming_overlap_ms = 200
        self.mgr._enqueue_streaming_segment()
        seg = self.mgr._segment_queue.get_nowait()
        self.assertTrue(len(seg["overlap"]) > 0)

    def test_is_final_flag(self):
        self.mgr._enqueue_streaming_segment(is_final=True)
        seg = self.mgr._segment_queue.get_nowait()
        self.assertTrue(seg["is_final"])

    def test_queue_full_drops_non_final(self):
        self.mgr._segment_queue = queue.Queue(maxsize=1)
        self.mgr.audio_buffer = [b"\x00"]
        self.mgr._enqueue_streaming_segment()
        self.mgr.audio_buffer = [b"\x01"]
        self.mgr._enqueue_streaming_segment()
        self.assertEqual(self.mgr._segment_queue.qsize(), 1)

    def test_queue_full_final_displaces_oldest(self):
        self.mgr._segment_queue = queue.Queue(maxsize=1)
        self.mgr.audio_buffer = [b"\x00"]
        self.mgr._enqueue_streaming_segment()
        self.mgr.audio_buffer = [b"\x01"]
        self.mgr._enqueue_streaming_segment(is_final=True)
        seg = self.mgr._segment_queue.get_nowait()
        self.assertTrue(seg["is_final"])

    def test_zero_overlap_ms_means_no_overlap(self):
        self.mgr.engine = "whisper"
        self.mgr.streaming_overlap_ms = 0
        self.mgr._enqueue_streaming_segment()
        seg = self.mgr._segment_queue.get_nowait()
        self.assertEqual(seg["overlap"], [])
        self.assertEqual(self.mgr.audio_buffer, [])


# ------------------------------------------------------------------
# _process_streaming_segment (router)
# ------------------------------------------------------------------
class TestProcessStreamingSegment(unittest.TestCase):
    def setUp(self):
        self.mgr = _make_manager()

    def test_empty_audio_chunks_returns_early(self):
        self.mgr._process_streaming_vosk = MagicMock()
        self.mgr._process_streaming_segment({"audio": [], "is_final": False})
        self.mgr._process_streaming_vosk.assert_not_called()

    def test_routes_to_vosk(self):
        self.mgr.engine = "vosk"
        self.mgr._process_streaming_vosk = MagicMock()
        self.mgr._process_streaming_segment({"audio": [b"\x00"], "is_final": False})
        self.mgr._process_streaming_vosk.assert_called_once_with([b"\x00"], False)

    def test_routes_to_whisper(self):
        self.mgr.engine = "whisper"
        self.mgr._process_streaming_whisper = MagicMock()
        self.mgr._process_streaming_segment({"audio": [b"\x00"], "is_final": True})
        self.mgr._process_streaming_whisper.assert_called_once_with([b"\x00"], True)

    def test_routes_to_whisper_cpp(self):
        self.mgr.engine = "whisper_cpp"
        self.mgr._process_streaming_whisper = MagicMock()
        self.mgr._process_streaming_segment({"audio": [b"\x00"], "is_final": False})
        self.mgr._process_streaming_whisper.assert_called_once()

    def test_unknown_engine_logs_error(self):
        self.mgr.engine = "unknown_engine"
        self.mgr._process_streaming_segment({"audio": [b"\x00"], "is_final": False})


# ------------------------------------------------------------------
# _process_streaming_vosk
# ------------------------------------------------------------------
class TestProcessStreamingVosk(unittest.TestCase):
    def setUp(self):
        self.mgr = _make_manager(engine="vosk")
        self.mgr.recognizer = MagicMock()
        self.cb = MagicMock()
        self.mgr._streaming_callbacks.append(self.cb)
        self.mgr._emit_text = MagicMock()

    def test_recognizer_none_returns_early(self):
        self.mgr.recognizer = None
        self.mgr._process_streaming_vosk([b"\x00"], False)
        self.cb.assert_not_called()

    def test_partial_result_fires_callback(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 0
        self.mgr.recognizer.PartialResult.return_value = json.dumps({"partial": "hello"})
        self.mgr._process_streaming_vosk([b"\x00"], False)
        self.cb.assert_called_once_with("hello", is_final=False)

    def test_partial_result_dedup(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 0
        self.mgr.recognizer.PartialResult.return_value = json.dumps({"partial": "hello"})
        self.mgr._process_streaming_vosk([b"\x00", b"\x01"], False)
        self.assertEqual(self.cb.call_count, 1)

    def test_empty_partial_ignored(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 0
        self.mgr.recognizer.PartialResult.return_value = json.dumps({"partial": ""})
        self.mgr._process_streaming_vosk([b"\x00"], False)
        self.cb.assert_not_called()

    def test_final_result_fires_callback_and_emit(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 1
        self.mgr.recognizer.Result.return_value = json.dumps({"text": "hello world"})
        self.mgr._process_streaming_vosk([b"\x00"], False)
        self.cb.assert_called_once_with("hello world", is_final=True)
        self.mgr._emit_text.assert_called_once_with("hello world")

    def test_final_result_dedup(self):
        self.mgr._last_streaming_final = "hello world"
        self.mgr.recognizer.AcceptWaveform.return_value = 1
        self.mgr.recognizer.Result.return_value = json.dumps({"text": "hello world"})
        self.mgr._process_streaming_vosk([b"\x00"], False)
        self.cb.assert_not_called()
        self.mgr._emit_text.assert_not_called()

    def test_is_final_calls_finalresult(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 0
        self.mgr.recognizer.PartialResult.return_value = json.dumps({"partial": ""})
        self.mgr.recognizer.FinalResult.return_value = json.dumps({"text": "final text"})
        self.mgr._process_streaming_vosk([b"\x00"], is_final=True)
        self.mgr.recognizer.FinalResult.assert_called_once()
        self.cb.assert_called_with("final text", is_final=True)
        self.mgr._emit_text.assert_called_with("final text")

    def test_is_final_empty_text_no_emit(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 0
        self.mgr.recognizer.PartialResult.return_value = json.dumps({"partial": ""})
        self.mgr.recognizer.FinalResult.return_value = json.dumps({"text": ""})
        self.mgr._process_streaming_vosk([b"\x00"], is_final=True)
        self.mgr._emit_text.assert_not_called()

    def test_partial_callback_exception_handled(self):
        self.cb.side_effect = RuntimeError("cb err")
        self.mgr.recognizer.AcceptWaveform.return_value = 0
        self.mgr.recognizer.PartialResult.return_value = json.dumps({"partial": "hello"})
        self.mgr._process_streaming_vosk([b"\x00"], False)

    def test_final_callback_exception_handled(self):
        self.cb.side_effect = RuntimeError("cb err")
        self.mgr.recognizer.AcceptWaveform.return_value = 1
        self.mgr.recognizer.Result.return_value = json.dumps({"text": "hello"})
        self.mgr._process_streaming_vosk([b"\x00"], False)

    def test_json_decode_error_in_partial(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 0
        self.mgr.recognizer.PartialResult.return_value = "not json"
        self.mgr._process_streaming_vosk([b"\x00"], False)
        self.cb.assert_not_called()

    def test_json_decode_error_in_final_result(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 1
        self.mgr.recognizer.Result.return_value = "not json"
        self.mgr._process_streaming_vosk([b"\x00"], False)
        self.cb.assert_not_called()

    def test_is_final_json_decode_error(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 0
        self.mgr.recognizer.PartialResult.return_value = json.dumps({"partial": ""})
        self.mgr.recognizer.FinalResult.return_value = "bad json"
        self.mgr._process_streaming_vosk([b"\x00"], is_final=True)
        self.mgr._emit_text.assert_not_called()

    def test_final_resets_partial_dedup(self):
        self.mgr.recognizer.AcceptWaveform.return_value = 1
        self.mgr.recognizer.Result.return_value = json.dumps({"text": "word"})
        self.mgr._last_streaming_partial = "partial"
        self.mgr._process_streaming_vosk([b"\x00"], False)
        self.assertEqual(self.mgr._last_streaming_partial, "")

    def test_is_final_callback_exception_in_finalresult(self):
        self.cb.side_effect = RuntimeError("err")
        self.mgr.recognizer.AcceptWaveform.return_value = 0
        self.mgr.recognizer.PartialResult.return_value = json.dumps({"partial": ""})
        self.mgr.recognizer.FinalResult.return_value = json.dumps({"text": "text"})
        self.mgr._process_streaming_vosk([b"\x00"], is_final=True)


# ------------------------------------------------------------------
# _process_streaming_whisper
# ------------------------------------------------------------------
class TestProcessStreamingWhisper(unittest.TestCase):
    def setUp(self):
        self.mgr = _make_manager(engine="whisper")
        self.cb = MagicMock()
        self.mgr._streaming_callbacks.append(self.cb)
        self.mgr._emit_text = MagicMock()

        self.real_np = sys.modules.get("numpy")
        mock_np = MagicMock()
        mock_arr = MagicMock()
        mock_arr.astype.return_value = mock_arr
        mock_arr.__truediv__ = MagicMock(return_value=mock_arr)
        mock_np.frombuffer.return_value = mock_arr
        mock_np.int16 = "int16"
        mock_np.float32 = "float32"
        sys.modules["numpy"] = mock_np
        self.mock_np = mock_np

        self.mock_torch = MagicMock()
        self.mock_torch.device.return_value = MagicMock()
        sys.modules["torch"] = self.mock_torch

    def tearDown(self):
        if self.real_np is not None:
            sys.modules["numpy"] = self.real_np
        else:
            sys.modules["numpy"] = MagicMock()

    def test_creates_transcript_buffer(self):
        self.mgr.model = MagicMock()
        self.mgr.model.device = self.mock_torch.device("cpu")
        self.mgr.model.transcribe.return_value = {"text": ""}
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.assertIsNotNone(self.mgr._transcript_buffer)

    def test_whisper_transcribe_called_with_correct_params(self):
        self.mgr.model = MagicMock()
        self.mgr.model.device = self.mock_torch.device("cpu")
        self.mgr.model.transcribe.return_value = {"text": "hello"}
        self.mgr.language = "en-us"
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        call_kwargs = self.mgr.model.transcribe.call_args
        self.assertEqual(call_kwargs[1]["language"], "en")
        self.assertEqual(call_kwargs[1]["task"], "transcribe")
        self.assertEqual(call_kwargs[1]["temperature"], 0.0)

    def test_whisper_auto_language(self):
        self.mgr.model = MagicMock()
        self.mgr.model.device = self.mock_torch.device("cpu")
        self.mgr.model.transcribe.return_value = {"text": "hello"}
        self.mgr.language = "auto"
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        call_kwargs = self.mgr.model.transcribe.call_args
        self.assertIsNone(call_kwargs[1]["language"])

    def test_whisper_other_language(self):
        self.mgr.model = MagicMock()
        self.mgr.model.device = self.mock_torch.device("cpu")
        self.mgr.model.transcribe.return_value = {"text": "hola"}
        self.mgr.language = "es"
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        call_kwargs = self.mgr.model.transcribe.call_args
        self.assertEqual(call_kwargs[1]["language"], "es")

    def test_whisper_model_none_returns_early(self):
        self.mgr.model = None
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.cb.assert_not_called()

    def test_whisper_transcribe_exception(self):
        self.mgr.model = MagicMock()
        self.mgr.model.device = self.mock_torch.device("cpu")
        self.mgr.model.transcribe.side_effect = RuntimeError("fail")
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.cb.assert_not_called()

    def test_whisper_cpp_delegates(self):
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(return_value="hello")
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.mgr._transcribe_with_whispercpp.assert_called_once()

    def test_whisper_cpp_exception(self):
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(side_effect=RuntimeError("fail"))
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.cb.assert_not_called()

    def test_whisper_cpp_returns_none(self):
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(return_value=None)
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.cb.assert_not_called()

    def test_empty_text_does_nothing(self):
        self.mgr.model = MagicMock()
        self.mgr.model.device = self.mock_torch.device("cpu")
        self.mgr.model.transcribe.return_value = {"text": ""}
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.cb.assert_not_called()

    def test_committed_text_fires_callback_and_emit(self):
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(return_value="hello")
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.mgr._transcribe_with_whispercpp.return_value = "hello world"
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.assertTrue(self.cb.called)

    def test_is_final_flushes_all_and_resets_buffer(self):
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(return_value="hello")
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.mgr._transcribe_with_whispercpp.return_value = "hello world"
        self.mgr._process_streaming_whisper([b"\x00\x00"], is_final=True)
        self.assertIsNone(self.mgr._transcript_buffer)

    def test_long_prompt_truncated(self):
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(return_value="word")
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.mgr._transcribe_with_whispercpp.return_value = "word"
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        with self.mgr._streaming_buffer_lock:
            if self.mgr._transcript_buffer:
                self.mgr._transcript_buffer._committed_words = ["w"] * 300
        self.mgr._transcribe_with_whispercpp.return_value = "new"
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)

    def test_streaming_commit_callback_exception_handled(self):
        self.cb.side_effect = RuntimeError("cb err")
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(return_value="hello")
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.mgr._transcribe_with_whispercpp.return_value = "hello world"
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)

    def test_partial_callback_exception_handled(self):
        call_count = [0]

        def side_effect_fn(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] > 1:
                raise RuntimeError("partial cb err")

        self.cb.side_effect = side_effect_fn
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(return_value="hello")
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)

    def test_is_final_callback_exception_handled(self):
        self.cb.side_effect = RuntimeError("err")
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(return_value="hello")
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        self.mgr._transcribe_with_whispercpp.return_value = "hello world"
        self.mgr._process_streaming_whisper([b"\x00\x00"], is_final=True)

    def test_buffer_none_after_insert_returns(self):
        self.mgr.engine = "whisper_cpp"
        self.mgr._transcribe_with_whispercpp = MagicMock(return_value="hello")
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)
        with self.mgr._streaming_buffer_lock:
            self.mgr._transcript_buffer = None
        self.mgr._transcribe_with_whispercpp.return_value = "world"
        self.mgr._process_streaming_whisper([b"\x00\x00"], False)


# ------------------------------------------------------------------
# _perform_recognition streaming paths
# ------------------------------------------------------------------
class TestPerformRecognitionStreaming(unittest.TestCase):
    def setUp(self):
        self.mgr = _make_manager()
        self.mgr._segment_queue = queue.Queue(maxsize=32)
        self.mgr._process_streaming_segment = MagicMock()
        self.mgr._process_audio_buffer = MagicMock()
        self.mgr._update_state = MagicMock()

    def test_streaming_segment_routed_correctly(self):
        seg = {"is_streaming": True, "audio": [b"\x00"], "is_final": False}
        self.mgr._segment_queue.put(seg)
        self.mgr._segment_queue.put(None)
        self.mgr.should_record = False
        self.mgr._perform_recognition()
        self.mgr._process_streaming_segment.assert_called_once_with(seg)
        self.mgr._process_audio_buffer.assert_not_called()

    def test_non_streaming_segment_routed_correctly(self):
        seg = [b"\x00", b"\x01"]
        self.mgr._segment_queue.put(seg)
        self.mgr._segment_queue.put(None)
        self.mgr.should_record = False
        self.mgr._perform_recognition()
        self.mgr._process_audio_buffer.assert_called_once_with(seg)
        self.mgr._process_streaming_segment.assert_not_called()

    def test_drain_handles_streaming_and_nonstreaming(self):
        streaming_seg = {
            "is_streaming": True,
            "audio": [b"\x00"],
            "is_final": True,
        }
        non_streaming_seg = [b"\x01"]
        self.mgr._segment_queue.put(None)
        self.mgr._segment_queue.put(streaming_seg)
        self.mgr._segment_queue.put(non_streaming_seg)
        self.mgr.should_record = False
        self.mgr._perform_recognition()
        self.mgr._process_streaming_segment.assert_called_once_with(streaming_seg)
        self.mgr._process_audio_buffer.assert_called_once_with(non_streaming_seg)

    def test_state_transitions_for_streaming(self):
        seg = {"is_streaming": True, "audio": [b"\x00"], "is_final": False}
        self.mgr._segment_queue.put(seg)
        self.mgr._segment_queue.put(None)
        self.mgr.should_record = True

        def stop_after_first(*args, **kwargs):
            self.mgr.should_record = False

        self.mgr._process_streaming_segment.side_effect = stop_after_first
        self.mgr._perform_recognition()
        state_calls = [c[0][0] for c in self.mgr._update_state.call_args_list]
        self.assertIn(RecognitionState.PROCESSING, state_calls)

    def test_none_in_drain_skipped(self):
        self.mgr._segment_queue.put(None)
        self.mgr._segment_queue.put(None)
        self.mgr.should_record = False
        self.mgr._perform_recognition()
        self.mgr._process_streaming_segment.assert_not_called()
        self.mgr._process_audio_buffer.assert_not_called()

    def test_empty_queue_exits_when_not_recording(self):
        self.mgr.should_record = False
        self.mgr._perform_recognition()


# ------------------------------------------------------------------
# Init streaming attributes
# ------------------------------------------------------------------
class TestInitStreamingAttributes(unittest.TestCase):
    def test_defaults(self):
        mgr = _make_manager()
        self.assertFalse(mgr.experimental_streaming)
        self.assertEqual(mgr.streaming_chunk_duration_ms, 1000)
        self.assertEqual(mgr.streaming_overlap_ms, 200)
        self.assertEqual(mgr._streaming_callbacks, [])
        self.assertIsNone(mgr._transcript_buffer)
        self.assertEqual(mgr._last_streaming_partial, "")
        self.assertEqual(mgr._last_streaming_final, "")

    def test_custom_values(self):
        mgr = _make_manager(
            experimental_streaming=True,
            streaming_chunk_duration_ms=2000,
            streaming_overlap_ms=500,
        )
        self.assertTrue(mgr.experimental_streaming)
        self.assertEqual(mgr.streaming_chunk_duration_ms, 2000)
        self.assertEqual(mgr.streaming_overlap_ms, 500)

    def test_start_recognition_resets_streaming_state(self):
        mgr = _make_manager()
        mgr._last_streaming_partial = "old"
        mgr._last_streaming_final = "old"
        from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer

        mgr._transcript_buffer = TranscriptBuffer()

        with patch("os.makedirs"), patch("os.path.exists", return_value=True):
            mock_thread = MagicMock()
            with patch("threading.Thread", return_value=mock_thread):
                mgr.state = RecognitionState.IDLE
                mgr._model_initialized = True
                mgr.start_recognition()

        self.assertEqual(mgr._last_streaming_partial, "")
        self.assertEqual(mgr._last_streaming_final, "")
        self.assertIsNone(mgr._transcript_buffer)


# ------------------------------------------------------------------
# common_types coverage
# ------------------------------------------------------------------
class TestCommonTypesProtocols(unittest.TestCase):
    def test_streaming_callback_protocol_callable(self):
        from vocalinux.common_types import StreamingCallbackProtocol  # noqa: F401

        def my_cb(text: str, is_final: bool) -> None:
            pass

        self.assertTrue(callable(my_cb))

    def test_speech_recognition_manager_protocol_has_streaming_methods(self):
        from vocalinux.common_types import SpeechRecognitionManagerProtocol

        self.assertTrue(hasattr(SpeechRecognitionManagerProtocol, "add_streaming_callback"))
        self.assertTrue(hasattr(SpeechRecognitionManagerProtocol, "remove_streaming_callback"))


# ------------------------------------------------------------------
# tray_indicator streaming callback coverage
# ------------------------------------------------------------------
class TestTrayIndicatorStreamingCallback(unittest.TestCase):
    def test_on_streaming_update_is_noop(self):
        with (
            patch("vocalinux.ui.tray_indicator.Gtk"),
            patch("vocalinux.ui.tray_indicator.GLib"),
            patch("vocalinux.ui.tray_indicator.GdkPixbuf"),
        ):
            from vocalinux.ui.tray_indicator import TrayIndicator

            mock_engine = MagicMock()
            mock_engine.state = RecognitionState.IDLE
            mock_engine.register_state_callback = MagicMock()
            mock_engine.add_streaming_callback = MagicMock()

            indicator = TrayIndicator.__new__(TrayIndicator)
            indicator.speech_engine = mock_engine
            indicator._on_streaming_update("hello", True)
            indicator._on_streaming_update("partial", False)


# ------------------------------------------------------------------
# transcript_buffer edge case coverage (line 40 + branch partials)
# ------------------------------------------------------------------
class TestTranscriptBufferEdgeCoverage(unittest.TestCase):
    def test_insert_whitespace_only(self):
        from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer

        buf = TranscriptBuffer()
        buf.insert("   ")
        self.assertEqual(buf.committed_text, "")
        self.assertEqual(buf.pending_text, "")

    def test_insert_none(self):
        from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer

        buf = TranscriptBuffer()
        buf.insert(None)
        self.assertEqual(buf.committed_text, "")

    def test_insert_empty_string(self):
        from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer

        buf = TranscriptBuffer()
        buf.insert("")
        self.assertEqual(buf.committed_text, "")

    def test_overlap_dedup_removes_committed_prefix(self):
        from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer

        buf = TranscriptBuffer()
        buf.insert("hello world")
        buf.insert("hello world foo bar")
        self.assertEqual(buf.committed_text, "hello world")
        buf.insert("hello world foo bar")
        self.assertTrue("foo" in buf.committed_text)

    def test_no_overlap_when_committed_empty(self):
        from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer

        buf = TranscriptBuffer()
        buf.insert("alpha beta")
        self.assertEqual(buf.committed_text, "")
        self.assertEqual(buf.pending_text, "alpha beta")

    def test_flush_all_empty_returns_none(self):
        from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer

        buf = TranscriptBuffer()
        self.assertIsNone(buf.flush_all())

    def test_reset_clears_everything(self):
        from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer

        buf = TranscriptBuffer()
        buf.insert("hello")
        buf.insert("hello world")
        buf.reset()
        self.assertEqual(buf.committed_text, "")
        self.assertEqual(buf.pending_text, "")
        self.assertFalse(buf.has_pending)

    def test_committed_overlap_dedup_with_multi_word_tail(self):
        from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer

        buf = TranscriptBuffer()
        buf.insert("the quick brown")
        buf.insert("the quick brown fox")
        self.assertEqual(buf.committed_text, "the quick brown")
        buf.insert("brown fox jumps")
        self.assertIn("fox", buf.committed_text)


if __name__ == "__main__":
    unittest.main()
