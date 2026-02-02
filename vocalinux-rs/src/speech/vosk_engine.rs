//! VOSK speech recognition engine.

use anyhow::{Context, Result};
use tracing::{debug, info};
use vosk::{Model, Recognizer};

use crate::config::{AppConfig, ModelSize};

/// VOSK model information
pub struct VoskModelInfo {
    pub name: &'static str,
    pub url: &'static str,
    pub size_mb: u32,
}

/// Get VOSK model info for language and size
pub fn get_model_info(language: &str, size: ModelSize) -> Option<VoskModelInfo> {
    // Map language codes to VOSK model names
    let models: &[(&str, &str, ModelSize, &str, u32)] = &[
        // English
        ("en-us", "vosk-model-small-en-us-0.15", ModelSize::Small, "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip", 40),
        ("en-us", "vosk-model-en-us-0.22", ModelSize::Medium, "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip", 1800),
        ("en-us", "vosk-model-en-us-0.22-lgraph", ModelSize::Large, "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22-lgraph.zip", 128),
        // Russian
        ("ru", "vosk-model-small-ru-0.22", ModelSize::Small, "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip", 45),
        ("ru", "vosk-model-ru-0.42", ModelSize::Medium, "https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip", 1800),
        // Spanish
        ("es", "vosk-model-small-es-0.42", ModelSize::Small, "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip", 39),
        // German
        ("de", "vosk-model-small-de-0.15", ModelSize::Small, "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip", 45),
        // French
        ("fr", "vosk-model-small-fr-0.22", ModelSize::Small, "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip", 41),
        // Italian
        ("it", "vosk-model-small-it-0.22", ModelSize::Small, "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip", 48),
        // Portuguese
        ("pt", "vosk-model-small-pt-0.3", ModelSize::Small, "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip", 31),
        // Chinese
        ("zh", "vosk-model-small-cn-0.22", ModelSize::Small, "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip", 42),
        // Hindi
        ("hi", "vosk-model-small-hi-0.22", ModelSize::Small, "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip", 42),
    ];

    for &(lang, name, model_size, url, size_mb) in models {
        if lang == language && model_size == size {
            return Some(VoskModelInfo { name, url, size_mb });
        }
    }

    // Fallback to en-us small
    if language != "en-us" || size != ModelSize::Small {
        return get_model_info("en-us", ModelSize::Small);
    }

    None
}

/// VOSK speech recognition engine
pub struct VoskEngine {
    model: Model,
    sample_rate: f32,
}

impl VoskEngine {
    /// Create a new VOSK engine
    pub fn new(language: &str, model_size: ModelSize) -> Result<Self> {
        let model_info = get_model_info(language, model_size)
            .context("No VOSK model available for this configuration")?;

        let models_dir = AppConfig::models_dir()?;
        let model_path = models_dir.join(model_info.name);

        if !model_path.exists() {
            anyhow::bail!(
                "VOSK model not found at {:?}. Please download it from Settings.",
                model_path
            );
        }

        info!("Loading VOSK model from {:?}", model_path);
        let model = Model::new(model_path.to_str().unwrap())
            .context("Failed to load VOSK model")?;

        Ok(Self {
            model,
            sample_rate: 16000.0,
        })
    }

    /// Recognize speech from audio samples
    pub fn recognize(&self, samples: &[i16]) -> Result<String> {
        let mut recognizer = Recognizer::new(&self.model, self.sample_rate)
            .context("Failed to create VOSK recognizer")?;

        // Convert samples to bytes
        let bytes: Vec<u8> = samples
            .iter()
            .flat_map(|&s| s.to_le_bytes())
            .collect();

        recognizer.accept_waveform(&bytes);
        let result = recognizer.final_result();

        // Parse JSON result
        if let Some(text) = result.single() {
            let text = text.text.trim().to_string();
            if !text.is_empty() {
                debug!("VOSK recognized: {}", text);
            }
            Ok(text)
        } else {
            Ok(String::new())
        }
    }

    /// Check if model exists
    pub fn model_exists(language: &str, model_size: ModelSize) -> Result<bool> {
        let model_info = match get_model_info(language, model_size) {
            Some(info) => info,
            None => return Ok(false),
        };

        let models_dir = AppConfig::models_dir()?;
        let model_path = models_dir.join(model_info.name);

        Ok(model_path.exists())
    }
}

/// Download VOSK model with progress callback
pub async fn download_model(
    language: &str,
    model_size: ModelSize,
    progress_callback: impl Fn(f32, String) + Send + 'static,
) -> Result<()> {
    let model_info = get_model_info(language, model_size)
        .context("No VOSK model available for this configuration")?;

    let models_dir = AppConfig::models_dir()?;
    std::fs::create_dir_all(&models_dir)?;

    let zip_path = models_dir.join(format!("{}.zip", model_info.name));
    let model_path = models_dir.join(model_info.name);

    if model_path.exists() {
        info!("VOSK model already exists at {:?}", model_path);
        return Ok(());
    }

    info!("Downloading VOSK model from {}", model_info.url);
    progress_callback(0.0, "Starting download...".to_string());

    // Download
    let response = reqwest::get(model_info.url).await?;
    let total_size = response.content_length().unwrap_or(0);

    let mut file = std::fs::File::create(&zip_path)?;
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

    // Extract
    progress_callback(1.0, "Extracting...".to_string());
    let file = std::fs::File::open(&zip_path)?;
    let mut archive = zip::ZipArchive::new(file)?;
    archive.extract(&models_dir)?;

    // Clean up
    std::fs::remove_file(&zip_path)?;

    progress_callback(1.0, "Complete!".to_string());
    info!("VOSK model downloaded and extracted to {:?}", model_path);

    Ok(())
}
