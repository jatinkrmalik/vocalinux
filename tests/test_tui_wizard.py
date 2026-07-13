"""Tests for the TUI installer wizard."""

import json

import pytest
from vocalinux_installer_tui.state import HardwareDetect, WizardState


class TestWizardState:
    """Test WizardState dataclass."""

    def test_defaults(self):
        """Test default values."""
        s = WizardState()
        assert s.engine == "whisper_cpp"
        assert s.whispercpp_model_size == "tiny"
        assert s.whisper_model_size == "tiny"
        assert s.vosk_model_size == "small"
        assert s.remote_api_url == ""
        assert s.whispercpp_backend == ""
        assert s.dev_mode is False
        assert s.skip_models is False
        assert s.rebuild_whispercpp == "ask"
        assert s.detected is None

    def test_json_roundtrip(self, tmp_path):
        """Test JSON serialization and deserialization."""
        s = WizardState(
            engine="vosk",
            dev_mode=True,
            detected=HardwareDetect(has_vulkan=True, gpu_name="RTX 4090"),
        )
        path = str(tmp_path / "state.json")
        s.save(path)
        loaded = WizardState.load(path)

        assert loaded.engine == "vosk"
        assert loaded.dev_mode is True
        assert loaded.detected is not None
        assert loaded.detected.has_vulkan is True
        assert loaded.detected.gpu_name == "RTX 4090"

    def test_json_roundtrip_without_hardware(self, tmp_path):
        """Test JSON roundtrip without hardware detection."""
        s = WizardState(engine="whisper", whisper_model_size="medium")
        path = str(tmp_path / "state.json")
        s.save(path)
        loaded = WizardState.load(path)

        assert loaded.engine == "whisper"
        assert loaded.whisper_model_size == "medium"
        assert loaded.detected is None

    def test_to_json(self):
        """Test to_json method."""
        s = WizardState(engine="remote_api", remote_api_url="https://api.example.com")
        json_str = s.to_json()
        data = json.loads(json_str)

        assert data["engine"] == "remote_api"
        assert data["remote_api_url"] == "https://api.example.com"

    def test_from_json(self):
        """Test from_json method."""
        json_str = json.dumps(
            {
                "engine": "vosk",
                "whispercpp_model_size": "tiny",
                "whisper_model_size": "tiny",
                "vosk_model_size": "small",
                "remote_api_url": "",
                "whispercpp_backend": "",
                "dev_mode": True,
                "skip_models": False,
                "rebuild_whispercpp": "yes",
                "detected": None,
            }
        )
        s = WizardState.from_json(json_str)

        assert s.engine == "vosk"
        assert s.dev_mode is True
        assert s.rebuild_whispercpp == "yes"


class TestHardwareDetect:
    """Test HardwareDetect dataclass."""

    def test_defaults(self):
        """Test default values."""
        h = HardwareDetect()
        assert h.has_nvidia is False
        assert h.gpu_name == ""
        assert h.gpu_memory == ""
        assert h.has_vulkan is False
        assert h.vulkan_device == ""
        assert h.distro_name == ""
        assert h.distro_family == ""

    def test_custom_values(self):
        """Test custom values."""
        h = HardwareDetect(
            has_nvidia=True,
            gpu_name="RTX 4090",
            gpu_memory="24GB",
            has_vulkan=True,
            vulkan_device="NVIDIA GeForce RTX 4090",
            distro_name="Ubuntu",
            distro_family="debian",
        )
        assert h.has_nvidia is True
        assert h.gpu_name == "RTX 4090"
        assert h.gpu_memory == "24GB"
        assert h.has_vulkan is True
        assert h.vulkan_device == "NVIDIA GeForce RTX 4090"
        assert h.distro_name == "Ubuntu"
        assert h.distro_family == "debian"


class TestInstallWizardApp:
    """Test InstallWizardApp instantiation."""

    def test_app_instantiation(self):
        """Test that the app can be instantiated."""
        from vocalinux_installer_tui.app import InstallWizardApp

        app = InstallWizardApp()
        assert app is not None
        assert app.wizard_state is not None
        assert app.wizard_state.engine == "whisper_cpp"

    def test_app_with_state(self):
        """Test app instantiation with custom state."""
        from vocalinux_installer_tui.app import InstallWizardApp

        state = WizardState(engine="vosk", dev_mode=True)
        app = InstallWizardApp(state=state)

        assert app.wizard_state.engine == "vosk"
        assert app.wizard_state.dev_mode is True
