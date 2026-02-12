"""
Whisper.cpp model information and hardware detection for Vocalinux.

This module provides model metadata and hardware acceleration detection
for whisper.cpp, supporting Vulkan, CUDA, and CPU backends.
"""

import logging
import os
import subprocess
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Whisper.cpp model information
# Models are downloaded from Hugging Face (ggml format)
WHISPERCPP_MODEL_INFO = {
    "tiny": {
        "size_mb": 39,
        "params": "39M",
        "desc": "Fastest, lowest accuracy",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
    },
    "base": {
        "size_mb": 74,
        "params": "74M",
        "desc": "Fast, good for basic use",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
    },
    "small": {
        "size_mb": 244,
        "params": "244M",
        "desc": "Balanced speed/accuracy",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
    },
    "medium": {
        "size_mb": 769,
        "params": "769M",
        "desc": "High accuracy, slower",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
    },
    "large": {
        "size_mb": 1550,
        "params": "1550M",
        "desc": "Highest accuracy, slowest",
        "url": "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3.bin",
    },
}

# Available models list
AVAILABLE_MODELS = list(WHISPERCPP_MODEL_INFO.keys())

# Compute backend types
class ComputeBackend:
    """Compute backend options for whisper.cpp."""

    VULKAN = "vulkan"
    CUDA = "cuda"
    CPU = "cpu"


def detect_vulkan_support() -> Tuple[bool, Optional[str]]:
    """
    Detect if Vulkan is available and get device info.

    Returns:
        Tuple of (is_available, device_name)
    """
    try:
        # Check for vulkaninfo command
        result = subprocess.run(
            ["vulkaninfo", "--summary"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Try to extract GPU name from output
            for line in result.stdout.split("\n"):
                if "deviceName" in line or "GPU" in line:
                    device_name = line.split(":")[-1].strip()
                    if device_name:
                        logger.info(f"Vulkan support detected: {device_name}")
                        return True, device_name
            logger.info("Vulkan support detected")
            return True, "Vulkan GPU"
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"Vulkan detection failed: {e}")

    return False, None


def detect_cuda_support() -> Tuple[bool, Optional[str]]:
    """
    Detect if NVIDIA CUDA is available and get device info.

    Returns:
        Tuple of (is_available, device_info)
    """
    try:
        # Check for nvidia-smi
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            gpu_info = result.stdout.strip().split(",")
            if gpu_info:
                gpu_name = gpu_info[0].strip()
                gpu_memory = gpu_info[1].strip() if len(gpu_info) > 1 else "unknown"
                logger.info(f"CUDA support detected: {gpu_name} ({gpu_memory})")
                return True, f"{gpu_name} ({gpu_memory})"
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"CUDA detection failed: {e}")

    return False, None


def detect_compute_backend() -> Tuple[str, str]:
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


def get_recommended_model() -> Tuple[str, str]:
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
        model_name: Name of the model (tiny, base, small, medium, large)

    Returns:
        Path to the model file
    """
    models_dir = os.path.expanduser("~/.local/share/vocalinux/models/whispercpp")
    os.makedirs(models_dir, exist_ok=True)

    if model_name == "large":
        # Large model uses v3 variant
        return os.path.join(models_dir, "ggml-large-v3.bin")
    else:
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
