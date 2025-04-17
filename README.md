# <img src="https://github.com/user-attachments/assets/56dabe5c-5c65-44d5-a36a-429c9fea0719" width="50" height="50"> Vocalinux 

[![Vocalinux CI](https://github.com/jatinkrmalik/vocalinux/workflows/Vocalinux%20CI/badge.svg)](https://github.com/jatinkrmalik/vocalinux/actions?query=workflow%3A%22Vocalinux+CI%22)
[![codecov](https://codecov.io/gh/jatinkrmalik/vocalinux/branch/main/graph/badge.svg)](https://codecov.io/gh/jatinkrmalik/vocalinux)
[![Status: Early Development](https://img.shields.io/badge/Status-Early%20Development-orange)](https://github.com/jatinkrmalik/vocalinux)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/jatinkrmalik/vocalinux/issues)
[![GitHub issues](https://img.shields.io/github/issues/jatinkrmalik/vocalinux)](https://github.com/jatinkrmalik/vocalinux/issues)
[![GitHub release](https://img.shields.io/github/v/release/jatinkrmalik/vocalinux?include_prereleases)](https://github.com/jatinkrmalik/vocalinux/releases)

![Vocalinux Users](https://github.com/user-attachments/assets/e3d8dd16-3d4f-408c-b899-93d85e98b107)

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

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality and consistency. The hooks will automatically check your code for linting errors before each commit, which helps prevent CI pipeline failures.

To set up pre-commit hooks:

1. Install pre-commit: `pip install pre-commit`
2. Install the git hooks: `pre-commit install`

Now, when you try to commit changes, the pre-commit hooks will automatically run and check your code. If any issues are found, the commit will be blocked until you fix them.

To manually run all pre-commit hooks on all files:
```
pre-commit run --all-files
```

### Pre-commit Checks

The following checks are performed by pre-commit:
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Code style and error detection
- Various file checks (trailing whitespace, merge conflicts, etc.)

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
