# Function to run tests with better error handling
run_tests() {
    print_info "Running tests..."

    # Check if pytest is installed in the virtual environment
    if ! "$VENV_DIR/bin/python" -c "import pytest" &>/dev/null; then
        print_info "Installing pytest and related packages..."
        pip install pytest pytest-mock pytest-cov || {
            print_error "Failed to install pytest. Cannot run tests."
            return 1
        }
    fi

    # Create a directory for test results
    local TEST_RESULTS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/vocalinux/test_results"
    mkdir -p "$TEST_RESULTS_DIR"
    local TEST_RESULTS_FILE="$TEST_RESULTS_DIR/pytest_$(date +%Y%m%d_%H%M%S).xml"

    print_info "Running tests with pytest..."
    print_info "This may take a few minutes..."

    # Run the tests with pytest and capture output
    local TEST_OUTPUT_FILE=$(mktemp)
    if pytest -v --junitxml="$TEST_RESULTS_FILE" | tee "$TEST_OUTPUT_FILE"; then
        print_success "All tests passed!"
        print_info "Test results saved to: $TEST_RESULTS_FILE"
        rm -f "$TEST_OUTPUT_FILE"
        return 0
    else
        local FAILED_COUNT=$(grep -c "FAILED" "$TEST_OUTPUT_FILE")
        print_error "$FAILED_COUNT tests failed!"
        print_info "Test results saved to: $TEST_RESULTS_FILE"
        print_info "Check the test output for details."
        rm -f "$TEST_OUTPUT_FILE"
        return 1
    fi
}

# Function to verify the installation
verify_installation() {
    print_info "Verifying installation..."
    local ISSUES=0

    # Check if virtual environment exists and is activated
    if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
        print_error "Virtual environment not found or incomplete."
        ISSUES=$((ISSUES + 1))
    fi

    # Check if vocalinux command is available
    if ! command -v vocalinux &>/dev/null && [ ! -f "$VENV_DIR/bin/vocalinux" ]; then
        print_error "Vocalinux command not found."
        ISSUES=$((ISSUES + 1))
    fi

    # Check if desktop entry is installed
    if [ ! -f "$DESKTOP_DIR/vocalinux.desktop" ]; then
        print_warning "Desktop entry not found. Application may not appear in application menu."
        ISSUES=$((ISSUES + 1))
    fi

    # Check if icons are installed
    local ICON_COUNT=0
    for icon in vocalinux.svg vocalinux-microphone.svg vocalinux-microphone-off.svg vocalinux-microphone-process.svg; do
        if [ -f "$ICON_DIR/$icon" ]; then
            ICON_COUNT=$((ICON_COUNT + 1))
        fi
    done

    if [ "$ICON_COUNT" -lt 4 ]; then
        print_warning "Some icons are missing. Application may not display correctly."
        ISSUES=$((ISSUES + 1))
    fi

    # Check if Python package is importable using venv python
    if ! "$VENV_DIR/bin/python" -c "import vocalinux" &>/dev/null; then
        print_error "Vocalinux Python package cannot be imported."
        ISSUES=$((ISSUES + 1))
    fi

    # Smoke-test the selected speech engine's native library at install time so that
    # "installed but does not run" failures (e.g. libwhisper.so.1 not found on Debian)
    # are surfaced here with actionable guidance rather than silently at first launch.
    local selected_engine="${SELECTED_ENGINE:-whisper_cpp}"
    if [[ "$selected_engine" == "whisper_cpp" ]]; then
        if ! is_pywhispercpp_installed; then
            print_error "pywhispercpp (whisper.cpp engine) installed but cannot be imported at runtime."
            print_error "This usually means libwhisper.so.1 is missing or not on the library path."
            print_error ""
            print_error "Diagnostic steps:"
            print_error "  1. Check for unresolved symbols:"
            print_error "     ldd \$(find $VENV_DIR -name '*.so' -path '*/pywhispercpp*' 2>/dev/null | head -1) 2>/dev/null | grep 'not found'"
            print_error "  2. Re-run the installer with: --rebuild-whispercpp"
            print_error "  3. Or switch to VOSK (no native build needed): --engine=vosk"
            ISSUES=$((ISSUES + 1))
        else
            print_success "pywhispercpp (whisper.cpp) import verified successfully."
        fi
    fi

    # Return the number of issues found
    return $ISSUES
}

