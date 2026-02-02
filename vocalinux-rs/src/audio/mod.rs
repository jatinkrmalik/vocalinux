//! Audio capture module using CPAL.

mod capture;
mod devices;
mod vad;

pub use capture::AudioCapture;
pub use devices::{get_input_devices, AudioDevice};
pub use vad::VoiceActivityDetector;

/// Audio sample format used throughout the application
pub type AudioSample = i16;

/// Standard sample rate for speech recognition
pub const SAMPLE_RATE: u32 = 16000;

/// Number of audio channels (mono)
pub const CHANNELS: u16 = 1;

/// Buffer size in samples
pub const BUFFER_SIZE: usize = 1024;
