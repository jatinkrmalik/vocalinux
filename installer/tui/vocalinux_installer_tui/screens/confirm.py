"""Confirmation screen."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, DataTable, Label

from ..state import WizardState


class ConfirmScreen(Screen[bool | None]):
    """Confirmation screen showing all choices."""

    def __init__(self, wizard_state: WizardState, **kwargs):
        super().__init__(**kwargs)
        self.wizard_state = wizard_state

    def compose(self) -> ComposeResult:
        with Container(id="confirm-container"):
            yield Label("Confirm Installation", id="title")
            yield Label("Review your choices:", id="subtitle")
            yield DataTable(id="summary-table")

            with Container(id="button-container"):
                yield Button("Back", variant="default", id="back-btn")
                yield Button("Begin Install", variant="primary", id="install-btn")

    def on_mount(self) -> None:
        table = self.query_one("#summary-table", DataTable)
        table.add_columns("Setting", "Value")

        state = self.wizard_state

        # Engine
        engine_names = {
            "whisper_cpp": "whisper.cpp",
            "whisper": "Whisper (OpenAI)",
            "vosk": "VOSK",
            "remote_api": "Remote API",
        }
        table.add_row("Engine", engine_names.get(state.engine, state.engine))

        # Model
        if state.engine == "whisper_cpp":
            table.add_row("Model Size", state.whispercpp_model_size)
        elif state.engine == "whisper":
            table.add_row("Model Size", state.whisper_model_size)
        elif state.engine == "vosk":
            table.add_row("Model Size", state.vosk_model_size)
        elif state.engine == "remote_api":
            table.add_row("API URL", state.remote_api_url or "(not set)")

        # Options
        table.add_row("Developer Mode", "Yes" if state.dev_mode else "No")
        table.add_row("Skip Models", "Yes" if state.skip_models else "No")
        table.add_row("Rebuild whisper.cpp", state.rebuild_whispercpp)

        # Hardware info
        if state.detected:
            if state.detected.gpu_name:
                table.add_row("GPU", state.detected.gpu_name)
            if state.detected.distro_name:
                table.add_row("Distribution", state.detected.distro_name)
