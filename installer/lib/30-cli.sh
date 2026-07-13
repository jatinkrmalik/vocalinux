# TTY/pipe detection: if stdin is a pipe but /dev/tty exists, redirect stdin so
# user input works normally. If no terminal is available at all (headless/CI),
# fall back to automatic mode.
detect_tty_and_pipe() {
    if [ ! -t 0 ]; then
        if [ -e /dev/tty ] && [ -r /dev/tty ]; then
            if { true < /dev/tty; } 2>/dev/null; then
                exec < /dev/tty
                INTERACTIVE_MODE="ask"
            else
                AUTO_MODE="yes"
                INTERACTIVE_MODE="no"
                NON_INTERACTIVE="yes"
            fi
        else
            AUTO_MODE="yes"
            INTERACTIVE_MODE="no"
            NON_INTERACTIVE="yes"
        fi
    fi
}

# Parse command line arguments
parse_cli_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dev)
                DEV_MODE="yes"
                shift
                ;;
            --test)
                RUN_TESTS="yes"
                shift
                ;;
            --venv-dir=*)
                CLI_VENV_DIR="${1#*=}"
                shift
                ;;
            --skip-models)
                SKIP_MODELS="yes"
                shift
                ;;
            --skip-system-deps)
                SKIP_SYSTEM_DEPS="yes"
                shift
                ;;
            --rebuild-whispercpp)
                REBUILD_WHISPERCPP="yes"
                shift
                ;;
            --no-rebuild-whispercpp)
                REBUILD_WHISPERCPP="no"
                shift
                ;;
            --engine=*)
                SELECTED_ENGINE="${1#*=}"
                shift
                ;;
            --interactive|-i)
                INTERACTIVE_MODE="yes"
                shift
                ;;
            --tag=*)
                INSTALL_TAG="${1#*=}"
                shift
                ;;
            --auto)
                AUTO_MODE="yes"
                INTERACTIVE_MODE="no"
                NON_INTERACTIVE="yes"
                shift
                ;;
            --help)
                echo "Vocalinux Installer"
                echo ""
                echo "Usage: $0 [options]"
                echo ""
                echo "Installation Modes:"
                echo "  (no flags)       Interactive mode - guided setup with recommendations"
                echo "  --auto           Automatic mode - install with defaults (whisper.cpp)"
                echo "  --auto --engine=whisper   Auto mode with specific engine"
                echo ""
                echo "Options:"
                echo "  --interactive, -i  Force interactive mode (default)"
                echo "  --auto           Non-interactive automatic installation"
                echo "  --engine=NAME    Speech engine: whisper_cpp (default), whisper, vosk, remote_api"
                echo "  --dev            Install in development mode with all dev dependencies"
                echo "  --test           Run tests after installation"
                echo "  --venv-dir=PATH  Specify custom virtual environment directory"
                echo "  --skip-models    Skip downloading speech models during installation"
                echo "  --skip-system-deps"
                echo "                  Skip package-manager dependency installation (advanced)"
                echo "  --rebuild-whispercpp     Rebuild/reinstall pywhispercpp even if already installed"
                echo "  --no-rebuild-whispercpp  Reuse existing pywhispercpp when present (auto-mode default)"
                echo "  --tag=TAG        Install specific release tag (default: latest release)"
                echo "  --help           Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0                           # Interactive mode (recommended)"
                echo "  $0 --auto                    # Auto-install with whisper.cpp"
                echo "  $0 --auto --engine=vosk      # Auto-install VOSK only"
                echo "  $0 --dev --test              # Dev mode with tests"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help to see available options"
                exit 1
                ;;
        esac
    done

    # If dev mode is enabled, automatically run tests
    if [[ "$DEV_MODE" == "yes" ]]; then
        RUN_TESTS="yes"
    fi
}

