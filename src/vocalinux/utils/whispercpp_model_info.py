"""
Whisper.cpp model information and hardware detection for Vocalinux.

This module provides model metadata and hardware acceleration detection
for whisper.cpp, supporting Vulkan, CUDA, and CPU backends.
"""

import logging
import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Whisper.cpp model information
# Models are downloaded from Hugging Face (ggml format)
_WHISPERCPP_REPO_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main"


def _model_url(model_name: str) -> str:
    """Build the Hugging Face URL for a ggml whisper.cpp model."""
    file_model_name = "large-v3" if model_name == "large" else model_name
    return f"{_WHISPERCPP_REPO_URL}/ggml-{file_model_name}.bin"


_WHISPERCPP_MODEL_SPECS = [
    ("tiny", 74, "39M", "Fastest, lowest accuracy"),
    ("tiny.en", 74, "39M", "English-only tiny model"),
    ("tiny-q5_1", 15, "39M", "Quantized tiny model, lowest memory"),
    ("tiny.en-q5_1", 15, "39M", "Quantized English-only tiny model"),
    ("tiny-q8_0", 32, "39M", "Q8 quantized tiny model"),
    ("base", 141, "74M", "Fast, good for basic use"),
    ("base.en", 141, "74M", "English-only base model"),
    ("base-q5_1", 60, "74M", "Quantized base model, lower memory"),
    ("base.en-q5_1", 60, "74M", "Quantized English-only base model"),
    ("base-q8_0", 82, "74M", "Q8 quantized base model"),
    ("small", 465, "244M", "Balanced speed/accuracy"),
    ("small.en", 465, "244M", "English-only small model"),
    ("small-q5_1", 163, "244M", "Quantized small model, lower memory"),
    ("small.en-q5_1", 163, "244M", "Quantized English-only small model"),
    ("small-q8_0", 190, "244M", "Q8 quantized small model"),
    ("medium", 1463, "769M", "High accuracy, slower"),
    ("medium.en", 1463, "769M", "English-only medium model"),
    ("medium-q5_0", 568, "769M", "Quantized medium model, lower memory"),
    ("medium.en-q5_0", 568, "769M", "Quantized English-only medium model"),
    ("medium-q8_0", 823, "769M", "Q8 quantized medium model"),
    ("large-v1", 2952, "1550M", "Legacy large v1 model"),
    ("large-v2", 2952, "1550M", "Legacy large v2 model"),
    ("large-v2-q5_0", 1170, "1550M", "Quantized large v2 model, lower memory"),
    ("large-v2-q8_0", 1660, "1550M", "Q8 quantized large v2 model"),
    ("large", 2952, "1550M", "Highest accuracy, maps to large v3"),
    ("large-v3-q5_0", 1170, "1550M", "Quantized large v3 model, lower memory"),
    ("large-v3-turbo", 1620, "809M", "High accuracy, lower memory than large"),
    ("large-v3-turbo-q5_0", 574, "809M", "Quantized large v3 Turbo model"),
    ("large-v3-turbo-q8_0", 874, "809M", "Q8 quantized large v3 Turbo model"),
]

WHISPERCPP_MODEL_INFO = {
    spec[0]: {
        "size_mb": spec[1],
        "params": spec[2],
        "desc": spec[3],
        "url": _model_url(spec[0]),
    }
    for spec in _WHISPERCPP_MODEL_SPECS
}

# Available models list
AVAILABLE_MODELS = list(WHISPERCPP_MODEL_INFO.keys())

MODEL_SIZES = ["tiny", "base", "small", "medium", "large"]

MODEL_VARIANTS_BY_SIZE = {
    "tiny": ["tiny", "tiny.en", "tiny-q5_1", "tiny.en-q5_1", "tiny-q8_0"],
    "base": ["base", "base.en", "base-q5_1", "base.en-q5_1", "base-q8_0"],
    "small": [
        "small",
        "small.en",
        "small-q5_1",
        "small.en-q5_1",
        "small-q8_0",
    ],
    "medium": ["medium", "medium.en", "medium-q5_0", "medium.en-q5_0", "medium-q8_0"],
    "large": [
        "large",
        "large-v3-q5_0",
        "large-v3-turbo",
        "large-v3-turbo-q5_0",
        "large-v3-turbo-q8_0",
        "large-v2",
        "large-v2-q5_0",
        "large-v2-q8_0",
        "large-v1",
    ],
}


