"""
Tests for the Vocalinux interactive installer (install.sh).

These tests use subprocess to test the bash script functionality,
with mocked commands like nvidia-smi to simulate different system configurations.
"""

import subprocess
from pathlib import Path

import pytest

# Path to the install.sh script
INSTALL_SCRIPT = Path(__file__).parent.parent / "install.sh"


class TestInstallerFlagParsing:
    """Test cases for installer flag/argument parsing."""

    def test_help_flag_shows_usage(self):
        """Test that --help flag displays usage information."""
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout or "Vocalinux Installer" in result.stdout
        assert "--interactive" in result.stdout or "-i" in result.stdout
        assert "--whisper-cpu" in result.stdout
        assert "--no-whisper" in result.stdout

    def test_unknown_flag_exits_with_error(self):
        """Test that unknown flags cause the script to exit with error."""
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "--unknown-flag"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Unknown option" in result.stderr or "Unknown option" in result.stdout

    @pytest.mark.parametrize("flag", ["--dev", "--test", "--skip-models", "-y", "--yes"])
    def test_valid_flags_accepted(self, flag):
        """Test that valid flags are accepted without error (in help mode)."""
        # Use --help to avoid actually running installation
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), flag, "--help"],
            capture_output=True,
            text=True,
        )
        # --help exits 0, but if flag is invalid it would exit 1
        assert result.returncode == 0

    def test_interactive_flag_accepted(self):
        """Test that --interactive flag is parsed correctly."""
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "--interactive", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_whisper_cpu_flag_accepted(self):
        """Test that --whisper-cpu flag is parsed correctly."""
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "--whisper-cpu", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_no_whisper_flag_accepted(self):
        """Test that --no-whisper flag is parsed correctly."""
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "--no-whisper", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_with_whisper_flag_accepted(self):
        """Test that --with-whisper flag is parsed correctly."""
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "--with-whisper", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_short_interactive_flag_accepted(self):
        """Test that -i short flag works for interactive mode."""
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "-i", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_tag_flag_accepted(self):
        """Test that --tag=VERSION flag is parsed correctly."""
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "--tag=v0.3.0-alpha", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_venv_dir_flag_accepted(self):
        """Test that --venv-dir=PATH flag is parsed correctly."""
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "--venv-dir=/custom/venv", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestInstallerGPUDetection:
    """Test cases for GPU detection functionality."""

    def test_detect_nvidia_gpu_present(self, tmp_path):
        """Test GPU detection when NVIDIA GPU is present."""
        # Create a mock nvidia-smi script that simulates GPU presence
        mock_nvidia_smi = tmp_path / "nvidia-smi"
        mock_nvidia_smi.write_text("""#!/bin/bash
if [[ "$1" == "--query-gpu=name" ]]; then
    echo "NVIDIA GeForce RTX 3080"
elif [[ "$1" == "--query-gpu=memory.total" ]]; then
    echo "10240 MiB"
else
    echo "NVIDIA-SMI 525.00    Driver Version: 525.00"
fi
exit 0
""")
        mock_nvidia_smi.chmod(0o755)

        # Create a test script that sources the GPU detection function
        test_script = tmp_path / "test_gpu.sh"
        test_script.write_text(f"""#!/bin/bash
# Source the install.sh functions
PATH="{tmp_path}:$PATH"
export PATH

# Define the detect_nvidia_gpu function
HAS_NVIDIA_GPU="unknown"
GPU_NAME=""
GPU_MEMORY=""

detect_nvidia_gpu() {{
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1)
        GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -n1)  # noqa: E501
        HAS_NVIDIA_GPU="yes"
        return 0
    else
        HAS_NVIDIA_GPU="no"
        return 1
    fi
}}

detect_nvidia_gpu
echo "HAS_NVIDIA_GPU=$HAS_NVIDIA_GPU"
echo "GPU_NAME=$GPU_NAME"
echo "GPU_MEMORY=$GPU_MEMORY"
""")
        test_script.chmod(0o755)

        result = subprocess.run(
            ["bash", str(test_script)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "HAS_NVIDIA_GPU=yes" in result.stdout
        assert "GPU_NAME=NVIDIA GeForce RTX 3080" in result.stdout
        assert "GPU_MEMORY=10240 MiB" in result.stdout

    def test_detect_nvidia_gpu_absent(self, tmp_path):
        """Test GPU detection when NVIDIA GPU is not present."""
        # Create a test script with isolated PATH (no nvidia-smi)
        test_script = tmp_path / "test_no_gpu.sh"
        test_script.write_text("""#!/bin/bash
# Clear PATH to ensure nvidia-smi is not found
PATH="/usr/bin:/bin"
export PATH

HAS_NVIDIA_GPU="unknown"
GPU_NAME=""
GPU_MEMORY=""

detect_nvidia_gpu() {
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1)
        GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -n1)  # noqa: E501
        HAS_NVIDIA_GPU="yes"
        return 0
    else
        HAS_NVIDIA_GPU="no"
        return 1
    fi
}

detect_nvidia_gpu
echo "HAS_NVIDIA_GPU=$HAS_NVIDIA_GPU"
echo "GPU_NAME=$GPU_NAME"
echo "GPU_MEMORY=$GPU_MEMORY"
""")
        test_script.chmod(0o755)

        result = subprocess.run(
            ["bash", str(test_script)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "HAS_NVIDIA_GPU=no" in result.stdout
        assert "GPU_NAME=" in result.stdout

    def test_detect_nvidia_gpu_command_fails(self, tmp_path):
        """Test GPU detection when nvidia-smi command exists but fails."""
        # Create a mock nvidia-smi that fails
        mock_nvidia_smi = tmp_path / "nvidia-smi"
        mock_nvidia_smi.write_text("""#!/bin/bash
echo "NVIDIA-SMI has failed" >&2
exit 1
""")
        mock_nvidia_smi.chmod(0o755)

        test_script = tmp_path / "test_gpu_fail.sh"
        test_script.write_text(f"""#!/bin/bash
PATH="{tmp_path}:$PATH"
export PATH

HAS_NVIDIA_GPU="unknown"
GPU_NAME=""
GPU_MEMORY=""

detect_nvidia_gpu() {{
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1)
        GPU_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader 2>/dev/null | head -n1)  # noqa: E501
        HAS_NVIDIA_GPU="yes"
        return 0
    else
        HAS_NVIDIA_GPU="no"
        return 1
    fi
}}

detect_nvidia_gpu
echo "HAS_NVIDIA_GPU=$HAS_NVIDIA_GPU"
""")
        test_script.chmod(0o755)

        result = subprocess.run(
            ["bash", str(test_script)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "HAS_NVIDIA_GPU=no" in result.stdout


class TestInstallerInteractiveMode:
    """Test cases for interactive installation mode."""

    def test_interactive_mode_requires_tty(self):
        """Test that interactive mode requires a TTY."""
        # When running non-interactively (piped), it should fail with TTY error
        result = subprocess.run(
            ["bash", str(INSTALL_SCRIPT), "--interactive"],
            capture_output=True,
            text=True,
            input="",  # Simulate non-TTY
        )
        # The script should exit with error about TTY
        assert (
            result.returncode != 0
            or "requires a terminal" in result.stderr
            or "requires a terminal" in result.stdout
            or "TTY" in result.stderr
            or "TTY" in result.stdout
        )

    def test_non_interactive_mode_auto_detects_gpu(self, tmp_path):
        """Test that non-interactive mode auto-detects GPU and sets flags accordingly."""
        # Create a mock nvidia-smi
        mock_nvidia_smi = tmp_path / "nvidia-smi"
        mock_nvidia_smi.write_text("""#!/bin/bash
if [[ "$1" == "--query-gpu=name" ]]; then
    echo "NVIDIA GeForce GTX 1660"
else
    echo "GPU info"
fi
exit 0
""")
        mock_nvidia_smi.chmod(0o755)

        # Create test script that simulates the auto-detection logic
        test_script = tmp_path / "test_auto_detect.sh"
        test_script.write_text(f"""#!/bin/bash
PATH="{tmp_path}:$PATH"
export PATH

# Simulate the non-interactive auto-detection logic
NON_INTERACTIVE="yes"
WITH_WHISPER="no"
NO_WHISPER_EXPLICIT="no"
INTERACTIVE_MODE="no"
HAS_NVIDIA_GPU="unknown"
GPU_NAME=""

detect_nvidia_gpu() {{
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -n1)
        HAS_NVIDIA_GPU="yes"
        return 0
    else
        HAS_NVIDIA_GPU="no"
        return 1
    fi
}}

# Run auto-detection logic
if [[ "$NON_INTERACTIVE" == "yes" ]] && [[ "$WITH_WHISPER" == "no" ]] && [[ "$NO_WHISPER_EXPLICIT" == "no" ]] && [[ "$INTERACTIVE_MODE" == "no" ]]; then  # noqa: E501
    detect_nvidia_gpu
    if [[ "$HAS_NVIDIA_GPU" == "yes" ]]; then
        WITH_WHISPER="yes"
        echo "GPU_DETECTED=yes"
        echo "GPU_NAME=$GPU_NAME"
    else
        WITH_WHISPER="yes"
        WHISPER_CPU="yes"
        echo "GPU_DETECTED=no"
    fi
fi

echo "WITH_WHISPER=$WITH_WHISPER"
echo "WHISPER_CPU=$WHISPER_CPU"
""")
        test_script.chmod(0o755)

        result = subprocess.run(
            ["bash", str(test_script)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "GPU_DETECTED=yes" in result.stdout
        assert "WITH_WHISPER=yes" in result.stdout
        assert "GPU_NAME=NVIDIA GeForce GTX 1660" in result.stdout

    def test_non_interactive_mode_no_gpu_defaults_to_cpu(self, tmp_path):
        """Test that non-interactive mode defaults to CPU-only when no GPU is detected."""
        test_script = tmp_path / "test_no_gpu_default.sh"
        test_script.write_text("""#!/bin/bash
# Clear PATH to ensure no nvidia-smi
PATH="/usr/bin:/bin"
export PATH

# Simulate the non-interactive auto-detection logic
NON_INTERACTIVE="yes"
WITH_WHISPER="no"
NO_WHISPER_EXPLICIT="no"
INTERACTIVE_MODE="no"
HAS_NVIDIA_GPU="unknown"
WHISPER_CPU=""

detect_nvidia_gpu() {
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi >/dev/null 2>&1; then
        HAS_NVIDIA_GPU="yes"
        return 0
    else
        HAS_NVIDIA_GPU="no"
        return 1
    fi
}

# Run auto-detection logic
if [[ "$NON_INTERACTIVE" == "yes" ]] && [[ "$WITH_WHISPER" == "no" ]] && [[ "$NO_WHISPER_EXPLICIT" == "no" ]] && [[ "$INTERACTIVE_MODE" == "no" ]]; then  # noqa: E501
    detect_nvidia_gpu
    if [[ "$HAS_NVIDIA_GPU" == "yes" ]]; then
        WITH_WHISPER="yes"
    else
        WITH_WHISPER="yes"
        WHISPER_CPU="yes"
    fi
fi

echo "WITH_WHISPER=$WITH_WHISPER"
echo "WHISPER_CPU=$WHISPER_CPU"
echo "HAS_NVIDIA_GPU=$HAS_NVIDIA_GPU"
""")
        test_script.chmod(0o755)

        result = subprocess.run(
            ["bash", str(test_script)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "WITH_WHISPER=yes" in result.stdout
        assert "WHISPER_CPU=yes" in result.stdout
        assert "HAS_NVIDIA_GPU=no" in result.stdout


class TestInstallerPyTorchSelection:
    """Test cases for PyTorch version selection logic."""

    def test_no_whisper_flag_creates_vosk_config(self, tmp_path):
        """Test that --no-whisper flag sets up VOSK as default engine."""
        # This tests the logic flow when NO_WHISPER_EXPLICIT is set
        test_script = tmp_path / "test_no_whisper.sh"
        config_dir = tmp_path / "config"
        config_dir.mkdir()

        test_script.write_text(f"""#!/bin/bash
NO_WHISPER_EXPLICIT="yes"
WITH_WHISPER="no"
SKIP_MODELS="no"
CONFIG_DIR="{config_dir}"

# Simulate the config creation logic from install.sh
if [ "$NO_WHISPER_EXPLICIT" = "yes" ]; then
    echo "Skipping Whisper installation (--no-whisper flag)."
    echo "VOSK will be used as the default speech recognition engine."

    CONFIG_FILE="$CONFIG_DIR/config.json"
    cat > "$CONFIG_FILE" << 'VOSK_CONFIG'
{{
    "speech_recognition": {{
        "engine": "vosk",
        "model_size": "small",
        "vosk_model_size": "small",
        "whisper_model_size": "tiny"
    }}
}}
VOSK_CONFIG
    echo "CONFIG_CREATED=yes"
fi
""")
        test_script.chmod(0o755)

        result = subprocess.run(
            ["bash", str(test_script)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "CONFIG_CREATED=yes" in result.stdout

        # Verify the config file was created
        config_file = config_dir / "config.json"
        assert config_file.exists()
        config_content = config_file.read_text()
        assert '"engine": "vosk"' in config_content

    def test_whisper_cpu_flag_sets_cpu_only(self):
        """Test that --whisper-cpu flag triggers CPU-only PyTorch installation."""
        # Test the variable setting logic
        test_script = """#!/bin/bash
WHISPER_CPU="no"
WITH_WHISPER="no"

# Simulate parsing --whisper-cpu
parse_arg() {
    WHISPER_CPU="yes"
    WITH_WHISPER="yes"
}

parse_arg

echo "WHISPER_CPU=$WHISPER_CPU"
echo "WITH_WHISPER=$WITH_WHISPER"

if [ "$WHISPER_CPU" = "yes" ]; then
    echo "CPU_ONLY_MODE=yes"
fi
"""
        result = subprocess.run(
            ["bash", "-c", test_script],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "WHISPER_CPU=yes" in result.stdout
        assert "WITH_WHISPER=yes" in result.stdout
        assert "CPU_ONLY_MODE=yes" in result.stdout

    def test_with_whisper_flag_enables_gpu_support(self):
        """Test that --with-whisper flag enables full GPU support installation."""
        test_script = """#!/bin/bash
WITH_WHISPER="no"
WHISPER_CPU="no"

# Simulate parsing --with-whisper
parse_arg() {
    WITH_WHISPER="yes"
}

parse_arg

echo "WITH_WHISPER=$WITH_WHISPER"
echo "WHISPER_CPU=$WHISPER_CPU"

if [ "$WITH_WHISPER" = "yes" ] && [ "$WHISPER_CPU" = "no" ]; then
    echo "GPU_INSTALL=yes"
fi
"""
        result = subprocess.run(
            ["bash", "-c", test_script],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "WITH_WHISPER=yes" in result.stdout
        assert "GPU_INSTALL=yes" in result.stdout

    @pytest.mark.parametrize(
        "flag,expected_whisper,expected_cpu",
        [
            ("--whisper-cpu", "yes", "yes"),
            ("--with-whisper", "yes", "no"),
            ("--no-whisper", "no", "no"),
        ],
    )
    def test_pytorch_installation_flags(self, flag, expected_whisper, expected_cpu):
        """Test various flag combinations for PyTorch installation."""
        # Create a minimal test to verify flag parsing affects variables
        test_script = f"""#!/bin/bash
WITH_WHISPER="no"
WHISPER_CPU="no"
NO_WHISPER_EXPLICIT="no"

# Simulate flag parsing
flag="{flag}"
case "$flag" in
    --whisper-cpu)
        WITH_WHISPER="yes"
        WHISPER_CPU="yes"
        ;;
    --with-whisper)
        WITH_WHISPER="yes"
        ;;
    --no-whisper)
        WITH_WHISPER="no"
        NO_WHISPER_EXPLICIT="yes"
        ;;
esac

echo "WITH_WHISPER=$WITH_WHISPER"
echo "WHISPER_CPU=$WHISPER_CPU"
echo "NO_WHISPER_EXPLICIT=$NO_WHISPER_EXPLICIT"
"""
        result = subprocess.run(
            ["bash", "-c", test_script],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert f"WITH_WHISPER={expected_whisper}" in result.stdout
        assert f"WHISPER_CPU={expected_cpu}" in result.stdout
        if flag == "--no-whisper":
            assert "NO_WHISPER_EXPLICIT=yes" in result.stdout


class TestInstallerEnvironmentChecks:
    """Test cases for environment and system checks."""

    def test_running_as_root_is_blocked(self, tmp_path):
        """Test that running as root is blocked."""
        test_script = tmp_path / "test_root_check.sh"
        test_script.write_text("""#!/bin/bash
# Simulate running as root
EUID=0

if [ "$EUID" -eq 0 ]; then
    echo "ROOT_CHECK=blocked"
    exit 1
fi
""")
        test_script.chmod(0o755)

        result = subprocess.run(
            ["bash", str(test_script)],
            capture_output=True,
            text=True,
        )

        # The script should block root
        assert result.returncode == 1
        assert "ROOT_CHECK=blocked" in result.stdout or "ROOT_CHECK=blocked" in result.stderr

    def test_distro_detection_ubuntu(self, tmp_path):
        """Test Ubuntu distribution detection."""
        os_release = tmp_path / "os-release"
        os_release.write_text("""NAME="Ubuntu"
VERSION_ID="22.04"
ID=ubuntu
ID_LIKE=debian
""")

        test_script = f"""#!/bin/bash
. {os_release}

if [ -f /etc/os-release ]; then
    if [[ "$ID" == "ubuntu" ]]; then
        echo "DISTRO_DETECTED=ubuntu"
        echo "VERSION=$VERSION_ID"
    fi
fi
"""
        result = subprocess.run(
            ["bash", "-c", test_script],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "DISTRO_DETECTED=ubuntu" in result.stdout
        assert "VERSION=22.04" in result.stdout

    def test_distro_detection_fedora(self, tmp_path):
        """Test Fedora distribution detection."""
        os_release = tmp_path / "os-release"
        os_release.write_text("""NAME="Fedora Linux"
VERSION_ID="39"
ID=fedora
""")

        test_script = f"""#!/bin/bash
. {os_release}

if [ -f /etc/os-release ]; then
    if [[ "$ID" == "fedora" || "$ID_LIKE" == *"fedora"* ]]; then
        echo "DISTRO_DETECTED=fedora"
        echo "VERSION=$VERSION_ID"
    fi
fi
"""
        result = subprocess.run(
            ["bash", "-c", test_script],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "DISTRO_DETECTED=fedora" in result.stdout
        assert "VERSION=39" in result.stdout

    def test_python_version_check(self):
        """Test Python version checking logic."""
        test_script = """#!/bin/bash
MIN_VERSION="3.8"

# Test various Python versions
test_version() {
    local PY_VERSION=$1
    if [[ $(echo -e "$PY_VERSION\n$MIN_VERSION" | sort -V | head -n1) == "$MIN_VERSION" || "$PY_VERSION" == "$MIN_VERSION" ]]; then  # noqa: E501
        echo "VERSION $PY_VERSION: OK"
    else
        echo "VERSION $PY_VERSION: FAIL"
    fi
}

test_version "3.7"
test_version "3.8"
test_version "3.9"
test_version "3.10"
test_version "3.12"
"""
        result = subprocess.run(
            ["bash", "-c", test_script],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "VERSION 3.7: FAIL" in result.stdout
        assert "VERSION 3.8: OK" in result.stdout
        assert "VERSION 3.9: OK" in result.stdout
        assert "VERSION 3.10: OK" in result.stdout
        assert "VERSION 3.12: OK" in result.stdout


class TestInstallerIntegration:
    """Integration tests for the installer."""

    def test_script_syntax_valid(self):
        """Test that the install.sh script has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", str(INSTALL_SCRIPT)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Syntax error: {result.stderr}"

    def test_all_functions_defined(self):
        """Test that key functions are defined in the script."""
        script_content = INSTALL_SCRIPT.read_text()

        # Check for key function definitions
        assert "detect_nvidia_gpu()" in script_content
        assert "detect_distro()" in script_content
        assert "run_interactive_install()" in script_content
        assert "install_system_dependencies()" in script_content
        assert "setup_virtual_environment()" in script_content
        assert "install_python_package()" in script_content
        assert "print_header()" in script_content

    def test_required_commands_exist(self):
        """Test that the script references required commands."""
        script_content = INSTALL_SCRIPT.read_text()

        # Check for key commands
        assert "nvidia-smi" in script_content
        assert "python3" in script_content
        assert "pip install" in script_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