# Display ASCII art banner
display_banner() {
    cat << "EOF"

  ▗▖  ▗▖ ▗▄▖  ▗▄▖ ▗▄▄▖▗▖   ▗▄▄▄▖▗▖  ▗▖▗▖ ▗▖▗▖  ▗▖
  ▐▌  ▐▌▐▌ ▐▌▐▌ ▐▌▐▌   ▐▌     █  ▐▛▚▖▐▌▐▌ ▐▌ ▝▚▞▘
  ▐▌  ▐▌▐▌ ▐▌▐▛▀▜▌▐▌   ▐▌     █  ▐▌ ▝▜▌▐▌ ▐▌  ▐▌
   ▝▚▞▘ ▝▚▄▞▘▐▌ ▐▌▝▚▄▄▖▐▙▄▄▖▗▄█▄▖▐▌  ▐▌▝▚▄▞▘▗▞▘▝▚▖

                     Voice Dictation for Linux

EOF

    print_info "Vocalinux Installer"
    print_info "=============================="
    echo ""
}

resolve_install_tag() {
    if [ -n "$INSTALL_TAG" ]; then
        return
    fi
    if command_exists curl; then
        local latest
        latest=$(curl -fsSL --connect-timeout 5 \
            "https://api.github.com/repos/jatinkrmalik/vocalinux/releases/latest" \
            2>/dev/null | grep '"tag_name"' | head -1 | cut -d'"' -f4)
        if [ -n "$latest" ]; then
            INSTALL_TAG="$latest"
            return
        fi
    fi
    INSTALL_TAG="v0.10.1-beta"
}

# Coupling fix #1: single writer for VENV_DIR.
# LOCAL_REPO_DIR is the path where the repo lives (passed from lib/40-repo.sh);
# when unset (e.g. local source checkout), VENV_DIR stays relative to the cwd.
resolve_venv_dir() {
    local LOCAL_REPO_DIR="${1:-}"
    if [ -n "$CLI_VENV_DIR" ]; then
        VENV_DIR="$CLI_VENV_DIR"
    elif [[ "${IS_REMOTE_INSTALL:-no}" == "yes" ]]; then
        VENV_DIR="$HOME/.local/share/vocalinux/venv"
    elif [ -n "$LOCAL_REPO_DIR" ]; then
        VENV_DIR="$LOCAL_REPO_DIR/$VENV_DIR"
    else
        VENV_DIR="$HOME/.local/share/vocalinux/venv"
    fi
}

# Coupling fix #2: single resolver for SELECTED_ENGINE.
# Called after parse_cli_args and the interactive TUI; fills in the
# non-interactive default if the user (or CLI) never picked one.
resolve_engine() {
    if [ -n "$SELECTED_ENGINE" ]; then
        return
    fi
    if [[ "$NON_INTERACTIVE" == "yes" ]]; then
        SELECTED_ENGINE="whisper_cpp"
        print_info "Automatic mode: Installing with whisper.cpp (default engine)"
        print_info "For other engines, use: --engine=whisper or --engine=vosk or --engine=remote_api"
        echo ""
    fi
}

# Interactive mode decision when stdin was a pipe but a TTY is available
resolve_interactive_mode() {
    if [[ "$INTERACTIVE_MODE" == "ask" ]]; then
        # Running via curl pipe but we have a terminal - ask user preference
        echo ""
        echo "Installation Mode:"
        echo "  1. Interactive (recommended) - guided setup with recommendations"
        echo "  2. Automatic - quick install with defaults (whisper.cpp)"
        echo ""
        read -p "Choose mode [1-2] (default: 1): " MODE_CHOICE
        MODE_CHOICE=${MODE_CHOICE:-1}

        if [[ "$MODE_CHOICE" == "2" ]]; then
            AUTO_MODE="yes"
            INTERACTIVE_MODE="no"
            NON_INTERACTIVE="yes"
        else
            INTERACTIVE_MODE="yes"
            NON_INTERACTIVE="no"
        fi
        echo ""
    fi
}