def get_model_size(model_name: str) -> str:
    """Return the top-level whisper.cpp size bucket for a model variant."""
    model_name = model_name.lower()
    if model_name.startswith("large"):
        return "large"
    return model_name.split(".", 1)[0].split("-", 1)[0]


def get_model_variants(model_size: str) -> list[str]:
    """Return available whisper.cpp variants for a size bucket."""
    return list(MODEL_VARIANTS_BY_SIZE.get(model_size.lower(), []))


def is_english_only_model(model_name: str) -> bool:
    """Return whether a whisper.cpp model variant is English-only."""
    return ".en" in model_name.lower()


# Compute backend types
class ComputeBackend:
    """Compute backend options for whisper.cpp."""

    VULKAN = "vulkan"
    CUDA = "cuda"
    CPU = "cpu"


def _normalize_gpu_name(name: str) -> str:
    """Normalize a GPU name for case-insensitive comparisons."""
    return re.sub(r"\s+", " ", name.strip()).casefold()


def get_whispercpp_compiled_backends() -> set[str]:
    """Detect which optional ggml backends are compiled into the active pywhispercpp install."""
    backends: set[str] = {ComputeBackend.CPU}

    try:
        import pywhispercpp
    except ImportError:
        return backends

    module_file = getattr(pywhispercpp, "__file__", None)
    if not module_file:
        return backends

    package_root = Path(module_file).resolve().parent.parent
    libs_dir = package_root / "pywhispercpp.libs"
    if not libs_dir.exists():
        return backends

    for lib_path in libs_dir.glob("libggml-*.so"):
        lib_name = lib_path.name.lower()
        if "vulkan" in lib_name:
            backends.add(ComputeBackend.VULKAN)
        if "cuda" in lib_name:
            backends.add(ComputeBackend.CUDA)

    return backends


def _parse_visible_device_indices(env_var: str) -> Optional[list[int]]:
    """Parse a comma-separated visible-device environment variable."""
    raw_value = os.environ.get(env_var)
    if raw_value is None:
        return None

    indices: list[int] = []
    for raw_part in raw_value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        try:
            indices.append(int(part))
        except ValueError:
            logger.debug("Ignoring invalid %s entry: %s", env_var, part)

    return indices


def _filter_devices_by_visible_env(
    devices: list[tuple[int, str]], env_var: str
) -> list[tuple[int, str]]:
    """Filter enumerated devices to the indices made visible via environment variables."""
    visible_indices = _parse_visible_device_indices(env_var)
    if visible_indices is None:
        return devices

    filtered_devices = [device for device in devices if device[0] in visible_indices]
    if filtered_devices:
        return filtered_devices

    logger.debug(
        "%s=%s did not match any enumerated devices; falling back to the full device list",
        env_var,
        os.environ.get(env_var),
    )
    return devices


def list_vulkan_devices() -> list[tuple[int, str]]:
    """
    Enumerate Vulkan devices visible to the current process.

    Returns:
        List of ``(index, name)`` tuples in the order reported by Vulkan.
    """
    devices: list[tuple[int, str]] = []

    try:
        result = subprocess.run(
            ["vulkaninfo", "--summary"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return devices

        for line in result.stdout.splitlines():
            match = re.search(r"deviceName\s*[:=]\s*(.+)$", line)
            if not match:
                continue

            device_name = match.group(1).strip()
            if device_name:
                devices.append((len(devices), device_name))
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"Vulkan device enumeration failed: {e}")

    return devices


def list_cuda_devices() -> list[tuple[int, str]]:
    """
    Enumerate CUDA devices visible to the current process.

    Returns:
        List of ``(index, name)`` tuples in the order reported by ``nvidia-smi``.
    """
    devices: list[tuple[int, str]] = []

    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return devices

        for line in result.stdout.splitlines():
            raw_line = line.strip()
            if not raw_line:
                continue

            parts = [part.strip() for part in raw_line.split(",", 1)]
            if len(parts) != 2:
                continue

            try:
                device_index = int(parts[0])
            except ValueError:
                continue

            devices.append((device_index, parts[1]))
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"CUDA device enumeration failed: {e}")

    return devices


