write_launcher_wrapper() {
    local BIN_NAME="$1"
    local GI_TYPELIB_PATH_VALUE="$2"
    local WRAPPER_PATH="$HOME/.local/bin/$BIN_NAME"

    mkdir -p "$(dirname "$WRAPPER_PATH")"
    cat > "$WRAPPER_PATH" << WRAPPER_EOF
#!/bin/bash
# Wrapper script for Vocalinux that sets required environment variables
# and applies the 'input' group for keyboard shortcuts on Wayland
export PYTHONNOUSERSITE=1
export GI_TYPELIB_PATH=$GI_TYPELIB_PATH_VALUE
PYWHISPERCPP_LIBRARY_PATH=""
PY_SITE_PATHS=\$("$VENV_DIR/bin/python" - <<'PY' 2>/dev/null
import sysconfig

paths = []
for key in ("platlib", "purelib"):
    path = sysconfig.get_paths().get(key)
    if path and path not in paths:
        paths.append(path)
print(" ".join(paths))
PY
)
for PY_SITE in \$PY_SITE_PATHS; do
    for PY_LIB_DIR in "\$PY_SITE/pywhispercpp.libs" "\$PY_SITE/pywhispercpp/.libs" "\$PY_SITE/pywhispercpp/lib"; do
        if [ -d "\$PY_LIB_DIR" ] && { ls "\$PY_LIB_DIR"/libwhisper*.so* >/dev/null 2>&1 || ls "\$PY_LIB_DIR"/libggml*.so* >/dev/null 2>&1; }; then
            if [ -z "\$PYWHISPERCPP_LIBRARY_PATH" ]; then
                PYWHISPERCPP_LIBRARY_PATH="\$PY_LIB_DIR"
            else
                PYWHISPERCPP_LIBRARY_PATH="\$PYWHISPERCPP_LIBRARY_PATH:\$PY_LIB_DIR"
            fi
        fi
    done
done
if [ -n "\$PYWHISPERCPP_LIBRARY_PATH" ]; then
    export LD_LIBRARY_PATH="\$PYWHISPERCPP_LIBRARY_PATH\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
fi

# Check if user is in input group but current session doesn't have it
if grep -q "^input:.*\b\$(whoami)\b" /etc/group 2>/dev/null && ! groups | grep -q '\binput\b'; then
    # Use sg to run with input group without requiring logout
    exec sg input -c "$VENV_DIR/bin/$BIN_NAME \$*"
else
    exec "$VENV_DIR/bin/$BIN_NAME" "\$@"
fi
WRAPPER_EOF
    chmod +x "$WRAPPER_PATH"
    print_info "Created wrapper: ~/.local/bin/$BIN_NAME"
}
