# Updating Vocalinux

How to upgrade an existing install, plus release notes by version.

## Quick update

### Installed via the official installer

```bash
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh
bash /tmp/vl.sh
```

The installer detects a running instance, updates in place, preserves configuration and models, and pulls new dependencies (including neural VAD when available).

### Installed from source

```bash
cd vocalinux
git fetch origin
git checkout v0.15.0
./install.sh
```

Latest development tree:

```bash
cd vocalinux
git pull origin main
./install.sh
```

### Check your version

```bash
vocalinux --version
# or
python3 -c "import vocalinux; print(vocalinux.version.__version__)"
```

### Update problems

Clean reinstall (keeps config and models by default):

```bash
./uninstall.sh --keep-config --keep-data
curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh
bash /tmp/vl.sh
```

If an old process is stuck, stop via the tray or the PID in the instance lock file (do not use `pkill -f vocalinux`; it can kill unrelated processes):

```bash
kill "$(tr -d '[:space:]' < "${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux/instance.lock")"
# If you use IBus injection:
kill "$(tr -d '[:space:]' < "${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux-ibus/engine.pid")"
vocalinux
```

Missing system packages: see [INSTALL.md](INSTALL.md) or [DISTRO_COMPATIBILITY.md](DISTRO_COMPATIBILITY.md).

---

## What's new in v0.15.0

0.15.0 is a **minor** release on the stable line. It redesigns settings navigation, adds AppImage packages, expands the speech-language catalog (Hungarian and many more), cleans up continuous dictation spacing/capitalization, adds power/GPU controls, and improves Wayland IBus on compositors that ship `ibus-wayland`, on top of the 0.14 packaging work (Flatpak, AUR, configurable hotkeys).

### Highlights

