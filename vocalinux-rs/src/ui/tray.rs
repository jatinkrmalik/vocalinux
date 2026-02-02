//! System tray implementation.

use std::sync::Arc;

use anyhow::Result;
use muda::{Menu, MenuEvent, MenuItem, PredefinedMenuItem};
use parking_lot::Mutex;
use tray_icon::{
    menu::MenuId,
    TrayIcon, TrayIconBuilder,
};
use tracing::{debug, error, info};

use crate::config::AppConfig;
use crate::speech::{RecognitionState, SpeechManager};

/// System tray manager
pub struct TrayManager {
    config: Arc<Mutex<AppConfig>>,
    speech_manager: Arc<SpeechManager>,
    tray_icon: Option<TrayIcon>,
}

impl TrayManager {
    pub fn new(
        config: Arc<Mutex<AppConfig>>,
        speech_manager: Arc<SpeechManager>,
    ) -> Self {
        Self {
            config,
            speech_manager,
            tray_icon: None,
        }
    }

    /// Start the system tray
    pub fn start(&self) -> Result<()> {
        info!("Starting system tray");

        // Create menu
        let menu = Menu::new();

        let toggle_item = MenuItem::new("Toggle Dictation", true, None);
        let settings_item = MenuItem::new("Settings...", true, None);
        let separator = PredefinedMenuItem::separator();
        let about_item = MenuItem::new("About Vocalinux", true, None);
        let quit_item = MenuItem::new("Quit", true, None);

        menu.append(&toggle_item)?;
        menu.append(&separator)?;
        menu.append(&settings_item)?;
        menu.append(&about_item)?;
        menu.append(&PredefinedMenuItem::separator())?;
        menu.append(&quit_item)?;

        // Create tray icon
        // Note: In a real implementation, you'd load actual icon files
        let icon = load_icon()?;

        let tray = TrayIconBuilder::new()
            .with_menu(Box::new(menu))
            .with_tooltip("Vocalinux - Voice Dictation")
            .with_icon(icon)
            .build()?;

        info!("System tray started");

        // Handle menu events
        let toggle_id = toggle_item.id().clone();
        let settings_id = settings_item.id().clone();
        let about_id = about_item.id().clone();
        let quit_id = quit_item.id().clone();

        let speech_manager = self.speech_manager.clone();

        std::thread::spawn(move || {
            loop {
                if let Ok(event) = MenuEvent::receiver().recv() {
                    if event.id == toggle_id {
                        debug!("Toggle dictation clicked");
                        if speech_manager.is_running() {
                            speech_manager.stop();
                        } else {
                            if let Err(e) = speech_manager.start() {
                                error!("Failed to start recognition: {}", e);
                            }
                        }
                    } else if event.id == settings_id {
                        debug!("Settings clicked");
                        // TODO: Show settings dialog
                    } else if event.id == about_id {
                        debug!("About clicked");
                        // TODO: Show about dialog
                    } else if event.id == quit_id {
                        debug!("Quit clicked");
                        std::process::exit(0);
                    }
                }
            }
        });

        Ok(())
    }

    /// Update tray icon based on state
    pub fn update_state(&mut self, state: RecognitionState) {
        if let Some(ref _tray) = self.tray_icon {
            let tooltip = match state {
                RecognitionState::Idle => "Vocalinux - Idle (Ctrl+Ctrl to start)",
                RecognitionState::Listening => "Vocalinux - Listening...",
                RecognitionState::Processing => "Vocalinux - Processing...",
                RecognitionState::Error => "Vocalinux - Error",
            };

            // Update tooltip
            // tray.set_tooltip(Some(tooltip));

            // Could also update icon here based on state
            debug!("Tray state updated: {:?}", state);
        }
    }
}

/// Load tray icon
fn load_icon() -> Result<tray_icon::Icon> {
    // Create a simple colored icon (in production, load from file)
    // This creates a 32x32 RGBA icon
    let width = 32u32;
    let height = 32u32;
    let mut rgba = vec![0u8; (width * height * 4) as usize];

    // Draw a simple microphone-like shape (green circle)
    for y in 0..height {
        for x in 0..width {
            let idx = ((y * width + x) * 4) as usize;
            let cx = width as f32 / 2.0;
            let cy = height as f32 / 2.0;
            let dx = x as f32 - cx;
            let dy = y as f32 - cy;
            let dist = (dx * dx + dy * dy).sqrt();

            if dist < 12.0 {
                // Green circle
                rgba[idx] = 76;      // R
                rgba[idx + 1] = 175; // G
                rgba[idx + 2] = 80;  // B
                rgba[idx + 3] = 255; // A
            } else if dist < 14.0 {
                // Dark green border
                rgba[idx] = 46;
                rgba[idx + 1] = 125;
                rgba[idx + 2] = 50;
                rgba[idx + 3] = 255;
            } else {
                // Transparent
                rgba[idx + 3] = 0;
            }
        }
    }

    let icon = tray_icon::Icon::from_rgba(rgba, width, height)?;
    Ok(icon)
}
