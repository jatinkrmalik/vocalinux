# Vocalinux Flatpak Packaging

This directory contains the Flatpak manifest and AppStream metadata for building
Vocalinux as a Flatpak.

## Current Scope

The manifest targets the default `whisper_cpp` engine. The VOSK engine is not
included in this Flatpak yet because the PyPI `vosk` package only publishes
platform wheels, not a source distribution. A Flathub-ready VOSK module will need
to build VOSK and its native dependencies from source, or VOSK support should be
made an optional non-Flatpak feature.

Global keyboard shortcuts are also limited inside the sandbox. The Flatpak does
not request direct `/dev/input` access, so Wayland users should expect tray/menu
control and IBus text injection rather than evdev-based push-to-talk shortcuts.

## Local Build

Install the current GNOME runtime and SDK:

```bash
flatpak install flathub org.gnome.Platform//50 org.gnome.Sdk//50
```

Build from the repository root:

```bash
flatpak-builder \
  --force-clean \
  build-dir \
  packaging/flatpak/com.vocalinux.Vocalinux.yml
```

For a Flathub-style local build with screenshot mirroring and linter inputs:

```bash
flatpak-builder \
  --force-clean \
  --repo=repo \
  --compose-url-policy=full \
  --mirror-screenshots-url=https://dl.flathub.org/media \
  build-dir \
  packaging/flatpak/com.vocalinux.Vocalinux.yml
flatpak run --command=flatpak-builder-lint org.flatpak.Builder manifest packaging/flatpak/com.vocalinux.Vocalinux.yml
flatpak run --command=flatpak-builder-lint org.flatpak.Builder builddir build-dir
flatpak run --command=flatpak-builder-lint org.flatpak.Builder repo repo
```

Run without installing:

```bash
flatpak-builder --run build-dir packaging/flatpak/com.vocalinux.Vocalinux.yml vocalinux --debug
```

Install locally:

```bash
flatpak-builder \
  --user \
  --install \
  --force-clean \
  build-dir \
  packaging/flatpak/com.vocalinux.Vocalinux.yml
```

Launch after installing:

```bash
flatpak run com.vocalinux.Vocalinux --debug
```

## Python Dependencies

`python3-dependencies.yaml` is generated with `flatpak-pip-generator` and keeps
the build itself offline. Regenerate it when `pyproject.toml` dependencies change:

```bash
pipx run flatpak-pip-generator \
  --runtime org.gnome.Sdk//50 \
  --yaml \
  --ignore-pkg 'vosk>=0.3.45' "PyGObject; sys_platform == 'linux'" \
  --output packaging/flatpak/python3-dependencies \
  pywhispercpp pydub pynput evdev requests tqdm numpy pyaudio python-xlib psutil lxml \
  meson-python pyproject-metadata
```

`python3-build-dependencies.yaml` is kept as a small hand-maintained helper so
source builds that use `--no-build-isolation` can import `mesonpy` before NumPy
is built.

## Flathub Submission Notes

For a Flathub PR:

1. Change the `vocalinux` module source from `type: dir` to a tagged release:

   ```yaml
   sources:
     - type: git
       url: https://github.com/jatinkrmalik/vocalinux.git
       tag: v0.10.2-beta
       commit: <release-commit-sha>
   ```

2. Keep build-time network access disabled. The manifest should only download
   declared sources before the build starts.
3. Re-run AppStream validation and `flatpak-builder` locally.
4. Be ready to justify the sandbox permissions, especially D-Bus access for IBus
   and status notifier support.

## Manifest Details

- Runtime: `org.gnome.Platform//50`
- SDK: `org.gnome.Sdk//50`
- Microphone access: `--socket=pulseaudio`
- GPU access: `--device=dri`
- Model downloads: `--share=network`
- Text injection: `--talk-name=org.freedesktop.IBus`
- Tray/status notifier: `--talk-name=org.kde.StatusNotifierWatcher`

Configuration and model data use the standard Flatpak XDG directories under
`~/.var/app/com.vocalinux.Vocalinux/`.
