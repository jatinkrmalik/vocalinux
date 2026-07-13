# Detect NVIDIA GPU presence
detect_nvidia_gpu() {
    # Coupling fix #3: idempotency guard. Multiple call sites in the
    # original script re-ran detection; cache the result here.
    [[ "${GPU_DETECTION_DONE:-no}" == "yes" ]] && return 0

    # Check if nvidia-smi command exists and can successfully query GPU
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
        # Extract GPU information for user feedback
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1)
        GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -n1)
        HAS_NVIDIA_GPU="yes"
        return 0
    else
        HAS_NVIDIA_GPU="no"
        return 1
    fi
}

cuda_toolkit_root_has_runtime_library() {
    local CUDA_ROOT="$1"

    compgen -G "$CUDA_ROOT/lib64/libcudart.so*" >/dev/null && return 0
    compgen -G "$CUDA_ROOT/lib/libcudart.so*" >/dev/null && return 0
    compgen -G "$CUDA_ROOT/lib/x86_64-linux-gnu/libcudart.so*" >/dev/null && return 0
    compgen -G "$CUDA_ROOT/targets/x86_64-linux/lib/libcudart.so*" >/dev/null && return 0
    compgen -G "$CUDA_ROOT/targets/aarch64-linux/lib/libcudart.so*" >/dev/null && return 0
    compgen -G "$CUDA_ROOT/targets/sbsa-linux/lib/libcudart.so*" >/dev/null && return 0
    return 1
}

validate_cuda_toolkit_root() {
    local CUDA_ROOT="$1"

    [ -n "$CUDA_ROOT" ] || return 1
    [ -x "$CUDA_ROOT/bin/nvcc" ] || return 1
    [ -f "$CUDA_ROOT/include/cuda_runtime.h" ] || return 1
    cuda_toolkit_root_has_runtime_library "$CUDA_ROOT" || return 1
}

candidate_cuda_toolkit_roots() {
    local CUDA_VAR
    for CUDA_VAR in CUDAToolkit_ROOT CUDA_HOME CUDA_PATH; do
        local CUDA_ROOT="${!CUDA_VAR:-}"
        [ -n "$CUDA_ROOT" ] && printf '%s\n' "$CUDA_ROOT"
    done

    if command -v nvcc >/dev/null 2>&1; then
        local NVCC_PATH
        local NVCC_ROOT
        NVCC_PATH=$(readlink -f "$(command -v nvcc)" 2>/dev/null || command -v nvcc)
        NVCC_ROOT=$(cd "$(dirname "$NVCC_PATH")/.." 2>/dev/null && pwd -P)
        [ -n "$NVCC_ROOT" ] && printf '%s\n' "$NVCC_ROOT"
    fi

    local CUDA_ROOT
    for CUDA_ROOT in /usr/local/cuda /usr/local/cuda-* /opt/cuda; do
        [ -d "$CUDA_ROOT" ] && printf '%s\n' "$CUDA_ROOT"
    done
}

find_valid_cuda_toolkit_root() {
    local QUIET="${1:-no}"
    local SEEN_ROOTS=""
    local CUDA_ROOT

    while IFS= read -r CUDA_ROOT; do
        [ -n "$CUDA_ROOT" ] || continue

        local NORMALIZED_ROOT
        NORMALIZED_ROOT=$(cd "$CUDA_ROOT" 2>/dev/null && pwd -P) || NORMALIZED_ROOT="$CUDA_ROOT"

        if [[ ":$SEEN_ROOTS:" == *":$NORMALIZED_ROOT:"* ]]; then
            continue
        fi
        SEEN_ROOTS="${SEEN_ROOTS:+$SEEN_ROOTS:}$NORMALIZED_ROOT"

        if validate_cuda_toolkit_root "$NORMALIZED_ROOT"; then
            printf '%s\n' "$NORMALIZED_ROOT"
            return 0
        fi

        if [[ "$QUIET" != "quiet" ]]; then
            print_warning "Ignoring incomplete CUDA toolkit root: $NORMALIZED_ROOT" >&2
            print_warning "  Required: bin/nvcc, include/cuda_runtime.h, and libcudart.so*" >&2
        fi
    done < <(candidate_cuda_toolkit_roots)

    return 1
}

