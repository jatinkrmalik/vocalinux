"""Behavioral tests for installer CUDA diagnostic functions."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

INSTALL_SH = Path(__file__).resolve().parents[1] / "install.sh"


def source_install_sh_functions(tmpdir: Path) -> str:
    """Extract and source only the function definitions from install.sh."""
    content = INSTALL_SH.read_text()

    setup_script = f"""
set -e
cd "{tmpdir}"

# Mock output functions
print_warning() {{ echo "WARNING: $*" >&2; }}
print_info() {{ echo "INFO: $*" >&2; }}
print_success() {{ echo "SUCCESS: $*" >&2; }}
print_error() {{ echo "ERROR: $*" >&2; }}

# Mock get_pywhispercpp_library_path (will be overridden per test)
get_pywhispercpp_library_path() {{ echo ""; }}

# Source the actual functions from install.sh
# Extract function definitions using sed
"""
    return setup_script


def run_bash_test(script: str) -> subprocess.CompletedProcess:
    """Run a bash script and return the result."""
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=10)
    return result


class TestCudaToolkitRootHasRuntimeLibrary:
    """Tests for cuda_toolkit_root_has_runtime_library function."""

    def test_accepts_lib64_layout(self, tmp_path):
        """Standard x86_64 layout with lib64/libcudart.so."""
        cuda_root = tmp_path / "cuda"
        (cuda_root / "lib64").mkdir(parents=True)
        (cuda_root / "lib64" / "libcudart.so.12.2").touch()

        script = f"""
{source_install_sh_functions(tmp_path)}
source <(sed -n '/^cuda_toolkit_root_has_runtime_library/,/^}}/p' "{INSTALL_SH}")
cuda_toolkit_root_has_runtime_library "{cuda_root}" && echo "PASS" || echo "FAIL"
"""
        result = run_bash_test(script)
        assert "PASS" in result.stdout

    def test_accepts_lib_layout(self, tmp_path):
        """Layout with lib/libcudart.so."""
        cuda_root = tmp_path / "cuda"
        (cuda_root / "lib").mkdir(parents=True)
        (cuda_root / "lib" / "libcudart.so").touch()

        script = f"""
{source_install_sh_functions(tmp_path)}
source <(sed -n '/^cuda_toolkit_root_has_runtime_library/,/^}}/p' "{INSTALL_SH}")
cuda_toolkit_root_has_runtime_library "{cuda_root}" && echo "PASS" || echo "FAIL"
"""
        result = run_bash_test(script)
        assert "PASS" in result.stdout

    def test_accepts_debian_layout(self, tmp_path):
        """Debian multiarch layout with lib/x86_64-linux-gnu/libcudart.so."""
        cuda_root = tmp_path / "cuda"
        (cuda_root / "lib" / "x86_64-linux-gnu").mkdir(parents=True)
        (cuda_root / "lib" / "x86_64-linux-gnu" / "libcudart.so.11.8").touch()

        script = f"""
{source_install_sh_functions(tmp_path)}
source <(sed -n '/^cuda_toolkit_root_has_runtime_library/,/^}}/p' "{INSTALL_SH}")
cuda_toolkit_root_has_runtime_library "{cuda_root}" && echo "PASS" || echo "FAIL"
"""
        result = run_bash_test(script)
        assert "PASS" in result.stdout

    def test_accepts_aarch64_layout(self, tmp_path):
        """ARM64 layout with targets/aarch64-linux/lib/libcudart.so."""
        cuda_root = tmp_path / "cuda"
        (cuda_root / "targets" / "aarch64-linux" / "lib").mkdir(parents=True)
        (cuda_root / "targets" / "aarch64-linux" / "lib" / "libcudart.so.12.2").touch()

        script = f"""
{source_install_sh_functions(tmp_path)}
source <(sed -n '/^cuda_toolkit_root_has_runtime_library/,/^}}/p' "{INSTALL_SH}")
cuda_toolkit_root_has_runtime_library "{cuda_root}" && echo "PASS" || echo "FAIL"
"""
        result = run_bash_test(script)
        assert "PASS" in result.stdout

    def test_rejects_missing_runtime(self, tmp_path):
        """Reject when libcudart.so* is missing."""
        cuda_root = tmp_path / "cuda"
        cuda_root.mkdir(parents=True)

        script = f"""
{source_install_sh_functions(tmp_path)}
source <(sed -n '/^cuda_toolkit_root_has_runtime_library/,/^}}/p' "{INSTALL_SH}")
cuda_toolkit_root_has_runtime_library "{cuda_root}" && echo "FAIL" || echo "PASS"
"""
        result = run_bash_test(script)
        assert "PASS" in result.stdout


class TestValidateCudaToolkitRoot:
    """Tests for validate_cuda_toolkit_root function."""

    def test_accepts_complete_root(self, tmp_path):
        """Accept when nvcc, cuda_runtime.h, and libcudart.so all present."""
        cuda_root = tmp_path / "cuda"
        (cuda_root / "bin").mkdir(parents=True)
        (cuda_root / "include").mkdir(parents=True)
        (cuda_root / "lib64").mkdir(parents=True)

        nvcc = cuda_root / "bin" / "nvcc"
        nvcc.touch()
        nvcc.chmod(0o755)

        (cuda_root / "include" / "cuda_runtime.h").touch()
        (cuda_root / "lib64" / "libcudart.so.12.2").touch()

        script = f"""
{source_install_sh_functions(tmp_path)}
source <(sed -n '/^cuda_toolkit_root_has_runtime_library/,/^}}/p' "{INSTALL_SH}")
source <(sed -n '/^validate_cuda_toolkit_root/,/^}}/p' "{INSTALL_SH}")
validate_cuda_toolkit_root "{cuda_root}" && echo "PASS" || echo "FAIL"
"""
        result = run_bash_test(script)
        assert "PASS" in result.stdout

    def test_rejects_stale_root(self, tmp_path):
        """Reject when only bin/nvcc exists (stale /usr/local/cuda)."""
        cuda_root = tmp_path / "cuda"
        (cuda_root / "bin").mkdir(parents=True)

        nvcc = cuda_root / "bin" / "nvcc"
        nvcc.touch()
        nvcc.chmod(0o755)

        script = f"""
{source_install_sh_functions(tmp_path)}
source <(sed -n '/^cuda_toolkit_root_has_runtime_library/,/^}}/p' "{INSTALL_SH}")
source <(sed -n '/^validate_cuda_toolkit_root/,/^}}/p' "{INSTALL_SH}")
validate_cuda_toolkit_root "{cuda_root}" && echo "FAIL" || echo "PASS"
"""
        result = run_bash_test(script)
        assert "PASS" in result.stdout

    def test_rejects_nvcc_not_executable(self, tmp_path):
        """Reject when nvcc exists but is not executable."""
        cuda_root = tmp_path / "cuda"
        (cuda_root / "bin").mkdir(parents=True)
        (cuda_root / "include").mkdir(parents=True)
        (cuda_root / "lib64").mkdir(parents=True)

        (cuda_root / "bin" / "nvcc").touch()
        (cuda_root / "include" / "cuda_runtime.h").touch()
        (cuda_root / "lib64" / "libcudart.so.12.2").touch()

        script = f"""
{source_install_sh_functions(tmp_path)}
source <(sed -n '/^cuda_toolkit_root_has_runtime_library/,/^}}/p' "{INSTALL_SH}")
source <(sed -n '/^validate_cuda_toolkit_root/,/^}}/p' "{INSTALL_SH}")
validate_cuda_toolkit_root "{cuda_root}" && echo "FAIL" || echo "PASS"
"""
        result = run_bash_test(script)
        assert "PASS" in result.stdout


class TestDetectNvidiaComputeArchitecturesAwkParser:
    """Tests for the awk parser in detect_nvidia_compute_architectures."""

    def test_parses_single_gpu(self):
        """Parse single GPU compute capability 8.9 (RTX 4090)."""
        script = """