| Feature | Description |
|---------|-------------|
| **Searchable settings** | Sidebar navigation with search replaces the seven-tab notebook (#601) |
| **AppImage** | Self-contained x86_64 and aarch64 builds attached to GitHub Releases (#573, #602) |
| **Language catalog** | ~33 selectable speech languages plus Auto-detect (incl. Hungarian); CLI choices derived from the same catalog; VOSK hides Whisper-only langs (#616, fixes #565) |
| **Dictation polish** | Auto-capitalize after `.` / `!` / `?`; append a trailing space after each completed utterance (#554, #608) |
| **Auto-pause + keep-alive** | Unload the model while configured apps run, or after an idle timeout (#592) |
| **Vulkan GPU selection** | Prefer a discrete GPU automatically; pick a device under Advanced settings (#590) |
| **ibus-wayland** | Prefer IBus on previously “unbridged” compositors when `ibus-wayland` is running (#614) |
| **CLI `--version`** | Print the installed version and exit (#563) |

### New Features

- **Searchable sidebar settings** — Topic pages in a sidebar with live search instead of seven notebook tabs (#601)
- **AppImage packaging** — Relocatable x86_64 and aarch64 AppImages built in the release workflow (#573, #602)
- **Expanded speech languages** — Hungarian plus many high-demand Whisper languages in Settings/CLI; official Alphacephei VOSK models where available; Whisper-only languages stay hidden in the VOSK dropdown (#616 by @jatinkrmalik, fixes #565)
- **Sidebar dictation controls** — Recognition status, mic level, Test Dictation, and Close stay visible in the settings sidebar footer while switching pages (#618)
- **Sentence capitalization** — Capitalize at the start of dictation and after sentence-ending punctuation (#554, closes #553)
- **Trailing space between utterances** — Completed transcriptions leave a trailing space so the next session does not glue onto the previous sentence (#608, fixes #605)
- **Auto-pause apps + model keep-alive** — Optional unload while selected processes run; idle timeout unload for battery/Optimus laptops (#592, closes #445, #591)
- **Vulkan discrete GPU auto-select + manual device** — Prefer discrete devices; override in Advanced settings (#590, closes #589)
- **IBus via ibus-wayland** — On compositors previously treated as unbridged, use IBus when `ibus-wayland` is available (#614 by @eiseleb47, closes #607)
- **`vocalinux --version`** — Print package version (#563, closes #555)

### Bug Fixes

- **Settings**: Restore Custom Shortcut entry / Record / Set controls after the sidebar settings refactor (#619)
- **Languages**: Map English (India) (`en-in`) to Whisper code `en` for whisper.cpp / Whisper / remote API (#617)
- **Audio**: Stop Bluetooth mic probing from corrupting the heap — one PortAudio open per capture session, stop-before-close, no stereo probe on mono-only devices (#599, fixes #567)
- **IBus**: Keep engine teardown correct when parent `do_destroy` fails (#613 by @eiseleb47, fixes #606)
- **Settings UI**: Flatten info notices so helper text matches the rest of the dialog (#615)
- **KDE Plasma Wayland**: Skip unbridged IBus when `ibus-wayland` is not present so injection does not silently fail (#577, fixes #574)
- **xdotool**: Preserve input focus after injection (#564, fixes #549)
- **Uninstall**: Remove IBus data dir; stop the app by PID file; remove `~/.local/bin` launcher wrappers reliably (#597, #569)
- **Installer**: Prefer both libgirepository 1.0 and 2.0 when present (#583, fixes #571)
- **AUR**: Virtual `python-pywhispercpp` dependency; clipboard/wtype tools as optdepends (#579, #586)
- **UI**: First-run dialog response without `Gtk.Dialog.do_response` (#580, fixes #566)
- **Vosk**: Italian and English-India entries in medium/large model tables (#551, fixes #550)
- **Docs**: Correct ydotool service setup guidance (#560, fixes #557)

### Docs / website

- Marketing site redesign with workstation craft (#582)
- Languages marketing page with honest per-engine badges (#616)
- Multi-distro tray icon FAQ (#584)
- robots.txt no longer blocks indexable pages (#610)
- Website CI lint / action warning cleanup (#611)

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.15.0).

---

## What's New in v0.14.2

0.14.2 is a stability patch on the **0.14 series**. The feature set is the same as 0.14.x; this release fixes IBus reliability and settings dialog sizing.

### 0.14 series highlights

| Feature | Description |
|---------|-------------|
| **Configurable Shortcuts** | Bind any modifier combination to a key — e.g. `Alt+R`, `Ctrl+Shift+V`, or `Super+F10` |
| **FunASR / SenseVoice Remote API** | Remote-API engine supports FunASR and SenseVoice via OpenAI-compatible endpoints |
| **Flatpak packaging** | Universal Flatpak (whisper.cpp) with sandbox-aware paths, global hotkeys, and Wayland paste injection |
| **AUR package** | Official Arch packaging and CI publish path |
| **Layout-aware hotkeys** | Combo keys respect non-US layouts |
| **Wayland / IBus reliability** | GNOME and KDE injection fixes, first-dictation FocusIn gate, engine process launch restored |
| **Audio / hybrid-CPU** | Recording device-index crash fixed; whisper.cpp no longer defaults to all cores on hybrid CPUs |

### Bug fixes in v0.14.2

- **IBus**: Restore engine process launch after the Flatpak XDG path import change. `start_engine_process` and the IBus component exec run `ibus_engine.py` by path, so the relative import failed with `ImportError` and Vocalinux fell back to ydotool/clipboard paste (#534)
- **IBus**: Wait for FocusIn before commit on scoped injection. Cold first activation on GNOME Wayland could commit before mutter bound a client context, so the first dictation of a session was dropped while logs still reported success (#533, fixes #523)
- **Settings UI**: Wrap each notebook tab in a vertical ScrolledWindow so the dialog fits 1080p monitors instead of growing past the screen; forward wheel events from unfocused combos/spins to the tab scroller and drop nested Advanced ScrolledWindow shadows (#538, #541)

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.14.2).

---

## What's New in v0.14.1

### Highlights

| Feature | Description |
|---------|-------------|
| **Flatpak packaging** | Universal Flatpak (whisper.cpp) with sandbox-aware paths, global hotkeys, and Wayland paste injection |
| **AUR package** | Official Arch packaging and CI publish path |
| **Layout-aware hotkeys** | Combo keys respect non-US layouts |
| **Installer / injection fixes** | `sg` on Ubuntu 26.04/Debian 13; XIM `none` treated as unset |

### New Features

- **Flatpak packaging** — GNOME Platform 50, whisper.cpp + Vulkan, ydotool/wl-copy injection, evdev global shortcuts; build via `packaging/flatpak/` (#484, closes #167)
- **AUR release package** — PKGBUILD and CI publish for Arch Linux (#518)

### Bug Fixes

- **Hotkeys**: Layout-aware combo keys for non-US layouts (#514)
- **Installer**: `sg` not found on Ubuntu 26.04 / Debian 13 (#524)
- **Text injection**: Treat XIM `none` as unset (#512)
- **Web**: Dependabot npm alerts in package-lock (#515)

### Docs

- Refreshed v0.14 UI screenshots and website gallery (#521)
- README Star History and related polish

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.14.1).

---

## What's New in v0.14.0-beta

### Highlights

| Feature | Description |
|---------|-------------|
| **Configurable Shortcuts** | Bind any modifier combination to a key — e.g. `Alt+R`, `Ctrl+Shift+V`, or `Super+F10` |
| **FunASR / SenseVoice Remote API** | Remote-API engine now supports FunASR and SenseVoice models via OpenAI-compatible endpoints |
| **GNOME Wayland IBus Reliability** | Text injection works again on GNOME Wayland with bare `xkb` layouts and engine restore fallbacks are fixed |
| **Audio Crash Fix** | Recording no longer crashes when the system audio device index changes between sessions |
| **Hybrid-CPU Efficiency** | whisper.cpp no longer defaults to all cores on hybrid Intel/AMD processors |

### New features

- **Configurable modifier+key hotkeys** — The Settings dialog now lets you set custom shortcuts using any combination of Ctrl, Alt, Shift, and Super plus a letter/number key. The legacy defaults still work, and you can now bind combinations like `Alt+R` or `Ctrl+Shift+V` (#493)
- **Remote API FunASR/SenseVoice support** — OpenAI-compatible remote endpoints can specify FunASR/SenseVoice model names (e.g. `sensevoice`) and return richer response shapes; SenseVoice metadata labels are stripped before text injection (#468)

### Bug fixes

- **GNOME Wayland/IBus**: Restore text injection when only a bare `xkb` engine is configured; the engine restore fallback now picks the correct IM engine instead of silently dropping text (#506, #500)
- **KDE Wayland/IBus**: Restore the KDE Plasma Wayland IBus text-injection path that was regressed in recent compositor-detection changes (#502)
- **Wayland injection**: Wait for held modifiers (Ctrl/Alt/Shift/Super) to release before injecting text, preventing accidental shortcut triggers and garbled output on modifier-heavy workflows (#494)
- **Shortcuts UI**: Keep preset and custom shortcut selection exclusive — selecting a preset now clears the custom field, and setting a custom combo selects the "Custom Shortcut" preset (#509)
- **whisper.cpp**: Stop defaulting to all CPU cores on hybrid processors (Intel Performance + Efficient cores), which caused UI lag and excess battery drain (#492)
- **Audio**: Fix a crash on recording start when the selected audio device index no longer matches the current system enumeration (#499)
- **Installer**: Include `xsel` as a fallback for the Wayland clipboard path when `xclip` is unavailable (#496)

### Improvements

- **Code style** — Removed an outdated long comment about whisper.cpp default thread counts (#505)

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.14.0-beta).

---

## What's New in v0.13.0-beta

### Highlights

| Feature | Description |
|---------|-------------|
| **Guided Whisper models** | Pick a whisper.cpp size and specialization (English-only, quantized, Turbo) with in-app guidance |
| **Hotplug keyboard support** | Shortcuts keep working on keyboards connected after startup |
| **Dictation spacing** | Spacing preserved between speech segments separated by a pause in the same session |
| **Wayland reliability** | Fixes silent text drops on wlroots/COSMIC compositors and garbled non-US-layout output |

### New features

- **Guided whisper.cpp model variants** — The Settings dialog now splits whisper.cpp selection into **Model Size** and **Specialization**, exposing English-only, quantized (Q5/Q8), Large v3 Turbo, and legacy large models with language-aware recommendations and hover guidance. Exact model IDs (e.g. `medium.en-q5_0`, `large-v3-turbo`) can also be passed to `--model` (#465)

### Bug fixes

- **Dictation**: Preserve spacing between speech segments separated by a pause (#464)
- **Shortcuts**: Rescan for hotplugged keyboards so shortcuts work on devices connected after startup (#467)
- **KDE Plasma Wayland**: Detect KDE Plasma Wayland sessions and guide you to enable IBus Wayland when `wtype` injection fails (#466)
- **Wayland**: Fix garbled output on non-US keyboard layouts and a clipboard-copy hang; ydotool now pastes through the clipboard (#480)
- **Wayland/IBus**: Use wtype/ydotool instead of IBus on compositors that don't bridge IBus to native apps like COSMIC, Sway, and Hyprland (#486)
- **Wayland/IBus**: Require a real IM engine on Wayland so a bare `xkb` layout no longer causes silent text drops on GNOME/Mutter and similar (#478)
- **Wayland**: Preserve the keyboard layout on Wayland by not running `setxkbmap` (was flipping XWayland apps to `us`) (#474)
- **UI**: Cap the settings dialog height on high-resolution displays (#465)

### Improvements

- **Performance**: Faster ydotool text injection via an explicit `--key-delay` (#488)
- **Website**: New documentation pages for Remote API, Silero VAD, advanced whisper.cpp settings, and desktop reliability (#470)
- **CI**: Automatic pull-request labeling by changed files (#473)

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.13.0-beta).

---

## What's New in v0.12.0-beta

### Highlights

| Feature | Description |
|---------|-------------|
| **Remote API engine** | Backend for compatible remote transcription services |
| **Silero VAD** | Neural VAD drops silence-only buffers for cleaner dictation |
| **Thread safety** | Hardened Remote API, IBus, and text injection threading |
| **IBus reliability** | Preserves user engines for dead keys and scoped activation |
| **Settings polish** | Advanced-only Remote Server controls and lower dialog height |
| **Installer and models** | CUDA auto-remediation and corrected model download metadata |

### New features

- **Remote API speech recognition engine** — Configure compatible remote transcription services alongside local engines (#335)
- **Silero VAD** — Neural voice activity detection filters silence-only buffers when ONNX Runtime support is installed (#447)

### Bug fixes

- **Threading**: Harden Remote API, IBus, and text injection thread safety (#452)
- **IBus**: Preserve user engines for dead keys and capture the current engine during scoped activation (#457, #458)
- **UI**: Keep the Remote Server section behind the Advanced toggle and reduce settings dialog height (#454, #456)
- **Installer**: Harden CUDA diagnostics with auto-remediation and behavioral tests (#451)
- **Models**: Correct whisper.cpp and VOSK download size metadata (#453)
- **Startup**: Allow launch without the pynput backend (#448)
- **Website**: Clarify speech demo browser support (#449)

### Improvements

- **Developer docs** — Remote API test server instructions for backend testing (#455)
- **Community** — GitHub Sponsors funding configuration added
- **Behavioral coverage** — CUDA diagnostics and release-facing reliability fixes include targeted tests

See the [full changelog](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.12.0-beta).

---

## Older releases (v0.8–v0.11)

Detailed notes for v0.11 and earlier live on GitHub Releases:

- [v0.11.0-beta](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.11.0-beta)
- [v0.10.2-beta](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.10.2-beta)
- [v0.10.1-beta](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.10.1-beta)
- [v0.10.0-beta](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.10.0-beta)
- [v0.9.0-beta](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.9.0-beta)
- [v0.8.0-beta](https://github.com/jatinkrmalik/vocalinux/releases/tag/v0.8.0-beta)

Full history: https://github.com/jatinkrmalik/vocalinux/releases

---

## Need help?

- [Installation guide](INSTALL.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [User guide](USER_GUIDE.md)
- [Support](../SUPPORT.md)
- [Report issues](https://github.com/jatinkrmalik/vocalinux/issues)
- [Discussions](https://github.com/jatinkrmalik/vocalinux/discussions)
