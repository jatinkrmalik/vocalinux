"""Options screen."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Checkbox, Label, RadioSet, RadioButton

from ..state import WizardState


class OptionsScreen(Screen[bool | None]):
    """Installation options screen."""

    def __init__(self, wizard_state: WizardState, **kwargs):
        super().__init__(**kwargs)
        self.wizard_state = wizard_state

    def compose(self) -> ComposeResult:
        with Container(id="options-container"):
            yield Label("Installation Options", id="title")

            yield Checkbox("Developer mode (install from source)", id="dev-mode")
            yield Checkbox("Skip model downloads", id="skip-models")

            yield Label("Rebuild whisper.cpp?", id="rebuild-label")
            yield RadioSet(
                RadioButton("Ask me later", value=True, id="ask"),
                RadioButton("Yes, rebuild", id="yes"),
                RadioButton("No, use pre-built", id="no"),
                id="rebuild-radioset",
            )

            with Container(id="button-container"):
                yield Button("Back", variant="default", id="back-btn")
                yield Button("Next", variant="primary", id="next-btn")

    def on_mount(self) -> None:
        dev_mode_cb = self.query_one("#dev-mode", Checkbox)
        dev_mode_cb.value = self.wizard_state.dev_mode

        skip_models_cb = self.query_one("#skip-models", Checkbox)
        skip_models_cb.value = self.wizard_state.skip_models

        rebuild_radioset = self.query_one("#rebuild-radioset", RadioSet)
        rebuild_map = {"ask": 0, "yes": 1, "no": 2}
        idx = rebuild_map.get(self.wizard_state.rebuild_whispercpp, 0)
        buttons = list(rebuild_radioset.children)
        if 0 <= idx < len(buttons):
            from textual.widgets import RadioButton

            button = buttons[idx]
            if isinstance(button, RadioButton):
                button.value = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.dismiss(None)
        elif event.button.id == "next-btn":
            dev_mode_cb = self.query_one("#dev-mode", Checkbox)
            self.wizard_state.dev_mode = dev_mode_cb.value

            skip_models_cb = self.query_one("#skip-models", Checkbox)
            self.wizard_state.skip_models = skip_models_cb.value

            rebuild_radioset = self.query_one("#rebuild-radioset", RadioSet)
            rebuild_map = ["ask", "yes", "no"]
            idx = rebuild_radioset.pressed_index
            if 0 <= idx < len(rebuild_map):
                self.wizard_state.rebuild_whispercpp = rebuild_map[idx]

            self.dismiss(True)
