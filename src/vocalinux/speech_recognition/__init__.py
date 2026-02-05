"""
Speech recognition module for Vocalinux
"""

from . import command_processor  # noqa: F401
from . import recognition_manager
from . import streaming_recognizer  # noqa: F401
from . import streaming_manager  # noqa: F401


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