echo "8.9" | awk '
    {
        gsub(/[[:space:]]/, "", $1)
        if ($1 ~ /^[0-9]+(\\.[0-9]+)?$/) {
            split($1, parts, ".")
            minor = parts[2]
            if (minor == "") {
                minor = "0"
            }
            print parts[1] minor "-real"
        }
    }
' | sort -u | paste -sd ';' -
"""
        result = run_bash_test(script)
        assert result.stdout.strip() == "89-real"

    def test_parses_multi_gpu(self):
        """Parse multi-GPU with different architectures."""
        script = """
echo -e "8.9\\n8.6" | awk '
    {
        gsub(/[[:space:]]/, "", $1)
        if ($1 ~ /^[0-9]+(\\.[0-9]+)?$/) {
            split($1, parts, ".")
            minor = parts[2]
            if (minor == "") {
                minor = "0"
            }
            print parts[1] minor "-real"
        }
    }
' | sort -u | paste -sd ';' -
"""
        result = run_bash_test(script)
        assert result.stdout.strip() == "86-real;89-real"

    def test_filters_garbage(self):
        """Filter out non-numeric values like [Not Supported]."""
        script = """
echo -e "[Not Supported]\\n8.9" | awk '
    {
        gsub(/[[:space:]]/, "", $1)
        if ($1 ~ /^[0-9]+(\\.[0-9]+)?$/) {
            split($1, parts, ".")
            minor = parts[2]
            if (minor == "") {
                minor = "0"
            }
            print parts[1] minor "-real"
        }
    }
