//! Main GTK4 application.

use std::cell::RefCell;
use std::rc::Rc;
use std::sync::Arc;
use std::thread;

use anyhow::Result;
use crossbeam_channel::Receiver;
use gtk4::prelude::*;
use gtk4::{glib, Application, ApplicationWindow};
use libadwaita as adw;
use libadwaita::prelude::*;
use parking_lot::Mutex;
use tracing::{debug, error, info};

use crate::config::AppConfig;
use crate::speech::{RecognitionState, SpeechManager, SpeechResult};
use crate::text_injection::TextInjector;

use super::settings::SettingsDialog;
use super::tray::TrayManager;

const APP_ID: &str = "com.vocalinux.Vocalinux";

/// Main Vocalinux application
pub struct VocalinuxApp {
    config: Arc<Mutex<AppConfig>>,
    speech_manager: Arc<SpeechManager>,
    text_injector: Arc<TextInjector>,
}

impl VocalinuxApp {
    pub fn new(config: AppConfig) -> Result<Self> {
        let config = Arc::new(Mutex::new(config));
        let speech_manager = Arc::new(SpeechManager::new(config.lock().clone())?);
        let text_injector = Arc::new(TextInjector::new()?);

        Ok(Self {
            config,
            speech_manager,
            text_injector,
        })
    }

    pub fn run(&self) {
        // Initialize GTK
        let app = adw::Application::builder()
            .application_id(APP_ID)
            .build();

        let config = self.config.clone();
        let speech_manager = self.speech_manager.clone();
        let text_injector = self.text_injector.clone();

        app.connect_activate(move |app| {
            Self::build_ui(app, config.clone(), speech_manager.clone(), text_injector.clone());
        });

        // Run the application
        app.run();
    }

    fn build_ui(
        app: &adw::Application,
        config: Arc<Mutex<AppConfig>>,
        speech_manager: Arc<SpeechManager>,
        text_injector: Arc<TextInjector>,
    ) {
        // Create main window (hidden by default - we use tray)
        let window = ApplicationWindow::builder()
            .application(app)
            .title("Vocalinux")
            .default_width(400)
            .default_height(300)
            .build();

        // Create tray manager
        let tray_manager = TrayManager::new(
            config.clone(),
            speech_manager.clone(),
        );

        // Set up speech result handler
        let result_receiver = speech_manager.get_result_receiver();
        let text_injector_clone = text_injector.clone();
        let config_clone = config.clone();

        // Spawn result handler thread
        thread::spawn(move || {
            Self::handle_speech_results(result_receiver, text_injector_clone, config_clone);
        });

        // Set up keyboard shortcut listener
        Self::setup_keyboard_shortcuts(speech_manager.clone());

        // Start tray
        if let Err(e) = tray_manager.start() {
            error!("Failed to start tray: {}", e);
        }

        // Show notification that app is running
        if config.lock().ui.show_notifications {
            notify_rust::Notification::new()
                .summary("Vocalinux")
                .body("Running in system tray. Press Ctrl+Ctrl to toggle dictation.")
                .icon("audio-input-microphone")
                .show()
                .ok();
        }

        // Keep window hidden if start_minimized
        if !config.lock().ui.start_minimized {
            // window.present();
        }
    }

    /// Handle speech recognition results
    fn handle_speech_results(
        receiver: Receiver<SpeechResult>,
        text_injector: Arc<TextInjector>,
        config: Arc<Mutex<AppConfig>>,
    ) {
        while let Ok(result) = receiver.recv() {
            match result {
                SpeechResult::Final(text) => {
                    debug!("Final text: {}", text);
                    if let Err(e) = text_injector.type_text(&text) {
                        error!("Failed to inject text: {}", e);
                    }
                }
                SpeechResult::Partial(text) => {
                    // Could show partial results in UI overlay
                    debug!("Partial text: {}", text);
                }
                SpeechResult::Action(action) => {
                    debug!("Action: {}", action);
                    if let Err(e) = text_injector.execute_action(&action) {
                        error!("Failed to execute action: {}", e);
                    }
                }
                SpeechResult::StateChange(state) => {
                    debug!("State changed: {:?}", state);
                    // Update tray icon based on state
                }
                SpeechResult::AudioLevel(level) => {
                    // Could update level indicator
                }
                SpeechResult::Error(msg) => {
                    error!("Speech error: {}", msg);
                    if config.lock().ui.show_notifications {
                        notify_rust::Notification::new()
                            .summary("Vocalinux Error")
                            .body(&msg)
                            .icon("dialog-error")
                            .show()
                            .ok();
                    }
                }
            }
        }
    }

    /// Set up global keyboard shortcuts
    fn setup_keyboard_shortcuts(speech_manager: Arc<SpeechManager>) {
        thread::spawn(move || {
            use rdev::{listen, Event, EventType, Key};

            let mut ctrl_press_time: Option<std::time::Instant> = None;
            let double_press_threshold = std::time::Duration::from_millis(500);

            let callback = move |event: Event| {
                if let EventType::KeyPress(Key::ControlLeft) | EventType::KeyPress(Key::ControlRight) = event.event_type {
                    let now = std::time::Instant::now();

                    if let Some(last_press) = ctrl_press_time {
                        if now.duration_since(last_press) < double_press_threshold {
                            // Double Ctrl press detected!
                            info!("Toggle recognition triggered");

                            if speech_manager.is_running() {
                                speech_manager.stop();
                            } else {
                                if let Err(e) = speech_manager.start() {
                                    error!("Failed to start recognition: {}", e);
                                }
                            }

                            ctrl_press_time = None;
                            return;
                        }
                    }

                    ctrl_press_time = Some(now);
                }
            };

            if let Err(e) = listen(callback) {
                error!("Failed to listen for keyboard events: {:?}", e);
            }
        });
    }
}
