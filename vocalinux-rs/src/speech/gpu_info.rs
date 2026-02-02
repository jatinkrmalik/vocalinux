//! GPU utilities and system information.

use std::process::Command;

use serde::{Deserialize, Serialize};
use tracing::{debug, warn};

/// GPU information
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct GpuInfo {
    /// GPU name
    pub name: String,
    /// Total VRAM in MB
    pub total_memory_mb: u64,
    /// Used VRAM in MB
    pub used_memory_mb: u64,
    /// Free VRAM in MB
    pub free_memory_mb: u64,
    /// Whether CUDA is available
    pub cuda_available: bool,
    /// CUDA version if available
    pub cuda_version: Option<String>,
    /// Driver version
    pub driver_version: Option<String>,
}

impl GpuInfo {
    /// Detect GPU and VRAM information
    pub fn detect() -> Option<Self> {
        // Try nvidia-smi first
        if let Some(info) = Self::detect_nvidia() {
            return Some(info);
        }

        // Could add AMD ROCm detection here in the future
        // if let Some(info) = Self::detect_amd() { ... }

        None
    }

    /// Detect NVIDIA GPU using nvidia-smi
    fn detect_nvidia() -> Option<Self> {
        // Query GPU info using nvidia-smi
        let output = Command::new("nvidia-smi")
            .args([
                "--query-gpu=name,memory.total,memory.used,memory.free,driver_version",
                "--format=csv,noheader,nounits"
            ])
            .output()
            .ok()?;

        if !output.status.success() {
            return None;
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let line = stdout.lines().next()?;
        let parts: Vec<&str> = line.split(',').map(|s| s.trim()).collect();

        if parts.len() < 5 {
            return None;
        }

        let name = parts[0].to_string();
        let total_memory_mb = parts[1].parse().unwrap_or(0);
        let used_memory_mb = parts[2].parse().unwrap_or(0);
        let free_memory_mb = parts[3].parse().unwrap_or(0);
        let driver_version = Some(parts[4].to_string());

        // Check CUDA version
        let cuda_version = Command::new("nvidia-smi")
            .output()
            .ok()
            .and_then(|o| {
                let s = String::from_utf8_lossy(&o.stdout);
                // Parse "CUDA Version: X.Y" from nvidia-smi output
                s.lines()
                    .find(|l| l.contains("CUDA Version"))
                    .and_then(|l| {
                        l.split("CUDA Version:")
                            .nth(1)
                            .map(|v| v.split_whitespace().next().unwrap_or("").to_string())
                    })
            });

        debug!(
            "Detected NVIDIA GPU: {} ({} MB total, {} MB free)",
            name, total_memory_mb, free_memory_mb
        );

        Some(Self {
            name,
            total_memory_mb,
            used_memory_mb,
            free_memory_mb,
            cuda_available: true,
            cuda_version,
            driver_version,
        })
    }

    /// Check if there's enough VRAM for a model
    pub fn can_fit_model(&self, required_mb: u64) -> bool {
        self.free_memory_mb >= required_mb
    }

    /// Get usage percentage
    pub fn usage_percent(&self) -> f32 {
        if self.total_memory_mb == 0 {
            return 0.0;
        }
        (self.used_memory_mb as f32 / self.total_memory_mb as f32) * 100.0
    }
}

/// Whisper model information
#[derive(Debug, Clone)]
pub struct WhisperModelInfo {
    pub name: &'static str,
    pub display_name: &'static str,
    pub size_mb: u64,
    /// Approximate VRAM needed for inference (in MB)
    pub vram_required_mb: u64,
    /// Approximate RAM needed if running on CPU (in MB)
    pub ram_required_mb: u64,
    /// Relative speed (1.0 = baseline tiny)
    pub relative_speed: f32,
    /// Relative accuracy (1.0 = baseline tiny)
    pub relative_accuracy: f32,
    pub download_url: &'static str,
}

/// All available Whisper models
pub const WHISPER_MODELS: &[WhisperModelInfo] = &[
    WhisperModelInfo {
        name: "tiny",
        display_name: "Tiny (75 MB)",
        size_mb: 75,
        vram_required_mb: 1000,   // ~1 GB VRAM
        ram_required_mb: 2000,    // ~2 GB RAM
        relative_speed: 1.0,
        relative_accuracy: 1.0,
        download_url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
    },
    WhisperModelInfo {
        name: "base",
        display_name: "Base (142 MB)",
        size_mb: 142,
        vram_required_mb: 1500,
        ram_required_mb: 3000,
        relative_speed: 0.7,
        relative_accuracy: 1.2,
        download_url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
    },
    WhisperModelInfo {
        name: "small",
        display_name: "Small (466 MB)",
        size_mb: 466,
        vram_required_mb: 2500,
        ram_required_mb: 5000,
        relative_speed: 0.4,
        relative_accuracy: 1.5,
        download_url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
    },
    WhisperModelInfo {
        name: "medium",
        display_name: "Medium (1.5 GB)",
        size_mb: 1500,
        vram_required_mb: 5000,
        ram_required_mb: 10000,
        relative_speed: 0.2,
        relative_accuracy: 1.8,
        download_url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
    },
    WhisperModelInfo {
        name: "large",
        display_name: "Large-v3 (2.9 GB)",
        size_mb: 2900,
        vram_required_mb: 10000,
        ram_required_mb: 16000,
        relative_speed: 0.1,
        relative_accuracy: 2.0,
        download_url: "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
    },
];

/// Get model info by name
pub fn get_whisper_model(name: &str) -> Option<&'static WhisperModelInfo> {
    WHISPER_MODELS.iter().find(|m| m.name == name)
}

