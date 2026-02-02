//! Speech recognition manager coordinating different engines.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;

use anyhow::{Context, Result};
use crossbeam_channel::{bounded, Receiver, Sender};
use parking_lot::Mutex;
use tracing::{debug, error, info, warn};

use crate::audio::{AudioCapture, AudioChunk, VoiceActivityDetector};
use crate::config::{AppConfig, ModelSize, SpeechEngine};

use super::command_processor::CommandProcessor;
use super::soniox::{SonioxClient, SonioxResult};

#[cfg(feature = "vosk")]
use super::vosk_engine::VoskEngine;

#[cfg(feature = "whisper")]
use super::whisper_engine::WhisperEngine;

/// Recognition state
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RecognitionState {
    Idle,
    Listening,
    Processing,
    Error,
}

/// Speech recognition result
#[derive(Debug, Clone)]
pub enum SpeechResult {
    /// Partial (interim) text - may change
    Partial(String),
    /// Final recognized text
    Final(String),
    /// Action command (e.g., "delete_last", "undo")
    Action(String),
    /// State change
    StateChange(RecognitionState),
    /// Audio level update (0-100)
    AudioLevel(f32),
    /// Error
    Error(String),
}

/// Callback type for speech results
pub type ResultCallback = Box<dyn Fn(SpeechResult) + Send + Sync>;

/// Main speech recognition manager
pub struct SpeechManager {
    config: Arc<Mutex<AppConfig>>,
    audio: Arc<Mutex<AudioCapture>>,
    command_processor: Arc<CommandProcessor>,

    // State
    state: Arc<Mutex<RecognitionState>>,
    is_running: Arc<AtomicBool>,

    // Result channel
    result_sender: Sender<SpeechResult>,
    result_receiver: Receiver<SpeechResult>,

    // Engine instances
    #[cfg(feature = "vosk")]
    vosk_engine: Arc<Mutex<Option<VoskEngine>>>,
    #[cfg(feature = "whisper")]
    whisper_engine: Arc<Mutex<Option<WhisperEngine>>>,
    soniox_client: Arc<Mutex<Option<SonioxClient>>>,
}

impl SpeechManager {
    pub fn new(config: AppConfig) -> Result<Self> {
        let (result_sender, result_receiver) = bounded(100);

        Ok(Self {
            config: Arc::new(Mutex::new(config)),
            audio: Arc::new(Mutex::new(AudioCapture::new())),
            command_processor: Arc::new(CommandProcessor::new()),
            state: Arc::new(Mutex::new(RecognitionState::Idle)),
            is_running: Arc::new(AtomicBool::new(false)),
            result_sender,
            result_receiver,
            #[cfg(feature = "vosk")]
            vosk_engine: Arc::new(Mutex::new(None)),
            #[cfg(feature = "whisper")]
            whisper_engine: Arc::new(Mutex::new(None)),
            soniox_client: Arc::new(Mutex::new(None)),
        })
    }

    /// Get result receiver for listening to speech events
    pub fn get_result_receiver(&self) -> Receiver<SpeechResult> {
        self.result_receiver.clone()
    }

    /// Get current state
    pub fn state(&self) -> RecognitionState {
        *self.state.lock()
    }

    /// Update state and notify
    fn set_state(&self, new_state: RecognitionState) {
        *self.state.lock() = new_state;
        let _ = self.result_sender.try_send(SpeechResult::StateChange(new_state));
    }

    /// Start speech recognition
    pub fn start(&self) -> Result<()> {
        if self.is_running.load(Ordering::SeqCst) {
            return Ok(());
        }

        let config = self.config.lock().clone();
        info!("Starting speech recognition with engine: {}", config.speech.engine);

        self.is_running.store(true, Ordering::SeqCst);
        self.set_state(RecognitionState::Listening);

        match config.speech.engine {
            SpeechEngine::Soniox => self.start_soniox(&config)?,
            #[cfg(feature = "vosk")]
            SpeechEngine::Vosk => self.start_vosk(&config)?,
            #[cfg(feature = "whisper")]
            SpeechEngine::Whisper => self.start_whisper(&config)?,
            #[allow(unreachable_patterns)]
            _ => anyhow::bail!("Engine not available in this build"),
        }

        Ok(())
    }

