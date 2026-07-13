# Detect hardware and recommend best engine
get_engine_recommendation() {
    detect_nvidia_gpu || true
    detect_vulkan || true

    local TOTAL_RAM_GB=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}' || echo "0")

    if [[ "$HAS_NVIDIA_GPU" == "yes" ]]; then
        echo "whisper_cpp:✓:NVIDIA GPU detected ($GPU_NAME) - Best performance with whisper.cpp"
    elif [[ "$HAS_VULKAN" == "yes" ]]; then
        echo "whisper_cpp:✓:$VULKAN_DEVICE detected - Great performance with whisper.cpp Vulkan"
    elif [ "$TOTAL_RAM_GB" -ge 8 ]; then
        echo "whisper_cpp:✓:No GPU detected, but ${TOTAL_RAM_GB}GB RAM - whisper.cpp CPU mode"
    else
        echo "vosk:⚠:Low RAM (${TOTAL_RAM_GB}GB) and no GPU - VOSK recommended for best performance"
    fi
}

detect_typelib_path() {
    if command -v pkg-config >/dev/null 2>&1; then
        local path=$(pkg-config --variable=typelibdir gobject-introspection-1.0 2>/dev/null)
        if [ -n "$path" ] && [ -d "$path" ]; then
            echo "$path"
            return 0
        fi
    fi

    for path in \
        /usr/lib/x86_64-linux-gnu/girepository-1.0 \
        /usr/lib/aarch64-linux-gnu/girepository-1.0 \
        /usr/lib/arm-linux-gnueabihf/girepository-1.0 \
        /usr/lib/riscv64-linux-gnu/girepository-1.0 \
        /usr/lib/powerpc64le-linux-gnu/girepository-1.0 \
        /usr/lib/s390x-linux-gnu/girepository-1.0 \
        /usr/lib64/girepository-1.0 \
        /usr/lib/girepository-1.0 \
        /usr/local/lib/girepository-1.0 \
        /usr/local/lib64/girepository-1.0; do
        if [ -d "$path" ]; then
            echo "$path"
            return 0
        fi
    done

    echo "/usr/lib/girepository-1.0"
    return 1
}

init_gi_typelib_detected() {
    GI_TYPELIB_DETECTED=$(detect_typelib_path)
    print_info "Detected GI_TYPELIB_PATH: $GI_TYPELIB_DETECTED"
}

# Write config.json for the given engine. One template replaces five heredocs.
# ENGINE: whisper_cpp | whisper | vosk | vosk_fallback | remote_api
write_config_json() {
    local ENGINE="$1"
    local MODEL_SIZE="tiny"
    local EXTRA_FIELDS=""

    case "$ENGINE" in
        vosk|vosk_fallback|remote_api) MODEL_SIZE="small" ;;
    esac

    if [[ "$ENGINE" == "remote_api" ]]; then
        EXTRA_FIELDS="
        \"remote_api_url\": \"${REMOTE_API_URL:-}\",
        \"remote_api_key\": \"\","
    fi

    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_DIR/config.json" << CONFIG_EOF
{
    "speech_recognition": {
        "engine": "$ENGINE",
        "model_size": "$MODEL_SIZE",
        "vosk_model_size": "small",
        "whisper_model_size": "tiny",
        "whisper_cpp_model_size": "tiny",$EXTRA_FIELDS
        "vad_sensitivity": 3,
        "silence_timeout": 2.0
    },
    "audio": {
        "device_index": null,
        "device_name": null
    },
    "shortcuts": {
        "toggle_recognition": "ctrl+ctrl"
    },
    "ui": {
        "start_minimized": false,
        "show_notifications": true
    },
    "advanced": {
        "debug_logging": false,
        "wayland_mode": false
    }
}
CONFIG_EOF
}
