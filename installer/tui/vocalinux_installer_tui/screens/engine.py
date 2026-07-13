"""Engine selection screen."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, RadioSet, RadioButton

from ..state import WizardState


class EngineScreen(Screen[bool | None]):
    """Engine selection screen."""

    def __init__(self, wizard_state: WizardState, **kwargs):
        super().__init__(**kwargs)
        self.wizard_state = wizard_state

    def compose(self) -> ComposeResult:
        with Container(id="engine-container"):
            yield Label("Speech Recognition Engine", id="title")

            # Recommendation based on hardware
            recommendation = self._get_recommendation()
            yield Label(recommendation, id="recommendation")

            yield RadioSet(
                RadioButton("whisper.cpp (Recommended)", value=True, id="whisper_cpp"),
                RadioButton("Whisper (OpenAI)", id="whisper"),
                RadioButton("VOSK", id="vosk"),
                RadioButton("Remote API", id="remote_api"),
                id="engine-radioset",
            )

            with Container(id="button-container"):
                yield Button("Back", variant="default", id="back-btn")
                yield Button("Next", variant="primary", id="next-btn")

    def _get_recommendation(self) -> str:
        """Get engine recommendation based on detected hardware."""
        detected = self.wizard_state.detected

        if detected and detected.has_nvidia and detected.has_vulkan:
            return "Recommended: whisper.cpp with GPU acceleration"
        elif detected and detected.has_vulkan:
            return "Recommended: whisper.cpp with Vulkan acceleration"
        elif detected and detected.has_nvidia:
            return "Recommended: whisper.cpp with CUDA acceleration"
        else:
            return "Recommended: whisper.cpp (CPU mode) or VOSK for lower resources"

    def on_mount(self) -> None:
        radioset = self.query_one("#engine-radioset", RadioSet)
        engine_map = {
            "whisper_cpp": 0,
            "whisper": 1,
            "vosk": 2,
            "remote_api": 3,
        }
        idx = engine_map.get(self.wizard_state.engine, 0)
        buttons = list(radioset.children)
        if 0 <= idx < len(buttons):
            from textual.widgets import RadioButton

            button = buttons[idx]
            if isinstance(button, RadioButton):
                button.value = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.dismiss(None)
        elif event.button.id == "next-btn":
            radioset = self.query_one("#engine-radioset", RadioSet)
            engine_map = ["whisper_cpp", "whisper", "vosk", "remote_api"]
            idx = radioset.pressed_index
            if 0 <= idx < len(engine_map):
                self.wizard_state.engine = engine_map[idx]
            self.dismiss(True)