    /// Start Soniox realtime recognition
    fn start_soniox(&self, config: &AppConfig) -> Result<()> {
        let api_key = config
            .soniox
            .api_key
            .clone()
            .context("Soniox API key not configured")?;

        // Create Soniox client
        let mut client = SonioxClient::new(
            api_key,
            config.speech.language.clone(),
            config.soniox.enable_speaker_diarization,
            config.soniox.enable_language_identification,
        );

        // Connect to Soniox
        let soniox_results = client.connect()?;
        *self.soniox_client.lock() = Some(client);

        // Start audio capture
        let audio_receiver = self.audio.lock().start()?;

        // Clone references for threads
        let is_running = self.is_running.clone();
        let result_sender = self.result_sender.clone();
        let soniox_client = self.soniox_client.clone();
        let command_processor = self.command_processor.clone();

        // Audio streaming thread
        let is_running_audio = is_running.clone();
        thread::spawn(move || {
            while is_running_audio.load(Ordering::SeqCst) {
                match audio_receiver.recv_timeout(std::time::Duration::from_millis(50)) {
                    Ok(chunk) => {
                        if let Some(ref client) = *soniox_client.lock() {
                            if client.send_audio(&chunk.samples).is_err() {
                                break;
                            }
                        }
                    }
                    Err(crossbeam_channel::RecvTimeoutError::Timeout) => continue,
                    Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
                }
            }
        });

        // Result processing thread
        thread::spawn(move || {
            while is_running.load(Ordering::SeqCst) {
                match soniox_results.recv_timeout(std::time::Duration::from_millis(50)) {
                    Ok(SonioxResult::Partial(text)) => {
                        let _ = result_sender.try_send(SpeechResult::Partial(text));
                    }
                    Ok(SonioxResult::Final(text)) => {
                        // Process commands
                        let (processed, actions) = command_processor.process(&text);
                        if !processed.is_empty() {
                            let _ = result_sender.try_send(SpeechResult::Final(processed));
                        }
                        for action in actions {
                            let _ = result_sender.try_send(SpeechResult::Action(action));
                        }
                    }
                    Ok(SonioxResult::Error(msg)) => {
                        let _ = result_sender.try_send(SpeechResult::Error(msg));
                    }
                    Ok(SonioxResult::Closed) => break,
                    Err(crossbeam_channel::RecvTimeoutError::Timeout) => continue,
                    Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
                }
            }
        });

        Ok(())
    }

    /// Start VOSK recognition (with VAD buffering)
    #[cfg(feature = "vosk")]
    fn start_vosk(&self, config: &AppConfig) -> Result<()> {
        // Initialize VOSK engine if needed
        {
            let mut engine = self.vosk_engine.lock();
            if engine.is_none() {
                *engine = Some(VoskEngine::new(
                    &config.speech.language,
                    config.speech.model_size,
                )?);
            }
        }

        // Start audio capture
        let audio_receiver = self.audio.lock().start()?;

        // Clone references
        let is_running = self.is_running.clone();
        let result_sender = self.result_sender.clone();
        let vosk_engine = self.vosk_engine.clone();
        let command_processor = self.command_processor.clone();
        let state = self.state.clone();

        let vad_sensitivity = config.speech.vad_sensitivity;
        let silence_timeout = config.speech.silence_timeout;

        // Recognition thread with VAD
        thread::spawn(move || {
            let mut vad = VoiceActivityDetector::new(vad_sensitivity, silence_timeout);
            let mut audio_buffer: Vec<i16> = Vec::new();

            while is_running.load(Ordering::SeqCst) {
                match audio_receiver.recv_timeout(std::time::Duration::from_millis(50)) {
                    Ok(chunk) => {
                        // Send audio level
                        let level = vad.current_level();
                        let _ = result_sender.try_send(SpeechResult::AudioLevel(level));

                        // Process VAD
                        match vad.process(&chunk.samples) {
                            Some(true) => {
                                // Silence timeout - process buffer
                                if !audio_buffer.is_empty() {
                                    *state.lock() = RecognitionState::Processing;
                                    let _ = result_sender
                                        .try_send(SpeechResult::StateChange(RecognitionState::Processing));

                                    if let Some(ref engine) = *vosk_engine.lock() {
                                        match engine.recognize(&audio_buffer) {
                                            Ok(text) if !text.is_empty() => {
                                                let (processed, actions) =
                                                    command_processor.process(&text);
                                                if !processed.is_empty() {
                                                    let _ = result_sender
                                                        .try_send(SpeechResult::Final(processed));
                                                }
                                                for action in actions {
                                                    let _ = result_sender
                                                        .try_send(SpeechResult::Action(action));
                                                }
                                            }
                                            Ok(_) => {}
                                            Err(e) => {
                                                warn!("VOSK recognition error: {}", e);
                                            }
                                        }
                                    }

                                    audio_buffer.clear();
                                    *state.lock() = RecognitionState::Listening;
                                    let _ = result_sender
                                        .try_send(SpeechResult::StateChange(RecognitionState::Listening));
                                }
                            }
                            Some(false) => {
                                // Speech detected - add to buffer
                                audio_buffer.extend_from_slice(&chunk.samples);
                            }
                            None => {
                                // Still accumulating silence
                                audio_buffer.extend_from_slice(&chunk.samples);
                            }
                        }
                    }
                    Err(crossbeam_channel::RecvTimeoutError::Timeout) => continue,
                    Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
                }
            }
        });

        Ok(())
    }