/// Whisper supported languages
pub const WHISPER_LANGUAGES: &[(&str, &str)] = &[
    ("auto", "Auto-detect"),
    ("en", "English"),
    ("zh", "Chinese"),
    ("de", "German"),
    ("es", "Spanish"),
    ("ru", "Russian"),
    ("ko", "Korean"),
    ("fr", "French"),
    ("ja", "Japanese"),
    ("pt", "Portuguese"),
    ("tr", "Turkish"),
    ("pl", "Polish"),
    ("ca", "Catalan"),
    ("nl", "Dutch"),
    ("ar", "Arabic"),
    ("sv", "Swedish"),
    ("it", "Italian"),
    ("id", "Indonesian"),
    ("hi", "Hindi"),
    ("fi", "Finnish"),
    ("vi", "Vietnamese"),
    ("he", "Hebrew"),
    ("uk", "Ukrainian"),
    ("el", "Greek"),
    ("ms", "Malay"),
    ("cs", "Czech"),
    ("ro", "Romanian"),
    ("da", "Danish"),
    ("hu", "Hungarian"),
    ("ta", "Tamil"),
    ("no", "Norwegian"),
    ("th", "Thai"),
    ("ur", "Urdu"),
    ("hr", "Croatian"),
    ("bg", "Bulgarian"),
    ("lt", "Lithuanian"),
    ("la", "Latin"),
    ("mi", "Maori"),
    ("ml", "Malayalam"),
    ("cy", "Welsh"),
    ("sk", "Slovak"),
    ("te", "Telugu"),
    ("fa", "Persian"),
    ("lv", "Latvian"),
    ("bn", "Bengali"),
    ("sr", "Serbian"),
    ("az", "Azerbaijani"),
    ("sl", "Slovenian"),
    ("kn", "Kannada"),
    ("et", "Estonian"),
    ("mk", "Macedonian"),
    ("br", "Breton"),
    ("eu", "Basque"),
    ("is", "Icelandic"),
    ("hy", "Armenian"),
    ("ne", "Nepali"),
    ("mn", "Mongolian"),
    ("bs", "Bosnian"),
    ("kk", "Kazakh"),
    ("sq", "Albanian"),
    ("sw", "Swahili"),
    ("gl", "Galician"),
    ("mr", "Marathi"),
    ("pa", "Punjabi"),
    ("si", "Sinhala"),
    ("km", "Khmer"),
    ("sn", "Shona"),
    ("yo", "Yoruba"),
    ("so", "Somali"),
    ("af", "Afrikaans"),
    ("oc", "Occitan"),
    ("ka", "Georgian"),
    ("be", "Belarusian"),
    ("tg", "Tajik"),
    ("sd", "Sindhi"),
    ("gu", "Gujarati"),
    ("am", "Amharic"),
    ("yi", "Yiddish"),
    ("lo", "Lao"),
    ("uz", "Uzbek"),
    ("fo", "Faroese"),
    ("ht", "Haitian Creole"),
    ("ps", "Pashto"),
    ("tk", "Turkmen"),
    ("nn", "Nynorsk"),
    ("mt", "Maltese"),
    ("sa", "Sanskrit"),
    ("lb", "Luxembourgish"),
    ("my", "Myanmar"),
    ("bo", "Tibetan"),
    ("tl", "Tagalog"),
    ("mg", "Malagasy"),
    ("as", "Assamese"),
    ("tt", "Tatar"),
    ("haw", "Hawaiian"),
    ("ln", "Lingala"),
    ("ha", "Hausa"),
    ("ba", "Bashkir"),
    ("jw", "Javanese"),
    ("su", "Sundanese"),
];