detect_nvidia_compute_architectures() {
    command -v nvidia-smi >/dev/null 2>&1 || return 1

    local COMPUTE_CAPS
    COMPUTE_CAPS=$(nvidia-smi --query-gpu=compute_cap --format=csv,noheader 2>/dev/null || true)
    [ -n "$COMPUTE_CAPS" ] || return 1

    printf '%s\n' "$COMPUTE_CAPS" | awk '
        {
            gsub(/[[:space:]]/, "", $1)
            if ($1 ~ /^[0-9]+(\.[0-9]+)?$/) {
                split($1, parts, ".")
                minor = parts[2]
                if (minor == "") {
                    minor = "0"
                }
                print parts[1] minor "-real"
            }
        }
    ' | sort -u | paste -sd ';' -
}

cuda_toolkit_supports_architectures() {
    local CUDA_ROOT="$1"
    local CUDA_ARCHS="$2"
    [ -n "$CUDA_ARCHS" ] || return 0

    local NVCC_ARCHS
    NVCC_ARCHS=$("$CUDA_ROOT/bin/nvcc" --list-gpu-arch 2>/dev/null || true)
    if [ -z "$NVCC_ARCHS" ]; then
        print_warning "Could not query supported CUDA architectures from $CUDA_ROOT/bin/nvcc" >&2
        print_warning "Continuing with detected CMAKE_CUDA_ARCHITECTURES=$CUDA_ARCHS" >&2
        return 0
    fi

    local IFS=';'
    local CUDA_ARCH
    for CUDA_ARCH in $CUDA_ARCHS; do
        local ARCH_DIGITS="${CUDA_ARCH%%-*}"
        if ! printf '%s\n' "$NVCC_ARCHS" | grep -q "compute_$ARCH_DIGITS"; then
            print_warning "CUDA toolkit at $CUDA_ROOT cannot target compute capability $ARCH_DIGITS." >&2
            print_warning "Install a newer CUDA toolkit, such as CUDA 11.8+ for RTX 40/Ada GPUs." >&2
            return 1
        fi
    done

    return 0
}

get_cuda_cmake_args() {
    local CUDA_ROOT="$1"
    local CUDA_ARGS="-DCUDAToolkit_ROOT=$CUDA_ROOT -DCMAKE_CUDA_COMPILER=$CUDA_ROOT/bin/nvcc"
    local CUDA_ARCHS

    CUDA_ARCHS=$(detect_nvidia_compute_architectures || true)
    if [ -n "$CUDA_ARCHS" ]; then
        cuda_toolkit_supports_architectures "$CUDA_ROOT" "$CUDA_ARCHS" || return 1
        CUDA_ARGS="$CUDA_ARGS -DCMAKE_CUDA_ARCHITECTURES=$CUDA_ARCHS"
    fi

    printf '%s\n' "$CUDA_ARGS"
}

# Detect Vulkan support for whisper.cpp
detect_vulkan() {
    # Coupling fix #3: idempotency guard. Multiple call sites in the
    # original script re-ran detection; cache the result here.
    [[ "${GPU_DETECTION_DONE:-no}" == "yes" ]] && return 0

    # Check for vulkaninfo command
    if command -v vulkaninfo >/dev/null 2>&1; then
        local vulkan_output=$(vulkaninfo --summary 2>/dev/null | head -20)
        if [ -n "$vulkan_output" ]; then
            HAS_VULKAN="yes"
            # Try to extract GPU name
            VULKAN_DEVICE=$(echo "$vulkan_output" | grep -i "deviceName" | head -1 | cut -d'=' -f2 | xargs)
            if [ -z "$VULKAN_DEVICE" ]; then
                VULKAN_DEVICE="Vulkan-compatible GPU"
            fi
            return 0
        fi
    fi
    HAS_VULKAN="no"
    return 1
}

