#!/usr/bin/env bash
# Build a relocatable x86_64 AppImage for Vocalinux.
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
set -euo pipefail

WHEEL="$1"
VERSION="$2"
OUTDIR="${3:-dist}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT
APPDIR="$WORKDIR/AppDir"
TOOLDIR="$WORKDIR/tools"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$TOOLDIR" "$OUTDIR"

echo "== Fetching AppImage tooling =="
curl -fsSL -o "$TOOLDIR/linuxdeploy" \
  https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
curl -fsSL -o "$TOOLDIR/linuxdeploy-plugin-gtk.sh" \
  https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh
curl -fsSL -o "$TOOLDIR/appimagetool" \
  https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x "$TOOLDIR/linuxdeploy" "$TOOLDIR/linuxdeploy-plugin-gtk.sh" "$TOOLDIR/appimagetool"

echo "== Bundling Python runtime =="
PY_PREFIX="$(python3 -c 'import sys; print(sys.prefix)')"
PY_VER="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
cp -L "$(command -v python3)" "$APPDIR/usr/bin/python3"
cp -r "$PY_PREFIX/lib/python${PY_VER}" "$APPDIR/usr/lib/python${PY_VER}"
rm -rf "$APPDIR/usr/lib/python${PY_VER}/site-packages"

echo "== Installing Vocalinux + PyGObject into the bundle =="
python3 -m pip install --no-cache-dir --prefix "$APPDIR/usr" "$WHEEL" PyGObject pycairo

echo "== Adding desktop entry + icon =="
install -Dm644 "$REPO_ROOT/vocalinux.desktop" "$APPDIR/usr/share/applications/vocalinux.desktop"
install -Dm644 "$REPO_ROOT/resources/icons/scalable/vocalinux.svg" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps/vocalinux.svg"

echo "== Copying GObject-Introspection typelibs (not handled by linuxdeploy-plugin-gtk) =="
mkdir -p "$APPDIR/usr/lib/girepository-1.0"
for typelib in Gtk-3.0 Gdk-3.0 GdkX11-3.0 GdkPixbuf-2.0 GLib-2.0 GObject-2.0 Gio-2.0 \
               Pango-1.0 PangoCairo-1.0 cairo-1.0 HarfBuzz-0.0 Atk-1.0 freetype2-2.0 \
               AppIndicator3-0.1 AyatanaAppIndicator3-0.1 Notify-0.7 IBus-1.0; do
  found="$(find /usr/lib -name "${typelib}.typelib" 2>/dev/null | head -1)"
  if [ -n "$found" ]; then
    cp "$found" "$APPDIR/usr/lib/girepository-1.0/"
  fi
done

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
ln -s "python${PY_VER}" "$APPDIR/usr/lib/python3"
chmod +x "$APPDIR/AppRun"

echo "== Running linuxdeploy (resolves the shared-library closure + GTK theming) =="
export DEPLOY_GTK_VERSION=3
"$TOOLDIR/linuxdeploy" --appdir "$APPDIR" \
  --plugin gtk \
  -e "$APPDIR/usr/bin/python3" \
  -d "$APPDIR/usr/share/applications/vocalinux.desktop" \
  -i "$APPDIR/usr/share/icons/hicolor/scalable/apps/vocalinux.svg"

echo "== Packaging AppImage =="
OUTPUT="$OUTDIR/Vocalinux-${VERSION}-x86_64.AppImage"
ARCH=x86_64 "$TOOLDIR/appimagetool" "$APPDIR" "$OUTPUT"
echo "Built $OUTPUT"
