# Download URL to DEST. LABEL is used in messages only.
# Returns 1 if tools/network missing or download empty; caller prints "on first run" context.
download_url() {
    local URL="$1"
    local DEST="$2"
    local LABEL="${3:-file}"

    if ! command_exists wget && ! command_exists curl; then
        print_warning "Neither wget nor curl found. Cannot download $LABEL."
        return 1
    fi
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        print_warning "No internet connection detected."
        return 1
    fi

    if command_exists wget; then
        if ! wget --progress=bar:force:noscroll -O "$DEST" "$URL" 2>&1; then
            print_error "Failed to download $LABEL with wget"
            rm -f "$DEST"
            return 1
        fi
    else
        if ! curl -L --progress-bar -o "$DEST" "$URL"; then
            print_error "Failed to download $LABEL with curl"
            rm -f "$DEST"
            return 1
        fi
    fi

    if [ ! -f "$DEST" ] || [ ! -s "$DEST" ]; then
        print_error "Downloaded $LABEL is empty or missing"
        rm -f "$DEST"
        return 1
    fi
    return 0
}

# Single-file model install: skip if present, download to .tmp, move into place, mark preinstalled.
install_single_file_model() {
    local LABEL="$1"
    local URL="$2"
    local DEST="$3"
    local MARKER_DIR="$4"
    local SIZE_HINT="$5"

    print_info "Installing $LABEL${SIZE_HINT:+ ($SIZE_HINT)}..."
    mkdir -p "$(dirname "$DEST")"

    if [ -f "$DEST" ]; then
        print_info "$LABEL already exists at $DEST"
        return 0
    fi

    print_info "Downloading $LABEL..."
    print_info "This may take a few minutes depending on your internet connection."

    local TEMP_FILE="$DEST.tmp"
    if ! download_url "$URL" "$TEMP_FILE" "$LABEL"; then
        print_warning "$LABEL will be downloaded on first application run."
        return 1
    fi

    mv "$TEMP_FILE" "$DEST"
    if [ -f "$DEST" ]; then
        local MODEL_SIZE
        MODEL_SIZE=$(du -h "$DEST" | cut -f1)
        print_success "$LABEL installed successfully ($MODEL_SIZE)"
        mkdir -p "$MARKER_DIR"
        echo "$(date)" > "$MARKER_DIR/.vocalinux_preinstalled"
        return 0
    fi

    print_error "$LABEL installation failed"
    return 1
}

install_whisper_model() {
    local WHISPER_DIR="$DATA_DIR/models/whisper"
    install_single_file_model \
        "Whisper tiny model" \
        "https://openaipublic.azureedge.net/main/whisper/models/65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9/tiny.pt" \
        "$WHISPER_DIR/tiny.pt" \
        "$WHISPER_DIR" \
        "~75MB"
}

install_vosk_models() {
    print_info "Installing VOSK speech recognition models..."

    local MODELS_DIR="$DATA_DIR/models"
    mkdir -p "$MODELS_DIR"

    local SMALL_MODEL_URL="https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    local SMALL_MODEL_NAME="vosk-model-small-en-us-0.15"
    local SMALL_MODEL_PATH="$MODELS_DIR/$SMALL_MODEL_NAME"

    if [ -d "$SMALL_MODEL_PATH" ]; then
        print_info "Small VOSK model already exists at $SMALL_MODEL_PATH"
        return 0
    fi

    print_info "Downloading small VOSK model (approximately 40MB)..."
    print_info "This may take a few minutes depending on your internet connection."

    local TEMP_ZIP="$MODELS_DIR/$(basename "$SMALL_MODEL_URL")"
    if ! download_url "$SMALL_MODEL_URL" "$TEMP_ZIP" "VOSK model"; then
        print_warning "VOSK models will be downloaded on first application run."
        return 1
    fi

    print_info "Extracting VOSK model..."
    if ! command_exists unzip; then
        print_error "unzip command not found. Cannot extract VOSK model."
        rm -f "$TEMP_ZIP"
        return 1
    fi
    if ! unzip -q "$TEMP_ZIP" -d "$MODELS_DIR"; then
        print_error "Failed to extract VOSK model"
        rm -f "$TEMP_ZIP"
        return 1
    fi
    rm -f "$TEMP_ZIP"

    if [ -d "$SMALL_MODEL_PATH" ]; then
        print_success "VOSK small model installed successfully at $SMALL_MODEL_PATH"
        chmod -R 755 "$SMALL_MODEL_PATH"
        echo "$(date)" > "$SMALL_MODEL_PATH/.vocalinux_preinstalled"
        return 0
    fi

    print_error "VOSK model extraction failed - directory not found"
    return 1
}

install_whispercpp_model() {
    local WHISPERCPP_DIR="$DATA_DIR/models/whispercpp"
    install_single_file_model \
        "whisper.cpp tiny model" \
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin" \
        "$WHISPERCPP_DIR/ggml-tiny.bin" \
        "$WHISPERCPP_DIR" \
        "~39MB"
}