    /// Start Whisper recognition (with VAD buffering)
    #[cfg(feature = "whisper")]
    fn start_whisper(&self, config: &AppConfig) -> Result<()> {
        // Initialize Whisper engine if needed
        {
            let mut engine = self.whisper_engine.lock();
            if engine.is_none() {
                *engine = Some(WhisperEngine::new(
                    &config.speech.language,
                    config.speech.model_size,
                )?);
            }
        }

        // Start audio capture
        let audio_receiver = self.audio.lock().start()?;

        // Clone references
        let is_running = self.is_running.clone();
        let result_sender = self.result_sender.clone();
        let whisper_engine = self.whisper_engine.clone();
        let command_processor = self.command_processor.clone();
        let state = self.state.clone();

        let vad_sensitivity = config.speech.vad_sensitivity;
        let silence_timeout = config.speech.silence_timeout;

        // Recognition thread with VAD
        thread::spawn(move || {
            let mut vad = VoiceActivityDetector::new(vad_sensitivity, silence_timeout);
            let mut audio_buffer: Vec<i16> = Vec::new();

            while is_running.load(Ordering::SeqCst) {
                match audio_receiver.recv_timeout(std::time::Duration::from_millis(50)) {
                    Ok(chunk) => {
                        let level = vad.current_level();
                        let _ = result_sender.try_send(SpeechResult::AudioLevel(level));

                        match vad.process(&chunk.samples) {
                            Some(true) => {
                                if !audio_buffer.is_empty() {
                                    *state.lock() = RecognitionState::Processing;
                                    let _ = result_sender
                                        .try_send(SpeechResult::StateChange(RecognitionState::Processing));

                                    if let Some(ref engine) = *whisper_engine.lock() {
                                        match engine.recognize(&audio_buffer) {
                                            Ok(text) if !text.is_empty() => {
                                                let (processed, actions) =
                                                    command_processor.process(&text);
                                                if !processed.is_empty() {
                                                    let _ = result_sender
                                                        .try_send(SpeechResult::Final(processed));
                                                }
                                                for action in actions {
                                                    let _ = result_sender
                                                        .try_send(SpeechResult::Action(action));
                                                }
                                            }
                                            Ok(_) => {}
                                            Err(e) => {
                                                warn!("Whisper recognition error: {}", e);
                                            }
                                        }
                                    }

                                    audio_buffer.clear();
                                    *state.lock() = RecognitionState::Listening;
                                    let _ = result_sender
                                        .try_send(SpeechResult::StateChange(RecognitionState::Listening));
                                }
                            }
                            Some(false) | None => {
                                audio_buffer.extend_from_slice(&chunk.samples);
                            }
                        }
                    }
                    Err(crossbeam_channel::RecvTimeoutError::Timeout) => continue,
                    Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
                }
            }
        });

        Ok(())
    }

    /// Stop speech recognition
    pub fn stop(&self) {
        if !self.is_running.load(Ordering::SeqCst) {
            return;
        }

        info!("Stopping speech recognition");
        self.is_running.store(false, Ordering::SeqCst);

        // Stop audio capture
        self.audio.lock().stop();

        // Disconnect Soniox if connected
        if let Some(mut client) = self.soniox_client.lock().take() {
            client.disconnect();
        }

        self.set_state(RecognitionState::Idle);
    }

    /// Check if running
    pub fn is_running(&self) -> bool {
        self.is_running.load(Ordering::SeqCst)
    }

    /// Update configuration
    pub fn update_config(&self, config: AppConfig) {
        *self.config.lock() = config;
    }

    /// Get current configuration
    pub fn config(&self) -> AppConfig {
        self.config.lock().clone()
    }
}

impl Drop for SpeechManager {
    fn drop(&mut self) {
        self.stop();
    }
}
