//! Text injection implementation.
//!
//! Supports X11 (via xdotool) and Wayland (via wtype/ydotool).

use std::process::Command;

use anyhow::{Context, Result};
use tracing::{debug, info, warn};

/// Display server type
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DisplayServer {
    X11,
    Wayland,
}

impl DisplayServer {
    /// Detect current display server from environment
    pub fn detect() -> Self {
        if let Ok(session_type) = std::env::var("XDG_SESSION_TYPE") {
            match session_type.to_lowercase().as_str() {
                "wayland" => return DisplayServer::Wayland,
                "x11" => return DisplayServer::X11,
                _ => {}
            }
        }

        // Fallback: check for WAYLAND_DISPLAY
        if std::env::var("WAYLAND_DISPLAY").is_ok() {
            return DisplayServer::Wayland;
        }

        // Default to X11
        DisplayServer::X11
    }
}

/// Text injector for typing text into applications
pub struct TextInjector {
    display_server: DisplayServer,
    /// Preferred Wayland tool (wtype, ydotool, or xdotool for XWayland)
    wayland_tool: Option<WaylandTool>,
}

#[derive(Debug, Clone, Copy)]
enum WaylandTool {
    Wtype,
    Ydotool,
    XdotoolFallback,
}

impl TextInjector {
    /// Create a new text injector
    pub fn new() -> Result<Self> {
        let display_server = DisplayServer::detect();
        info!("Detected display server: {:?}", display_server);

        let wayland_tool = if display_server == DisplayServer::Wayland {
            Self::detect_wayland_tool()
        } else {
            None
        };

        if display_server == DisplayServer::Wayland {
            match wayland_tool {
                Some(WaylandTool::Wtype) => info!("Using wtype for text injection"),
                Some(WaylandTool::Ydotool) => info!("Using ydotool for text injection"),
                Some(WaylandTool::XdotoolFallback) => {
                    warn!("Using xdotool (XWayland fallback) for text injection")
                }
                None => warn!("No Wayland text injection tool available"),
            }
        } else {
            // Check if xdotool is available
            if !Self::command_exists("xdotool") {
                warn!("xdotool not found - text injection may not work");
            }
        }

        Ok(Self {
            display_server,
            wayland_tool,
        })
    }

    /// Create injector with forced display server setting
    pub fn with_display_server(display_server: DisplayServer) -> Result<Self> {
        let wayland_tool = if display_server == DisplayServer::Wayland {
            Self::detect_wayland_tool()
        } else {
            None
        };

        Ok(Self {
            display_server,
            wayland_tool,
        })
    }

    /// Detect available Wayland tool
    fn detect_wayland_tool() -> Option<WaylandTool> {
        if Self::command_exists("wtype") {
            Some(WaylandTool::Wtype)
        } else if Self::command_exists("ydotool") {
            Some(WaylandTool::Ydotool)
        } else if Self::command_exists("xdotool") {
            Some(WaylandTool::XdotoolFallback)
        } else {
            None
        }
    }

