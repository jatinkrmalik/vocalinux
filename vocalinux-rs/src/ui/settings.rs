//! Settings dialog.

use std::sync::Arc;

use gtk4::prelude::*;
use gtk4::{
    Align, Box as GtkBox, Button, ComboBoxText, Entry, Grid, Label, Orientation,
    ProgressBar, Scale, SpinButton, Switch, Window,
};
use libadwaita as adw;
use libadwaita::prelude::*;
use parking_lot::Mutex;
use tracing::{error, info};

use crate::audio::get_input_devices;
use crate::config::{AppConfig, ModelSize, SpeechEngine};
use crate::speech::SpeechManager;

/// Settings dialog
pub struct SettingsDialog {
    config: Arc<Mutex<AppConfig>>,
    speech_manager: Arc<SpeechManager>,
}

impl SettingsDialog {
    pub fn new(config: Arc<Mutex<AppConfig>>, speech_manager: Arc<SpeechManager>) -> Self {
        Self {
            config,
            speech_manager,
        }
    }

    /// Show the settings dialog
    pub fn show(&self, parent: Option<&impl IsA<Window>>) {
        let dialog = adw::PreferencesWindow::builder()
            .title("Vocalinux Settings")
            .modal(true)
            .build();

        if let Some(parent) = parent {
            dialog.set_transient_for(Some(parent));
        }

        // Add preference pages
        dialog.add(&self.create_speech_page());
        dialog.add(&self.create_audio_page());
        dialog.add(&self.create_soniox_page());
        dialog.add(&self.create_ui_page());

        dialog.present();
    }

