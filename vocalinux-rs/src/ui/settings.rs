//! Settings dialog.

use std::cell::RefCell;
use std::rc::Rc;
use std::sync::Arc;

use gtk4::glib;
use gtk4::prelude::*;
use gtk4::{
    Align, Box as GtkBox, Button, Label, LevelBar, Orientation,
    ProgressBar, Scale, Separator, SpinButton,
};
use libadwaita as adw;
use libadwaita::prelude::*;
use parking_lot::Mutex;
use tracing::{debug, error, info};

use crate::audio::get_input_devices;
use crate::config::{AppConfig, ModelSize, SpeechEngine};
use crate::speech::{
    get_whisper_model, recommend_whisper_model, GpuInfo, SystemMemory,
    SpeechManager, WHISPER_LANGUAGES, WHISPER_MODELS,
};

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
    pub fn show(&self, parent: Option<&impl IsA<gtk4::Window>>) {
        let dialog = adw::PreferencesWindow::builder()
            .title("Vocalinux Settings")
            .modal(true)
            .build();

        if let Some(parent) = parent {
            dialog.set_transient_for(Some(parent));
        }

        // Add preference pages
        dialog.add(&self.create_speech_page());
        dialog.add(&self.create_whisper_page());
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

        let engine_model = gtk4::StringList::new(&[
            "VOSK (Offline)",
            "Whisper (Offline)",
            "Soniox (Cloud Realtime)"
        ]);
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
        page.add(&engine_group);

        // VAD settings group
        let vad_group = adw::PreferencesGroup::builder()
            .title("Voice Activity Detection")
            .description("Settings for detecting speech (VOSK/Whisper only)")
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

    /// Create Whisper-specific settings page with GPU info
    fn create_whisper_page(&self) -> adw::PreferencesPage {
        let page = adw::PreferencesPage::builder()
            .title("Whisper")
            .icon_name("applications-science-symbolic")
            .build();

        // Detect GPU info
        let gpu_info = GpuInfo::detect();
        let sys_memory = SystemMemory::detect();
        let recommendation = recommend_whisper_model(gpu_info.as_ref());

        // System Info Group
        let system_group = adw::PreferencesGroup::builder()
            .title("System Information")
            .description("GPU and memory status")
            .build();

        // GPU Status
        if let Some(ref gpu) = gpu_info {
            let gpu_row = adw::ActionRow::builder()
                .title("GPU")
                .subtitle(&gpu.name)
                .build();

            let cuda_label = Label::new(Some(&format!(
                "CUDA {}",
                gpu.cuda_version.as_deref().unwrap_or("N/A")
            )));
            cuda_label.add_css_class("success");
            gpu_row.add_suffix(&cuda_label);
            system_group.add(&gpu_row);

            // VRAM Usage
            let vram_row = adw::ActionRow::builder()
                .title("GPU Memory (VRAM)")
                .subtitle(&format!(
                    "{} MB used / {} MB total ({} MB free)",
                    gpu.used_memory_mb, gpu.total_memory_mb, gpu.free_memory_mb
                ))
                .build();

            let vram_bar = LevelBar::for_interval(0.0, gpu.total_memory_mb as f64);
            vram_bar.set_value(gpu.used_memory_mb as f64);
            vram_bar.set_width_request(150);
            vram_bar.set_valign(Align::Center);
            vram_row.add_suffix(&vram_bar);
            system_group.add(&vram_row);
        } else {
            let no_gpu_row = adw::ActionRow::builder()
                .title("GPU")
                .subtitle("No CUDA GPU detected - will use CPU")
                .build();

            let cpu_label = Label::new(Some("CPU Mode"));
            cpu_label.add_css_class("warning");
            no_gpu_row.add_suffix(&cpu_label);
            system_group.add(&no_gpu_row);
        }

        // System RAM
        let ram_row = adw::ActionRow::builder()
            .title("System Memory (RAM)")
            .subtitle(&format!(
                "{} MB available / {} MB total",
                sys_memory.available_mb, sys_memory.total_mb
            ))
            .build();

        if sys_memory.total_mb > 0 {
            let ram_bar = LevelBar::for_interval(0.0, sys_memory.total_mb as f64);
            ram_bar.set_value((sys_memory.total_mb - sys_memory.available_mb) as f64);
            ram_bar.set_width_request(150);
            ram_bar.set_valign(Align::Center);
            ram_row.add_suffix(&ram_bar);
        }
        system_group.add(&ram_row);

        page.add(&system_group);

        // Recommendation Group
        let rec_group = adw::PreferencesGroup::builder()
            .title("Recommendation")
            .build();

        let rec_row = adw::ActionRow::builder()
            .title(&format!("Recommended: {} model", recommendation.recommended_model.to_uppercase()))
            .subtitle(&recommendation.reason)
            .build();

        let mode_label = Label::new(Some(if recommendation.will_use_gpu {
            "GPU"
        } else {
            "CPU"
        }));
        mode_label.add_css_class(if recommendation.will_use_gpu { "success" } else { "warning" });
        rec_row.add_suffix(&mode_label);
        rec_group.add(&rec_row);

        let speed_row = adw::ActionRow::builder()
            .title("Expected Performance")
            .subtitle(recommendation.estimated_speed)
            .build();
        rec_group.add(&speed_row);

        page.add(&rec_group);

        // Model Selection Group
        let model_group = adw::PreferencesGroup::builder()
            .title("Model Selection")
            .description("Choose Whisper model size")
            .build();

        // Create model entries with VRAM requirements
        let model_names: Vec<String> = WHISPER_MODELS.iter().map(|m| {
            let gpu_fit = gpu_info.as_ref()
                .map(|g| g.can_fit_model(m.vram_required_mb))
                .unwrap_or(false);

            let status = if gpu_fit {
                "✓ GPU"
            } else if sys_memory.available_mb >= m.ram_required_mb {
                "○ CPU"
            } else {
                "✗ Low mem"
            };

            format!("{} [{}]", m.display_name, status)
        }).collect();

        let model_row = adw::ComboRow::builder()
            .title("Model")
            .subtitle("Larger = more accurate but slower")
            .build();

        let model_list = gtk4::StringList::new(
            &model_names.iter().map(|s| s.as_str()).collect::<Vec<_>>()
        );
        model_row.set_model(Some(&model_list));

        // Set current selection
        let current_size = match self.config.lock().speech.model_size {
            ModelSize::Tiny => 0,
            ModelSize::Base => 1,
            ModelSize::Small => 2,
            ModelSize::Medium => 3,
            ModelSize::Large => 4,
        };
        model_row.set_selected(current_size);

        let config = self.config.clone();
        model_row.connect_selected_notify(move |row| {
            let mut cfg = config.lock();
            cfg.speech.model_size = match row.selected() {
                0 => ModelSize::Tiny,
                1 => ModelSize::Base,
                2 => ModelSize::Small,
                3 => ModelSize::Medium,
                _ => ModelSize::Large,
            };
            if let Err(e) = cfg.save() {
                error!("Failed to save config: {}", e);
            }
        });

        model_group.add(&model_row);

        // Model info display
        let current_model = get_whisper_model(
            match self.config.lock().speech.model_size {
                ModelSize::Tiny => "tiny",
                ModelSize::Base => "base",
                ModelSize::Small => "small",
                ModelSize::Medium => "medium",
                ModelSize::Large => "large",
            }
        );

        if let Some(model) = current_model {
            let info_row = adw::ActionRow::builder()
                .title("Memory Requirements")
                .subtitle(&format!(
                    "GPU: {} MB VRAM | CPU: {} MB RAM",
                    model.vram_required_mb, model.ram_required_mb
                ))
                .build();
            model_group.add(&info_row);
        }

        // Download button
        let download_row = adw::ActionRow::builder()
            .title("Download Model")
            .subtitle("Download selected model for offline use")
            .build();

        let download_button = Button::builder()
            .label("Download")
            .valign(Align::Center)
            .build();

        download_row.add_suffix(&download_button);
        model_group.add(&download_row);

        page.add(&model_group);

        // Language Selection Group
        let lang_group = adw::PreferencesGroup::builder()
            .title("Language")
            .description("Whisper supports 99+ languages")
            .build();

        let lang_row = adw::ComboRow::builder()
            .title("Language")
            .subtitle("Select recognition language or auto-detect")
            .build();

        let lang_names: Vec<&str> = WHISPER_LANGUAGES.iter().map(|(_, name)| *name).collect();
        let lang_list = gtk4::StringList::new(&lang_names);
        lang_row.set_model(Some(&lang_list));

        // Find current language index
        let current_lang = &self.config.lock().speech.language;
        let lang_idx = WHISPER_LANGUAGES.iter()
            .position(|(code, _)| code == current_lang)
            .unwrap_or(0);
        lang_row.set_selected(lang_idx as u32);

        let config = self.config.clone();
        lang_row.connect_selected_notify(move |row| {
            let idx = row.selected() as usize;
            if let Some((code, _)) = WHISPER_LANGUAGES.get(idx) {
                let mut cfg = config.lock();
                cfg.speech.language = code.to_string();
                if let Err(e) = cfg.save() {
                    error!("Failed to save config: {}", e);
                }
            }
        });

        lang_group.add(&lang_row);

        // Language info
        let lang_info = adw::ActionRow::builder()
            .title("Auto-detect")
            .subtitle("Whisper can automatically detect the spoken language")
            .build();
        lang_group.add(&lang_info);

        page.add(&lang_group);

        // Refresh GPU button
        let refresh_group = adw::PreferencesGroup::new();

        let refresh_row = adw::ActionRow::builder()
            .title("Refresh GPU Information")
            .subtitle("Update GPU memory usage")
            .build();

        let refresh_button = Button::builder()
            .label("Refresh")
            .valign(Align::Center)
            .build();

        refresh_button.connect_clicked(move |_| {
            // In a real app, this would refresh the GPU info
            // For now, just show it would need to reload the dialog
            info!("GPU info refresh requested");
        });

        refresh_row.add_suffix(&refresh_button);
        refresh_group.add(&refresh_row);

        page.add(&refresh_group);

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

        // Soniox language hints
        let lang_group = adw::PreferencesGroup::builder()
            .title("Language Hints")
            .description("Improve accuracy by specifying expected languages")
            .build();

        let lang_row = adw::ComboRow::builder()
            .title("Primary Language")
            .subtitle("Main language you'll be speaking")
            .build();

        // Soniox supports many languages
        let soniox_langs = gtk4::StringList::new(&[
            "Auto-detect",
            "English",
            "Russian",
            "Spanish",
            "German",
            "French",
            "Chinese",
            "Japanese",
            "Korean",
            "Portuguese",
            "Italian",
            "Dutch",
            "Polish",
            "Turkish",
            "Arabic",
            "Hindi",
        ]);
        lang_row.set_model(Some(&soniox_langs));

        lang_group.add(&lang_row);
        page.add(&lang_group);

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

        let realtime_row = adw::ActionRow::builder()
            .title("Realtime Streaming")
            .subtitle("Text appears instantly as you speak (<200ms latency)")
            .build();

        let realtime_label = Label::new(Some("Live"));
        realtime_label.add_css_class("success");
        realtime_row.add_suffix(&realtime_label);
        info_group.add(&realtime_row);

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
