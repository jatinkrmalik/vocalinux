get_pywhispercpp_library_path() {
    [ -x "$VENV_DIR/bin/python" ] || return 1
    "$VENV_DIR/bin/python" - <<'PY' 2>/dev/null
from pathlib import Path
import site
import sys
import sysconfig

roots = []
for attr in ("getsitepackages",):
    get_paths = getattr(site, attr, None)
    if get_paths is None:
        continue
    try:
        roots.extend(get_paths())
    except Exception:
        pass

user_site = getattr(site, "getusersitepackages", lambda: None)()
if user_site and getattr(site, "ENABLE_USER_SITE", False):
    roots.append(user_site)

for key in ("platlib", "purelib"):
    path = sysconfig.get_paths().get(key)
    if path:
        roots.append(path)

roots.extend(path for path in sys.path if path)

dirs = []
seen = set()
for root in roots:
    root_path = Path(root)
    candidates = [
        root_path / "pywhispercpp.libs",
        root_path / "pywhispercpp" / ".libs",
        root_path / "pywhispercpp" / "lib",
        root_path,
    ]
    for candidate in candidates:
        try:
            resolved = str(candidate.resolve())
        except OSError:
            continue
        if resolved in seen or not candidate.is_dir():
            continue
        if any(candidate.glob("libwhisper*.so*")) or any(candidate.glob("libggml*.so*")):
            seen.add(resolved)
            dirs.append(resolved)

print(":".join(dirs))
PY
}

is_pywhispercpp_gpu_capable() {
    is_pywhispercpp_backend_capable cuda || is_pywhispercpp_backend_capable vulkan
}

is_pywhispercpp_backend_capable() {
    local BACKEND
    BACKEND=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')

    local LIB_DIRS
    LIB_DIRS=$(get_pywhispercpp_library_path || true)
    [ -n "$LIB_DIRS" ] || return 1

    local EXPECTED_LIB=""
    case "$BACKEND" in
        cuda)
            EXPECTED_LIB="libggml-cuda.so"
            ;;
        vulkan)
            EXPECTED_LIB="libggml-vulkan.so"
            ;;
        *)
            return 1
            ;;
    esac

    local IFS=:
    local LIB_DIR
    for LIB_DIR in $LIB_DIRS; do
        if compgen -G "$LIB_DIR/$EXPECTED_LIB*" >/dev/null; then
            return 0
        fi
    done

    return 1
}

is_pywhispercpp_cuda_linkage_usable() {
    if ! command -v readelf >/dev/null 2>&1; then
        print_warning "readelf not found; skipping CUDA linkage verification." >&2
        return 0
    fi

    local LIB_DIRS
    LIB_DIRS=$(get_pywhispercpp_library_path || true)
    [ -n "$LIB_DIRS" ] || return 1

    local HAS_PATCHELF=false
    if command -v patchelf >/dev/null 2>&1; then
        HAS_PATCHELF=true
    fi

    local IFS=:
    local LIB_DIR
    for LIB_DIR in $LIB_DIRS; do
        local CUDA_LIB
        for CUDA_LIB in "$LIB_DIR"/libggml-cuda.so*; do
            [ -f "$CUDA_LIB" ] || continue
            local BUNDLED_LIBS
            BUNDLED_LIBS=$(readelf -d "$CUDA_LIB" 2>/dev/null | sed -En 's/.*Shared library: \[(libcuda-[^]]+\.so).*/\1/p')
            if [ -z "$BUNDLED_LIBS" ]; then
                continue
            fi

            local BUNDLED_LIB
            while IFS= read -r BUNDLED_LIB; do
                [ -n "$BUNDLED_LIB" ] || continue
                print_warning "CUDA backend links against bundled $BUNDLED_LIB instead of libcuda.so.1:"
                print_warning "  $CUDA_LIB"

                if [[ "$HAS_PATCHELF" == "true" ]]; then
                    print_info "Attempting to relink with patchelf ($BUNDLED_LIB → libcuda.so.1)..."
                    if patchelf --replace-needed "$BUNDLED_LIB" libcuda.so.1 "$CUDA_LIB" 2>/dev/null; then
                        print_success "Successfully relinked $CUDA_LIB to libcuda.so.1"
                    else
                        print_warning "patchelf relink failed for $CUDA_LIB"
                        print_warning "Treating CUDA verification as failed so the installer does not report broken GPU support."
                        return 1
                    fi
                else
                    print_warning "Install patchelf to attempt automatic relinking: sudo apt install patchelf"
                    print_warning "Treating CUDA verification as failed so the installer does not report broken GPU support."
                    return 1
                fi
            done <<< "$BUNDLED_LIBS"
        done
    done

    return 0
}

