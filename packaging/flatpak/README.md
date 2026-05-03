# Vocalinux Flatpak Packaging

This directory contains the Flatpak manifest and metadata for distributing
Vocalinux via [Flathub](https://flathub.org).

## Quick Start (Local Build)

### Prerequisites

Install the Flatpak runtime and SDK:

```bash
flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46
```

### Build

The manifest is configured for **local testing** (`type: dir` with `path: .`) so it
builds from your current checkout rather than cloning from GitHub. It also enables
`network: true` during build so `pip` can download Python dependencies from PyPI.

From the repository root:

```bash
flatpak-builder \
  --force-clean \
  build-dir \
  packaging/flatpak/com.vocalinux.Vocalinux.yml
```

### Run (without installing)

```bash
flatpak-builder --run build-dir packaging/flatpak/com.vocalinux.Vocalinux.yml vocalinux
```

### Install locally

```bash
flatpak-builder \
  --user \
  --install \
  --force-clean \
  build-dir \
  packaging/flatpak/com.vocalinux.Vocalinux.yml
```

Then launch:

```bash
flatpak run com.vocalinux.Vocalinux
```

## Flathub Submission

To publish on Flathub, follow the official
[Flathub Submission Documentation](https://docs.flathub.org/docs/for-app-authors/submission/).

### Step 1: Fork the Flathub repository

```bash
git clone https://github.com/flathub/flathub.git
cd flathub
git checkout -b com.vocalinux.Vocalinux
```

### Step 2: Copy and adapt the manifest

Copy `com.vocalinux.Vocalinux.yml` into the forked repo root, then make these
changes for Flathub:

1. **Change the source** from local directory to Git tag:
   ```yaml
   sources:
     - type: git
       url: https://github.com/jatinkrmalik/vocalinux.git
       tag: v0.10.2-beta
   ```

2. **Remove `network: true`** from `build-options` (Flathub builders do not
   allow network access during build). Instead, pre-download all Python
   wheels and use `--no-index --find-links`:
   ```yaml
   build-commands:
     - pip3 install --no-build-isolation --no-index --find-links=./wheels --prefix=/app .
   ```
   Or use `flatpak-pip-generator` to generate a dependencies module.

3. **Keep the rest** of the manifest unchanged.

### Step 3: Open a Pull Request

Push the branch and open a PR against `flathub/flathub`. Flathub maintainers
will review the manifest, test the build, and provide feedback.

### Step 4: After merge

Once merged, Flathub will:
- Build the app on their CI infrastructure
- Sign and publish the bundle
- The app will appear in GNOME Software, KDE Discover, and other app stores

## Manifest Details

### Runtime

- **Runtime**: `org.gnome.Platform` version `46`
- **SDK**: `org.gnome.Sdk` version `46`

The GNOME runtime provides GTK3, PyGObject, and AppIndicator libraries out of
the box.

### Permissions

| Permission | Purpose |
|------------|---------|
| `--share=network` | Download speech models on first run |
| `--socket=pulseaudio` | Microphone capture (works with PipeWire too) |
| `--device=all` | Microphone access, Vulkan GPU, keyboard events |
| `--filesystem=xdg-config/vocalinux` | Configuration storage |
| `--filesystem=xdg-data/vocalinux` | Speech model storage |
| `--talk-name=org.freedesktop.IBus` | IBus text injection engine |
| `--talk-name=org.kde.StatusNotifierWatcher` | System tray icon (KDE) |
| `--talk-name=org.gnome.Shell` | System tray icon (GNOME) |

### Known Limitations

- **Global keyboard shortcuts** via `evdev` may have reduced functionality inside
the Flatpak sandbox. The app falls back to `pynput` which works through X11/Wayland.
- **IBus engine** is the preferred text injection method on Wayland and works
fully within the sandbox.
- **GPU acceleration**: Vulkan support is available via `--device=all`. CUDA is
not available inside the Flatpak sandbox; whisper.cpp will use Vulkan or CPU.

## Maintenance

When releasing a new version:

1. Update the `tag` in `com.vocalinux.Vocalinux.yml`
2. Update the `<releases>` section in `com.vocalinux.Vocalinux.metainfo.xml`
3. Test the local build
4. Open a PR to the Flathub repository with the updated manifest

The CI workflow `.github/workflows/release.yml` includes a `build-flatpak` job
that automatically builds the Flatpak on every release tag.