run_interactive_install() {
    clear_screen
    cat << "EOF"

                 Interactive Installation Guide
                 ===============================

EOF

    echo "Welcome! This guided installation will help you set up Vocalinux"
    echo "with the best options for your system."
    echo ""
    echo "All speech engines are 100% offline, local, and private."
    echo "Your voice data never leaves your computer."
    echo ""

    # Step 1: Detect and display system info
    print_header "Step 1: Your System"
    echo "Detected: $DISTRO_NAME $DISTRO_VERSION"

    # Get hardware recommendation
    local RECOMMENDATION=$(get_engine_recommendation)
    local RECOMMENDED_ENGINE=$(echo "$RECOMMENDATION" | cut -d':' -f1)
    local RECOMMENDED_ICON=$(echo "$RECOMMENDATION" | cut -d':' -f2)
    local RECOMMENDED_REASON=$(echo "$RECOMMENDATION" | cut -d':' -f3-)

    echo "Hardware: $RECOMMENDED_REASON"
    echo ""

    # Step 2: Choose speech recognition engine
    print_header "Step 2: Choose Speech Recognition Engine"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────────┐"
    echo "  │  1. WHISPER.CPP  * RECOMMENDED                              │"
    echo "  │     • Fastest, most accurate, works with any GPU            │"
    echo "  │     • Supports NVIDIA (CUDA), AMD, Intel (Vulkan)           │"
    echo "  │     • CPU-only mode available for older systems             │"
    echo "  │     • Models: tiny (39MB) to large (1.5GB)                  │"
    echo "  │     • 99+ languages with auto-detection                     │"
    echo "  └─────────────────────────────────────────────────────────────┘"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────────┐"
    echo "  │  2. WHISPER (OpenAI)                                        │"
    echo "  │     • PyTorch-based, high accuracy                          │"
    echo "  │     • Only supports NVIDIA GPUs (CUDA)                      │"
    echo "  │     • Larger download (~2GB with CUDA)                      │"
    echo "  │     • Good for development/research                         │"
    echo "  └─────────────────────────────────────────────────────────────┘"
    echo ""
    echo "  ┌─────────────────────────────────────────────────────────────┐"
    echo "  │  3. VOSK                                                    │"
    echo "  │     • Lightweight and fast                                  │"
    echo "  │     • Works on older/low-RAM systems                        │"
    echo "  │     • ~40MB download                                        │"
    echo "  │     • Good for basic dictation needs                        │"
    echo "  └─────────────────────────────────────────────────────────────┘"
    echo ""
    echo "  ┌───────────────────────────────────────────────────────────────┐"
    echo "  │  4. REMOTE API (ADVANCED)                                     │"
    echo "  │     • Offload processing to a GPU server on your network      │"
    echo "  │     • Ideal for laptops without GPU                           │"
    echo "  │     • Supports whisper.cpp server & OpenAI-compatible APIs    │"
    echo "  │     • Minimal local resources needed                          │"
    echo "  │     • Requires a remote server to be running                  │"
    echo "  └───────────────────────────────────────────────────────────────┘"
    echo ""

    # Show recommendation
    case "$RECOMMENDED_ENGINE" in
        whisper_cpp)
            echo "  → Recommendation: whisper.cpp (best performance for your hardware)"
            DEFAULT_CHOICE="1"
            ;;
        vosk)
            echo "  → Recommendation: VOSK (lightweight option for your system)"
            DEFAULT_CHOICE="3"
            ;;
        *)
            echo "  → Recommendation: whisper.cpp (best overall experience)"
            DEFAULT_CHOICE="1"
            ;;
    esac
    echo ""

    read -p "Choose engine [1-4] (default: $DEFAULT_CHOICE): " ENGINE_CHOICE
    ENGINE_CHOICE=${ENGINE_CHOICE:-$DEFAULT_CHOICE}

    case "$ENGINE_CHOICE" in
        1)
            SELECTED_ENGINE="whisper_cpp"
            ENGINE_DISPLAY="Whisper.cpp (Recommended)"
            ;;
        2)
            SELECTED_ENGINE="whisper"
            ENGINE_DISPLAY="Whisper (OpenAI)"
            ;;
        3)
            SELECTED_ENGINE="vosk"
            ENGINE_DISPLAY="VOSK (Lightweight)"
            ;;
        4)
            SELECTED_ENGINE="remote_api"
            ENGINE_DISPLAY="Remote API"
            ;;
        *)
            SELECTED_ENGINE="whisper_cpp"
            ENGINE_DISPLAY="Whisper.cpp (Recommended)"
            ;;
    esac

    # Step 3: Whisper.cpp backend selection (if whisper.cpp chosen)
    if [[ "$SELECTED_ENGINE" == "whisper_cpp" ]]; then
        print_header "Step 3: Choose Whisper.cpp Backend"
        echo ""

        # Detect available backends
        local BACKEND_INFO=$(detect_whispercpp_backends)
        local RECOMMENDED_BACKEND=$(echo "$BACKEND_INFO" | cut -d':' -f1)
        local RECOMMENDED_REASON=$(echo "$BACKEND_INFO" | cut -d':' -f2)
        local CAN_BUILD_GPU=$(echo "$BACKEND_INFO" | cut -d':' -f3)
        local HAS_VULKAN=$(echo "$BACKEND_INFO" | cut -d':' -f4)
        local HAS_NVIDIA=$(echo "$BACKEND_INFO" | cut -d':' -f5)
        local HAS_VULKAN_DEV=$(echo "$BACKEND_INFO" | cut -d':' -f6)
        local HAS_CUDA_DEV=$(echo "$BACKEND_INFO" | cut -d':' -f7)
        local VULKAN_COMPAT=$(echo "$BACKEND_INFO" | cut -d':' -f8)
        local VULKAN_COMPAT_REASON=$(echo "$BACKEND_INFO" | cut -d':' -f9)

        # Show warning for incompatible GPUs
        if [[ "$VULKAN_COMPAT" == "incompatible" ]]; then
            echo ""
            print_warning "═══════════════════════════════════════════════════════════════"
            print_warning "  ⚠️  INCOMPATIBLE GPU DETECTED"
            print_warning "═══════════════════════════════════════════════════════════════"
            print_warning ""
            print_warning "  Your GPU: $VULKAN_COMPAT_REASON"
            print_warning ""
            print_warning "  This Intel GPU lacks VK_KHR_16bit_storage support, which is"
            print_warning "  required for whisper.cpp Vulkan acceleration."
            print_warning ""
            print_warning "  The CPU backend will be used instead, which is still fast!"
            print_warning ""
            print_warning "═══════════════════════════════════════════════════════════════"
            echo ""
        fi

        echo "Whisper.cpp can use different backends for speech recognition:"
        echo ""

        if [[ "$CAN_BUILD_GPU" == "true" ]]; then
            echo "  ┌─────────────────────────────────────────────────────────────┐"
            echo "  │  1. GPU (Vulkan/CUDA)  * RECOMMENDED                        │"
            echo "  │     • Fastest performance with GPU acceleration             │"
            echo "  │     • $RECOMMENDED_REASON                                   │"
            echo "  │     • Requires building from source (takes ~2-5 min)        │"
            echo "  └─────────────────────────────────────────────────────────────┘"
            echo ""
            echo "  ┌─────────────────────────────────────────────────────────────┐"
            echo "  │  2. CPU (Pre-built)                                         │"
            echo "  │     • Works on all systems                                  │"
            echo "  │     • Faster installation (no compilation)                  │"
            echo "  │     • Good performance on modern CPUs                       │"
            echo "  └─────────────────────────────────────────────────────────────┘"
            echo ""
            echo "  → Recommendation: GPU backend for best performance"
            local DEFAULT_BACKEND="1"
        else
            echo "  ┌─────────────────────────────────────────────────────────────┐"
            echo "  │  1. GPU (Vulkan/CUDA)                                       │"
            echo "  │     • ⚠️  GPU libraries not detected                        │"
            echo "  │     • Requires: libvulkan-dev, glslc/glslang-tools (Vulkan) │"
            echo "  │              or: CUDA toolkit (NVIDIA)                      │"
            echo "  └─────────────────────────────────────────────────────────────┘"
            echo ""
            echo "  ┌─────────────────────────────────────────────────────────────┐"
            echo "  │  2. CPU (Pre-built)  * RECOMMENDED                          │"
            echo "  │     • Works on all systems                                  │"
            echo "  │     • Fast installation (no compilation)                    │"
            echo "  │     • Good performance on modern CPUs                       │"
            echo "  └─────────────────────────────────────────────────────────────┘"
            echo ""

            if [[ "$HAS_VULKAN" == "yes" && "$HAS_VULKAN_DEV" != "true" ]]; then
                echo "  💡 Tip: Install 'libvulkan-dev' and a shader compiler for GPU support:"
                echo "     sudo apt install libvulkan-dev glslc 2>/dev/null || sudo apt install libvulkan-dev glslang-tools"
                echo ""
            elif [[ "$HAS_NVIDIA" == "yes" && "$HAS_CUDA_DEV" != "true" ]]; then
                echo "  💡 Tip: Install CUDA toolkit for NVIDIA GPU support:"
                echo "     https://developer.nvidia.com/cuda-downloads"
                echo ""
            fi

            echo "  → Recommendation: CPU backend (GPU libraries not detected)"
            local DEFAULT_BACKEND="2"
        fi

        read -p "Choose backend [1-2] (default: $DEFAULT_BACKEND): " BACKEND_CHOICE
        BACKEND_CHOICE=${BACKEND_CHOICE:-$DEFAULT_BACKEND}

        if [[ "$BACKEND_CHOICE" == "1" ]]; then
            WHISPERCPP_BACKEND="gpu"
            BACKEND_DISPLAY="GPU (Vulkan/CUDA)"
        else
            WHISPERCPP_BACKEND="cpu"
            BACKEND_DISPLAY="CPU (Pre-built)"
        fi

        echo ""
    fi

    # Step 3 for Remote API: Configure server URL
    if [[ "$SELECTED_ENGINE" == "remote_api" ]]; then
        print_header "Step 3: Configure Remote Server"
        echo ""
        print_info "You need a speech recognition server running on your local network."
        echo ""
        echo "  Supported servers:"
        echo "    • whisper.cpp server:  ./server -m model.bin --host 0.0.0.0 --port 8080"
        echo "    • LocalAI:            docker run -p 8080:8080 localai/localai"
        echo "    • Faster Whisper:      faster-whisper-server --host 0.0.0.0 --port 8080"
        echo "    • Any OpenAI-compatible speech API"
        echo ""
        read -p "Enter remote server URL (or leave blank to set later): " REMOTE_API_URL_INPUT
        if [ -n "$REMOTE_API_URL_INPUT" ]; then
            REMOTE_API_URL="$REMOTE_API_URL_INPUT"
            REMOTE_DISPLAY="$REMOTE_API_URL"
        else
            REMOTE_API_URL=""
            REMOTE_DISPLAY="(configure later in Settings)"
        fi
        echo ""
    fi

    # Step 4: Model download preference (skip for remote_api)
    if [[ "$SELECTED_ENGINE" != "remote_api" ]]; then
    print_header "Step 4: Model Download"
    echo ""
    echo "Speech recognition models can be downloaded now or later."
    echo ""
    echo "  1. Download now (recommended)"
    echo "     • Faster first run - ready to use immediately"
    echo "     • Offline capable right after install"
    echo ""
    echo "  2. Download later"
    echo "     • Smaller initial install"
    echo "     • Models download automatically on first use"
    echo ""

    read -p "Download models now? [1-2] (default: 1): " MODELS_CHOICE
    MODELS_CHOICE=${MODELS_CHOICE:-1}

    if [[ "$MODELS_CHOICE" == "2" ]]; then
        SKIP_MODELS="yes"
        MODELS_DISPLAY="Download on first use"
    else
        MODELS_DISPLAY="Download now (recommended)"
    fi
    else
        # Remote API: No need to download model
        SKIP_MODELS="yes"
        MODELS_DISPLAY="Not needed (remote processing)"
    fi

    # Summary
    print_header "Installation Summary"
    echo ""
    echo "  Speech Engine: $ENGINE_DISPLAY"
    if [[ "$SELECTED_ENGINE" == "whisper_cpp" ]]; then
        echo "  Backend: ${BACKEND_DISPLAY:-CPU (Pre-built)}"
        if [[ "${WHISPERCPP_BACKEND}" == "gpu" ]]; then
            echo "  Note: GPU build will compile from source (2-5 minutes)"
        fi
    fi
    if [[ "$SELECTED_ENGINE" == "remote_api" ]]; then
        echo "  Remote Server: $REMOTE_DISPLAY"
    fi
    echo "  Models: $MODELS_DISPLAY"
    echo "  Install Location: ${INSTALL_DIR:-\$HOME/.local/share/vocalinux}"
    echo ""
    read -p "Press Enter to continue with installation, or Ctrl+C to cancel..."
    echo ""
}
