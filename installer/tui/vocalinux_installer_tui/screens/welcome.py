"""Welcome screen."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label


class WelcomeScreen(Screen[bool | None]):
    """Welcome screen with start/quit buttons."""

    def compose(self) -> ComposeResult:
        with Container(id="welcome-container"):
            yield Label("Vocalinux Installer", id="title")
            yield Label(
                "Interactive installer for voice recognition software.\n"
                "This wizard will guide you through engine selection, "
                "model configuration, and installation.",
                id="subtitle",
            )
            with Container(id="button-container"):
                yield Button("Start", variant="primary", id="start-btn")
                yield Button("Quit", variant="default", id="quit-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start-btn":
            self.dismiss(True)
        elif event.button.id == "quit-btn":
            self.dismiss(None)
