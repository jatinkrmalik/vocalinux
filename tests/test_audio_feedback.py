"""
Tests for the audio feedback functionality.
"""

import os
import sys
import unittest
from unittest.mock import patch

import pytest

# We need to use absolute paths for patching in module scope
AUDIO_FEEDBACK_MODULE = "vocalinux.ui.audio_feedback"


@pytest.fixture(autouse=True)
def reset_audio_module():
    """Reset the audio_feedback module before each test to allow proper testing."""
    # Remove the mock that conftest installs
    if AUDIO_FEEDBACK_MODULE in sys.modules:
        del sys.modules[AUDIO_FEEDBACK_MODULE]

    yield

    # Restore the mock after test for other tests that need it
    from conftest import mock_audio_feedback

    sys.modules[AUDIO_FEEDBACK_MODULE] = mock_audio_feedback


class TestAudioFeedback(unittest.TestCase):
    """Test cases for audio feedback functionality."""

    def test_resource_paths(self):
        """Test that resource paths are correctly set up."""
        # Import fresh module
        import vocalinux.ui.audio_feedback as audio_feedback

        # Import the resource manager to test paths
        from vocalinux.utils.resource_manager import ResourceManager

        resource_manager = ResourceManager()

        # Verify that resource paths are correctly set and accessible
        self.assertTrue(
            resource_manager.resources_dir.endswith("resources"),
            f"Resources directory is not valid: {resource_manager.resources_dir}",
        )
        self.assertTrue(
            resource_manager.sounds_dir.endswith("sounds"),
            f"Sounds directory path is not valid: {resource_manager.sounds_dir}",
        )
        self.assertEqual(os.path.basename(audio_feedback.START_SOUND), "start_recording.wav")
        self.assertEqual(os.path.basename(audio_feedback.STOP_SOUND), "stop_recording.wav")
        self.assertEqual(os.path.basename(audio_feedback.ERROR_SOUND), "error.wav")

    def test_get_audio_player_pulseaudio(self):
        """Test detecting PulseAudio player."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.shutil, "which") as mock_which:
            # Mock shutil.which to return True for paplay and False for others
            def which_side_effect(cmd):
                return cmd == "paplay"

            mock_which.side_effect = which_side_effect

            # Call the function
            player, formats = audio_feedback._get_audio_player()

            # Verify the correct player was detected
            self.assertEqual(player, "paplay")
            self.assertEqual(formats, ["wav"])

    def test_get_audio_player_alsa(self):
        """Test detecting ALSA player."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.shutil, "which") as mock_which:
            # Mock shutil.which to return False for paplay, True for aplay
            def which_side_effect(cmd):
                return {
                    "paplay": False,
                    "aplay": True,
                    "play": False,
                    "mplayer": False,
                }.get(cmd, False)

            mock_which.side_effect = which_side_effect

            # Call the function
            player, formats = audio_feedback._get_audio_player()

            # Verify the correct player was detected
            self.assertEqual(player, "aplay")
            self.assertEqual(formats, ["wav"])

    def test_get_audio_player_sox(self):
        """Test detecting SoX player."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.shutil, "which") as mock_which:
            # Mock shutil.which to return False for paplay/aplay, True for play
            def which_side_effect(cmd):
                return {
                    "paplay": False,
                    "aplay": False,
                    "play": True,
                    "mplayer": False,
                }.get(cmd, False)

            mock_which.side_effect = which_side_effect

            # Call the function
            player, formats = audio_feedback._get_audio_player()

            # Verify the correct player was detected
            self.assertEqual(player, "play")
            self.assertEqual(formats, ["wav"])

    def test_get_audio_player_mplayer(self):
        """Test detecting MPlayer."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.shutil, "which") as mock_which:
            # Mock shutil.which to return False for all except mplayer
            def which_side_effect(cmd):
                return {
                    "paplay": False,
                    "aplay": False,
                    "play": False,
                    "mplayer": True,
                }.get(cmd, False)

            mock_which.side_effect = which_side_effect

            # Call the function
            player, formats = audio_feedback._get_audio_player()

            # Verify the correct player was detected
            self.assertEqual(player, "mplayer")
            self.assertEqual(formats, ["wav"])

    def test_get_audio_player_none(self):
        """Test behavior when no audio player is available."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.shutil, "which", return_value=None):
            # Call the function
            player, formats = audio_feedback._get_audio_player()

            # Verify no player was detected
            self.assertIsNone(player)
            self.assertEqual(formats, [])

    def test_play_sound_file_missing(self):
        """Test playing a missing sound file."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.os.path, "exists", return_value=False):
            # Call the function
            result = audio_feedback._play_sound_file("nonexistent.wav")

            # Verify the function returned False
            self.assertFalse(result)

    def test_play_sound_file_no_player(self):
        """Test playing sound with no available player."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.os.path, "exists", return_value=True), patch.object(
            audio_feedback, "_get_audio_player", return_value=(None, [])
        ):
            # Call the function
            result = audio_feedback._play_sound_file("test.wav")

            # Verify the function returned False
            self.assertFalse(result)

    def test_play_sound_file_paplay(self):
        """Test playing sound with paplay."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.os.path, "exists", return_value=True), patch.object(
            audio_feedback,
            "_get_audio_player",
            return_value=("paplay", ["wav"]),
        ), patch.object(audio_feedback.subprocess, "Popen") as mock_popen:
            # Call the function
            result = audio_feedback._play_sound_file("test.wav")

            # Verify the function returned True and called Popen correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "paplay")
            self.assertEqual(args[0][1], "test.wav")

    def test_play_sound_file_aplay(self):
        """Test playing sound with aplay."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.os.path, "exists", return_value=True), patch.object(
            audio_feedback,
            "_get_audio_player",
            return_value=("aplay", ["wav"]),
        ), patch.object(audio_feedback.subprocess, "Popen") as mock_popen:
            # Call the function
            result = audio_feedback._play_sound_file("test.wav")

            # Verify the function returned True and called Popen correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "aplay")
            self.assertEqual(args[0][1], "-q")
            self.assertEqual(args[0][2], "test.wav")

    def test_play_sound_file_mplayer(self):
        """Test playing sound with mplayer."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.os.path, "exists", return_value=True), patch.object(
            audio_feedback,
            "_get_audio_player",
            return_value=("mplayer", ["wav"]),
        ), patch.object(audio_feedback.subprocess, "Popen") as mock_popen:
            # Call the function
            result = audio_feedback._play_sound_file("test.wav")

            # Verify the function returned True and called Popen correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "mplayer")
            self.assertEqual(args[0][1], "-really-quiet")
            self.assertEqual(args[0][2], "test.wav")

    def test_play_sound_file_play(self):
        """Test playing sound with play (SoX)."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.os.path, "exists", return_value=True), patch.object(
            audio_feedback, "_get_audio_player", return_value=("play", ["wav"])
        ), patch.object(audio_feedback.subprocess, "Popen") as mock_popen:
            # Call the function
            result = audio_feedback._play_sound_file("test.wav")

            # Verify the function returned True and called Popen correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "play")
            self.assertEqual(args[0][1], "-q")
            self.assertEqual(args[0][2], "test.wav")

    def test_play_sound_file_exception(self):
        """Test handling exception when playing sound."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.os.path, "exists", return_value=True), patch.object(
            audio_feedback,
            "_get_audio_player",
            return_value=("paplay", ["wav"]),
        ), patch.object(
            audio_feedback.subprocess,
            "Popen",
            side_effect=Exception("Mock error"),
        ):
            # Call the function
            result = audio_feedback._play_sound_file("test.wav")

            # Verify the function returned False
            self.assertFalse(result)

    def test_play_start_sound(self):
        """Test playing start sound."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback, "_play_sound_file") as mock_play:
            # Call the function
            audio_feedback.play_start_sound()

            # Verify _play_sound_file was called with correct path
            mock_play.assert_called_once_with(audio_feedback.START_SOUND)

    def test_play_stop_sound(self):
        """Test playing stop sound."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback, "_play_sound_file") as mock_play:
            # Call the function
            audio_feedback.play_stop_sound()

            # Verify _play_sound_file was called with correct path
            mock_play.assert_called_once_with(audio_feedback.STOP_SOUND)

    def test_play_error_sound(self):
        """Test playing error sound."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback, "_play_sound_file") as mock_play:
            # Call the function
            audio_feedback.play_error_sound()

            # Verify _play_sound_file was called with correct path
            mock_play.assert_called_once_with(audio_feedback.ERROR_SOUND)

    def test_play_sound_file_ci_test_player(self):
        """Test playing sound with ci_test_player (GitHub Actions fallback)."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.os.path, "exists", return_value=True), patch.object(
            audio_feedback,
            "_get_audio_player",
            return_value=("ci_test_player", ["wav"]),
        ), patch.object(audio_feedback.subprocess, "Popen") as mock_popen:
            # Call the function
            result = audio_feedback._play_sound_file("test.wav")

            # Verify the function returned True and called Popen correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "ci_test_player")
            self.assertEqual(args[0][1], "test.wav")

    def test_get_audio_player_github_actions_fallback(self):
        """Test ci_test_player assignment in GitHub Actions without audio player."""
        # Import the module first
        import vocalinux.ui.audio_feedback as audio_feedback

        with patch.object(audio_feedback.shutil, "which", return_value=None), patch.object(
            audio_feedback.os.path, "exists", return_value=True
        ), patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}):
            # First verify _get_audio_player returns None
            player, formats = audio_feedback._get_audio_player()
            self.assertIsNone(player)

            # Now test _play_sound_file which should assign ci_test_player
            with patch.object(audio_feedback.subprocess, "Popen") as mock_popen:
                result = audio_feedback._play_sound_file("test.wav")

                # Should have used ci_test_player
                self.assertTrue(result)
                mock_popen.assert_called_once()
                args, _ = mock_popen.call_args
                self.assertEqual(args[0][0], "ci_test_player")
