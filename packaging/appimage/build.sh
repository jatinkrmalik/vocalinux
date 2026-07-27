#!/usr/bin/env bash
# Build a relocatable AppImage for Vocalinux, natively for whichever
# architecture this script runs on (x86_64 or aarch64) - no cross-compiling.
#
# Usage: build.sh <path-to-wheel> <version> [output-dir]
#
# Bundles a full copy of the active Python interpreter (relocated via
# PYTHONHOME, not a venv, since venvs hard-code absolute paths) plus
# PyGObject/GTK3/AppIndicator/IBus GObject-Introspection typelibs, since
# those are needed by `gi.repository` at runtime and linuxdeploy-plugin-gtk
# does not bundle them (it targets native C GTK apps, which don't need
# introspection data).
#
# ponytail: text-injection CLI tools (xdotool/wtype/ydotool) are not
# bundled, same runtime prerequisite as the PyPI install path documented
# in docs/INSTALL.md. Add bundling if users hit missing-binary complaints.
#
# GPU note: the pip pywhispercpp wheel is CPU-only. Vulkan/CUDA rebuilds
# stay on install.sh for now; the AppImage logs when GPU libs are absent.
set -euo pipefail

WHEEL="$1"
VERSION="$2"
OUTDIR="${3:-dist}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ARCH="$(uname -m)"
PYTHON="${PYTHON:-python3}"

case "$ARCH" in
  x86_64|aarch64) ;;
  *) echo "Unsupported architecture: $ARCH (need x86_64 or aarch64)" >&2; exit 1 ;;
esac

TYPELIBS=(
  Gtk-3.0 Gdk-3.0 GdkX11-3.0 GdkPixbuf-2.0 GLib-2.0 GObject-2.0 Gio-2.0
  Pango-1.0 PangoCairo-1.0 cairo-1.0 HarfBuzz-0.0 Atk-1.0 freetype2-2.0
  AppIndicator3-0.1 AyatanaAppIndicator3-0.1 Notify-0.7 IBus-1.0 Rsvg-2.0
)

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
APPDIR="$WORKDIR/AppDir"
TOOLDIR="$WORKDIR/tools"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$TOOLDIR" "$OUTDIR"

# Nested AppImages need extract-and-run on hosts without usable FUSE.
export APPIMAGE_EXTRACT_AND_RUN="${APPIMAGE_EXTRACT_AND_RUN:-1}"

echo "== Fetching AppImage tooling ($ARCH) =="
curl -fsSL -o "$TOOLDIR/linuxdeploy" \
  "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-${ARCH}.AppImage"
curl -fsSL -o "$TOOLDIR/linuxdeploy-plugin-gtk.sh" \
  https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh
curl -fsSL -o "$TOOLDIR/appimagetool" \
  "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${ARCH}.AppImage"
chmod +x "$TOOLDIR/linuxdeploy" "$TOOLDIR/linuxdeploy-plugin-gtk.sh" "$TOOLDIR/appimagetool"

echo "== Bundling Python runtime ($PYTHON) =="
# Use base_prefix so a venv builder still ships a full stdlib (encodings, etc.).
PY_PREFIX="$("$PYTHON" -c 'import sys; print(sys.base_prefix)')"
PY_VER="$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
PY_BIN="$("$PYTHON" -c 'import sys; print(sys.base_prefix)')/bin/python${PY_VER}"
if [ ! -x "$PY_BIN" ]; then
  PY_BIN="$("$PYTHON" -c 'import sys; print(sys.base_prefix)')/bin/python3"
fi
if [ ! -x "$PY_BIN" ]; then
  PY_BIN="$("$PYTHON" -c 'import sys; print(sys.executable)')"
fi
cp -L "$PY_BIN" "$APPDIR/usr/bin/python3"
cp -r "$PY_PREFIX/lib/python${PY_VER}" "$APPDIR/usr/lib/python${PY_VER}"
rm -rf "$APPDIR/usr/lib/python${PY_VER}/site-packages"

echo "== Installing Vocalinux + runtime deps into the bundle =="
# --ignore-installed: pip otherwise treats the builder env's packages as
# satisfying deps and skips copying vosk/pywhispercpp/etc. into AppDir.
"$PYTHON" -m pip install --no-cache-dir --ignore-installed --prefix "$APPDIR/usr" \
  "$WHEEL" PyGObject pycairo onnxruntime

