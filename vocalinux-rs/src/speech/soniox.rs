//! Soniox realtime speech recognition client.
//!
//! Uses WebSocket streaming for low-latency transcription.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

use anyhow::{Context, Result};
use crossbeam_channel::{bounded, Receiver, Sender};
use futures_util::{SinkExt, StreamExt};
use parking_lot::Mutex;
use serde::{Deserialize, Serialize};
use tokio::runtime::Runtime;
use tokio_tungstenite::{connect_async, tungstenite::Message};
use tracing::{debug, error, info, warn};

const SONIOX_WS_URL: &str = "wss://stt-rt.soniox.com/transcribe-websocket";

/// Soniox configuration message
#[derive(Debug, Serialize)]
struct SonioxConfig {
    api_key: String,
    model: String,
    audio_format: String,
    sample_rate: u32,
    num_channels: u32,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    language_hints: Vec<String>,
    enable_endpoint_detection: bool,
    enable_language_identification: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    enable_speaker_diarization: Option<bool>,
}

/// Token from Soniox response
#[derive(Debug, Deserialize)]
pub struct SonioxToken {
    pub text: String,
    #[serde(default)]
    pub start_ms: u64,
    #[serde(default)]
    pub end_ms: u64,
    #[serde(default)]
    pub confidence: f32,
    #[serde(default)]
    pub is_final: bool,
    pub speaker: Option<String>,
    pub language: Option<String>,
}

/// Soniox transcription response
#[derive(Debug, Deserialize)]
pub struct SonioxResponse {
    #[serde(default)]
    pub tokens: Vec<SonioxToken>,
    #[serde(default)]
    pub audio_final_proc_ms: u64,
    #[serde(default)]
    pub audio_total_proc_ms: u64,
    // Error fields
    pub error_code: Option<u32>,
    pub error_message: Option<String>,
}

/// Result sent from Soniox client
#[derive(Debug, Clone)]
pub enum SonioxResult {
    /// Partial (non-final) transcription
    Partial(String),
    /// Final transcription
    Final(String),
    /// Error occurred
    Error(String),
    /// Connection closed
    Closed,
}

/// Soniox realtime client
pub struct SonioxClient {
    api_key: String,
    language: String,
    enable_speaker_diarization: bool,
    enable_language_identification: bool,

    // Runtime and connection state
    runtime: Option<Runtime>,
    is_connected: Arc<AtomicBool>,
    audio_sender: Arc<Mutex<Option<Sender<Vec<u8>>>>>,
    result_receiver: Option<Receiver<SonioxResult>>,
}

impl SonioxClient {
    pub fn new(
        api_key: String,
        language: String,
        enable_speaker_diarization: bool,
        enable_language_identification: bool,
    ) -> Self {
        Self {
            api_key,
            language,
            enable_speaker_diarization,
            enable_language_identification,
            runtime: None,
            is_connected: Arc::new(AtomicBool::new(false)),
            audio_sender: Arc::new(Mutex::new(None)),
            result_receiver: None,
        }
    }

    /// Connect to Soniox and start streaming
    pub fn connect(&mut self) -> Result<Receiver<SonioxResult>> {
        if self.is_connected.load(Ordering::SeqCst) {
            anyhow::bail!("Already connected");
        }

        // Create runtime
        let runtime = Runtime::new().context("Failed to create tokio runtime")?;

        // Create channels
        let (audio_tx, audio_rx) = bounded::<Vec<u8>>(100);
        let (result_tx, result_rx) = bounded::<SonioxResult>(100);

        *self.audio_sender.lock() = Some(audio_tx);
        self.result_receiver = Some(result_rx.clone());

        let api_key = self.api_key.clone();
        let language = self.language.clone();
        let enable_diarization = self.enable_speaker_diarization;
        let enable_lang_id = self.enable_language_identification;
        let is_connected = self.is_connected.clone();

        // Spawn connection task
        runtime.spawn(async move {
            if let Err(e) = run_connection(
                api_key,
                language,
                enable_diarization,
                enable_lang_id,
                audio_rx,
                result_tx,
                is_connected.clone(),
            )
            .await
            {
                error!("Soniox connection error: {}", e);
            }
            is_connected.store(false, Ordering::SeqCst);
        });

        self.runtime = Some(runtime);
        self.is_connected.store(true, Ordering::SeqCst);

        info!("Soniox client connected");
        Ok(result_rx)
    }

