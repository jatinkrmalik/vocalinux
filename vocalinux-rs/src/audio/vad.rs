//! Voice Activity Detection (VAD) module.

use super::{AudioSample, SAMPLE_RATE};

/// Simple energy-based Voice Activity Detector
pub struct VoiceActivityDetector {
    /// Sensitivity level (1-5, higher = more sensitive)
    sensitivity: u8,
    /// Silence timeout in seconds
    silence_timeout: f32,
    /// Accumulated silence duration
    silence_duration: f32,
    /// Whether speech has been detected in current session
    speech_detected: bool,
    /// Current audio level (0-100)
    current_level: f32,
}

impl VoiceActivityDetector {
    pub fn new(sensitivity: u8, silence_timeout: f32) -> Self {
        Self {
            sensitivity: sensitivity.clamp(1, 5),
            silence_timeout,
            silence_duration: 0.0,
            speech_detected: false,
            current_level: 0.0,
        }
    }

    /// Calculate the energy threshold based on sensitivity
    fn threshold(&self) -> f32 {
        // Higher sensitivity = lower threshold = easier to trigger
        500.0 / (self.sensitivity as f32).max(1.0)
    }

    /// Process audio samples and detect speech
    ///
    /// Returns `Some(true)` if silence timeout reached (should process buffer),
    /// `Some(false)` if speech detected, `None` if still listening
    pub fn process(&mut self, samples: &[AudioSample]) -> Option<bool> {
        // Calculate mean absolute amplitude
        let sum: i64 = samples.iter().map(|&s| (s as i64).abs()).sum();
        let mean_amplitude = sum as f32 / samples.len() as f32;

        // Update current level (normalized to 0-100)
        // 16-bit audio max is ~32768
        self.current_level = (mean_amplitude / 327.68).min(100.0);

        let threshold = self.threshold();
        let chunk_duration = samples.len() as f32 / SAMPLE_RATE as f32;

        if mean_amplitude < threshold {
            // Silence detected
            self.silence_duration += chunk_duration;

            if self.silence_duration > self.silence_timeout && self.speech_detected {
                // Silence timeout reached after speech - process buffer
                self.reset();
                return Some(true);
            }
        } else {
            // Speech detected
            if !self.speech_detected {
                self.speech_detected = true;
            }
            self.silence_duration = 0.0;
            return Some(false);
        }

        None
    }

    /// Reset VAD state for new utterance
    pub fn reset(&mut self) {
        self.silence_duration = 0.0;
        self.speech_detected = false;
    }

    /// Get current audio level (0-100)
    pub fn current_level(&self) -> f32 {
        self.current_level
    }

    /// Check if speech was detected in current session
    pub fn has_speech(&self) -> bool {
        self.speech_detected
    }

    /// Update sensitivity
    pub fn set_sensitivity(&mut self, sensitivity: u8) {
        self.sensitivity = sensitivity.clamp(1, 5);
    }

    /// Update silence timeout
    pub fn set_silence_timeout(&mut self, timeout: f32) {
        self.silence_timeout = timeout.clamp(0.5, 5.0);
    }
}
