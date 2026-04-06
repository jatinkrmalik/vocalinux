"""
Tests for the streaming transcription feature.

Covers TranscriptBuffer (LA-2 dedup logic), streaming config defaults,
and config manager integration for streaming settings.
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from vocalinux.speech_recognition.transcript_buffer import TranscriptBuffer
from vocalinux.ui.config_manager import DEFAULT_CONFIG, ConfigManager


class TestTranscriptBufferBasic(unittest.TestCase):
    def setUp(self):
        self.buf = TranscriptBuffer()

    def test_empty_buffer_has_no_committed_or_pending(self):
        self.assertEqual(self.buf.committed_text, "")
        self.assertEqual(self.buf.pending_text, "")
        self.assertFalse(self.buf.has_pending)

    def test_insert_single_pass_nothing_committed(self):
        self.buf.insert("hello world")
        self.assertEqual(self.buf.committed_text, "")
        self.assertEqual(self.buf.pending_text, "hello world")
        self.assertTrue(self.buf.has_pending)

    def test_insert_same_text_twice_commits_all(self):
        self.buf.insert("hello world")
        self.buf.insert("hello world")
        self.assertEqual(self.buf.committed_text, "hello world")
        self.assertEqual(self.buf.pending_text, "")
        self.assertFalse(self.buf.has_pending)

    def test_insert_growing_text_commits_prefix(self):
        self.buf.insert("hello")
        self.buf.insert("hello world")
        self.assertEqual(self.buf.committed_text, "hello")
        self.assertEqual(self.buf.pending_text, "world")

    def test_insert_empty_string_is_noop(self):
        self.buf.insert("hello")
        self.buf.insert("")
        self.assertEqual(self.buf.pending_text, "hello")

    def test_insert_whitespace_only_is_noop(self):
        self.buf.insert("   ")
        self.assertFalse(self.buf.has_pending)
        self.assertEqual(self.buf.committed_text, "")


class TestTranscriptBufferFlush(unittest.TestCase):
    def setUp(self):
        self.buf = TranscriptBuffer()

    def test_flush_returns_committed_only(self):
        self.buf.insert("hello")
        self.buf.insert("hello world")
        result = self.buf.flush()
        self.assertEqual(result, "hello")

    def test_flush_returns_none_when_empty(self):
        self.assertIsNone(self.buf.flush())

    def test_flush_returns_delta_only_once(self):
        self.buf.insert("hello")
        self.buf.insert("hello world")
        self.assertEqual(self.buf.flush(), "hello")
        self.assertIsNone(self.buf.flush())

    def test_flush_then_more_committed_returns_new_delta(self):
        self.buf.insert("one")
        self.buf.insert("one two")
        self.assertEqual(self.buf.flush(), "one")

        self.buf.insert("one two three")
        self.assertEqual(self.buf.flush(), "two")

    def test_flush_all_returns_committed_and_pending(self):
        self.buf.insert("hello")
        self.buf.insert("hello world foo bar")
        result = self.buf.flush_all()
        self.assertEqual(result, "hello world foo bar")

    def test_flush_all_after_flush_returns_unemitted_plus_pending(self):
        self.buf.insert("hello")
        self.buf.insert("hello world")
        self.assertEqual(self.buf.flush(), "hello")

        self.buf.insert("hello world again")
        result = self.buf.flush_all()
        self.assertEqual(result, "world again")

    def test_flush_all_clears_state(self):
        self.buf.insert("hello")
        self.buf.insert("hello world")
        self.buf.flush_all()
        self.assertEqual(self.buf.committed_text, "")
        self.assertEqual(self.buf.pending_text, "")
        self.assertFalse(self.buf.has_pending)

    def test_flush_all_returns_none_when_empty(self):
        self.assertIsNone(self.buf.flush_all())


class TestTranscriptBufferReset(unittest.TestCase):
    def setUp(self):
        self.buf = TranscriptBuffer()

    def test_reset_clears_everything(self):
        self.buf.insert("hello world")
        self.buf.insert("hello world foo")
        self.buf.reset()
        self.assertEqual(self.buf.committed_text, "")
        self.assertEqual(self.buf.pending_text, "")
        self.assertFalse(self.buf.has_pending)


class TestTranscriptBufferOverlap(unittest.TestCase):
    def setUp(self):
        self.buf = TranscriptBuffer()

    def test_committed_tail_dedup_across_inserts(self):
        self.buf.insert("the quick brown")
        self.buf.insert("the quick brown fox jumps")
        self.assertEqual(self.buf.committed_text, "the quick brown")
        self.assertEqual(self.buf.pending_text, "fox jumps")

    def test_three_pass_progressive_commit(self):
        self.buf.insert("one")
        self.buf.insert("one two")
        self.assertEqual(self.buf.committed_text, "one")
        self.buf.insert("one two three")
        self.assertEqual(self.buf.committed_text, "one two")
        self.assertEqual(self.buf.pending_text, "three")

    def test_diverging_text_resets_buffer(self):
        self.buf.insert("hello world")
        self.buf.insert("goodbye moon")
        self.assertEqual(self.buf.pending_text, "goodbye moon")


class TestTranscriptBufferCaseInsensitive(unittest.TestCase):
    def setUp(self):
        self.buf = TranscriptBuffer()

    def test_case_insensitive_matching(self):
        self.buf.insert("Hello World")
        self.buf.insert("hello world")
        self.assertEqual(self.buf.committed_text, "hello world")

    def test_mixed_case_growing(self):
        self.buf.insert("The Quick")
        self.buf.insert("the quick brown fox")
        self.assertEqual(self.buf.committed_text, "the quick")
        self.assertEqual(self.buf.pending_text, "brown fox")


class TestStreamingConfigDefaults(unittest.TestCase):
    def test_streaming_disabled_by_default(self):
        sr = DEFAULT_CONFIG["speech_recognition"]
        self.assertFalse(sr["experimental_streaming"])

    def test_chunk_duration_default(self):
        sr = DEFAULT_CONFIG["speech_recognition"]
        self.assertEqual(sr["streaming_chunk_duration_ms"], 1000)

    def test_overlap_default(self):
        sr = DEFAULT_CONFIG["speech_recognition"]
        self.assertEqual(sr["streaming_overlap_ms"], 200)


class TestStreamingConfigIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_root = tempfile.mkdtemp(prefix="vocalinux-streaming-test-")
        self.temp_config_dir = os.path.join(self.temp_root, ".config", "vocalinux")
        os.makedirs(self.temp_config_dir, exist_ok=True)
        self.temp_config_file = os.path.join(self.temp_config_dir, "config.json")

        self.patches = [
            patch(
                "vocalinux.ui.config_manager.CONFIG_DIR",
                self.temp_config_dir,
            ),
            patch(
                "vocalinux.ui.config_manager.CONFIG_FILE",
                self.temp_config_file,
            ),
            patch("vocalinux.ui.config_manager.logger"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.temp_root, ignore_errors=True)

    def test_streaming_settings_round_trip(self):
        cm = ConfigManager()
        cm.load_config()
        cm.set("speech_recognition", "experimental_streaming", True)
        cm.set("speech_recognition", "streaming_chunk_duration_ms", 2000)
        cm.save_config()

        cm2 = ConfigManager()
        cm2.load_config()
        settings = cm2.get_settings()
        sr = settings["speech_recognition"]
        self.assertTrue(sr["experimental_streaming"])
        self.assertEqual(sr["streaming_chunk_duration_ms"], 2000)

    def test_streaming_settings_in_update_speech_recognition(self):
        cm = ConfigManager()
        cm.load_config()
        cm.update_speech_recognition_settings(
            {
                "engine": "vosk",
                "model_size": "small",
                "language": "en-us",
                "experimental_streaming": True,
                "streaming_chunk_duration_ms": 3000,
            }
        )
        cm.save_config()

        cm2 = ConfigManager()
        cm2.load_config()
        sr = cm2.get_settings()["speech_recognition"]
        self.assertTrue(sr["experimental_streaming"])
        self.assertEqual(sr["streaming_chunk_duration_ms"], 3000)

    def test_config_file_has_streaming_keys(self):
        cm = ConfigManager()
        cm.load_config()
        cm.save_config()

        with open(self.temp_config_file) as f:
            data = json.load(f)

        sr = data["speech_recognition"]
        self.assertIn("experimental_streaming", sr)
        self.assertIn("streaming_chunk_duration_ms", sr)
        self.assertIn("streaming_overlap_ms", sr)


if __name__ == "__main__":
    unittest.main()
