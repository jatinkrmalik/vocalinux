"""
Tests for the audio feedback functionality.
"""

import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest

# We need to use absolute paths for patching in module scope
AUDIO_FEEDBACK_MODULE = "vocalinux.ui.audio_feedback"

# Import the module under test
from vocalinux.ui.audio_feedback import (
    ERROR_SOUND,
    START_SOUND,
    STOP_SOUND,
)


@pytest.fixture(autouse=True)
def reset_modules():
    """Reset imported modules before each test to avoid state leakage."""
    # Store original module
    if AUDIO_FEEDBACK_MODULE in sys.modules:
        original_module = sys.modules[AUDIO_FEEDBACK_MODULE]
        del sys.modules[AUDIO_FEEDBACK_MODULE]
    else:
        original_module = None

    # Let the test run
    yield

    # Restore original module if it existed
    if original_module:
        sys.modules[AUDIO_FEEDBACK_MODULE] = original_module


class TestAudioFeedback(unittest.TestCase):
    """Test cases for audio feedback functionality."""

    def test_resource_paths(self):
        """Test that resource paths are correctly set up."""
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
        self.assertEqual(os.path.basename(START_SOUND), "start_recording.wav")
        self.assertEqual(os.path.basename(STOP_SOUND), "stop_recording.wav")
        self.assertEqual(os.path.basename(ERROR_SOUND), "error.wav")

    def test_get_audio_player_pulseaudio(self):
        """Test detecting PulseAudio player."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.shutil.which") as mock_which:
            # Mock shutil.which to return True for paplay and False for others
            def which_side_effect(cmd):
                return cmd == "paplay"

            mock_which.side_effect = which_side_effect

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _get_audio_player

            # Call the function
            player, formats = _get_audio_player()

            # Verify the correct player was detected
            self.assertEqual(player, "paplay")
            self.assertEqual(formats, ["wav"])

    def test_get_audio_player_alsa(self):
        """Test detecting ALSA player."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.shutil.which") as mock_which:
            # Mock shutil.which to return False for paplay, True for aplay
            def which_side_effect(cmd):
                return {
                    "paplay": False,
                    "aplay": True,
                    "play": False,
                    "mplayer": False,
                }.get(cmd, False)

            mock_which.side_effect = which_side_effect

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _get_audio_player

            # Call the function
            player, formats = _get_audio_player()

            # Verify the correct player was detected
            self.assertEqual(player, "aplay")
            self.assertEqual(formats, ["wav"])

    def test_get_audio_player_sox(self):
        """Test detecting SoX player."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.shutil.which") as mock_which:
            # Mock shutil.which to return False for paplay/aplay, True for play
            def which_side_effect(cmd):
                return {
                    "paplay": False,
                    "aplay": False,
                    "play": True,
                    "mplayer": False,
                }.get(cmd, False)

            mock_which.side_effect = which_side_effect

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _get_audio_player

            # Call the function
            player, formats = _get_audio_player()

            # Verify the correct player was detected
            self.assertEqual(player, "play")
            self.assertEqual(formats, ["wav"])

    def test_get_audio_player_mplayer(self):
        """Test detecting MPlayer."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.shutil.which") as mock_which:
            # Mock shutil.which to return False for all except mplayer
            def which_side_effect(cmd):
                return {
                    "paplay": False,
                    "aplay": False,
                    "play": False,
                    "mplayer": True,
                }.get(cmd, False)

            mock_which.side_effect = which_side_effect

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _get_audio_player

            # Call the function
            player, formats = _get_audio_player()

            # Verify the correct player was detected
            self.assertEqual(player, "mplayer")
            self.assertEqual(formats, ["wav"])

    def test_get_audio_player_none(self):
        """Test behavior when no audio player is available."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.shutil.which") as mock_which:
            # Mock shutil.which to return False for all players
            mock_which.return_value = None

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _get_audio_player

            # Call the function
            player, formats = _get_audio_player()

            # Verify no player was detected
            self.assertIsNone(player)
            self.assertEqual(formats, [])

    def test_play_sound_file_missing(self):
        """Test playing a missing sound file."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.os.path.exists", return_value=False):
            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _play_sound_file

            # Call the function
            result = _play_sound_file("nonexistent.wav")

            # Verify the function returned False
            self.assertFalse(result)

    def test_play_sound_file_no_player(self):
        """Test playing sound with no available player."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.os.path.exists", return_value=True), patch(
            f"{AUDIO_FEEDBACK_MODULE}._get_audio_player", return_value=(None, [])
        ):

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _play_sound_file

            # Call the function
            result = _play_sound_file("test.wav")

            # Verify the function returned False
            self.assertFalse(result)

    def test_play_sound_file_paplay(self):
        """Test playing sound with paplay."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.os.path.exists", return_value=True), patch(
            f"{AUDIO_FEEDBACK_MODULE}._get_audio_player",
            return_value=("paplay", ["wav"]),
        ), patch(f"{AUDIO_FEEDBACK_MODULE}.subprocess.Popen") as mock_popen:

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _play_sound_file

            # Call the function
            result = _play_sound_file("test.wav")

            # Verify the function returned True and called Popen correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "paplay")
            self.assertEqual(args[0][1], "test.wav")

    def test_play_sound_file_aplay(self):
        """Test playing sound with aplay."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.os.path.exists", return_value=True), patch(
            f"{AUDIO_FEEDBACK_MODULE}._get_audio_player",
            return_value=("aplay", ["wav"]),
        ), patch(f"{AUDIO_FEEDBACK_MODULE}.subprocess.Popen") as mock_popen:

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _play_sound_file

            # Call the function
            result = _play_sound_file("test.wav")

            # Verify the function returned True and called Popen correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "aplay")
            self.assertEqual(args[0][1], "-q")
            self.assertEqual(args[0][2], "test.wav")

    def test_play_sound_file_mplayer(self):
        """Test playing sound with mplayer."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.os.path.exists", return_value=True), patch(
            f"{AUDIO_FEEDBACK_MODULE}._get_audio_player",
            return_value=("mplayer", ["wav"]),
        ), patch(f"{AUDIO_FEEDBACK_MODULE}.subprocess.Popen") as mock_popen:

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _play_sound_file

            # Call the function
            result = _play_sound_file("test.wav")

            # Verify the function returned True and called Popen correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "mplayer")
            self.assertEqual(args[0][1], "-really-quiet")
            self.assertEqual(args[0][2], "test.wav")

    def test_play_sound_file_play(self):
        """Test playing sound with play (SoX)."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.os.path.exists", return_value=True), patch(
            f"{AUDIO_FEEDBACK_MODULE}._get_audio_player", return_value=("play", ["wav"])
        ), patch(f"{AUDIO_FEEDBACK_MODULE}.subprocess.Popen") as mock_popen:

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _play_sound_file

            # Call the function
            result = _play_sound_file("test.wav")

            # Verify the function returned True and called Popen correctly
            self.assertTrue(result)
            mock_popen.assert_called_once()
            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0][0], "play")
            self.assertEqual(args[0][1], "-q")
            self.assertEqual(args[0][2], "test.wav")

    def test_play_sound_file_exception(self):
        """Test handling exception when playing sound."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}.os.path.exists", return_value=True), patch(
            f"{AUDIO_FEEDBACK_MODULE}._get_audio_player",
            return_value=("paplay", ["wav"]),
        ), patch(
            f"{AUDIO_FEEDBACK_MODULE}.subprocess.Popen",
            side_effect=Exception("Mock error"),
        ):

            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import _play_sound_file

            # Call the function
            result = _play_sound_file("test.wav")

            # Verify the function returned False
            self.assertFalse(result)

    def test_play_start_sound(self):
        """Test playing start sound."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}._play_sound_file") as mock_play:
            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import START_SOUND, play_start_sound

            # Call the function
            play_start_sound()

            # Verify _play_sound_file was called with correct path
            mock_play.assert_called_once_with(START_SOUND)

    def test_play_stop_sound(self):
        """Test playing stop sound."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}._play_sound_file") as mock_play:
            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import STOP_SOUND, play_stop_sound

            # Call the function
            play_stop_sound()

            # Verify _play_sound_file was called with correct path
            mock_play.assert_called_once_with(STOP_SOUND)

    def test_play_error_sound(self):
        """Test playing error sound."""
        with patch(f"{AUDIO_FEEDBACK_MODULE}._play_sound_file") as mock_play:
            # Re-import to get fresh functions with our patches applied
            from vocalinux.ui.audio_feedback import ERROR_SOUND, play_error_sound

            # Call the function
            play_error_sound()

            # Verify _play_sound_file was called with correct path
            mock_play.assert_called_once_with(ERROR_SOUND)