echo "== Adding desktop entry + icon =="
install -Dm644 "$REPO_ROOT/vocalinux.desktop" "$APPDIR/usr/share/applications/vocalinux.desktop"
# AppImage desktop integration expects Exec=AppRun; set WM class for the tray app.
sed -i \
  -e 's|^Exec=.*|Exec=AppRun|' \
  -e '/^StartupWMClass=/d' \
  "$APPDIR/usr/share/applications/vocalinux.desktop"
printf 'StartupWMClass=vocalinux\n' >> "$APPDIR/usr/share/applications/vocalinux.desktop"
install -Dm644 "$REPO_ROOT/resources/icons/scalable/vocalinux.svg" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps/vocalinux.svg"

copy_typelibs() {
  local dest="$1"
  mkdir -p "$dest"
  local typelib found
  for typelib in "${TYPELIBS[@]}"; do
    found="$(find /usr/lib -name "${typelib}.typelib" 2>/dev/null | head -1 || true)"
    if [ -n "$found" ]; then
      cp "$found" "$dest/"
    fi
  done
}

echo "== Copying GObject-Introspection typelibs (not handled by linuxdeploy-plugin-gtk) =="
copy_typelibs "$APPDIR/usr/lib/girepository-1.0"

echo "== Writing AppRun =="
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PYTHONHOME="$HERE/usr"
export PYTHONPATH="$HERE/usr/lib/python3:$HERE/usr/lib/python3/site-packages"
export GI_TYPELIB_PATH="$HERE/usr/lib/girepository-1.0"
export LD_LIBRARY_PATH="$HERE/usr/lib:${LD_LIBRARY_PATH:-}"
export XDG_DATA_DIRS="$HERE/usr/share:${XDG_DATA_DIRS:-/usr/share}"
exec "$HERE/usr/bin/python3" -m vocalinux.main "$@"
APPRUN
# PYTHONPATH above uses a version-agnostic symlink so AppRun doesn't need
# to know the exact interpreter minor version at runtime.
ln -sfn "python${PY_VER}" "$APPDIR/usr/lib/python3"
chmod +x "$APPDIR/AppRun"

echo "== Running linuxdeploy (resolves the shared-library closure + GTK theming) =="
export DEPLOY_GTK_VERSION=3
"$TOOLDIR/linuxdeploy" --appdir "$APPDIR" \
  --plugin gtk \
  -e "$APPDIR/usr/bin/python3" \
  -d "$APPDIR/usr/share/applications/vocalinux.desktop" \
  -i "$APPDIR/usr/share/icons/hicolor/scalable/apps/vocalinux.svg"

echo "== Pruning typelibs back to the allowlist (linuxdeploy copies the host set) =="
rm -rf "$APPDIR/usr/lib/girepository-1.0"
copy_typelibs "$APPDIR/usr/lib/girepository-1.0"

echo "== Patching linuxdeploy GTK AppRun hook (Wayland-friendly GDK backend) =="
GTK_HOOK="$APPDIR/apprun-hooks/linuxdeploy-plugin-gtk.sh"
if [ -f "$GTK_HOOK" ]; then
  # Upstream forces GDK_BACKEND=x11 even on Wayland, which breaks hover/focus
  # for GTK widgets under Plasma (XWayland). Prefer native Wayland unless the
  # user opts into X11 via VOCALINUX_FORCE_X11=1.
  python3 - "$GTK_HOOK" <<'PY'
import pathlib, re, sys
path = pathlib.Path(sys.argv[1])
text = path.read_text()
replacement = (
    '# Prefer Wayland when available; force X11 only when requested.\n'
    'if [ "${VOCALINUX_FORCE_X11:-0}" = "1" ]; then\n'
    '    export GDK_BACKEND=x11\n'
    'elif [ -n "${WAYLAND_DISPLAY:-}" ] || [ "${XDG_SESSION_TYPE:-}" = "wayland" ]; then\n'
    '    export GDK_BACKEND=wayland\n'
    'else\n'
    '    export GDK_BACKEND=x11\n'
    'fi'
)
new, n = re.subn(
    r'^[ \t]*export GDK_BACKEND=x11[^\n]*$',
    replacement,
    text,
    count=1,
    flags=re.M,
)
if n != 1:
    raise SystemExit(f"failed to patch GDK_BACKEND in {path} (matches={n})")
path.write_text(new)
print(f"Patched {path}")
PY
else
  echo "Warning: GTK AppRun hook not found at $GTK_HOOK" >&2
fi

echo "== Packaging AppImage =="
OUTPUT="$OUTDIR/Vocalinux-${VERSION}-${ARCH}.AppImage"
ARCH="$ARCH" "$TOOLDIR/appimagetool" "$APPDIR" "$OUTPUT"
echo "Built $OUTPUT"
