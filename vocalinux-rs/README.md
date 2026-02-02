# Vocalinux (Rust Edition)

Voice-controlled dictation for Linux, rewritten in Rust for better performance and easier distribution.

## Features

- **Multiple Speech Engines:**
  - **VOSK** - Offline recognition, supports 20+ languages
  - **Whisper** - High-accuracy offline recognition via whisper.cpp
  - **Soniox** - Cloud-based realtime recognition with <200ms latency

- **Native Performance:** Single binary, no Python dependencies
- **Modern UI:** GTK4 + libadwaita for a native GNOME look
- **System Tray:** Always accessible from your desktop
- **Wayland Support:** Works with wtype/ydotool on Wayland
- **Secure Storage:** API keys stored in system keyring

## Installation

### Building from Source

```bash
# Install dependencies (Ubuntu/Debian)
sudo apt install build-essential pkg-config \
    libgtk-4-dev libadwaita-1-dev \
    libasound2-dev libssl-dev \
    libappindicator3-dev libxdo-dev

# Build
cd vocalinux-rs
cargo build --release

# Install (optional)
sudo cp target/release/vocalinux /usr/local/bin/
```

### Feature Flags

Build with specific engines:

```bash
# Only Soniox (smallest binary, cloud-only)
cargo build --release --no-default-features --features soniox

# VOSK + Soniox (no Whisper)
cargo build --release --no-default-features --features "vosk,soniox"

# All engines (default)
cargo build --release
```

## Usage

1. Start Vocalinux - it will appear in your system tray
2. Press **Ctrl+Ctrl** (double tap Ctrl) to toggle dictation
3. Speak - text will be typed into the focused application
4. Press **Ctrl+Ctrl** again to stop

### Voice Commands

| Command | Action |
|---------|--------|
| "period" / "full stop" | . |
| "comma" | , |
| "question mark" | ? |
| "new line" | Enter |
| "new paragraph" | Double Enter |
| "delete that" | Undo last text |
| "undo" | Ctrl+Z |
| "redo" | Ctrl+Y |
| "copy" | Ctrl+C |
| "paste" | Ctrl+V |

### Using Soniox (Realtime Cloud)

1. Get an API key at [soniox.com](https://soniox.com)
2. Open Settings → Soniox
3. Enter your API key
4. Select "Soniox" as the engine

Soniox provides instant transcription as you speak (no waiting for silence).

## Configuration

Config file: `~/.config/vocalinux/config.json`

```json
{
  "speech": {
    "engine": "soniox",
    "language": "en-us",
    "model_size": "small",
    "vad_sensitivity": 3,
    "silence_timeout": 2.0
  },
  "audio": {
    "device_name": null
  },
  "soniox": {
    "enable_speaker_diarization": false,
    "enable_language_identification": false
  },
  "ui": {
    "start_minimized": false,
    "show_notifications": true,
    "show_partial_results": true
  }
}
```

## System Requirements

- Linux with X11 or Wayland
- GTK 4.12+
- libadwaita 1.4+
- ALSA or PulseAudio

### For text injection:

- **X11:** xdotool
- **Wayland:** wtype or ydotool

## Architecture

```
vocalinux-rs/
├── src/
│   ├── main.rs              # Entry point
│   ├── audio/               # Audio capture (cpal)
│   │   ├── capture.rs       # Audio recording
│   │   ├── devices.rs       # Device enumeration
│   │   └── vad.rs           # Voice Activity Detection
│   ├── speech/              # Speech recognition
│   │   ├── manager.rs       # Engine coordination
│   │   ├── soniox.rs        # Soniox WebSocket client
│   │   ├── vosk_engine.rs   # VOSK integration
│   │   ├── whisper_engine.rs # Whisper integration
│   │   └── command_processor.rs # Voice commands
│   ├── text_injection/      # Text input
│   │   └── injector.rs      # xdotool/wtype wrapper
│   ├── config/              # Configuration
│   │   └── mod.rs           # Config management
│   └── ui/                  # GTK4 interface
│       ├── app.rs           # Main application
│       ├── settings.rs      # Settings dialog
│       └── tray.rs          # System tray
└── Cargo.toml
```

## License

MIT License