    /// Create speech recognition settings page
    fn create_speech_page(&self) -> adw::PreferencesPage {
        let page = adw::PreferencesPage::builder()
            .title("Speech")
            .icon_name("audio-input-microphone-symbolic")
            .build();

        // Engine selection group
        let engine_group = adw::PreferencesGroup::builder()
            .title("Recognition Engine")
            .description("Choose the speech recognition engine")
            .build();

        let engine_row = adw::ComboRow::builder()
            .title("Engine")
            .subtitle("Select speech recognition engine")
            .build();

        let engine_model = gtk4::StringList::new(&["VOSK (Offline)", "Whisper (Offline)", "Soniox (Cloud Realtime)"]);
        engine_row.set_model(Some(&engine_model));

        let current_engine = match self.config.lock().speech.engine {
            SpeechEngine::Vosk => 0,
            SpeechEngine::Whisper => 1,
            SpeechEngine::Soniox => 2,
        };
        engine_row.set_selected(current_engine);

        let config = self.config.clone();
        engine_row.connect_selected_notify(move |row| {
            let mut cfg = config.lock();
            cfg.speech.engine = match row.selected() {
                0 => SpeechEngine::Vosk,
                1 => SpeechEngine::Whisper,
                _ => SpeechEngine::Soniox,
            };
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        engine_group.add(&engine_row);

        // Language row
        let language_row = adw::ComboRow::builder()
            .title("Language")
            .subtitle("Recognition language")
            .build();

        let languages = gtk4::StringList::new(&[
            "English (US)", "Russian", "Spanish", "German", "French",
            "Italian", "Portuguese", "Chinese", "Hindi", "Auto-detect"
        ]);
        language_row.set_model(Some(&languages));

        engine_group.add(&language_row);

        // Model size row
        let model_row = adw::ComboRow::builder()
            .title("Model Size")
            .subtitle("Larger models are more accurate but slower")
            .build();

        let models = gtk4::StringList::new(&["Tiny", "Small", "Base", "Medium", "Large"]);
        model_row.set_model(Some(&models));

        let current_size = match self.config.lock().speech.model_size {
            ModelSize::Tiny => 0,
            ModelSize::Small => 1,
            ModelSize::Base => 2,
            ModelSize::Medium => 3,
            ModelSize::Large => 4,
        };
        model_row.set_selected(current_size);

        let config = self.config.clone();
        model_row.connect_selected_notify(move |row| {
            let mut cfg = config.lock();
            cfg.speech.model_size = match row.selected() {
                0 => ModelSize::Tiny,
                1 => ModelSize::Small,
                2 => ModelSize::Base,
                3 => ModelSize::Medium,
                _ => ModelSize::Large,
            };
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        engine_group.add(&model_row);

        // Download model button
        let download_row = adw::ActionRow::builder()
            .title("Download Model")
            .subtitle("Download the selected model for offline use")
            .build();

        let download_button = Button::builder()
            .label("Download")
            .valign(Align::Center)
            .build();

        download_row.add_suffix(&download_button);
        engine_group.add(&download_row);

        page.add(&engine_group);

        // VAD settings group
        let vad_group = adw::PreferencesGroup::builder()
            .title("Voice Activity Detection")
            .description("Settings for detecting speech")
            .build();

        let sensitivity_row = adw::ActionRow::builder()
            .title("Sensitivity")
            .subtitle("How sensitive to speech (1-5)")
            .build();

        let sensitivity_scale = Scale::with_range(Orientation::Horizontal, 1.0, 5.0, 1.0);
        sensitivity_scale.set_value(self.config.lock().speech.vad_sensitivity as f64);
        sensitivity_scale.set_width_request(200);
        sensitivity_scale.set_valign(Align::Center);

        let config = self.config.clone();
        sensitivity_scale.connect_value_changed(move |scale| {
            let mut cfg = config.lock();
            cfg.speech.vad_sensitivity = scale.value() as u8;
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        sensitivity_row.add_suffix(&sensitivity_scale);
        vad_group.add(&sensitivity_row);

        let silence_row = adw::ActionRow::builder()
            .title("Silence Timeout")
            .subtitle("Seconds of silence before processing")
            .build();

        let silence_spin = SpinButton::with_range(0.5, 5.0, 0.5);
        silence_spin.set_value(self.config.lock().speech.silence_timeout as f64);
        silence_spin.set_valign(Align::Center);

        let config = self.config.clone();
        silence_spin.connect_value_changed(move |spin| {
            let mut cfg = config.lock();
            cfg.speech.silence_timeout = spin.value() as f32;
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        silence_row.add_suffix(&silence_spin);
        vad_group.add(&silence_row);

        page.add(&vad_group);

        page
    }

    /// Create audio settings page
    fn create_audio_page(&self) -> adw::PreferencesPage {
        let page = adw::PreferencesPage::builder()
            .title("Audio")
            .icon_name("audio-card-symbolic")
            .build();

        let group = adw::PreferencesGroup::builder()
            .title("Audio Input")
            .description("Select microphone device")
            .build();

        let device_row = adw::ComboRow::builder()
            .title("Input Device")
            .subtitle("Select audio input device")
            .build();

        // Populate devices
        let mut device_names = vec!["Default".to_string()];
        if let Ok(devices) = get_input_devices() {
            for device in devices {
                device_names.push(device.name);
            }
        }

        let devices_model = gtk4::StringList::new(
            &device_names.iter().map(|s| s.as_str()).collect::<Vec<_>>()
        );
        device_row.set_model(Some(&devices_model));

        group.add(&device_row);

        // Test audio button
        let test_row = adw::ActionRow::builder()
            .title("Test Audio")
            .subtitle("Test the selected audio device")
            .build();

        let test_button = Button::builder()
            .label("Test")
            .valign(Align::Center)
            .build();

        test_row.add_suffix(&test_button);
        group.add(&test_row);

        page.add(&group);

        page
    }

    /// Create Soniox settings page
    fn create_soniox_page(&self) -> adw::PreferencesPage {
        let page = adw::PreferencesPage::builder()
            .title("Soniox")
            .icon_name("network-server-symbolic")
            .build();

        let group = adw::PreferencesGroup::builder()
            .title("Soniox Cloud Settings")
            .description("Configure Soniox realtime speech recognition")
            .build();

        // API Key row
        let api_key_row = adw::PasswordEntryRow::builder()
            .title("API Key")
            .build();

        // Show masked key if exists
        if self.config.lock().soniox.api_key.is_some() {
            api_key_row.set_text("••••••••••••••••");
        }

        let config = self.config.clone();
        api_key_row.connect_changed(move |entry| {
            let text = entry.text();
            if !text.is_empty() && !text.starts_with('•') {
                let mut cfg = config.lock();
                if let Err(e) = cfg.save_soniox_api_key(&text) {
                    error!("Failed to save API key: {}", e);
                }
            }
        });

        group.add(&api_key_row);

        // Test connection button
        let test_row = adw::ActionRow::builder()
            .title("Test Connection")
            .subtitle("Verify your API key works")
            .build();

        let test_button = Button::builder()
            .label("Test")
            .valign(Align::Center)
            .build();

        let config = self.config.clone();
        test_button.connect_clicked(move |button| {
            button.set_sensitive(false);
            button.set_label("Testing...");

            let api_key = config.lock().soniox.api_key.clone();

            if let Some(key) = api_key {
                // Test connection in background
                let button_clone = button.clone();
                glib::spawn_future_local(async move {
                    match crate::speech::soniox::test_connection(&key).await {
                        Ok(()) => {
                            button_clone.set_label("Success!");
                            info!("Soniox connection test successful");
                        }
                        Err(e) => {
                            button_clone.set_label("Failed");
                            error!("Soniox connection test failed: {}", e);
                        }
                    }
                    button_clone.set_sensitive(true);
                });
            } else {
                button.set_label("No API Key");
                button.set_sensitive(true);
            }
        });

        test_row.add_suffix(&test_button);
        group.add(&test_row);

        // Speaker diarization switch
        let diarization_row = adw::SwitchRow::builder()
            .title("Speaker Diarization")
            .subtitle("Identify different speakers")
            .active(self.config.lock().soniox.enable_speaker_diarization)
            .build();

        let config = self.config.clone();
        diarization_row.connect_active_notify(move |row| {
            let mut cfg = config.lock();
            cfg.soniox.enable_speaker_diarization = row.is_active();
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        group.add(&diarization_row);

        // Language identification switch
        let lang_id_row = adw::SwitchRow::builder()
            .title("Language Identification")
            .subtitle("Auto-detect spoken language")
            .active(self.config.lock().soniox.enable_language_identification)
            .build();

        let config = self.config.clone();
        lang_id_row.connect_active_notify(move |row| {
            let mut cfg = config.lock();
            cfg.soniox.enable_language_identification = row.is_active();
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        group.add(&lang_id_row);

        page.add(&group);

        // Info group
        let info_group = adw::PreferencesGroup::builder()
            .title("About Soniox")
            .build();

        let info_row = adw::ActionRow::builder()
            .title("Get API Key")
            .subtitle("Sign up at soniox.com to get your API key")
            .activatable(true)
            .build();

        info_row.connect_activated(|_| {
            let _ = open::that("https://soniox.com");
        });

        info_group.add(&info_row);
        page.add(&info_group);

        page
    }

    /// Create UI settings page
    fn create_ui_page(&self) -> adw::PreferencesPage {
        let page = adw::PreferencesPage::builder()
            .title("Interface")
            .icon_name("preferences-desktop-appearance-symbolic")
            .build();

        let group = adw::PreferencesGroup::builder()
            .title("General")
            .build();

        // Start minimized
        let minimized_row = adw::SwitchRow::builder()
            .title("Start Minimized")
            .subtitle("Start in system tray")
            .active(self.config.lock().ui.start_minimized)
            .build();

        let config = self.config.clone();
        minimized_row.connect_active_notify(move |row| {
            let mut cfg = config.lock();
            cfg.ui.start_minimized = row.is_active();
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        group.add(&minimized_row);

        // Show notifications
        let notifications_row = adw::SwitchRow::builder()
            .title("Show Notifications")
            .subtitle("Show desktop notifications")
            .active(self.config.lock().ui.show_notifications)
            .build();

        let config = self.config.clone();
        notifications_row.connect_active_notify(move |row| {
            let mut cfg = config.lock();
            cfg.ui.show_notifications = row.is_active();
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        group.add(&notifications_row);

        // Show partial results
        let partial_row = adw::SwitchRow::builder()
            .title("Show Partial Results")
            .subtitle("Show interim transcription while speaking")
            .active(self.config.lock().ui.show_partial_results)
            .build();

        let config = self.config.clone();
        partial_row.connect_active_notify(move |row| {
            let mut cfg = config.lock();
            cfg.ui.show_partial_results = row.is_active();
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        group.add(&partial_row);

        page.add(&group);

        // Shortcuts group
        let shortcuts_group = adw::PreferencesGroup::builder()
            .title("Keyboard Shortcuts")
            .build();

        let toggle_row = adw::ActionRow::builder()
            .title("Toggle Recognition")
            .subtitle("Press Ctrl twice to toggle")
            .build();

        let shortcut_label = Label::new(Some("Ctrl + Ctrl"));
        shortcut_label.add_css_class("dim-label");
        toggle_row.add_suffix(&shortcut_label);

        shortcuts_group.add(&toggle_row);
        page.add(&shortcuts_group);

        // About group
        let about_group = adw::PreferencesGroup::builder()
            .title("About")
            .build();

        let version_row = adw::ActionRow::builder()
            .title("Version")
            .subtitle(env!("CARGO_PKG_VERSION"))
            .build();

        about_group.add(&version_row);
        page.add(&about_group);

        page
    }
}
