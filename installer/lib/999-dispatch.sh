# Top-level execution: linear flow that calls into the libs.
# Each phase is a thin wrapper (see installer/phases/) but the dispatch here
# is the actual code that runs.

# Phase 1: TTY/CLI parsing
detect_tty_and_pipe
parse_cli_args "$@"
display_banner
check_running_processes
resolve_install_tag

# Phase 2: repo setup (uses Coupling fix #1: resolve_venv_dir)
setup_install_repo
resolve_venv_dir "$INSTALL_DIR"
cd "$INSTALL_DIR"

print_info "Using virtual environment: $VENV_DIR"
[[ "$DEV_MODE" == "yes" ]] && print_info "Installing in development mode"
[[ "$RUN_TESTS" == "yes" ]] && print_info "Tests will be run after installation"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root or with sudo."
    exit 1
fi

# Phase 3: detect distro + GPU
detect_distro

# Check compatibility
if [[ "$DISTRO_FAMILY" == "debian" ]]; then
    print_info "Detected Debian — fully supported. Continuing with Debian-specific configuration."
elif [[ "$DISTRO_FAMILY" != "ubuntu" ]]; then
    print_warning "This installer is primarily designed for Ubuntu/Debian-based systems. Your system: $DISTRO_NAME"
    print_warning "The application may still work, but you might need to install dependencies manually."
    if [[ "$NON_INTERACTIVE" == "yes" ]]; then
        print_info "Non-interactive mode: continuing anyway..."
    else
        read -p "Do you want to continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    # Check version for Ubuntu-based systems
    if ! check_ubuntu_version; then
        if [[ "$NON_INTERACTIVE" == "yes" ]]; then
            print_info "Non-interactive mode: continuing anyway..."
        else
            read -p "Do you want to continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
fi

# Phase 4: mode selection / interactive
resolve_interactive_mode
if [[ "$INTERACTIVE_MODE" == "yes" ]]; then
    if [ ! -t 0 ]; then
        print_error "Interactive mode requires a terminal (TTY)."
        print_error "Download and run the installer directly from a terminal:"
        print_error "  curl -fsSL https://raw.githubusercontent.com/jatinkrmalik/vocalinux/main/install.sh -o /tmp/vl.sh && bash /tmp/vl.sh"
        exit 1
    fi
    run_interactive_install
fi

# Coupling fix #2: fill in engine default after interactive TUI (which sets SELECTED_ENGINE).
resolve_engine

# Phase 5: hardware detection (with Coupling fix #3 idempotency)
detect_nvidia_gpu || true
detect_vulkan || true
GPU_DETECTION_DONE="yes"

# Coupling fix #4: single source of truth for GI_TYPELIB_PATH, consumed by
# verification, wrapper scripts, and the desktop entry.
init_gi_typelib_detected

# Phase 6: system dependencies
if [[ "$SKIP_SYSTEM_DEPS" == "yes" ]]; then
    print_warning "Skipping system dependency installation (--skip-system-deps specified)."
    print_warning "Make sure GTK, PyGObject, AppIndicator/Ayatana, PortAudio, and text input tools are installed."
else
    install_system_dependencies
fi

# Phase 7: XDG dirs + text input tools (lib/85-textinput.sh defines them, then runs the function)
install_text_input_tools

# Create necessary directories
print_info "Creating application directories..."
mkdir -p "$CONFIG_DIR"
mkdir -p "$DATA_DIR/models"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Phase 8: Python venv
if ! check_python_version; then
    print_warning "Continuing with unsupported Python version. Some features may not work correctly."
fi
setup_virtual_environment
create_activation_script

# Phase 9: install Python package (whisper.cpp default)
if ! install_python_package; then
    print_error "Failed to install Vocalinux package. Installation cannot continue."
    exit 1
fi

# Phase 10: desktop integration
install_desktop_entry || print_warning "Desktop entry installation failed"
install_icons || print_warning "Icon installation failed"
install_resources_to_venv || print_warning "Venv resource installation failed"

# Phase 11: model downloads
if [ "$SKIP_MODELS" = "no" ]; then
    if is_pywhispercpp_installed; then
        print_info "whisper.cpp is installed - downloading tiny model (default engine)..."
        install_whispercpp_model || print_warning "whisper.cpp model download failed - model will be downloaded on first run"
    fi
    if "$VENV_DIR/bin/python" -c "import whisper" 2>/dev/null; then
        print_info "Whisper (OpenAI) is installed - downloading tiny model..."
        install_whisper_model || print_warning "Whisper model download failed - model will be downloaded on first run"
    fi
else
    print_info "Skipping model downloads (--skip-models specified)"
    print_info "Models will be downloaded automatically on first application run"
fi

if [ "$SKIP_MODELS" = "no" ]; then
    install_vosk_models || print_warning "VOSK model installation failed - models will be downloaded on first run"
else
    print_info "Skipping VOSK model installation (--skip-models specified)"
    print_info "Models will be downloaded automatically on first application run"
fi

update_icon_cache

# Phase 12: tests + verify + welcome
if [[ "$RUN_TESTS" == "yes" ]]; then
    if run_tests; then
        print_success "Test suite completed successfully."
    else
        print_warning "Test suite completed with failures."
        print_warning "You can still use the application, but some features might not work as expected."
    fi
fi

verify_installation
INSTALL_ISSUES=$?

print_welcome_message $INSTALL_ISSUES

print_success "Installation process completed!"
