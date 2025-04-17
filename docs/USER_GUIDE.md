# User Guide

This guide explains how to use Vocalinux effectively.

## Getting Started

After installing Vocalinux (see the [Installation Guide](INSTALL.md)), you can start the application from the terminal or add it to your startup applications.

## Basic Usage

### Starting and Stopping Voice Typing

1. **Launch the application**: Run `vocalinux` in a terminal or launch it from your application menu
2. **Find the tray icon**: Look for the microphone icon in your system tray
3. **Start voice typing**: Click the tray icon and select "Start Voice Typing" from the menu, or use the double-tap Ctrl keyboard shortcut
4. **Speak clearly**: As you speak, your words will be transcribed into the currently focused application
5. **Stop voice typing**: Click the tray icon and select "Stop Voice Typing" when you're done, or use the double-tap Ctrl keyboard shortcut again

### Understanding the Status Icons

- **Microphone off** (gray): Voice typing is inactive
- **Microphone on** (blue): Voice typing is active and listening
- **Microphone processing** (orange): Voice typing is processing your speech

## Voice Commands

Vocalinux supports several commands that you can speak to control formatting:

| Command | Action |
|---------|--------|
| "new line" or "new paragraph" | Inserts a line break |
| "period" or "full stop" | Types a period (.) |
| "comma" | Types a comma (,) |
| "question mark" | Types a question mark (?) |
| "exclamation point" or "exclamation mark" | Types an exclamation point (!) |
| "semicolon" | Types a semicolon (;) |
| "colon" | Types a colon (:) |
| "delete that" or "scratch that" | Deletes the last sentence |
| "capitalize" or "uppercase" | Capitalizes the next word |
| "all caps" | Makes the next word ALL CAPS |

## Tips for Better Recognition

1. **Use a good microphone**: A quality microphone significantly improves recognition accuracy
2. **Speak clearly**: Enunciate your words clearly but naturally
3. **Moderate pace**: Don't speak too quickly or too slowly
4. **Quiet environment**: Minimize background noise when possible
5. **Learn commands**: Familiarize yourself with voice commands for punctuation and formatting
6. **Use larger models**: For better accuracy, use `vocalinux --model medium` or `--model large`

## Customization

### Keyboard Shortcuts

Vocalinux supports global keyboard shortcuts for starting and stopping voice typing:

- **Double-tap Ctrl** (default): Quickly press the Ctrl key twice to toggle voice typing on or off
- **Custom shortcuts**: You can configure additional keyboard shortcuts if needed:
  1. Open the application settings from the tray icon menu
  2. Go to the "Shortcuts" tab
  3. Set your preferred keyboard shortcut

### Model Settings

You can change the speech recognition model for better accuracy or faster performance:

1. Open settings from the tray icon menu
2. Go to the "Recognition" tab
3. Select your preferred model size
4. Choose between VOSK (offline, faster) and Whisper (offline, more accurate)

## Troubleshooting

If you encounter issues, check the [Installation Guide](INSTALL.md) troubleshooting section or run the application with debug logging:

```bash
vocalinux --debug
```

Check the logs for error messages and possible solutions.