verify_pywhispercpp_backend_install() {
    local BACKEND="$1"

    if ! is_pywhispercpp_installed; then
        print_warning "pywhispercpp installed but import verification failed for $BACKEND backend."
        return 1
    fi

    if ! is_pywhispercpp_backend_capable "$BACKEND"; then
        print_warning "pywhispercpp installed but $BACKEND backend libraries were not found."
        return 1
    fi

    if [[ "$BACKEND" == "CUDA" ]] && ! is_pywhispercpp_cuda_linkage_usable; then
        return 1
    fi

    return 0
}

print_pip_log_tail() {
    local PIP_LOG_FILE="$1"
    local LINE_COUNT="${2:-80}"

    if [ -s "$PIP_LOG_FILE" ]; then
        print_warning "Last $LINE_COUNT lines from pip build log ($PIP_LOG_FILE):"
        tail -n "$LINE_COUNT" "$PIP_LOG_FILE" | sed 's/^/    /'
    else
        print_warning "Pip build log is empty or missing: $PIP_LOG_FILE"
    fi
}

with_pywhispercpp_library_path() {
    local PYWHISPERCPP_LIBRARY_PATH
    PYWHISPERCPP_LIBRARY_PATH=$(get_pywhispercpp_library_path || true)

    if [ -n "$PYWHISPERCPP_LIBRARY_PATH" ]; then
        LD_LIBRARY_PATH="$PYWHISPERCPP_LIBRARY_PATH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" "$@"
    else
        "$@"
    fi
}

get_pywhispercpp_cmake_args() {
    printf '%s\n' '-DCMAKE_INSTALL_RPATH=$ORIGIN -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON'
}

install_cpu_pywhispercpp() {
    local PIP_LOG_FILE="$1"
    local PYWHISPERCPP_CMAKE_ARGS
    PYWHISPERCPP_CMAKE_ARGS=$(get_pywhispercpp_cmake_args)

    CMAKE_ARGS="${CMAKE_ARGS:+$CMAKE_ARGS }$PYWHISPERCPP_CMAKE_ARGS" \
        pip install --verbose --force-reinstall --no-cache-dir pywhispercpp --log "$PIP_LOG_FILE"
}

is_pywhispercpp_installed() {
    [ -x "$VENV_DIR/bin/python" ] || return 1
    with_pywhispercpp_library_path "$VENV_DIR/bin/python" -c "from pywhispercpp.model import Model" >/dev/null 2>&1
}

get_pywhispercpp_version() {
    [ -x "$VENV_DIR/bin/python" ] || return 1
    "$VENV_DIR/bin/python" - <<'PY' 2>/dev/null
from importlib import metadata

try:
    print(metadata.version("pywhispercpp"))
except metadata.PackageNotFoundError:
    raise SystemExit(1)
PY
}

should_rebuild_whispercpp() {
    local INSTALLED_VERSION
    INSTALLED_VERSION=$(get_pywhispercpp_version || true)

    print_success "Found existing pywhispercpp installation${INSTALLED_VERSION:+ (version $INSTALLED_VERSION)}"

    case "$REBUILD_WHISPERCPP" in
        yes)
            print_info "Rebuilding pywhispercpp because --rebuild-whispercpp was specified."
            return 0
            ;;
        no)
            print_info "Reusing existing pywhispercpp installation."
            return 1
            ;;
    esac

    if [[ "$NON_INTERACTIVE" == "yes" ]]; then
        if [[ "$HAS_NVIDIA_GPU" == "yes" || "$HAS_VULKAN" == "yes" ]] && ! is_pywhispercpp_gpu_capable; then
            print_info "Non-interactive mode: GPU detected but pywhispercpp lacks GPU support. Rebuilding..."
            return 0
        fi
        print_info "Non-interactive mode: reusing existing pywhispercpp installation."
        print_info "Use --rebuild-whispercpp to force a rebuild."
        return 1
    fi

    if [[ "$HAS_NVIDIA_GPU" == "yes" || "$HAS_VULKAN" == "yes" ]] && ! is_pywhispercpp_gpu_capable; then
        print_info "GPU detected but pywhispercpp lacks GPU support. Rebuilding..."
        return 0
    fi

    read -p "Rebuild/reinstall pywhispercpp? This can take several minutes. (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    fi

    print_info "Reusing existing pywhispercpp installation."
    return 1
}

