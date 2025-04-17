"""
Tests for the audio feedback module.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import pytest

from src.ui.audio_feedback import (
    _get_audio_player,
    _play_sound_file,
    play_error_sound,
    play_start_sound,
    play_stop_sound,
)


class TestAudioFeedback(unittest.TestCase):
    """Test cases for the audio feedback module."""

    @patch("src.ui.audio_feedback.shutil.which")
    def test_get_audio_player_paplay(self, mock_which):
        """Test that paplay is selected when available."""
        # Mock paplay being available
        mock_which.side_effect = lambda cmd: cmd if cmd == "paplay" else None
        
        player, formats = _get_audio_player()
        self.assertEqual(player, "paplay")
        self.assertEqual(formats, ["wav"])
    
    @patch("src.ui.audio_feedback.shutil.which")
    def test_get_audio_player_aplay(self, mock_which):
        """Test that aplay is selected when paplay is not available."""
        # Mock aplay being available, but paplay not available
        mock_which.side_effect = lambda cmd: cmd if cmd == "aplay" else None
        
        player, formats = _get_audio_player()
        self.assertEqual(player, "aplay")
        self.assertEqual(formats, ["wav"])
    
    @patch("src.ui.audio_feedback.shutil.which")
    def test_get_audio_player_none(self, mock_which):
        """Test behavior when no audio player is available."""
        # Mock no audio players being available
        mock_which.return_value = None
        
        player, formats = _get_audio_player()
        self.assertIsNone(player)
        self.assertEqual(formats, [])
    
    @patch("src.ui.audio_feedback._get_audio_player")
    @patch("src.ui.audio_feedback.subprocess.Popen")
    @patch("src.ui.audio_feedback.os.path.exists")
    def test_play_sound_file_paplay(self, mock_exists, mock_popen, mock_get_player):
        """Test playing a sound file with paplay."""
        # Setup mocks
        mock_exists.return_value = True
        mock_get_player.return_value = ("paplay", ["wav"])
        
        # Call function with a mock sound path
        result = _play_sound_file("/path/to/sound.wav")
        
        # Assert function succeeded and called Popen with correct args
        self.assertTrue(result)
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "paplay")
        self.assertEqual(args[1], "/path/to/sound.wav")
    
    @patch("src.ui.audio_feedback._get_audio_player")
    @patch("src.ui.audio_feedback.subprocess.Popen")
    @patch("src.ui.audio_feedback.os.path.exists")
    def test_play_sound_file_aplay(self, mock_exists, mock_popen, mock_get_player):
        """Test playing a sound file with aplay."""
        # Setup mocks
        mock_exists.return_value = True
        mock_get_player.return_value = ("aplay", ["wav"])
        
        # Call function with a mock sound path
        result = _play_sound_file("/path/to/sound.wav")
        
        # Assert function succeeded and called Popen with correct args
        self.assertTrue(result)
        mock_popen.assert_called_once()
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "aplay")
        self.assertEqual(args[1], "-q")
        self.assertEqual(args[2], "/path/to/sound.wav")
    
    @patch("src.ui.audio_feedback._get_audio_player")
    @patch("src.ui.audio_feedback.os.path.exists")
    def test_play_sound_file_missing_file(self, mock_exists, mock_get_player):
        """Test playing a non-existent sound file."""
        # Setup mocks
        mock_exists.return_value = False
        
        # Call function with a mock sound path
        result = _play_sound_file("/path/to/missing.wav")
        
        # Assert function failed
        self.assertFalse(result)
        # Get audio player should not be called if file doesn't exist
        mock_get_player.assert_not_called()
    
    @patch("src.ui.audio_feedback._get_audio_player")
    @patch("src.ui.audio_feedback.os.path.exists")
    def test_play_sound_file_no_player(self, mock_exists, mock_get_player):
        """Test playing a sound file when no player is available."""
        # Setup mocks
        mock_exists.return_value = True
        mock_get_player.return_value = (None, [])
        
        # Call function with a mock sound path
        result = _play_sound_file("/path/to/sound.wav")
        
        # Assert function failed
        self.assertFalse(result)
    
    @patch("src.ui.audio_feedback._play_sound_file")
    def test_play_start_sound(self, mock_play_sound):
        """Test the play_start_sound function."""
        # Call the function
        play_start_sound()
        
        # Assert _play_sound_file was called with the correct sound file
        mock_play_sound.assert_called_once()
        self.assertTrue("start_recording.wav" in mock_play_sound.call_args[0][0])
    
    @patch("src.ui.audio_feedback._play_sound_file")
    def test_play_stop_sound(self, mock_play_sound):
        """Test the play_stop_sound function."""
        # Call the function
        play_stop_sound()
        
        # Assert _play_sound_file was called with the correct sound file
        mock_play_sound.assert_called_once()
        self.assertTrue("stop_recording.wav" in mock_play_sound.call_args[0][0])
    
    @patch("src.ui.audio_feedback._play_sound_file")
    def test_play_error_sound(self, mock_play_sound):
        """Test the play_error_sound function."""
        # Call the function
        play_error_sound()
        
        # Assert _play_sound_file was called with the correct sound file
        mock_play_sound.assert_called_once()
        self.assertTrue("error.wav" in mock_play_sound.call_args[0][0])