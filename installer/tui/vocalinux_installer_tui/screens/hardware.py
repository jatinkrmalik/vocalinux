"""Hardware detection screen."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, DataTable, Label

from ..phase_invoker import run_phase
from ..state import HardwareDetect, WizardState


class HardwareScreen(Screen[bool | None]):
    """Hardware detection and display screen."""

    def __init__(self, wizard_state: WizardState, **kwargs):
        super().__init__(**kwargs)
        self.wizard_state = wizard_state

    def compose(self) -> ComposeResult:
        with Container(id="hardware-container"):
            yield Label("Hardware Detection", id="title")
            yield Label("Detected system capabilities:", id="subtitle")
            yield DataTable(id="hardware-table")
            with Container(id="button-container"):
                yield Button("Back", variant="default", id="back-btn")
                yield Button("Next", variant="primary", id="next-btn")

    async def on_mount(self) -> None:
        table = self.query_one("#hardware-table", DataTable)
        table.add_columns("Property", "Value")

        # Run detection phase
        detected = HardwareDetect()
        try:
            output_lines = []

            def capture_line(line: str) -> None:
                output_lines.append(line)

            phase_script = "installer/phases/30-detect-hardware.sh"
            await run_phase(phase_script, on_line=capture_line)

            # Parse KEY=VALUE output
            for line in output_lines:
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"')

                    if key == "HAS_NVIDIA":
                        detected.has_nvidia = value.lower() == "true"
                    elif key == "GPU_NAME":
                        detected.gpu_name = value
                    elif key == "GPU_MEMORY":
                        detected.gpu_memory = value
                    elif key == "HAS_VULKAN":
                        detected.has_vulkan = value.lower() == "true"
                    elif key == "VULKAN_DEVICE":
                        detected.vulkan_device = value
                    elif key == "DISTRO_NAME":
                        detected.distro_name = value
                    elif key == "DISTRO_FAMILY":
                        detected.distro_family = value

        except Exception as e:
            # Detection failed, use defaults
            pass

        self.wizard_state.detected = detected

        # Populate table
        table.add_row("NVIDIA GPU", "Yes" if detected.has_nvidia else "No")
        if detected.gpu_name:
            table.add_row("GPU Model", detected.gpu_name)
        if detected.gpu_memory:
            table.add_row("GPU Memory", detected.gpu_memory)
        table.add_row("Vulkan Support", "Yes" if detected.has_vulkan else "No")
        if detected.vulkan_device:
            table.add_row("Vulkan Device", detected.vulkan_device)
        if detected.distro_name:
            table.add_row("Distribution", detected.distro_name)
        if detected.distro_family:
            table.add_row("Distro Family", detected.distro_family)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.dismiss(None)
        elif event.button.id == "next-btn":
            self.dismiss(True)
