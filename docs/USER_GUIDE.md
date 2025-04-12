# Vocalinux User Guide

This guide explains how to use Vocalinux effectively.

## Quick Start

1. Launch Vocalinux from your applications menu or by typing `vocalinux` in a terminal.
2. The application will appear as an icon in your system tray.
3. Press the keyboard shortcut (default: Alt+Shift+V) to start recording.
4. Speak clearly into your microphone.
5. Press the same shortcut again to stop recording and insert the transcribed text.

## Voice Commands

Vocalinux supports various voice commands to control text formatting and editing:

### Punctuation Commands

| Command | Result |
|---------|--------|
| "Period" | . |
| "Comma" | , |
| "Question mark" | ? |
| "Exclamation mark" | ! |
| "Colon" | : |
| "Semicolon" | ; |
| "Quote" or "Quotation mark" | " |
| "Single quote" | ' |
| "Open parenthesis" | ( |
| "Close parenthesis" | ) |
| "Open bracket" | [ |
| "Close bracket" | ] |

### Formatting Commands

| Command | Action |
|---------|--------|
| "New line" | Inserts a line break |
| "Tab" or "Indent" | Inserts a tab character |
| "Capitalize" | Capitalizes the next word |
| "Uppercase" | Converts to UPPERCASE |
| "Lowercase" | Converts to lowercase |
| "Bold" | Applies bold formatting (in supported applications) |
| "Italic" | Applies italic formatting (in supported applications) |
| "Underline" | Applies underline formatting (in supported applications) |

### Editing Commands

| Command | Action |
|---------|--------|
| "Delete" or "Remove" | Deletes the selected text or character before cursor |
| "Delete word" | Deletes the current word |
| "Delete line" | Deletes the current line |
| "Delete sentence" | Deletes the current sentence |
| "Delete paragraph" | Deletes the current paragraph |
| "Select word" | Selects the current word |
| "Select line" | Selects the current line |
| "Select sentence" | Selects the current sentence |
| "Select paragraph" | Selects the current paragraph |
| "Select all" | Selects all text |
| "Copy" | Copies selected text |
| "Cut" | Cuts selected text |
| "Paste" | Pastes from clipboard |
| "Undo" | Undoes last action |
| "Redo" | Redoes last undone action |

### Navigation Commands

| Command | Action |
|---------|--------|
| "Go to line [number]" | Moves cursor to specified line |
| "Move up [number]" | Moves cursor up |
| "Move down [number]" | Moves cursor down |
| "Move left [number]" | Moves cursor left |
| "Move right [number]" | Moves cursor right |

### Application Control

| Command | Action |
|---------|--------|
| "Save file" or "Save document" | Saves current file |
| "Stop listening" or "Stop dictation" | Stops voice recording |

## Configuration

Vocalinux can be configured in several ways:

### System Tray Menu

Right-click the Vocalinux icon in your system tray to access the menu:

- **Start/Stop Recognition**: Toggle voice recognition
- **Settings**: Open the configuration file
- **Help**: Open this user guide
- **About**: Show information about Vocalinux
- **Quit**: Exit the application

### Configuration File

The configuration file is located at `~/.config/vocalinux/config.json`. You can edit it with any text editor:

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

### Settings Explained

- **recognition**:
  - **engine**: Speech recognition engine to use ("vosk" or "whisper")
  - **model_size**: Model size to use ("small", "medium", "large")
  - **auto_punctuate**: Whether to add punctuation automatically
  - **vad_sensitivity**: Voice Activity Detection sensitivity (1-5)
  - **timeout**: Seconds of silence before stopping recognition

- **shortcuts**:
  - **toggle_recognition**: Keyboard shortcut to start/stop recognition

- **ui**:
  - **start_minimized**: Start the application minimized
  - **show_notifications**: Show desktop notifications
  - **audio_feedback**: Play sounds for recognition events

- **advanced**:
  - **debug_logging**: Enable debug logging
  - **wayland_mode**: Force Wayland compatibility mode

## Command Line Options

You can start Vocalinux with various command line options:

```bash
# Start with debug logging enabled
vocalinux --debug

# Use a specific speech recognition engine
vocalinux --engine whisper

# Use a specific model size
vocalinux --model medium

# Force Wayland compatibility mode
vocalinux --wayland
```

## Custom Sounds

You can customize the audio feedback by replacing the sound files in the `~/.local/share/vocalinux/sounds/` directory:

- `start_recording.mp3`: Played when recording starts
- `stop_recording.mp3`: Played when recording stops
- `error.mp3`: Played when an error occurs

Both MP3 and WAV formats are supported.

## Troubleshooting

### Recognition Not Working

- Check that your microphone is connected and working
- Try a different recognition engine: `vocalinux --engine whisper`
- Try a different model size: `vocalinux --model medium`

### Text Not Appearing

- Make sure the application window has focus when you stop dictation
- For Wayland users, try forcing Wayland mode: `vocalinux --wayland`
- Try typing some text manually to ensure the cursor is active

### Application Crashing

- Run with debug logging: `vocalinux --debug`
- Check the terminal output for error messages
- Ensure all dependencies are correctly installed

## Improving Recognition Accuracy

- Speak clearly and at a moderate pace
- Use good quality microphone
- Minimize background noise
- Position the microphone correctly
- Try a larger model size for better accuracy (at the cost of speed)

## Support and Feedback

If you encounter issues or have suggestions for improvements:

- Visit our GitHub repository: https://github.com/vocalinux/vocalinux
- Create an issue for bugs or feature requests
- Join our community discussions

Thank you for using Vocalinux!