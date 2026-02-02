//! Configuration management for Vocalinux.

use std::fs;
use std::path::PathBuf;

use anyhow::{Context, Result};
use directories::ProjectDirs;
use serde::{Deserialize, Serialize};
use tracing::{debug, info, warn};

/// Speech recognition engine type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "lowercase")]
pub enum SpeechEngine {
    #[default]
    Vosk,
    Whisper,
    Soniox,
}

impl std::fmt::Display for SpeechEngine {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            SpeechEngine::Vosk => write!(f, "vosk"),
            SpeechEngine::Whisper => write!(f, "whisper"),
            SpeechEngine::Soniox => write!(f, "soniox"),
        }
    }
}

/// Model size for speech recognition
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
#[serde(rename_all = "lowercase")]
pub enum ModelSize {
    Tiny,
    #[default]
    Small,
    Base,
    Medium,
    Large,
}

impl std::fmt::Display for ModelSize {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ModelSize::Tiny => write!(f, "tiny"),
            ModelSize::Small => write!(f, "small"),
            ModelSize::Base => write!(f, "base"),
            ModelSize::Medium => write!(f, "medium"),
            ModelSize::Large => write!(f, "large"),
        }
    }
}

/// Speech recognition configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpeechConfig {
    pub engine: SpeechEngine,
    pub language: String,
    pub model_size: ModelSize,
    pub vad_sensitivity: u8,
    pub silence_timeout: f32,
}

impl Default for SpeechConfig {
    fn default() -> Self {
        Self {
            engine: SpeechEngine::default(),
            language: "en-us".to_string(),
            model_size: ModelSize::default(),
            vad_sensitivity: 3,
            silence_timeout: 2.0,
        }
    }
}

/// Audio configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioConfig {
    pub device_name: Option<String>,
    pub sample_rate: u32,
}

impl Default for AudioConfig {
    fn default() -> Self {
        Self {
            device_name: None,
            sample_rate: 16000,
        }
    }
}

/// Soniox cloud configuration
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct SonioxConfig {
    /// API key is stored in system keyring, not in config file
    #[serde(skip)]
    pub api_key: Option<String>,
    pub enable_speaker_diarization: bool,
    pub enable_language_identification: bool,
}

/// UI configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiConfig {
    pub start_minimized: bool,
    pub show_notifications: bool,
    pub show_partial_results: bool,
}

impl Default for UiConfig {
    fn default() -> Self {
        Self {
            start_minimized: false,
            show_notifications: true,
            show_partial_results: true,
        }
    }
}

/// Keyboard shortcuts configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ShortcutsConfig {
    pub toggle_recognition: String,
}

impl Default for ShortcutsConfig {
    fn default() -> Self {
        Self {
            toggle_recognition: "ctrl+ctrl".to_string(),
        }
    }
}

/// Main application configuration
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AppConfig {
    pub speech: SpeechConfig,
    pub audio: AudioConfig,
    pub soniox: SonioxConfig,
    pub ui: UiConfig,
    pub shortcuts: ShortcutsConfig,
}

impl AppConfig {
    /// Get the configuration directory path
    pub fn config_dir() -> Result<PathBuf> {
        let proj_dirs = ProjectDirs::from("com", "vocalinux", "vocalinux")
            .context("Failed to determine config directory")?;
        Ok(proj_dirs.config_dir().to_path_buf())
    }

    /// Get the data directory path (for models)
    pub fn data_dir() -> Result<PathBuf> {
        let proj_dirs = ProjectDirs::from("com", "vocalinux", "vocalinux")
            .context("Failed to determine data directory")?;
        Ok(proj_dirs.data_dir().to_path_buf())
    }

    /// Get the models directory path
    pub fn models_dir() -> Result<PathBuf> {
        let data_dir = Self::data_dir()?;
        Ok(data_dir.join("models"))
    }

    /// Get the configuration file path
    fn config_path() -> Result<PathBuf> {
        let config_dir = Self::config_dir()?;
        Ok(config_dir.join("config.json"))
    }

    /// Load configuration from file or create default
    pub fn load() -> Result<Self> {
        let config_path = Self::config_path()?;

        if config_path.exists() {
            debug!("Loading config from {:?}", config_path);
            let content = fs::read_to_string(&config_path)
                .context("Failed to read config file")?;
            let mut config: Self = serde_json::from_str(&content)
                .context("Failed to parse config file")?;

            // Load API key from keyring
            config.load_soniox_api_key();

            Ok(config)
        } else {
            info!("Config file not found, creating default");
            let config = Self::default();
            config.save()?;
            Ok(config)
        }
    }

    /// Save configuration to file
    pub fn save(&self) -> Result<()> {
        let config_path = Self::config_path()?;
        let config_dir = config_path.parent().unwrap();

        // Create config directory if it doesn't exist
        fs::create_dir_all(config_dir)
            .context("Failed to create config directory")?;

        // Save config (API key is not included due to #[serde(skip)])
        let content = serde_json::to_string_pretty(self)
            .context("Failed to serialize config")?;
        fs::write(&config_path, content)
            .context("Failed to write config file")?;

        debug!("Config saved to {:?}", config_path);
        Ok(())
    }

    /// Load Soniox API key from system keyring
    fn load_soniox_api_key(&mut self) {
        match keyring::Entry::new("vocalinux", "soniox_api_key") {
            Ok(entry) => {
                match entry.get_password() {
                    Ok(key) => {
                        self.soniox.api_key = Some(key);
                        debug!("Loaded Soniox API key from keyring");
                    }
                    Err(keyring::Error::NoEntry) => {
                        debug!("No Soniox API key found in keyring");
                    }
                    Err(e) => {
                        warn!("Failed to load Soniox API key: {}", e);
                    }
                }
            }
            Err(e) => {
                warn!("Failed to access keyring: {}", e);
            }
        }
    }

    /// Save Soniox API key to system keyring
    pub fn save_soniox_api_key(&mut self, api_key: &str) -> Result<()> {
        let entry = keyring::Entry::new("vocalinux", "soniox_api_key")
            .context("Failed to create keyring entry")?;

        entry.set_password(api_key)
            .context("Failed to save API key to keyring")?;

        self.soniox.api_key = Some(api_key.to_string());
        info!("Soniox API key saved to keyring");
        Ok(())
    }

    /// Delete Soniox API key from keyring
    pub fn delete_soniox_api_key(&mut self) -> Result<()> {
        let entry = keyring::Entry::new("vocalinux", "soniox_api_key")
            .context("Failed to create keyring entry")?;

        match entry.delete_credential() {
            Ok(()) => {
                self.soniox.api_key = None;
                info!("Soniox API key deleted from keyring");
            }
            Err(keyring::Error::NoEntry) => {
                self.soniox.api_key = None;
            }
            Err(e) => {
                return Err(anyhow::anyhow!("Failed to delete API key: {}", e));
            }
        }
        Ok(())
    }
}