def resolve_gpu_selection(
    requested_name: str,
    allowed_backends: Optional[list[str]] = None,
    preferred_backend: Optional[str] = None,
) -> tuple[str, int, str]:
    """
    Resolve a persisted GPU name to the currently visible backend and device index.

    Args:
        requested_name: User-provided or persisted GPU name.
        allowed_backends: Optional list of allowed backends to search.
        preferred_backend: Optional backend to prefer when names match multiple backends.

    Returns:
        Tuple of ``(backend, device_index, resolved_device_name)``.

    Raises:
        ValueError: If the named GPU cannot be found.
    """
    backend_sources = {
        ComputeBackend.VULKAN: list_vulkan_devices,
        ComputeBackend.CUDA: list_cuda_devices,
    }

    allowed = allowed_backends or [ComputeBackend.VULKAN, ComputeBackend.CUDA]
    backend_order = list(allowed)
    if preferred_backend in backend_order:
        backend_order.remove(preferred_backend)
        backend_order.insert(0, preferred_backend)

    normalized_request = _normalize_gpu_name(requested_name)
    exact_matches: list[tuple[str, int, str]] = []
    partial_matches: list[tuple[str, int, str]] = []
    available_devices: list[str] = []

    for backend in backend_order:
        enumerator = backend_sources.get(backend)
        if enumerator is None:
            continue

        for device_index, device_name in enumerator():
            available_devices.append(f"{backend}:{device_name}")
            normalized_device = _normalize_gpu_name(device_name)
            candidate = (backend, device_index, device_name)

            if normalized_device == normalized_request:
                exact_matches.append(candidate)
            elif normalized_request and normalized_request in normalized_device:
                partial_matches.append(candidate)

    if exact_matches:
        return exact_matches[0]

    if len(partial_matches) == 1:
        return partial_matches[0]

    if len(partial_matches) > 1:
        matches = ", ".join(f"{backend}:{name}" for backend, _, name in partial_matches)
        raise ValueError(f"GPU name '{requested_name}' is ambiguous. Matching devices: {matches}")

    available = ", ".join(available_devices) if available_devices else "none"
    raise ValueError(f"GPU '{requested_name}' not found. Available GPUs: {available}")


@lru_cache(maxsize=1)
def detect_vulkan_support() -> tuple[bool, Optional[str]]:
    """
    Detect if Vulkan is available and get device info.

    Returns:
        Tuple of (is_available, device_name)
    """
    try:
        devices = _filter_devices_by_visible_env(list_vulkan_devices(), "GGML_VK_VISIBLE_DEVICES")
        if devices:
            _, device_name = devices[0]
            logger.info(f"Vulkan support detected: {device_name}")
            return True, device_name
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"Vulkan detection failed: {e}")

    return False, None


