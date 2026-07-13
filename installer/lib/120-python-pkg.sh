# Function to install Python package with error handling and verification
install_python_package() {
    # Create a temporary directory for pip logs
    local PIP_LOG_DIR=$(mktemp -d)
    local PIP_LOG_FILE="$PIP_LOG_DIR/pip_log.txt"

    # Coupling fix #4: GI_TYPELIB_DETECTED is now a global set by
    # init_gi_typelib_detected (called from the dispatch phase before this).
    # Verification and wrapper creation all read the same value.
    print_info "Detected GI_TYPELIB_PATH: $GI_TYPELIB_DETECTED"

    local WHISPERCPP_ALREADY_INSTALLED=false
    if is_pywhispercpp_installed; then
        WHISPERCPP_ALREADY_INSTALLED=true
    fi

    # Function to verify package installation
    verify_package_installed() {
        local PKG_NAME="vocalinux"
        # Use venv python and set GI_TYPELIB_PATH for PyGObject
        # Use the detected path for cross-distro compatibility
        GI_TYPELIB_PATH="$GI_TYPELIB_DETECTED" "$VENV_DIR/bin/python" -c "import $PKG_NAME" 2>/dev/null
        return $?
    }

    # Silero/ONNX Runtime gives much better speech/silence decisions, but
    # onnxruntime wheels are not guaranteed for every Python/platform combo.
    # Install it opportunistically so fresh installs and rerun-updates get the
    # neural VAD when available without blocking the amplitude fallback path.
    install_vad_support() {
        local PIP_LOG_FILE="$1"
        local EDITABLE_MODE="${2:-no}"

        print_info "Installing neural VAD support (Silero / ONNX Runtime)..."
        local VAD_INSTALL_SUCCESS=false
        if [[ "$EDITABLE_MODE" == "yes" ]]; then
            pip install -e ".[vad]" --log "$PIP_LOG_FILE" && VAD_INSTALL_SUCCESS=true
        else
            pip install ".[vad]" --log "$PIP_LOG_FILE" && VAD_INSTALL_SUCCESS=true
        fi

        if [[ "$VAD_INSTALL_SUCCESS" == "true" ]]; then
            if "$VENV_DIR/bin/python" - <<'PY' 2>/dev/null
from vocalinux.speech_recognition.silero_vad import is_silero_available
raise SystemExit(0 if is_silero_available() else 1)
PY
            then
                print_success "Neural VAD support installed and verified successfully."
            else
                print_warning "Neural VAD dependencies installed, but Silero VAD could not be verified."
                print_warning "Vocalinux will use amplitude-based VAD until this is resolved."
            fi
        else
            print_warning "Failed to install neural VAD support."
            print_warning "Vocalinux will still work using amplitude-based VAD."
            print_warning "Check the pip log for details: $PIP_LOG_FILE"
        fi
    }

    if [[ "$DEV_MODE" == "yes" ]]; then
        print_info "Installing Vocalinux in development mode..."

        # Install in development mode with logging
        pip install -e . --log "$PIP_LOG_FILE" || {
            print_error "Failed to install Vocalinux in development mode."
            print_error "Check the pip log for details: $PIP_LOG_FILE"
            return 1
        }

        # Install test dependencies
        print_info "Installing test dependencies..."
        pip install pytest pytest-mock pytest-cov --log "$PIP_LOG_FILE" || {
            print_warning "Failed to install some test dependencies. Tests may not run correctly."
        }

        # Install all optional dependencies for development
        print_info "Installing all optional dependencies for development..."
        pip install -e ".[whisper,dev]" --log "$PIP_LOG_FILE" || {
            print_warning "Failed to install some optional dependencies."
            print_warning "Some features may not work correctly."
        }

        install_vad_support "$PIP_LOG_FILE" yes

        if [[ "${SELECTED_ENGINE:-whisper_cpp}" == "whisper_cpp" ]]; then
            install_whispercpp_with_gpu_support "$PIP_LOG_FILE"
        fi
    else
        print_info "Installing Vocalinux..."

        # Install the package with logging (includes pywhispercpp by default)
        pip install . --log "$PIP_LOG_FILE" || {
            print_error "Failed to install Vocalinux."
            print_error "Check the pip log for details: $PIP_LOG_FILE"
            return 1
        }

        install_vad_support "$PIP_LOG_FILE"

        # Engine installation logic:
        # - SELECTED_ENGINE is set by interactive mode or --engine flag
        # - WHISPERCPP_BACKEND is set by interactive mode ("gpu" or "cpu")
        # - Default is whisper_cpp for best performance
        case "${SELECTED_ENGINE:-whisper_cpp}" in
            whisper_cpp)
                install_whispercpp_with_gpu_support "$PIP_LOG_FILE"
                ;;

            whisper)
                print_info "Installing Whisper (OpenAI) with PyTorch..."
                print_info "Note: This engine requires NVIDIA GPU for acceleration"
                print_info "      For AMD/Intel GPUs, whisper.cpp is recommended"

                local WHISPER_INSTALL_SUCCESS=false

                # Install PyTorch and whisper
                print_info "Installing PyTorch..."
                if pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu --log "$PIP_LOG_FILE" 2>&1; then
                    print_success "PyTorch installed successfully"

                    print_info "Installing openai-whisper..."
                    if pip install openai-whisper --log "$PIP_LOG_FILE" 2>&1; then
                        # Verify the installation by importing the module
                        if "$VENV_DIR/bin/python" -c "import whisper" 2>/dev/null; then
                            WHISPER_INSTALL_SUCCESS=true
                            print_success "Whisper installed and verified successfully"
                        else
                            print_error "Whisper package installed but import failed"
                        fi
                    else
                        print_error "Failed to install openai-whisper package"
                    fi
                else
                    print_error "Failed to install PyTorch"
                fi

                if [[ "$WHISPER_INSTALL_SUCCESS" == "true" ]]; then
                    # Create config with whisper as default
                    local WHISPER_CONFIG="$CONFIG_DIR/config.json"
                    if [ ! -f "$WHISPER_CONFIG" ]; then
                        # Coupling fix #5: replace heredoc with write_config_json.
                        write_config_json whisper
                    fi
                else
                    print_warning "Failed to install Whisper (OpenAI)"
                    print_warning "Falling back to whisper.cpp (recommended engine)"
                    print_info ""
                    print_info "The Whisper (OpenAI) engine installation failed."
                    print_info "whisper.cpp will be installed instead, which is:"
                    print_info "  - Faster and more accurate"
                    print_info "  - Works with any GPU (NVIDIA, AMD, Intel)"
                    print_info "  - Uses Vulkan for GPU acceleration"
                    print_info ""

                    # Fall back to whisper.cpp installation
                    install_cpu_pywhispercpp "$PIP_LOG_FILE" || {
                        print_error "Failed to install pywhispercpp fallback"
                        print_error "Please try installing manually: pip install pywhispercpp"
                        return 1
                    }
                    print_success "Installed whisper.cpp as fallback"

                    # Create config with whisper_cpp as default
                    local FALLBACK_CONFIG="$CONFIG_DIR/config.json"
                    if [ ! -f "$FALLBACK_CONFIG" ]; then
                        # Coupling fix #5: replace heredoc with write_config_json.
                        write_config_json whisper_cpp
                    fi
                fi
                ;;

            vosk)
                print_info "Installing VOSK (lightweight option)..."
                print_info "VOSK is fast and works well on older systems."

                # Create config with vosk as default
                local VOSK_CONFIG_FILE="$CONFIG_DIR/config.json"
                if [ ! -f "$VOSK_CONFIG_FILE" ]; then
                    # Coupling fix #5: replace heredoc with write_config_json.
                    write_config_json vosk
                fi
                ;;

            remote_api)
                print_info "Setting up Remote API engine..."
                print_info ""
                print_info "╔════════════════════════════════════════════════════════╗"
                print_info "║  Setting up REMOTE API Engine                          ║"
                print_info "╠════════════════════════════════════════════════════════╣"
                print_info "║  • Offloads speech recognition to a remote server      ║"
                print_info "║  • Ideal for laptops without GPU                       ║"
                print_info "║  • Supports whisper.cpp server & OpenAI APIs           ║"
                print_info "║  • Requires: a server running on your network          ║"
                print_info "╚════════════════════════════════════════════════════════╝"
                print_info ""

                # Ensure requests library is installed
                print_info "Installing requests library..."
                pip install requests --log "$PIP_LOG_FILE" || {
                    print_error "Failed to install requests library"
                    return 1
                }
                print_success "requests library installed"

                # URL was collected upfront by run_interactive_install
                # (or left blank in auto/non-interactive mode).
                local REMOTE_API_URL="${REMOTE_API_URL:-}"

                # Create configuration file
                local REMOTE_CONFIG_FILE="$CONFIG_DIR/config.json"
                if [ ! -f "$REMOTE_CONFIG_FILE" ]; then
                    # Coupling fix #5: replace heredoc with write_config_json.
                    write_config_json remote_api
                fi

                if [ -n "$REMOTE_API_URL" ]; then
                    print_success "Remote API configured with server: $REMOTE_API_URL"
                else
                    print_warning "No server URL configured. You can set it later in Settings."
                fi
                ;;
        esac
    fi

    # Verify installation
    if verify_package_installed; then
        print_success "Vocalinux package installed successfully!"
        # Clean up log file if installation was successful
        rm -rf "$PIP_LOG_DIR"

        # GI_TYPELIB_PATH was already detected at the start of install_python_package

        # Create wrapper scripts in ~/.local/bin for easy access
        mkdir -p "$HOME/.local/bin"

        # Create launcher wrappers (sg input for Wayland shortcuts without re-login)
        write_launcher_wrapper vocalinux "$GI_TYPELIB_DETECTED"
        write_launcher_wrapper vocalinux-gui "$GI_TYPELIB_DETECTED"

        # Check if ~/.local/bin is in PATH
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            print_warning "~/.local/bin is not in your PATH"
            print_info "Add this line to your ~/.bashrc or ~/.zshrc:"
            print_info '  export PATH="$HOME/.local/bin:$PATH"'
        fi

        return 0
    else
        print_error "Vocalinux package installation verification failed."
        print_error "Check the pip log for details: $PIP_LOG_FILE"
        return 1
    fi
}