/// Model recommendation based on system capabilities
#[derive(Debug, Clone)]
pub struct ModelRecommendation {
    pub recommended_model: &'static str,
    pub reason: String,
    pub will_use_gpu: bool,
    pub estimated_speed: &'static str,
}

/// Get model recommendation based on available GPU
pub fn recommend_whisper_model(gpu_info: Option<&GpuInfo>) -> ModelRecommendation {
    match gpu_info {
        Some(gpu) if gpu.cuda_available => {
            let free_vram = gpu.free_memory_mb;

            if free_vram >= 10000 {
                ModelRecommendation {
                    recommended_model: "large",
                    reason: format!(
                        "GPU {} has {} MB free VRAM - can run Large model for best accuracy",
                        gpu.name, free_vram
                    ),
                    will_use_gpu: true,
                    estimated_speed: "Slow but most accurate",
                }
            } else if free_vram >= 5000 {
                ModelRecommendation {
                    recommended_model: "medium",
                    reason: format!(
                        "GPU {} has {} MB free VRAM - Medium model offers good balance",
                        gpu.name, free_vram
                    ),
                    will_use_gpu: true,
                    estimated_speed: "Moderate speed, high accuracy",
                }
            } else if free_vram >= 2500 {
                ModelRecommendation {
                    recommended_model: "small",
                    reason: format!(
                        "GPU {} has {} MB free VRAM - Small model recommended",
                        gpu.name, free_vram
                    ),
                    will_use_gpu: true,
                    estimated_speed: "Good speed and accuracy",
                }
            } else if free_vram >= 1500 {
                ModelRecommendation {
                    recommended_model: "base",
                    reason: format!(
                        "GPU {} has {} MB free VRAM - Base model fits",
                        gpu.name, free_vram
                    ),
                    will_use_gpu: true,
                    estimated_speed: "Fast with decent accuracy",
                }
            } else {
                ModelRecommendation {
                    recommended_model: "tiny",
                    reason: format!(
                        "GPU {} has only {} MB free VRAM - using Tiny model",
                        gpu.name, free_vram
                    ),
                    will_use_gpu: true,
                    estimated_speed: "Fastest, basic accuracy",
                }
            }
        }
        _ => {
            // No GPU - recommend based on typical CPU capabilities
            ModelRecommendation {
                recommended_model: "base",
                reason: "No CUDA GPU detected - using CPU. Base model recommended for balance of speed and accuracy.".to_string(),
                will_use_gpu: false,
                estimated_speed: "Moderate (CPU)",
            }
        }
    }
}

/// System memory info
#[derive(Debug, Clone, Default)]
pub struct SystemMemory {
    pub total_mb: u64,
    pub available_mb: u64,
}

impl SystemMemory {
    pub fn detect() -> Self {
        // Read from /proc/meminfo on Linux
        if let Ok(content) = std::fs::read_to_string("/proc/meminfo") {
            let mut total = 0u64;
            let mut available = 0u64;

            for line in content.lines() {
                if line.starts_with("MemTotal:") {
                    total = parse_meminfo_value(line);
                } else if line.starts_with("MemAvailable:") {
                    available = parse_meminfo_value(line);
                }
            }

            return Self {
                total_mb: total / 1024,      // Convert from KB to MB
                available_mb: available / 1024,
            };
        }

        Self::default()
    }
}

fn parse_meminfo_value(line: &str) -> u64 {
    line.split_whitespace()
        .nth(1)
        .and_then(|v| v.parse().ok())
        .unwrap_or(0)
}
