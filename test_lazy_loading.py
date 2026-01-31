#!/usr/bin/env python3
"""
Standalone test script for SpeechRecognitionManager lazy loading.
This script isolates the manager from GUI dependencies to test lazy loading.
"""

import sys
import os
import logging
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock dependencies that aren't needed for the core functionality
class MockAudioFeedback:
    @staticmethod
    def play_error_sound():
        pass
    
    @staticmethod 
    def play_start_sound():
        pass
        
    @staticmethod
    def play_stop_sound():
        pass

# Mock the audio_feedback module
sys.modules['vocalinux.ui.audio_feedback'] = MockAudioFeedback()

# Mock other UI dependencies
sys.modules['vocalinux.ui.tray_indicator'] = type('Module', (), {})()
sys.modules['vocalinux.ui.settings_dialog'] = type('Module', (), {})()

# Mock pynput
pynput_module = type('Module', (), {})()
pynput_module.keyboard = type('Module', (), {})()
pynput_module.keyboard.Listener = type('Listener', (), {'__init__': lambda s, *a, **k: None, 'start': lambda s: None, 'stop': lambda s: None})()
pynput_module.keyboard.Key = type('Key', (), {})
sys.modules['pynput'] = pynput_module
sys.modules['pynput.keyboard'] = pynput_module.keyboard

# Mock vosk
vosk_module = type('Module', (), {})()
vosk_module.KaldiRecognizer = type('KaldiRecognizer', (), {'__init__': lambda s, *a, **k: None, 'AcceptWaveform': lambda s, *a: None, 'FinalResult': lambda s: '{"text": ""}'})()
vosk_module.Model = type('Model', (), {'__init__': lambda s, *a: None})()
sys.modules['vosk'] = vosk_module

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_current_startup_time():
    """Test the current startup time without lazy loading."""
    print("=" * 60)
    print("TESTING CURRENT STARTUP TIME")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Test with defer_download=True (current implementation)
        from vocalinux.speech_recognition.recognition_manager import SpeechRecognitionManager
        
        print("Creating SpeechRecognitionManager with defer_download=True...")
        manager = SpeechRecognitionManager(
            engine='vosk', 
            model_size='small', 
            language='en-us', 
            defer_download=True
        )
        
        end_time = time.time()
        startup_time = end_time - start_time
        
        print(f"✓ Current startup time: {startup_time:.3f} seconds")
        print(f"✓ Model initialized: {manager.model_ready}")
        print(f"✓ Model loaded: {manager._model_initialized}")
        
        return startup_time, manager
        
    except Exception as e:
        print(f"✗ Error during startup: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_lazy_loading():
    """Test lazy loading implementation."""
    print("\n" + "=" * 60)
    print("TESTING LAZY LOADING IMPLEMENTATION")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # Import the lazy version
        from vocalinux.speech_recognition.recognition_manager_lazy import SpeechRecognitionManager
        
        print("Creating SpeechRecognitionManager (lazy version)...")
        manager = SpeechRecognitionManager(
            engine='vosk', 
            model_size='small', 
            language='en-us'
        )
        
        end_time = time.time()
        startup_time = end_time - start_time
        
        print(f"✓ Lazy startup time: {startup_time:.3f} seconds")
        print(f"✓ Model initialized: {manager.model_ready}")
        print(f"✓ Model loaded: {manager._model_initialized}")
        
        # Test first use loading
        print("\nTesting first use (should trigger model loading)...")
        first_use_start = time.time()
        
        # This should trigger lazy loading
        try:
            manager._ensure_model_loaded()
            first_use_end = time.time()
            first_use_time = first_use_end - first_use_start
            
            print(f"✓ First use load time: {first_use_time:.3f} seconds")
            print(f"✓ Model now ready: {manager.model_ready}")
            
        except Exception as e:
            print(f"! First use error (expected if no model): {e}")
        
        return startup_time, manager
        
    except Exception as e:
        print(f"✗ Error during lazy loading: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print("Vocalinux Issue #91 - Lazy Loading Performance Test")
    print("This script tests startup performance with and without lazy loading")
    
    # Test current implementation
    current_time, current_manager = test_current_startup_time()
    
    # Test lazy loading implementation  
    lazy_time, lazy_manager = test_lazy_loading()
    
    # Summary
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    
    if current_time and lazy_time:
        improvement = current_time - lazy_time
        improvement_percent = (improvement / current_time) * 100
        
        print(f"Current startup time:  {current_time:.3f}s")
        print(f"Lazy startup time:     {lazy_time:.3f}s")
        print(f"Improvement:           {improvement:.3f}s ({improvement_percent:.1f}%)")
        
        if improvement > 0:
            print("✓ LAZY LOADING SUCCESSFULLY REDUCES STARTUP TIME!")
        else:
            print("! Lazy loading did not improve startup time")
    else:
        print("Could not complete comparison due to errors")