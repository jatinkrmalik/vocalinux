//! Audio device enumeration.

use anyhow::{Context, Result};
use cpal::traits::{DeviceTrait, HostTrait};
use tracing::{debug, warn};

/// Represents an audio input device
#[derive(Debug, Clone)]
pub struct AudioDevice {
    pub name: String,
    pub is_default: bool,
}

/// Get list of available audio input devices
pub fn get_input_devices() -> Result<Vec<AudioDevice>> {
    let host = cpal::default_host();
    let default_device = host.default_input_device();
    let default_name = default_device
        .as_ref()
        .and_then(|d| d.name().ok());

    let mut devices = Vec::new();

    match host.input_devices() {
        Ok(input_devices) => {
            for device in input_devices {
                match device.name() {
                    Ok(name) => {
                        let is_default = default_name.as_ref() == Some(&name);
                        debug!("Found input device: {} (default: {})", name, is_default);
                        devices.push(AudioDevice { name, is_default });
                    }
                    Err(e) => {
                        warn!("Failed to get device name: {}", e);
                    }
                }
            }
        }
        Err(e) => {
            warn!("Failed to enumerate input devices: {}", e);
        }
    }

    Ok(devices)
}

/// Get a CPAL device by name
pub fn get_device_by_name(name: &str) -> Result<cpal::Device> {
    let host = cpal::default_host();

    for device in host.input_devices().context("Failed to enumerate devices")? {
        if let Ok(device_name) = device.name() {
            if device_name == name {
                return Ok(device);
            }
        }
    }

    anyhow::bail!("Device not found: {}", name)
}

/// Get the default input device
pub fn get_default_device() -> Result<cpal::Device> {
    let host = cpal::default_host();
    host.default_input_device()
        .context("No default input device available")
}
