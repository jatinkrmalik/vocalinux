# User guide

How to use Vocalinux day to day. Install first: [INSTALL.md](INSTALL.md).

## Getting started

1. Launch Vocalinux (`vocalinux` or the application menu)
2. Find the microphone icon in the system tray
3. Start dictation with the tray menu or your keyboard shortcut
4. Speak into the focused application; text is injected when an utterance completes
5. Stop with the same shortcut (toggle) or by releasing the key (push-to-talk)

### Start on login

Enable **Start on Login** from the first-run dialog, tray menu, or Settings. Vocalinux writes an XDG autostart entry (`~/.config/autostart/vocalinux.desktop`) and starts as a normal user app (`--start-minimized`). It does not create a systemd service.

Works on common desktop environments (GNOME, KDE, Xfce, Cinnamon, MATE, LXQt). Minimal window-manager sessions may need their own autostart helper.

### Status icons

| Icon state | Meaning |
|------------|---------|
| Gray (off) | Inactive |
| Blue (on) | Listening |
| Orange | Processing speech |

### Dictation formatting

Vocalinux capitalizes the start of dictation and letters after `.`, `!`, or `?`. Each completed utterance leaves a trailing space so the next session does not glue onto the previous sentence.

## Shortcuts

Configure under **Settings → Shortcuts**:

| Mode | Behavior |
|------|----------|
| **Toggle** (default) | Double-tap the shortcut key (Ctrl by default) to start/stop |
| **Push-to-talk** | Hold the shortcut while speaking; release to stop |

Left/right modifier keys and custom modifier+key combos (for example `Alt+R`) are supported.

## Voice commands

Optional spoken commands for punctuation and editing (English phrases; can be disabled in Settings):

| Command | Action |
|---------|--------|
| "new line" / "new paragraph" | Line break |
| "period" / "full stop" | `.` |
| "comma" | `,` |
| "question mark" | `?` |
| "exclamation point" / "exclamation mark" | `!` |
| "semicolon" | `;` |
| "colon" | `:` |
| "delete that" / "scratch that" | Delete last sentence |
| "capitalize" / "uppercase" | Capitalize next word |
| "all caps" | Next word in ALL CAPS |

## Engines and models

Open **Settings → Speech Engine** (sidebar search works).

### Engines

| Engine | Best for | GPU | Footprint |
|--------|----------|-----|-----------|
| **whisper.cpp** (default) | Most users | Vulkan (AMD, Intel, NVIDIA) | ~74MB default model |
| **Whisper** (OpenAI) | PyTorch/CUDA workflows | NVIDIA/CUDA | Large (PyTorch stack) |
| **VOSK** | Low RAM / older machines | CPU | ~40MB |
| **Remote API** | Offload to a server | N/A (server-side) | Opt-in; see [HTTP_REMOTE.md](HTTP_REMOTE.md) |

### Model size (whisper.cpp / Whisper)

| Size | Approx. size | Tradeoff |
|------|--------------|----------|
| tiny | ~74MB | Fastest; real-time friendly |
| base | ~141MB | Balance of speed and accuracy |
| small | ~465MB | Better accuracy |
| medium | ~1.5GB | High accuracy |
| large | ~3.0GB | Best accuracy; heavier |

For whisper.cpp, also pick a **Specialization**: standard multilingual, English-only, quantized (lower memory), Turbo, or legacy large. English-only specializations limit the language selector to English. Exact IDs (for example `medium.en-q5_0`, `large-v3-turbo`) work with `--model`.

### GPU

whisper.cpp prefers Vulkan when available, then other backends, then CPU. On multi-GPU machines a discrete device is preferred; override under **Advanced** (`whispercpp_gpu_device`). Check logs with `vocalinux --debug`.

### Auto-pause and keep-alive

Under Settings:

- **Auto-pause apps** — unload the model while listed apps run
- **Model keep-alive** — unload after idle timeout to free GPU/CPU

## Tips for better recognition

1. Use a decent microphone and reduce background noise when you can
2. Speak clearly at a natural pace
3. Prefer `tiny`/`base` for snappy dictation; larger models when accuracy matters more than latency
4. English-only or quantized specializations help when they match your use case
5. Confirm Vulkan/CUDA in debug logs if transcription is slower than expected

## CLI

```bash
vocalinux --help
vocalinux --version
vocalinux --debug
vocalinux --engine whisper_cpp
vocalinux --model medium.en-q5_0
vocalinux --wayland
vocalinux --start-minimized
```

## Troubleshooting

Run with debug logging:

```bash
vocalinux --debug
```

Install, audio, tray, and injection issues: [INSTALL.md](INSTALL.md) troubleshooting section. Distro-specific notes: [DISTRO_COMPATIBILITY.md](DISTRO_COMPATIBILITY.md). Updates: [UPDATE.md](UPDATE.md).

Still stuck? [GitHub Issues](https://github.com/jatinkrmalik/vocalinux/issues) or [Discussions](https://github.com/jatinkrmalik/vocalinux/discussions).
