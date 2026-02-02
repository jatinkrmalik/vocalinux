//! Whisper speech recognition engine using whisper-rs (whisper.cpp bindings).

use anyhow::{Context, Result};
use tracing::{debug, info};
use whisper_rs::{FullParams, SamplingStrategy, WhisperContext, WhisperContextParameters};

use crate::config::{AppConfig, ModelSize};

/// Whisper model information
pub struct WhisperModelInfo {
    pub name: &'static str,
    pub url: &'static str,
    pub size_mb: u32,
}

/// Get Whisper model info for size
pub fn get_model_info(size: ModelSize) -> WhisperModelInfo {
    match size {
        ModelSize::Tiny => WhisperModelInfo {
            name: "ggml-tiny.bin",
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
            size_mb: 75,
        },
        ModelSize::Base => WhisperModelInfo {
            name: "ggml-base.bin",
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
            size_mb: 142,
        },
        ModelSize::Small => WhisperModelInfo {
            name: "ggml-small.bin",
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
            size_mb: 466,
        },
        ModelSize::Medium => WhisperModelInfo {
            name: "ggml-medium.bin",
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
            size_mb: 1500,
        },
        ModelSize::Large => WhisperModelInfo {
            name: "ggml-large-v3.bin",
            url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
            size_mb: 2900,
        },
    }
}

/// Whisper speech recognition engine
pub struct WhisperEngine {
    context: WhisperContext,
    language: String,
}

impl WhisperEngine {
    /// Create a new Whisper engine
    pub fn new(language: &str, model_size: ModelSize) -> Result<Self> {
        let model_info = get_model_info(model_size);

        let models_dir = AppConfig::models_dir()?;
        let whisper_dir = models_dir.join("whisper");
        let model_path = whisper_dir.join(model_info.name);

        if !model_path.exists() {
            anyhow::bail!(
                "Whisper model not found at {:?}. Please download it from Settings.",
                model_path
            );
        }

        info!("Loading Whisper model from {:?}", model_path);

        let context = WhisperContext::new_with_params(
            model_path.to_str().unwrap(),
            WhisperContextParameters::default(),
        )
        .context("Failed to load Whisper model")?;

        Ok(Self {
            context,
            language: language.to_string(),
        })
    }

    /// Recognize speech from audio samples (i16 format)
    pub fn recognize(&self, samples: &[i16]) -> Result<String> {
        // Convert i16 to f32 (normalized to [-1, 1])
        let samples_f32: Vec<f32> = samples
            .iter()
            .map(|&s| s as f32 / 32768.0)
            .collect();

        self.recognize_f32(&samples_f32)
    }

    /// Recognize speech from audio samples (f32 format)
    pub fn recognize_f32(&self, samples: &[f32]) -> Result<String> {
        let mut params = FullParams::new(SamplingStrategy::Greedy { best_of: 1 });

        // Configure parameters
        params.set_print_special(false);
        params.set_print_progress(false);
        params.set_print_realtime(false);
        params.set_print_timestamps(false);

        // Set language
        if self.language != "auto" {
            let lang = if self.language == "en-us" { "en" } else { &self.language };
            params.set_language(Some(lang));
        }

        // Temperature for consistent output
        params.set_temperature(0.0);

        // Run inference
        let mut state = self.context.create_state()
            .context("Failed to create Whisper state")?;

        state.full(params, samples)
            .context("Failed to run Whisper inference")?;

        // Get result
        let num_segments = state.full_n_segments()
            .context("Failed to get number of segments")?;

        let mut result = String::new();
        for i in 0..num_segments {
            if let Ok(segment) = state.full_get_segment_text(i) {
                result.push_str(&segment);
            }
        }

        let text = result.trim().to_string();
        if !text.is_empty() {
            debug!("Whisper recognized: {}", text);
        }

        Ok(text)
    }

    /// Check if model exists
    pub fn model_exists(model_size: ModelSize) -> Result<bool> {
        let model_info = get_model_info(model_size);
        let models_dir = AppConfig::models_dir()?;
        let whisper_dir = models_dir.join("whisper");
        let model_path = whisper_dir.join(model_info.name);

        Ok(model_path.exists())
    }
}

/// Download Whisper model with progress callback
pub async fn download_model(
    model_size: ModelSize,
    progress_callback: impl Fn(f32, String) + Send + 'static,
) -> Result<()> {
    let model_info = get_model_info(model_size);

    let models_dir = AppConfig::models_dir()?;
    let whisper_dir = models_dir.join("whisper");
    std::fs::create_dir_all(&whisper_dir)?;

    let model_path = whisper_dir.join(model_info.name);
    let temp_path = whisper_dir.join(format!("{}.tmp", model_info.name));

    if model_path.exists() {
        info!("Whisper model already exists at {:?}", model_path);
        return Ok(());
    }

    info!("Downloading Whisper model from {}", model_info.url);
    progress_callback(0.0, "Starting download...".to_string());

    // Download
    let response = reqwest::get(model_info.url).await?;
    let total_size = response.content_length().unwrap_or(0);

    let mut file = std::fs::File::create(&temp_path)?;
    let mut downloaded: u64 = 0;

    use futures_util::StreamExt;
    use std::io::Write;

    let mut stream = response.bytes_stream();
    while let Some(chunk) = stream.next().await {
        let chunk = chunk?;
        file.write_all(&chunk)?;
        downloaded += chunk.len() as u64;

        if total_size > 0 {
            let progress = downloaded as f32 / total_size as f32;
            let status = format!(
                "{:.1} / {:.1} MB",
                downloaded as f32 / 1_000_000.0,
                total_size as f32 / 1_000_000.0
            );
            progress_callback(progress, status);
        }
    }

    // Rename temp to final
    std::fs::rename(&temp_path, &model_path)?;

    progress_callback(1.0, "Complete!".to_string());
    info!("Whisper model downloaded to {:?}", model_path);

    Ok(())
}