    /// Check if a command exists
    fn command_exists(cmd: &str) -> bool {
        Command::new("which")
            .arg(cmd)
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false)
    }

    /// Type text into the focused application
    pub fn type_text(&self, text: &str) -> Result<()> {
        if text.is_empty() {
            return Ok(());
        }

        debug!("Injecting text: {:?}", text);

        match self.display_server {
            DisplayServer::X11 => self.type_text_x11(text),
            DisplayServer::Wayland => self.type_text_wayland(text),
        }
    }

    /// Type text using X11 (xdotool)
    fn type_text_x11(&self, text: &str) -> Result<()> {
        let status = Command::new("xdotool")
            .args(["type", "--clearmodifiers", "--", text])
            .status()
            .context("Failed to run xdotool")?;

        if !status.success() {
            anyhow::bail!("xdotool failed with status: {}", status);
        }

        Ok(())
    }

    /// Type text using Wayland tools
    fn type_text_wayland(&self, text: &str) -> Result<()> {
        match self.wayland_tool {
            Some(WaylandTool::Wtype) => {
                let output = Command::new("wtype")
                    .arg("--")
                    .arg(text)
                    .output()
                    .context("Failed to run wtype")?;

                if !output.status.success() {
                    let stderr = String::from_utf8_lossy(&output.stderr);
                    anyhow::bail!("wtype failed: {}", stderr);
                }
            }
            Some(WaylandTool::Ydotool) => {
                let status = Command::new("ydotool")
                    .args(["type", "--", text])
                    .status()
                    .context("Failed to run ydotool")?;

                if !status.success() {
                    anyhow::bail!("ydotool failed with status: {}", status);
                }
            }
            Some(WaylandTool::XdotoolFallback) => {
                // Use xdotool through XWayland
                self.type_text_x11(text)?;
            }
            None => {
                anyhow::bail!(
                    "No Wayland text injection tool available. \
                    Please install wtype or ydotool."
                );
            }
        }

        Ok(())
    }

    /// Send a key combination (e.g., "ctrl+z" for undo)
    pub fn send_keys(&self, keys: &str) -> Result<()> {
        debug!("Sending keys: {}", keys);

        match self.display_server {
            DisplayServer::X11 => self.send_keys_x11(keys),
            DisplayServer::Wayland => self.send_keys_wayland(keys),
        }
    }

    /// Send keys using X11 (xdotool)
    fn send_keys_x11(&self, keys: &str) -> Result<()> {
        let status = Command::new("xdotool")
            .args(["key", "--clearmodifiers", keys])
            .status()
            .context("Failed to run xdotool key")?;

        if !status.success() {
            anyhow::bail!("xdotool key failed with status: {}", status);
        }

        Ok(())
    }

    /// Send keys using Wayland tools
    fn send_keys_wayland(&self, keys: &str) -> Result<()> {
        // Convert key notation (e.g., "ctrl+z") to tool-specific format
        match self.wayland_tool {
            Some(WaylandTool::Wtype) => {
                // wtype uses -M for modifiers and -k for keys
                let (modifiers, key) = Self::parse_key_combo(keys);
                let mut cmd = Command::new("wtype");

                for modifier in &modifiers {
                    cmd.arg("-M").arg(modifier);
                }

                cmd.arg("-k").arg(&key);

                for modifier in modifiers.iter().rev() {
                    cmd.arg("-m").arg(modifier);
                }

                let output = cmd.output().context("Failed to run wtype")?;
                if !output.status.success() {
                    let stderr = String::from_utf8_lossy(&output.stderr);
                    anyhow::bail!("wtype failed: {}", stderr);
                }
            }
            Some(WaylandTool::Ydotool) => {
                let status = Command::new("ydotool")
                    .args(["key", keys])
                    .status()
                    .context("Failed to run ydotool key")?;

                if !status.success() {
                    anyhow::bail!("ydotool key failed with status: {}", status);
                }
            }
            Some(WaylandTool::XdotoolFallback) => {
                self.send_keys_x11(keys)?;
            }
            None => {
                anyhow::bail!("No Wayland key injection tool available");
            }
        }

        Ok(())
    }

    /// Parse key combination into modifiers and key
    fn parse_key_combo(keys: &str) -> (Vec<String>, String) {
        let parts: Vec<&str> = keys.split('+').collect();
        if parts.len() == 1 {
            return (vec![], parts[0].to_string());
        }

        let modifiers: Vec<String> = parts[..parts.len() - 1]
            .iter()
            .map(|&s| s.to_lowercase())
            .collect();
        let key = parts.last().unwrap().to_string();

        (modifiers, key)
    }

    /// Execute an action command
    pub fn execute_action(&self, action: &str) -> Result<()> {
        debug!("Executing action: {}", action);

        match action {
            "delete_that" | "scratch_that" => {
                // Could implement smarter deletion based on last text
                // For now, just send backspace
                self.send_keys("BackSpace")?;
            }
            "undo" | "undo_that" => {
                self.send_keys("ctrl+z")?;
            }
            "redo" | "redo_that" => {
                self.send_keys("ctrl+y")?;
            }
            "select_all" => {
                self.send_keys("ctrl+a")?;
            }
            "copy" | "copy_that" => {
                self.send_keys("ctrl+c")?;
            }
            "cut" | "cut_that" => {
                self.send_keys("ctrl+x")?;
            }
            "paste" | "paste_that" => {
                self.send_keys("ctrl+v")?;
            }
            _ => {
                warn!("Unknown action: {}", action);
            }
        }

        Ok(())
    }

    /// Get display server
    pub fn display_server(&self) -> DisplayServer {
        self.display_server
    }
}

impl Default for TextInjector {
    fn default() -> Self {
        Self::new().unwrap_or(Self {
            display_server: DisplayServer::X11,
            wayland_tool: None,
        })
    }
}