# Check for incompatible Intel GPUs that don't support VK_KHR_16bit_storage
# These GPUs will fail with "device does not support 16-bit storage" error
# Affected: Intel Gen7 and older (Ivy Bridge, Haswell, Sandy Bridge)
# See: https://github.com/jatinkrmalik/vocalinux/issues/238
#
# IMPORTANT: This check filters out software renderers (llvmpipe, etc.) and only
# evaluates real hardware GPUs. Modern AMD, Intel (Gen8+), and NVIDIA GPUs all
# support VK_KHR_16bit_storage, so this mainly catches very old Intel Gen7 GPUs.
check_vulkan_gpu_compatibility() {
    # List of known incompatible GPU patterns (old Intel Gen7 and older)
    local INCOMPATIBLE_PATTERNS=(
        "Ivy Bridge"
        "Haswell"
        "Sandy Bridge"
        "HD Graphics 2500"
        "HD Graphics 4000"
        "HD Graphics 4400"
        "HD Graphics 4600"
        "HD Graphics P4600"
        "HD Graphics P4700"
        "IVB"
        "HSW"
        "SNB"
    )

    # Software renderers and virtual devices to skip (not real hardware GPUs)
    # These are CPU-based implementations that shouldn't affect compatibility detection
    local SOFTWARE_RENDERER_PATTERNS=(
        "llvmpipe"
        "swiftshader"
        "lavapipe"
        "zink"
        "virtio"
        "venus"
    )

    # Check if vulkaninfo is available
    if ! command -v vulkaninfo >/dev/null 2>&1; then
        echo "unknown:vulkaninfo not available"
        return 1
    fi

    # Get all device names from vulkaninfo
    local DEVICE_NAMES_RAW
    DEVICE_NAMES_RAW=$(vulkaninfo --summary 2>/dev/null | awk -F'=' '/deviceName/ {gsub(/^[ \t]+|[ \t]+$/, "", $2); if ($2 != "") print $2}')

    # Separate hardware GPUs from software renderers
    local HARDWARE_GPUS=""
    local HARDWARE_GPU_COUNT=0
    while IFS= read -r device_name; do
        [ -z "$device_name" ] && continue

        local is_software=false
        for pattern in "${SOFTWARE_RENDERER_PATTERNS[@]}"; do
            if echo "$device_name" | grep -iq "$pattern"; then
                is_software=true
                break
            fi
        done

        if [ "$is_software" = false ]; then
            if [ -n "$HARDWARE_GPUS" ]; then
                HARDWARE_GPUS="${HARDWARE_GPUS}, ${device_name}"
            else
                HARDWARE_GPUS="$device_name"
            fi
            ((HARDWARE_GPU_COUNT++))
        fi
    done <<< "$DEVICE_NAMES_RAW"

    # If no hardware GPUs found, we can't determine compatibility
    if [ -z "$HARDWARE_GPUS" ]; then
        echo "unknown:No hardware GPU found (only software renderers)"
        return 1
    fi

    # Get Vulkan features and check for VK_KHR_16bit_storage
    # Modern GPUs (AMD, Intel Gen8+, NVIDIA) all support this extension
    local FEATURES_OUTPUT
    FEATURES_OUTPUT=$(vulkaninfo --features 2>/dev/null)

    if [ -n "$FEATURES_OUTPUT" ]; then
        # Check for VK_KHR_16bit_storage extension or equivalent features
        if echo "$FEATURES_OUTPUT" | grep -q "VK_KHR_16bit_storage"; then
            echo "compatible:${HARDWARE_GPUS}"
            return 0
        fi

        # Alternative: check for 16-bit storage features directly
        if echo "$FEATURES_OUTPUT" | grep -Eq "storageBuffer16BitAccess[[:space:]]*=[[:space:]]*true|uniformAndStorageBuffer16BitAccess[[:space:]]*=[[:space:]]*true"; then
            echo "compatible:${HARDWARE_GPUS}"
            return 0
        fi
    fi

    # If Vulkan features check didn't confirm support, check against known incompatible patterns
    # This handles systems where vulkaninfo --features doesn't show the extension
    local INCOMPATIBLE_GPUS=""
    local HAS_COMPATIBLE_GPU=false

    while IFS= read -r device_name; do
        [ -z "$device_name" ] && continue

        # Skip software renderers
        local is_software=false
        for pattern in "${SOFTWARE_RENDERER_PATTERNS[@]}"; do
            if echo "$device_name" | grep -iq "$pattern"; then
                is_software=true
                break
            fi
        done
        [ "$is_software" = true ] && continue

        # Check against known incompatible patterns
        local is_incompatible=false
        for pattern in "${INCOMPATIBLE_PATTERNS[@]}"; do
            if echo "$device_name" | grep -iq "$pattern"; then
                is_incompatible=true
                break
            fi
        done

        if [ "$is_incompatible" = true ]; then
            if [ -n "$INCOMPATIBLE_GPUS" ]; then
                INCOMPATIBLE_GPUS="${INCOMPATIBLE_GPUS}, ${device_name}"
            else
                INCOMPATIBLE_GPUS="$device_name"
            fi
        else
            # GPU doesn't match known incompatible patterns - assume compatible
            HAS_COMPATIBLE_GPU=true
        fi
    done <<< "$DEVICE_NAMES_RAW"

    if [ "$HAS_COMPATIBLE_GPU" = true ]; then
        echo "compatible:${HARDWARE_GPUS}"
        return 0
    fi

    if [ -n "$INCOMPATIBLE_GPUS" ]; then
        echo "incompatible:${INCOMPATIBLE_GPUS}"
        return 1
    fi

    echo "unknown:Could not classify Vulkan GPU compatibility"
    return 1
}

