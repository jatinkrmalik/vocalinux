# Vocalinux

A seamless voice dictation system for Linux, comparable to the built-in solutions on macOS and Windows.

## Overview

Vocalinux provides a user-friendly speech-to-text solution for Linux users with:

- Activation via customizable keyboard shortcuts (default: Alt+Shift+V)
- Real-time transcription with minimal latency
- Universal compatibility across applications
- Offline operation for privacy and reliability
- Visual indicators for microphone status
- Audio feedback for recognition status

## Technical Foundation

This project leverages existing open-source technologies:
- Speech recognition: VOSK API / Whisper
- Text injection: xdotool (X11) / ydotool/wtype (Wayland)
- User interface: GTK for system tray and settings
- Audio feedback: PulseAudio for sound notifications

## Project Structure

```
vocalinux/
├── docs/                      # Documentation
│   ├── INSTALL.md            # Installation guide
│   └── USER_GUIDE.md         # User guide with command reference
├── resources/                 # Resource files
│   └── sounds/               # Audio notification sounds
│       ├── start_recording.mp3  # Sound when recording starts
│       ├── stop_recording.mp3   # Sound when recording stops
│       └── error.mp3            # Sound when an error occurs
├── src/                       # Source code
│   ├── __init__.py           # Package initialization
│   ├── main.py               # Main entry point
│   ├── speech_recognition/   # Speech recognition components
│   │   ├── __init__.py
│   │   ├── command_processor.py  # Voice commands processor
│   │   └── recognition_manager.py  # Speech recognition engine management
│   ├── text_injection/       # Text injection components
│   │   ├── __init__.py
│   │   └── text_injector.py  # X11/Wayland text injection
│   └── ui/                   # User interface components
│       ├── __init__.py
│       ├── audio_feedback.py  # Audio notification system
│       ├── config_manager.py  # Configuration management
│       ├── keyboard_shortcuts.py  # Keyboard shortcut handling
│       └── tray_indicator.py  # System tray UI
├── tests/                     # Test suite
│   └── test_basic.py         # Basic unit tests
├── install.sh                 # Installation script
├── LICENSE                    # GPLv3 license
├── README.md                  # This file
├── setup.py                   # Python package configuration
└── vocalinux.desktop          # Desktop entry file
```

## Installation

### Prerequisites

- Ubuntu 22.04 or newer (may work on other Linux distributions)
- Python 3.6 or newer
- X11 or Wayland desktop environment

### Quick Install

```bash
# Clone the repository
git clone https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux

# Run the installer script
./install.sh
```

The installer will:
1. Install system dependencies
2. Set up Python dependencies
3. Configure the application
4. Create a desktop entry

For detailed installation instructions, see [docs/INSTALL.md](docs/INSTALL.md).

## Usage

### Starting the Application

After installation, you can start Vocalinux in several ways:

```bash
# From the terminal
vocalinux

# With debugging enabled
vocalinux --debug

# With a specific speech recognition engine
vocalinux --engine whisper

# With a specific model size
vocalinux --model medium
```

### Using Voice Dictation

1. Press the keyboard shortcut (default: Alt+Shift+V) to start recording
2. You'll hear a start sound when recording begins
3. Speak clearly into your microphone
4. Press the same shortcut again or pause speaking to stop recording
5. You'll hear a stop sound when recording ends

### Using Voice Commands

Vocalinux supports various voice commands for text formatting:

| Command | Action |
|---------|--------|
| "new line" | Inserts a line break |
| "period" | Types a period (.) |
| "comma" | Types a comma (,) |
| "question mark" | Types a question mark (?) |
| "delete that" | Deletes the last sentence |
| "capitalize" | Capitalizes the next word |

For a complete list of commands, see [docs/USER_GUIDE.md](docs/USER_GUIDE.md).

## Configuration

Configuration is stored in `~/.config/vocalinux/config.json` and includes:

```json
{
    "recognition": {
        "engine": "vosk",
        "model_size": "small",
        "auto_punctuate": true,
        "vad_sensitivity": 3,
        "timeout": 2.0
    },
    "shortcuts": {
        "toggle_recognition": "alt+shift+v"
    },
    "ui": {
        "start_minimized": false,
        "show_notifications": true,
        "audio_feedback": true
    },
    "advanced": {
        "debug_logging": false,
        "wayland_mode": false
    }
}
```

### Custom Sounds

You can customize the audio feedback by replacing the sound files in the `resources/sounds/` directory:

- `start_recording.mp3` - Played when recording starts
- `stop_recording.mp3` - Played when recording stops
- `error.mp3` - Played when an error occurs

Both MP3 and WAV formats are supported, with MP3 being the primary format.

## Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/jatinkrmalik/vocalinux.git
cd vocalinux

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/
```

### Key Components

1. **Speech Recognition Manager** (`src/speech_recognition/recognition_manager.py`)
   - Manages speech recognition engines (VOSK, Whisper)
   - Handles audio recording and voice activity detection
   - Processes recognition results

2. **Command Processor** (`src/speech_recognition/command_processor.py`)
   - Interprets voice commands in recognition results
   - Converts commands to text or actions

3. **Text Injector** (`src/text_injection/text_injector.py`)
   - Injects text into active applications
   - Supports both X11 and Wayland environments
   - Automatically falls back to XWayland when needed

4. **Audio Feedback** (`src/ui/audio_feedback.py`)
   - Provides audio cues for application states
   - Supports both MP3 and WAV formats
   - Uses system audio players (PulseAudio/ALSA)

5. **Tray Indicator** (`src/ui/tray_indicator.py`)
   - Provides system tray interface
   - Shows recognition status
   - Offers menu for control

6. **Keyboard Shortcut Manager** (`src/ui/keyboard_shortcuts.py`)
   - Manages global keyboard shortcuts
   - Enables activation from any application
   - Handles modifier key normalization

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src
```

## Roadmap

Future development plans include:

1. Custom icon design
2. Graphical settings dialog
3. Advanced voice commands for specific applications
4. Multi-language support
5. Better integration with popular applications
6. Improved model management
7. Customizable keyboard shortcuts via GUI
8. More audio feedback options

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.