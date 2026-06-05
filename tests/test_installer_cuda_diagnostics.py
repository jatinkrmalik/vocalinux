"""Regression checks for installer CUDA diagnostics."""

import unittest
from pathlib import Path

INSTALLER = Path(__file__).resolve().parents[1] / "install.sh"


def _installer_source() -> str:
    return INSTALLER.read_text(encoding="utf-8")


class InstallerCudaDiagnosticsTests(unittest.TestCase):
    def test_installer_disables_user_site_packages(self) -> None:
        """Keep user-site packages out of the venv, activation script, and wrappers."""
        source = _installer_source()

        self.assertGreaterEqual(source.count("export PYTHONNOUSERSITE=1"), 4)
        self.assertIn('getattr(site, "ENABLE_USER_SITE", False)', source)

    def test_cuda_toolkit_validation_requires_complete_root(self) -> None:
        """CUDA roots must not be accepted when only a stale /usr/local/cuda exists."""
        source = _installer_source()

        self.assertIn("validate_cuda_toolkit_root()", source)
        self.assertIn("$CUDA_ROOT/bin/nvcc", source)
        self.assertIn("$CUDA_ROOT/include/cuda_runtime.h", source)
        self.assertIn("$CUDA_ROOT/lib64/libcudart.so*", source)
        self.assertIn("Ignoring incomplete CUDA toolkit root", source)

    def test_cuda_build_passes_explicit_cmake_toolkit_and_architecture(self) -> None:
        """CUDA builds should steer CMake away from stale defaults."""
        source = _installer_source()

        self.assertIn("-DCUDAToolkit_ROOT=$CUDA_ROOT", source)
        self.assertIn("-DCMAKE_CUDA_COMPILER=$CUDA_ROOT/bin/nvcc", source)
        self.assertIn("-DCMAKE_CUDA_ARCHITECTURES=$CUDA_ARCHS", source)
        self.assertIn("CUDA_CMAKE_ARGS=$(get_cuda_cmake_args", source)
        self.assertIn("GGML_CUDA=1", source)

    def test_gpu_build_failures_print_pip_log_tail_before_cpu_fallback(self) -> None:
        """Backend failures should expose the real pip/CMake log."""
        source = _installer_source()

        self.assertIn("print_pip_log_tail()", source)
        self.assertIn("Vulkan build failed; checking for NVIDIA GPU to try CUDA", source)
        self.assertIn("CUDA build failed.", source)
        self.assertIn(
            "Continuing with CPU-only pywhispercpp; GPU acceleration is not active.",
            source,
        )

    def test_backend_verification_checks_gpu_libraries_and_cuda_linkage(self) -> None:
        """Do not report GPU support unless native backend libraries exist."""
        source = _installer_source()

        self.assertIn("verify_pywhispercpp_backend_install()", source)
        self.assertIn("libggml-vulkan.so", source)
        self.assertIn("libggml-cuda.so", source)
        self.assertIn("libcuda.so.1", source)
        self.assertIn("libcuda-[^]]+\\.so", source)


if __name__ == "__main__":
    unittest.main()