    /// Send audio data to Soniox
    pub fn send_audio(&self, samples: &[i16]) -> Result<()> {
        if !self.is_connected.load(Ordering::SeqCst) {
            anyhow::bail!("Not connected");
        }

        // Convert i16 samples to bytes (little-endian)
        let bytes: Vec<u8> = samples
            .iter()
            .flat_map(|&s| s.to_le_bytes())
            .collect();

        if let Some(ref sender) = *self.audio_sender.lock() {
            sender.try_send(bytes).ok();
        }

        Ok(())
    }

    /// Disconnect from Soniox
    pub fn disconnect(&mut self) {
        self.is_connected.store(false, Ordering::SeqCst);
        *self.audio_sender.lock() = None;
        self.result_receiver = None;

        if let Some(runtime) = self.runtime.take() {
            // Give tasks time to clean up
            std::thread::sleep(std::time::Duration::from_millis(100));
            runtime.shutdown_timeout(std::time::Duration::from_secs(1));
        }

        info!("Soniox client disconnected");
    }

    /// Check if connected
    pub fn is_connected(&self) -> bool {
        self.is_connected.load(Ordering::SeqCst)
    }

    /// Get result receiver
    pub fn get_result_receiver(&self) -> Option<Receiver<SonioxResult>> {
        self.result_receiver.clone()
    }
}

impl Drop for SonioxClient {
    fn drop(&mut self) {
        self.disconnect();
    }
}

