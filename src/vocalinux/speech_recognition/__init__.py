"""
Speech recognition module for Vocalinux
"""

from . import command_processor, recognition_manager, streaming_recognizer, streaming_manager


def get_audio_input_devices():
    """Get available audio input devices."""
    return recognition_manager.get_audio_input_devices()


def test_audio_input(device_index=None, duration=1.0):
    """Test audio input from a device."""
    return recognition_manager.test_audio_input(device_index, duration)


# Export the main classes for easy importing
SpeechRecognitionManager = recognition_manager.SpeechRecognitionManager
StreamingRecognitionManager = streaming_manager.StreamingRecognitionManager
StreamingSpeechRecognizer = streaming_recognizer.StreamingSpeechRecognizer
