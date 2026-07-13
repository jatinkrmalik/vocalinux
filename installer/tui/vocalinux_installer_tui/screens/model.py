"""Model selection screen."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Input, Label, RadioSet, RadioButton

from ..state import WizardState


class ModelScreen(Screen[bool | None]):
    """Model selection screen - engine-conditional."""

    def __init__(self, wizard_state: WizardState, **kwargs):
        super().__init__(**kwargs)
        self.wizard_state = wizard_state

    def compose(self) -> ComposeResult:
        with Container(id="model-container"):
            yield Label("Model Selection", id="title")

            engine = self.wizard_state.engine

            if engine == "whisper_cpp":
                yield Label("Select whisper.cpp model size:", id="subtitle")
                yield RadioSet(
                    RadioButton("tiny (fastest, least accurate)", value=True, id="tiny"),
                    RadioButton("base", id="base"),
                    RadioButton("small", id="small"),
                    RadioButton("medium", id="medium"),
                    RadioButton("large (slowest, most accurate)", id="large"),
                    id="model-radioset",
                )
            elif engine == "whisper":
                yield Label("Select Whisper model size:", id="subtitle")
                yield RadioSet(
                    RadioButton("tiny (fastest, least accurate)", value=True, id="tiny"),
                    RadioButton("base", id="base"),
                    RadioButton("small", id="small"),
                    RadioButton("medium", id="medium"),
                    RadioButton("large (slowest, most accurate)", id="large"),
                    id="model-radioset",
                )
            elif engine == "vosk":
                yield Label("VOSK model:", id="subtitle")
                yield Label("small (default for VOSK)", id="model-info")
            elif engine == "remote_api":
                yield Label("Remote API Configuration:", id="subtitle")
                yield Label("API Endpoint URL:", id="url-label")
                yield Input(
                    placeholder="https://api.example.com/transcribe",
                    id="api-url-input",
                )

            with Container(id="button-container"):
                yield Button("Back", variant="default", id="back-btn")
                yield Button("Next", variant="primary", id="next-btn")

    def on_mount(self) -> None:
        engine = self.wizard_state.engine

        if engine in ("whisper_cpp", "whisper"):
            radioset = self.query_one("#model-radioset", RadioSet)
            model_size = (
                self.wizard_state.whispercpp_model_size
                if engine == "whisper_cpp"
                else self.wizard_state.whisper_model_size
            )
            model_map = {"tiny": 0, "base": 1, "small": 2, "medium": 3, "large": 4}
            idx = model_map.get(model_size, 0)
            buttons = list(radioset.children)
            if 0 <= idx < len(buttons):
                from textual.widgets import RadioButton

                button = buttons[idx]
                if isinstance(button, RadioButton):
                    button.value = True
        elif engine == "remote_api":
            input_widget = self.query_one("#api-url-input", Input)
            input_widget.value = self.wizard_state.remote_api_url

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.dismiss(None)
        elif event.button.id == "next-btn":
            engine = self.wizard_state.engine

            if engine == "whisper_cpp":
                radioset = self.query_one("#model-radioset", RadioSet)
                model_map = ["tiny", "base", "small", "medium", "large"]
                idx = radioset.pressed_index
                if 0 <= idx < len(model_map):
                    self.wizard_state.whispercpp_model_size = model_map[idx]
            elif engine == "whisper":
                radioset = self.query_one("#model-radioset", RadioSet)
                model_map = ["tiny", "base", "small", "medium", "large"]
                idx = radioset.pressed_index
                if 0 <= idx < len(model_map):
                    self.wizard_state.whisper_model_size = model_map[idx]
            elif engine == "remote_api":
                input_widget = self.query_one("#api-url-input", Input)
                self.wizard_state.remote_api_url = input_widget.value

            self.dismiss(True)