install_whispercpp_with_gpu_support() {
    local PIP_LOG_FILE="$1"

    print_info ""
    print_info "╔════════════════════════════════════════════════════════╗"
    print_info "║  Installing WHISPER.CPP (Recommended)                  ║"
    print_info "╠════════════════════════════════════════════════════════╣"
    print_info "║  • Fastest speech recognition                          ║"
    print_info "║  • Works with any GPU: NVIDIA, AMD, Intel              ║"
    print_info "║  • Uses Vulkan for GPU acceleration                    ║"
    print_info "║  • CPU-only mode available                             ║"
    print_info "╚════════════════════════════════════════════════════════╝"
    print_info ""

    # Detect GPU and install pywhispercpp with appropriate GPU support
    detect_nvidia_gpu || true
    detect_vulkan || true

    local GPU_BACKEND="CPU"
    local GPU_INSTALL_SUCCESS=false
    local SKIP_WHISPERCPP_INSTALL=false
    local PYWHISPERCPP_CMAKE_ARGS
    PYWHISPERCPP_CMAKE_ARGS=$(get_pywhispercpp_cmake_args)

    if [[ "$WHISPERCPP_ALREADY_INSTALLED" == "true" ]]; then
        GPU_BACKEND="existing"
        if should_rebuild_whispercpp; then
            print_info "Existing pywhispercpp will be replaced."
        else
            SKIP_WHISPERCPP_INSTALL=true
        fi
    fi

    # Check if user explicitly chose CPU backend in interactive mode
    if [[ "$SKIP_WHISPERCPP_INSTALL" == "true" ]]; then
        print_info "Skipping pywhispercpp reinstall; existing compiled bindings remain in place."
    elif [[ "${WHISPERCPP_BACKEND}" == "cpu" ]]; then
        print_info "ℹ Installing CPU-only version (as requested)..."
        GPU_BACKEND="CPU"
    else
        # Try Vulkan first (works with all GPUs: NVIDIA, AMD, Intel)
        if [[ "$HAS_VULKAN" == "yes" ]]; then
            print_info "✓ Vulkan detected: $VULKAN_DEVICE"
            print_info "  Installing pywhispercpp with Vulkan support..."
            GPU_BACKEND="Vulkan"
            print_info "Installing pywhispercpp ($GPU_BACKEND backend)..."
            if CMAKE_ARGS="${CMAKE_ARGS:+$CMAKE_ARGS }$PYWHISPERCPP_CMAKE_ARGS" \
                GGML_VULKAN=1 \
                pip install --verbose --force-reinstall --no-cache-dir git+https://github.com/absadiki/pywhispercpp --log "$PIP_LOG_FILE" 2>&1; then
                if verify_pywhispercpp_backend_install "$GPU_BACKEND"; then
                    GPU_INSTALL_SUCCESS=true
                else
                    print_pip_log_tail "$PIP_LOG_FILE"
                fi
            else
                print_warning "Vulkan build failed; checking for NVIDIA GPU to try CUDA..."
                print_pip_log_tail "$PIP_LOG_FILE"
            fi
        fi

        # If Vulkan failed or not available, try CUDA for NVIDIA GPUs
        if [[ "$GPU_INSTALL_SUCCESS" != "true" && "$HAS_NVIDIA_GPU" == "yes" ]]; then
            print_info "✓ NVIDIA GPU detected: $GPU_NAME"
            print_info "  Installing pywhispercpp with CUDA support..."
            GPU_BACKEND="CUDA"

            local CUDA_TOOLKIT_ROOT=""
            local CUDA_CMAKE_ARGS=""
            if CUDA_TOOLKIT_ROOT=$(find_valid_cuda_toolkit_root); then
                if CUDA_CMAKE_ARGS=$(get_cuda_cmake_args "$CUDA_TOOLKIT_ROOT"); then
                    print_info "Using CUDA toolkit: $CUDA_TOOLKIT_ROOT"
                    print_info "Installing pywhispercpp ($GPU_BACKEND backend)..."
                    if CMAKE_ARGS="${CMAKE_ARGS:+$CMAKE_ARGS }$PYWHISPERCPP_CMAKE_ARGS $CUDA_CMAKE_ARGS" \
                        GGML_CUDA=1 \
                        pip install --verbose --force-reinstall --no-cache-dir git+https://github.com/absadiki/pywhispercpp --log "$PIP_LOG_FILE" 2>&1; then
                        if verify_pywhispercpp_backend_install "$GPU_BACKEND"; then
                            GPU_INSTALL_SUCCESS=true
                        else
                            print_pip_log_tail "$PIP_LOG_FILE"
                        fi
                    else
                        print_warning "CUDA build failed."
                        print_pip_log_tail "$PIP_LOG_FILE"
                    fi
                else
                    print_warning "Skipping CUDA build because the detected toolkit cannot target this NVIDIA GPU."
                fi
            else
                print_warning "No complete CUDA toolkit root found; skipping CUDA build."
                print_info "  Required CUDA files: bin/nvcc, include/cuda_runtime.h, and libcudart.so*"
            fi
        fi
    fi

    # Fall back to CPU version if GPU install failed or no GPU detected
    if [[ "$SKIP_WHISPERCPP_INSTALL" != "true" && "$GPU_INSTALL_SUCCESS" != "true" ]]; then
        if [[ "$GPU_BACKEND" != "CPU" ]]; then
            print_warning "Failed to install pywhispercpp with $GPU_BACKEND support, falling back to CPU version..."

            # Provide helpful error messages for common issues
            if [[ "$GPU_BACKEND" == "Vulkan" ]]; then
                print_info "  To use Vulkan GPU acceleration, please install Vulkan development libraries:"
                print_info "    Ubuntu/Debian: sudo apt install libvulkan-dev vulkan-tools glslc || glslang-tools"
                print_info "    Fedora: sudo dnf install vulkan-loader-devel vulkan-tools glslang"
                print_info "    Arch: sudo pacman -S vulkan-headers vulkan-tools glslang"
                print_info "    openSUSE: sudo zypper install vulkan-devel vulkan-tools shaderc"
            elif [[ "$GPU_BACKEND" == "CUDA" ]]; then
                print_info "  To use CUDA GPU acceleration, please install CUDA toolkit:"
                print_info "    Visit: https://developer.nvidia.com/cuda-downloads"
            fi
        elif [[ "${WHISPERCPP_BACKEND}" != "cpu" ]]; then
            print_info "ℹ No GPU detected - installing CPU-only version"
            print_info "  CPU mode is still very fast!"
        fi
        if [[ "$GPU_BACKEND" != "CPU" ]]; then
            print_warning "Continuing with CPU-only pywhispercpp; GPU acceleration is not active."
        fi
        GPU_BACKEND="CPU"
        print_info "Installing pywhispercpp ($GPU_BACKEND backend)..."
        install_cpu_pywhispercpp "$PIP_LOG_FILE" || {
            print_error "Failed to install pywhispercpp"
            return 1
        }
    fi

    if [[ "$SKIP_WHISPERCPP_INSTALL" == "true" ]]; then
        print_success "pywhispercpp reused from existing installation"
    else
        print_success "pywhispercpp installed with $GPU_BACKEND backend"
    fi

    if ! is_pywhispercpp_installed; then
        print_warning "pywhispercpp installed but import verification failed."
        print_warning "This can happen when libwhisper.so is installed beside the Python extension without a runtime library path."

        if [[ "$SKIP_WHISPERCPP_INSTALL" != "true" ]]; then
            print_warning "Trying RPATH-aware CPU pywhispercpp fallback..."
            GPU_BACKEND="CPU"
            if install_cpu_pywhispercpp "$PIP_LOG_FILE"; then
                print_success "CPU pywhispercpp fallback installed"
            else
                print_warning "CPU pywhispercpp fallback installation failed"
            fi
        fi
    fi

    if ! is_pywhispercpp_installed; then
        print_warning "pywhispercpp is still unavailable; setting VOSK as the default engine so Vocalinux can start."
        print_warning "You can switch back to whisper.cpp from Settings after reinstalling pywhispercpp."
        SELECTED_ENGINE="vosk"

        local FALLBACK_VOSK_CONFIG="$CONFIG_DIR/config.json"
        if [ ! -f "$FALLBACK_VOSK_CONFIG" ]; then
            # Coupling fix #5: this is one of the 5 heredoc blocks; now via write_config_json.
            write_config_json vosk_fallback
        fi
    fi
    echo ""
}