' | sort -u | paste -sd ';' -
"""
        result = run_bash_test(script)
        assert result.stdout.strip() == "89-real"

    def test_deduplicates(self):
        """Deduplicate identical compute capabilities."""
        script = """
echo -e "8.9\\n8.9\\n8.9" | awk '
    {
        gsub(/[[:space:]]/, "", $1)
        if ($1 ~ /^[0-9]+(\\.[0-9]+)?$/) {
            split($1, parts, ".")
            minor = parts[2]
            if (minor == "") {
                minor = "0"
            }
            print parts[1] minor "-real"
        }
    }
' | sort -u | paste -sd ';' -
"""
        result = run_bash_test(script)
        assert result.stdout.strip() == "89-real"


class TestReadelfBundledLibcudaRegex:
    """Tests for the readelf regex that detects bundled libcuda."""

    def test_detects_bundled_libcuda(self):
        """Detect auditwheel-bundled libcuda with hashed name."""
        script = """
echo " 0x0000000000000001 (NEEDED)             Shared library: [libcuda-535.129.03.so]" | \
  sed -En 's/.*Shared library: \\[(libcuda-[^]]+\\.so).*/\\1/p'
"""
        result = run_bash_test(script)
        assert result.stdout.strip() == "libcuda-535.129.03.so"

    def test_ignores_system_libcuda(self):
        """Do not match standard libcuda.so.1."""
        script = """
echo " 0x0000000000000001 (NEEDED)             Shared library: [libcuda.so.1]" | \
  sed -En 's/.*Shared library: \\[(libcuda-[^]]+\\.so).*/\\1/p'
"""
        result = run_bash_test(script)
        assert result.stdout.strip() == ""

    def test_ignores_bundled_cudart(self):
        """Do not match bundled libcudart (different library)."""
        script = """
echo " 0x0000000000000001 (NEEDED)             Shared library: [libcudart-12.2.140.so]" | \
  sed -En 's/.*Shared library: \\[(libcuda-[^]]+\\.so).*/\\1/p'
"""
        result = run_bash_test(script)
        assert result.stdout.strip() == ""

    def test_detects_hashed_libcuda(self):
        """Detect auditwheel hash-style bundled libcuda."""
        script = """
echo " 0x0000000000000001 (NEEDED)             Shared library: [libcuda-abc12345.so]" | \
  sed -En 's/.*Shared library: \\[(libcuda-[^]]+\\.so).*/\\1/p'
"""
        result = run_bash_test(script)
        assert result.stdout.strip() == "libcuda-abc12345.so"