# Detect available GPU backends for whisper.cpp and recommend the best option
detect_whispercpp_backends() {
    detect_nvidia_gpu || true
    detect_vulkan || true

    # Check for Vulkan dev libraries
    local HAS_VULKAN_DEV=false
    if pkg-config --exists vulkan 2>/dev/null || [ -f /usr/include/vulkan/vulkan.h ]; then
        HAS_VULKAN_DEV=true
    fi

    # Check for CUDA
    local HAS_CUDA_DEV=false
    if find_valid_cuda_toolkit_root quiet >/dev/null 2>&1; then
        HAS_CUDA_DEV=true
    fi

    # Check Vulkan GPU compatibility (Gen7 and older Intel GPUs lack 16-bit storage support)
    # Skip this check for NVIDIA GPUs since they use CUDA, not Vulkan
    local VULKAN_COMPATIBLE="unknown"
    local VULKAN_COMPAT_REASON=""
    if [[ "$HAS_VULKAN" == "yes" && "$HAS_NVIDIA_GPU" != "yes" ]]; then
        local COMPAT_RESULT
        COMPAT_RESULT=$(check_vulkan_gpu_compatibility)
        VULKAN_COMPATIBLE=$(echo "$COMPAT_RESULT" | cut -d':' -f1)
        VULKAN_COMPAT_REASON=$(echo "$COMPAT_RESULT" | cut -d':' -f2-)
    elif [[ "$HAS_NVIDIA_GPU" == "yes" ]]; then
        # NVIDIA GPUs use CUDA, so Vulkan compatibility is irrelevant
        VULKAN_COMPATIBLE="not_applicable"
        VULKAN_COMPAT_REASON="NVIDIA GPU uses CUDA"
    fi

    # Determine recommendation (Priority: CUDA > Vulkan > CPU)
    # IMPORTANT: The installer WILL install dev libraries (libvulkan-dev, glslc, CUDA) later,
    # so we recommend GPU if there's a compatible GPU regardless of current library status.
    local RECOMMENDED_BACKEND="cpu"
    local RECOMMENDED_REASON=""
    local CAN_BUILD_GPU=false

    # NVIDIA GPU - best option, uses CUDA
    if [[ "$HAS_NVIDIA_GPU" == "yes" ]]; then
        RECOMMENDED_BACKEND="cuda"
        if [[ "$HAS_CUDA_DEV" == "true" ]]; then
            RECOMMENDED_REASON="NVIDIA GPU with CUDA toolkit installed"
        else
            RECOMMENDED_REASON="NVIDIA GPU detected (CUDA toolkit will be installed)"
        fi
        CAN_BUILD_GPU=true
    # Vulkan-compatible GPU (AMD, Intel Gen8+) - second choice
    elif [[ "$HAS_VULKAN" == "yes" && "$VULKAN_COMPATIBLE" == "compatible" ]]; then
        RECOMMENDED_BACKEND="vulkan"
        if [[ "$HAS_VULKAN_DEV" == "true" ]]; then
            RECOMMENDED_REASON="Vulkan GPU detected with dev libraries"
        else
            RECOMMENDED_REASON="Vulkan GPU detected (dev libraries will be installed)"
        fi
        CAN_BUILD_GPU=true
    # Vulkan GPU but compatibility unknown - allow GPU build as fallback
    elif [[ "$HAS_VULKAN" == "yes" && "$VULKAN_COMPATIBLE" == "unknown" ]]; then
        RECOMMENDED_BACKEND="vulkan"
        RECOMMENDED_REASON="Possible Vulkan GPU (will verify during build)"
        CAN_BUILD_GPU=true
    # Incompatible Vulkan GPU (old Intel Gen7) - CPU only
    elif [[ "$VULKAN_COMPATIBLE" == "incompatible" ]]; then
        RECOMMENDED_BACKEND="cpu"
        RECOMMENDED_REASON="Incompatible GPU ($VULKAN_COMPAT_REASON) - CPU mode recommended"
        CAN_BUILD_GPU=false
    else
        RECOMMENDED_BACKEND="cpu"
        RECOMMENDED_REASON="No compatible GPU detected"
        CAN_BUILD_GPU=false
    fi

    echo "${RECOMMENDED_BACKEND}:${RECOMMENDED_REASON}:${CAN_BUILD_GPU}:${HAS_VULKAN}:${HAS_NVIDIA_GPU}:${HAS_VULKAN_DEV}:${HAS_CUDA_DEV}:${VULKAN_COMPATIBLE}:${VULKAN_COMPAT_REASON}"
}
