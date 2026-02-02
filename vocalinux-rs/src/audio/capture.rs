//! Audio capture implementation using CPAL.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use anyhow::{Context, Result};
use cpal::traits::{DeviceTrait, StreamTrait};
use cpal::{SampleFormat, StreamConfig};
use crossbeam_channel::{bounded, Receiver, Sender};
use parking_lot::Mutex;
use tracing::{debug, error, info, warn};

use super::devices::{get_default_device, get_device_by_name};
use super::{AudioSample, BUFFER_SIZE, CHANNELS, SAMPLE_RATE};

/// Audio chunk sent to speech recognition
#[derive(Debug, Clone)]
pub struct AudioChunk {
    pub samples: Vec<AudioSample>,
    pub timestamp_ms: u64,
}

/// Callback type for audio level updates
pub type AudioLevelCallback = Box<dyn Fn(f32) + Send + Sync>;

/// Audio capture manager
pub struct AudioCapture {
    /// Whether currently recording
    is_recording: Arc<AtomicBool>,
    /// Audio stream (kept alive while recording)
    stream: Option<cpal::Stream>,
    /// Channel for sending audio chunks
    sender: Option<Sender<AudioChunk>>,
    /// Channel for receiving audio chunks
    receiver: Option<Receiver<AudioChunk>>,
    /// Selected device name (None = default)
    device_name: Option<String>,
    /// Audio level callback
    level_callback: Arc<Mutex<Option<AudioLevelCallback>>>,
    /// Start timestamp
    start_time: Arc<Mutex<Option<std::time::Instant>>>,
}

impl AudioCapture {
    pub fn new() -> Self {
        Self {
            is_recording: Arc::new(AtomicBool::new(false)),
            stream: None,
            sender: None,
            receiver: None,
            device_name: None,
            level_callback: Arc::new(Mutex::new(None)),
            start_time: Arc::new(Mutex::new(None)),
        }
    }

    /// Set the audio input device by name
    pub fn set_device(&mut self, device_name: Option<String>) {
        self.device_name = device_name;
    }

    /// Set callback for audio level updates
    pub fn set_level_callback<F>(&self, callback: F)
    where
        F: Fn(f32) + Send + Sync + 'static,
    {
        *self.level_callback.lock() = Some(Box::new(callback));
    }

    /// Start audio capture
    pub fn start(&mut self) -> Result<Receiver<AudioChunk>> {
        if self.is_recording.load(Ordering::SeqCst) {
            anyhow::bail!("Already recording");
        }

        // Get the device
        let device = match &self.device_name {
            Some(name) => {
                info!("Using audio device: {}", name);
                get_device_by_name(name)?
            }
            None => {
                info!("Using default audio device");
                get_default_device()?
            }
        };

        let device_name = device.name().unwrap_or_else(|_| "Unknown".to_string());
        debug!("Opening audio device: {}", device_name);

        // Configure the stream
        let config = StreamConfig {
            channels: CHANNELS,
            sample_rate: cpal::SampleRate(SAMPLE_RATE),
            buffer_size: cpal::BufferSize::Fixed(BUFFER_SIZE as u32),
        };

        // Create channel for audio chunks
        let (sender, receiver) = bounded::<AudioChunk>(100);
        self.sender = Some(sender.clone());
        self.receiver = Some(receiver.clone());

        // Set start time
        *self.start_time.lock() = Some(std::time::Instant::now());

        let is_recording = self.is_recording.clone();
        let level_callback = self.level_callback.clone();
        let start_time = self.start_time.clone();

        // Build the input stream
        let stream = device
            .build_input_stream(
                &config,
                move |data: &[i16], _: &cpal::InputCallbackInfo| {
                    if !is_recording.load(Ordering::SeqCst) {
                        return;
                    }

                    // Calculate audio level for callback
                    if let Some(ref callback) = *level_callback.lock() {
                        let sum: i64 = data.iter().map(|&s| (s as i64).abs()).sum();
                        let mean = sum as f32 / data.len() as f32;
                        let level = (mean / 327.68).min(100.0);
                        callback(level);
                    }

                    // Calculate timestamp
                    let timestamp_ms = start_time
                        .lock()
                        .map(|t| t.elapsed().as_millis() as u64)
                        .unwrap_or(0);

                    // Send audio chunk
                    let chunk = AudioChunk {
                        samples: data.to_vec(),
                        timestamp_ms,
                    };

                    if sender.try_send(chunk).is_err() {
                        warn!("Audio buffer full, dropping chunk");
                    }
                },
                move |err| {
                    error!("Audio stream error: {}", err);
                },
                None, // No timeout
            )
            .context("Failed to build input stream")?;

        // Start the stream
        stream.play().context("Failed to start audio stream")?;
        self.stream = Some(stream);
        self.is_recording.store(true, Ordering::SeqCst);

        info!("Audio capture started on device: {}", device_name);
        Ok(receiver)
    }

    /// Stop audio capture
    pub fn stop(&mut self) {
        self.is_recording.store(false, Ordering::SeqCst);

        // Drop the stream to stop recording
        if let Some(stream) = self.stream.take() {
            drop(stream);
        }

        // Clear channels
        self.sender = None;
        self.receiver = None;
        *self.start_time.lock() = None;

        info!("Audio capture stopped");
    }

    /// Check if currently recording
    pub fn is_recording(&self) -> bool {
        self.is_recording.load(Ordering::SeqCst)
    }

    /// Get the audio receiver (for streaming to speech recognition)
    pub fn get_receiver(&self) -> Option<Receiver<AudioChunk>> {
        self.receiver.clone()
    }
}

impl Drop for AudioCapture {
    fn drop(&mut self) {
        self.stop();
    }
}
