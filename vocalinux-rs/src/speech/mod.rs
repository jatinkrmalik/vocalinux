//! Speech recognition module supporting multiple engines.

mod command_processor;
pub mod gpu_info;
mod manager;
mod soniox;

#[cfg(feature = "vosk")]
mod vosk_engine;

#[cfg(feature = "whisper")]
mod whisper_engine;

pub use command_processor::CommandProcessor;
pub use gpu_info::{
    get_whisper_model, recommend_whisper_model, GpuInfo, ModelRecommendation,
    SystemMemory, WhisperModelInfo, WHISPER_LANGUAGES, WHISPER_MODELS,
};
pub use manager::{RecognitionState, SpeechManager, SpeechResult};
pub use soniox::SonioxClient;

#[cfg(feature = "vosk")]
pub use vosk_engine::VoskEngine;

#[cfg(feature = "whisper")]
pub use whisper_engine::WhisperEngine;
