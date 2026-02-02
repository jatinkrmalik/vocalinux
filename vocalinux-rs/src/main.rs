//! Vocalinux - Voice-controlled dictation for Linux
//!
//! A native Rust application for speech-to-text dictation on Linux,
//! supporting multiple STT engines: VOSK (offline), Whisper (offline), and Soniox (realtime cloud).

mod audio;
mod config;
mod speech;
mod text_injection;
mod ui;

use anyhow::Result;
use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;

use crate::config::AppConfig;
use crate::ui::app::VocalinuxApp;

fn main() -> Result<()> {
    // Initialize logging
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .with_target(false)
        .init();

    info!("Starting Vocalinux v{}", env!("CARGO_PKG_VERSION"));

    // Load configuration
    let config = AppConfig::load()?;
    info!("Configuration loaded: engine={}", config.speech.engine);

    // Initialize GTK application
    let app = VocalinuxApp::new(config)?;
    app.run();

    Ok(())
}