# Function to print beautiful welcome message
print_welcome_message() {
    local ISSUES=$1

    # ASCII art header
    cat << 'EOF'

  ▗▖  ▗▖ ▗▄▖  ▗▄▄▖▗▄▖ ▗▖   ▗▄▄▄▖▗▖  ▗▖▗▖ ▗▖▗▖  ▗▖
  ▐▌  ▐▌▐▌ ▐▌▐▌   ▐▌ ▐▌▐▌     █  ▐▛▚▖▐▌▐▌ ▐▌ ▝▚▞▘
  ▐▌  ▐▌▐▌ ▐▌▐▌   ▐▛▀▜▌▐▌     █  ▐▌ ▝▜▌▐▌ ▐▌  ▐▌
   ▝▚▞▘ ▝▚▄▞▘▝▚▄▄▖▐▌ ▐▌▐▙▄▄▖▗▄█▄▖▐▌  ▐▌▝▚▄▞▘▗▞▘▝▚▖

                     ✓ Installation Complete!

EOF

    # Success or warning message
    if [ "$ISSUES" -eq 0 ]; then
        print_success "Vocalinux has been installed successfully!"
    else
        print_warning "Installation complete with $ISSUES minor issue(s)"
        print_warning "The application should still work normally."
    fi

    # Get engine info for display
    local ENGINE_INFO="${SELECTED_ENGINE:-whisper_cpp}"
    local ENGINE_DISPLAY_NAME=""
    local BACKEND_INFO=""

    case "$ENGINE_INFO" in
        whisper_cpp)
            ENGINE_DISPLAY_NAME="Whisper.cpp"
            if [[ "${WHISPERCPP_BACKEND}" == "gpu" ]]; then
                BACKEND_INFO="GPU Accelerated"
            else
                BACKEND_INFO="CPU"
            fi
            ;;
        whisper)
            ENGINE_DISPLAY_NAME="Whisper (OpenAI)"
            BACKEND_INFO="PyTorch/CUDA"
            ;;
        vosk)
            ENGINE_DISPLAY_NAME="VOSK"
            BACKEND_INFO="Lightweight"
            ;;
        remote_api)
            ENGINE_DISPLAY_NAME="Remote API"
            BACKEND_INFO="Network (offloaded to remote server)"
            ;;
    esac

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  📦 What Was Installed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "  Application:    Vocalinux (voice dictation for Linux)"
    echo "  Engine:         $ENGINE_DISPLAY_NAME"
    if [[ -n "$BACKEND_INFO" ]]; then
        echo "  Backend:        $BACKEND_INFO"
    fi
    echo "  Location:       ${INSTALL_DIR:-\$HOME/.local/share/vocalinux}"
    echo "  Virtual Env:    $VENV_DIR"
    echo "  Config:         $CONFIG_DIR"
    echo ""

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🚀 Getting Started"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. Launch Vocalinux"
    echo "   • From app menu: Look for 'Vocalinux'"
    echo "   • From terminal: Run 'vocalinux' command"
    echo ""
    echo "2. Find the icon in your system tray (top bar)"
    echo "   • Click for settings and status"
    echo "   • Right-click for menu options"
    echo ""
    echo "3. Start dictating!"
    echo -e "   \e[1mDouble-tap Ctrl\e[0m anywhere to toggle recording"
    echo ""

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🎤 Testing Your Setup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. Open any text editor (gedit, VS Code, LibreOffice, etc.)"
    echo "2. Double-tap Ctrl to start recording"
    echo "3. Say: 'Hello world period'"
    echo "4. Double-tap Ctrl to stop"
    echo "5. You should see: 'Hello world.'"
    echo ""
    echo "💡 Voice commands: 'period' 'comma' 'new line' 'delete that'"
    echo ""

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🔧 Managing Vocalinux"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Commands:"
    echo "  vocalinux              Start the application"
    echo "  vocalinux --debug      Start with debug logging"
    echo "  vocalinux-gui          Open settings GUI"
    echo ""
    echo "To activate the virtual environment:"
    echo "  source ${ACTIVATION_SCRIPT:-activate-vocalinux.sh}"
    echo ""
    echo "To uninstall:"
    echo "  ./uninstall.sh"
    echo ""

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  📚 Need Help?"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "• Issues & Bugs:  https://github.com/jatinkrmalik/vocalinux/issues"
    echo "• Documentation:  https://github.com/jatinkrmalik/vocalinux"
    echo "• Star on GitHub: ⭐ https://github.com/jatinkrmalik/vocalinux"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "  \e[1m\e[32m✨ Happy Dictating! ✨\e[0m"
    echo ""

    # Installation details (optional, for debugging)
    if [[ "$VERBOSE" == "yes" ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  🔍 Installation Details (Debug Mode)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Virtual environment: $VENV_DIR"
        echo "Desktop entry: $DESKTOP_DIR/vocalinux.desktop"
        echo "Configuration: $CONFIG_DIR"
        echo "Data directory: $DATA_DIR"
        echo "Wrapper script: $HOME/.local/bin/vocalinux"
        echo ""
    fi
}