/// Run the WebSocket connection
async fn run_connection(
    api_key: String,
    language: String,
    enable_diarization: bool,
    enable_lang_id: bool,
    audio_rx: Receiver<Vec<u8>>,
    result_tx: Sender<SonioxResult>,
    is_connected: Arc<AtomicBool>,
) -> Result<()> {
    info!("Connecting to Soniox at {}", SONIOX_WS_URL);

    let (ws_stream, _) = connect_async(SONIOX_WS_URL)
        .await
        .context("Failed to connect to Soniox")?;

    let (mut write, mut read) = ws_stream.split();

    // Send configuration
    let config = SonioxConfig {
        api_key,
        model: "stt-rt-v3".to_string(),
        audio_format: "pcm_s16le".to_string(),
        sample_rate: 16000,
        num_channels: 1,
        language_hints: if language != "auto" {
            vec![language.clone()]
        } else {
            vec![]
        },
        enable_endpoint_detection: true,
        enable_language_identification: enable_lang_id || language == "auto",
        enable_speaker_diarization: if enable_diarization { Some(true) } else { None },
    };

    let config_json = serde_json::to_string(&config)?;
    debug!("Sending Soniox config: {}", config_json);
    write.send(Message::Text(config_json)).await?;

    info!("Soniox connected and configured");

    // Track accumulated text
    let mut current_partial = String::new();

    // Spawn audio sender task
    let is_connected_clone = is_connected.clone();
    let audio_task = tokio::spawn(async move {
        while is_connected_clone.load(Ordering::SeqCst) {
            match audio_rx.recv_timeout(std::time::Duration::from_millis(50)) {
                Ok(audio_data) => {
                    if write.send(Message::Binary(audio_data)).await.is_err() {
                        break;
                    }
                }
                Err(crossbeam_channel::RecvTimeoutError::Timeout) => continue,
                Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
            }
        }
        // Send close frame
        let _ = write.send(Message::Close(None)).await;
    });

    // Receive responses
    while is_connected.load(Ordering::SeqCst) {
        match tokio::time::timeout(std::time::Duration::from_millis(100), read.next()).await {
            Ok(Some(Ok(Message::Text(text)))) => {
                match serde_json::from_str::<SonioxResponse>(&text) {
                    Ok(response) => {
                        // Check for errors
                        if let Some(error_code) = response.error_code {
                            let msg = response
                                .error_message
                                .unwrap_or_else(|| format!("Error code: {}", error_code));
                            error!("Soniox error: {}", msg);
                            let _ = result_tx.try_send(SonioxResult::Error(msg));
                            break;
                        }

                        // Process tokens
                        let mut final_text = String::new();
                        let mut partial_text = String::new();

                        for token in response.tokens {
                            if token.is_final {
                                final_text.push_str(&token.text);
                            } else {
                                partial_text.push_str(&token.text);
                            }
                        }

                        // Send final text
                        if !final_text.is_empty() {
                            debug!("Soniox final: {}", final_text);
                            let _ = result_tx.try_send(SonioxResult::Final(final_text));
                        }

                        // Send partial text if changed
                        if partial_text != current_partial {
                            current_partial = partial_text.clone();
                            if !partial_text.is_empty() {
                                debug!("Soniox partial: {}", partial_text);
                                let _ = result_tx.try_send(SonioxResult::Partial(partial_text));
                            }
                        }
                    }
                    Err(e) => {
                        warn!("Failed to parse Soniox response: {}", e);
                    }
                }
            }
            Ok(Some(Ok(Message::Close(_)))) => {
                info!("Soniox connection closed by server");
                break;
            }
            Ok(Some(Err(e))) => {
                error!("WebSocket error: {}", e);
                break;
            }
            Ok(None) => break,
            Err(_) => continue, // Timeout, continue loop
        }
    }

    // Clean up
    audio_task.abort();
    let _ = result_tx.try_send(SonioxResult::Closed);

    Ok(())
}

/// Test Soniox connection with API key
pub async fn test_connection(api_key: &str) -> Result<()> {
    info!("Testing Soniox connection...");

    let (ws_stream, _) = connect_async(SONIOX_WS_URL)
        .await
        .context("Failed to connect to Soniox")?;

    let (mut write, mut read) = ws_stream.split();

    // Send minimal config to test API key
    let config = SonioxConfig {
        api_key: api_key.to_string(),
        model: "stt-rt-v3".to_string(),
        audio_format: "pcm_s16le".to_string(),
        sample_rate: 16000,
        num_channels: 1,
        language_hints: vec!["en".to_string()],
        enable_endpoint_detection: false,
        enable_language_identification: false,
        enable_speaker_diarization: None,
    };

    write.send(Message::Text(serde_json::to_string(&config)?)).await?;

    // Wait for response (or timeout)
    match tokio::time::timeout(std::time::Duration::from_secs(5), read.next()).await {
        Ok(Some(Ok(Message::Text(text)))) => {
            let response: SonioxResponse = serde_json::from_str(&text)?;
            if let Some(error_code) = response.error_code {
                let msg = response.error_message.unwrap_or_default();
                if error_code == 401 {
                    anyhow::bail!("Invalid API key");
                }
                anyhow::bail!("Soniox error {}: {}", error_code, msg);
            }
            info!("Soniox connection test successful");
            Ok(())
        }
        Ok(Some(Ok(Message::Close(_)))) => {
            // Connection closed immediately might mean auth failed
            anyhow::bail!("Connection closed - possibly invalid API key")
        }
        Ok(Some(Err(e))) => anyhow::bail!("WebSocket error: {}", e),
        Ok(None) => anyhow::bail!("Connection closed unexpectedly"),
        Err(_) => {
            // Timeout is actually OK - means no immediate error
            info!("Soniox connection test successful (no immediate error)");
            Ok(())
        }
    }
}
