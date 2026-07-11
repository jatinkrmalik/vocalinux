"""Regression guards for installer contracts fixed by #451 and #496."""

from pathlib import Path

INSTALLER_SOURCE = (Path(__file__).resolve().parents[1] / "install.sh").read_text(encoding="utf-8")


def test_installer_disables_user_site_packages():
    assert INSTALLER_SOURCE.count("export PYTHONNOUSERSITE=1") >= 4
    assert 'getattr(site, "ENABLE_USER_SITE", False)' in INSTALLER_SOURCE


def test_cuda_build_keeps_validation_diagnostics_and_cpu_fallback():
    required = (
        "validate_cuda_toolkit_root()",
        "$CUDA_ROOT/bin/nvcc",
        "$CUDA_ROOT/include/cuda_runtime.h",
        "-DCUDAToolkit_ROOT=$CUDA_ROOT",
        "-DCMAKE_CUDA_COMPILER=$CUDA_ROOT/bin/nvcc",
        "-DCMAKE_CUDA_ARCHITECTURES=$CUDA_ARCHS",
        "GGML_CUDA=1",
        "print_pip_log_tail()",
        "CUDA build failed.",
        "Continuing with CPU-only pywhispercpp; GPU acceleration is not active.",
        "verify_pywhispercpp_backend_install()",
        "libggml-vulkan.so",
        "libggml-cuda.so",
        "libcuda.so.1",
        "--replace-needed",
    )
    for snippet in required:
        assert snippet in INSTALLER_SOURCE


def test_all_distro_package_lists_keep_clipboard_fallbacks():
    package_lists = (
        "local APT_PACKAGES_UBUNTU=",
        "local APT_PACKAGES_DEBIAN_BASE=",
        "local DNF_PACKAGES=",
        "local PACMAN_PACKAGES=",
        "local ZYPPER_PACKAGES=",
        "local EMERGE_PACKAGES=",
        "local APK_PACKAGES=",
        "local XBPS_PACKAGES=",
        "local EOPKG_PACKAGES=",
    )
    for name in package_lists:
        line = next(line for line in INSTALLER_SOURCE.splitlines() if name in line)
        assert all(package in line for package in ("xclip", "xsel", "wl-clipboard"))
