# User Guide

This guide explains how to use Vocalinux effectively.

## Getting Started

After installing Vocalinux (see the [Installation Guide](INSTALL.md)), you can start the application from the terminal and optionally enable start-on-login.

## Start on Login (Autostart)

Vocalinux supports login autostart using the standard Linux desktop-session mechanism.

- **Where to enable it**:
  - First-run welcome dialog
  - Tray menu: **Start on Login**
  - Settings dialog: **Start on Login**
- **What Vocalinux creates**:
  - `vocalinux.desktop` in `$XDG_CONFIG_HOME/autostart/` or `~/.config/autostart/`
- **How it starts**:
  - As a regular user GUI app in your desktop session (`--start-minimized`)
- **What it does not do**:
  - It does not create a `systemd` service/unit for autostart

### Desktop Compatibility Notes

- Works on most mainstream desktop environments (GNOME, KDE, Xfce, Cinnamon, MATE, LXQt)
- On minimal/custom window managers, autostart may require an autostart manager or desktop-specific startup hook

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
6. **Use GPU acceleration**: If you have a GPU (AMD, Intel, or NVIDIA), whisper.cpp will automatically use it for faster transcription
7. **Choose the right model**: 
   - For real-time dictation: Use `tiny` or `base` (fastest)
   - For better accuracy: Use `vocalinux --model medium` or `--model large`
8. **Check debug logs**: Run `vocalinux --debug` to see which backend is being used (Vulkan, CUDA, or CPU)

## Customization

### Keyboard Shortcut

Vocalinux uses a double-tap Ctrl keyboard shortcut for starting and stopping voice typing:

- **Double-tap Ctrl**: Quickly press the Ctrl key twice to toggle voice typing on or off
- The time between taps should be less than 0.3 seconds to be recognized as a double-tap

### Model Settings

You can change the speech recognition engine and model for better accuracy or faster performance:

### Choosing Your Engine

Vocalinux now offers **three speech recognition engines**:

1. **whisper.cpp** ⭐ (Default) - High-performance C++ engine
   - Fastest installation (~1-2 min)
   - Works with AMD, Intel, NVIDIA GPUs via Vulkan
   - True multi-threading (no Python GIL)
   - Best for most users

2. **Whisper** (OpenAI) - PyTorch-based engine
   - NVIDIA GPU only (requires CUDA)
   - Larger download (~2.3GB with PyTorch)
   - Installation takes ~5-10 min
   - Use if you specifically need PyTorch features

3. **VOSK** - Lightweight engine
   - Smallest footprint (~40MB)
   - CPU only
   - Great for older systems or minimal resource usage

### Changing Engine and Model

1. Open settings from the tray icon menu (right-click)
2. Go to the "Recognition" tab
3. Select your **Speech Engine**:
   - whisper_cpp (recommended)
   - whisper
   - vosk
4. Select your **Model Size**:
   - **tiny** (~39MB) - Fastest, good for real-time dictation
   - **base** (~74MB) - Good balance
   - **small** (~244MB) - Better accuracy
   - **medium** (~769MB) - High accuracy
   - **large** (~1.5GB) - Best accuracy, slower

### When to Use Each Model

**For real-time dictation:** Use **tiny** or **base** - they're fast enough to keep up with your speech.

**For transcription:** Use **small** or **medium** - better accuracy for recorded audio.

**For maximum accuracy:** Use **large** - best results but requires more RAM and GPU power.

### GPU Acceleration

**whisper.cpp** automatically uses GPU acceleration when available:

- **Vulkan** (AMD, Intel, NVIDIA) - Automatically detected and used
- **CUDA** (NVIDIA only) - Fallback if Vulkan not available
- **CPU** - Always works as fallback

To check which backend is being used, look for these log messages when starting Vocalinux:
```
[INFO] whisper.cpp using Vulkan GPU backend: AMD Radeon RX 6800
[INFO] whisper.cpp configured with n_threads=16
```

## Troubleshooting

If you encounter issues, check the [Installation Guide](INSTALL.md) troubleshooting section or run the application with debug logging:

```bash
vocalinux --debug
```

Check the logs for error messages and possible solutions.