@lru_cache(maxsize=1)
def detect_cuda_support() -> tuple[bool, Optional[str]]:
    """
    Detect if NVIDIA CUDA is available and get device info.

    Returns:
        Tuple of (is_available, device_info)
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            devices: list[tuple[int, str, str]] = []
            for line in result.stdout.splitlines():
                raw_line = line.strip()
                if not raw_line:
                    continue

                parts = [part.strip() for part in raw_line.split(",", 2)]
                if len(parts) < 2:
                    continue

                try:
                    device_index = int(parts[0])
                except ValueError:
                    continue

                gpu_name = parts[1]
                gpu_memory = parts[2] if len(parts) > 2 else "unknown"
                devices.append((device_index, gpu_name, gpu_memory))

            visible_indices = _parse_visible_device_indices("CUDA_VISIBLE_DEVICES")
            if visible_indices is not None:
                filtered_devices = [device for device in devices if device[0] in visible_indices]
                if filtered_devices:
                    devices = filtered_devices

            if devices:
                _, gpu_name, gpu_memory = devices[0]
                logger.info(f"CUDA support detected: {gpu_name} ({gpu_memory})")
                return True, f"{gpu_name} ({gpu_memory})"
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"CUDA detection failed: {e}")

    return False, None


@lru_cache(maxsize=1)
def detect_compute_backend() -> tuple[str, str]:
    """
    Detect the best available compute backend.

    Priority order: Vulkan > CUDA > CPU

    Returns:
        Tuple of (backend_type, backend_info)
    """
    # Try Vulkan first (supports AMD, Intel, NVIDIA)
    has_vulkan, vulkan_info = detect_vulkan_support()
    if has_vulkan and vulkan_info:
        return ComputeBackend.VULKAN, vulkan_info

    # Try CUDA next (NVIDIA only)
    has_cuda, cuda_info = detect_cuda_support()
    if has_cuda and cuda_info:
        return ComputeBackend.CUDA, cuda_info

    # Fall back to CPU
    cpu_info = detect_cpu_info()
    return ComputeBackend.CPU, cpu_info


@lru_cache(maxsize=1)
def detect_cpu_info() -> str:
    """
    Detect CPU information for CPU backend.

    Returns:
        CPU info string
    """
    try:
        # Try to get CPU model from /proc/cpuinfo
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    cpu_name = line.split(":")[1].strip()
                    return cpu_name
    except Exception as e:
        logger.debug(f"Could not read CPU info: {e}")

    # Fallback to nproc
    try:
        result = subprocess.run(
            ["nproc"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            cpu_count = result.stdout.strip()
            return f"{cpu_count} cores"
    except Exception:
        pass

    return "CPU"


def get_recommended_model() -> tuple[str, str]:
    """
    Get the recommended whisper.cpp model based on system configuration.

    Returns:
        Tuple of (model_name, reason)
    """
    try:
        import psutil

        ram_gb = psutil.virtual_memory().total // (1024**3)

        # Detect available compute backends
        backend, backend_info = detect_compute_backend()

        if backend == ComputeBackend.VULKAN:
            # Vulkan can handle larger models efficiently
            if ram_gb >= 8:
                return "small", f"Vulkan GPU with {ram_gb}GB RAM"
            else:
                return "base", f"Vulkan GPU with {ram_gb}GB RAM"
        elif backend == ComputeBackend.CUDA:
            # CUDA has more VRAM typically
            if "GB" in backend_info:
                try:
                    vram_gb = int(backend_info.split("GB")[0].split("(")[-1].strip())
                    if vram_gb >= 8:
                        return "medium", f"CUDA GPU with {vram_gb}GB VRAM"
                    elif vram_gb >= 4:
                        return "small", f"CUDA GPU with {vram_gb}GB VRAM"
                    else:
                        return "base", f"CUDA GPU with limited VRAM"
                except (ValueError, IndexError):
                    pass
            return "small", f"CUDA GPU detected"
        else:
            # CPU-only recommendations based on RAM
            if ram_gb >= 16:
                return "base", f"{ram_gb}GB RAM - CPU inference"
            elif ram_gb >= 8:
                return "tiny", f"{ram_gb}GB RAM - optimized for speed"
            else:
                return "tiny", f"Limited RAM ({ram_gb}GB) - fastest model"

    except ImportError:
        logger.debug("psutil not available for system detection")

    # Default recommendation
    return "tiny", "Default recommendation"


def get_model_path(model_name: str) -> str:
    """
    Get the path where a model should be stored.

    Args:
        model_name: Name of the model (for example tiny, base, small, medium, large)

    Returns:
        Path to the model file
    """
    models_dir = os.path.expanduser("~/.local/share/vocalinux/models/whispercpp")
    os.makedirs(models_dir, exist_ok=True)

    model_info = WHISPERCPP_MODEL_INFO.get(model_name)
    if model_info and model_info.get("url"):
        return os.path.join(models_dir, os.path.basename(model_info["url"]))

    return os.path.join(models_dir, f"ggml-{model_name}.bin")


def is_model_downloaded(model_name: str) -> bool:
    """
    Check if a whisper.cpp model is downloaded.

    Args:
        model_name: Name of the model

    Returns:
        True if model exists, False otherwise
    """
    model_path = get_model_path(model_name)
    return os.path.exists(model_path)


def get_backend_display_name(backend: str) -> str:
    """
    Get a user-friendly display name for a compute backend.

    Args:
        backend: Backend type (vulkan, cuda, cpu)

    Returns:
        Display name string
    """
    names = {
        ComputeBackend.VULKAN: "Vulkan GPU",
        ComputeBackend.CUDA: "NVIDIA CUDA",
        ComputeBackend.CPU: "CPU",
    }
    return names.get(backend, backend.upper())
