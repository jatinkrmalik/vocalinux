"""Wizard state management."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Optional


@dataclass
class HardwareDetect:
    """Detected hardware information."""

    has_nvidia: bool = False
    gpu_name: str = ""
    gpu_memory: str = ""
    has_vulkan: bool = False
    vulkan_device: str = ""
    distro_name: str = ""
    distro_family: str = ""


@dataclass
class WizardState:
    """Complete wizard state for installation."""

    engine: str = "whisper_cpp"
    whispercpp_model_size: str = "tiny"
    whisper_model_size: str = "tiny"
    vosk_model_size: str = "small"
    remote_api_url: str = ""
    whispercpp_backend: str = ""
    dev_mode: bool = False
    skip_models: bool = False
    rebuild_whispercpp: str = "ask"
    detected: Optional[HardwareDetect] = None

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, data: str) -> WizardState:
        """Deserialize from JSON string."""
        d = json.loads(data)
        detected = None
        if "detected" in d:
            detected_data = d.pop("detected")
            if detected_data:
                detected = HardwareDetect(**detected_data)
        return cls(detected=detected, **d)

    def save(self, path: str) -> None:
        """Save state to file."""
        with open(path, "w") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> WizardState:
        """Load state from file."""
        with open(path) as f:
            return cls.from_json(f.read())
