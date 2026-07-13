"""Main Textual application."""

from textual.app import App

from .state import WizardState
from .screens.welcome import WelcomeScreen
from .screens.hardware import HardwareScreen
from .screens.engine import EngineScreen
from .screens.model import ModelScreen
from .screens.options import OptionsScreen
from .screens.confirm import ConfirmScreen
from .screens.install import InstallScreen


class InstallWizardApp(App[WizardState]):
    """Vocalinux installation wizard application."""

    CSS_PATH = None
    TITLE = "Vocalinux Installer"

    DEFAULT_CSS = """
    Screen {
        align: center middle;
    }

    #welcome-container,
    #hardware-container,
    #engine-container,
    #model-container,
    #options-container,
    #confirm-container,
    #install-container {
        width: 80;
        height: auto;
        max-height: 90%;
        border: solid $primary;
        padding: 1 2;
    }

    #title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #subtitle {
        text-align: center;
        margin-bottom: 1;
    }

    #recommendation {
        text-style: italic;
        margin-bottom: 1;
    }

    #button-container {
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    Button {
        margin: 0 1;
    }

    DataTable {
        height: auto;
        max-height: 15;
        margin: 1 0;
    }

    RadioSet {
        margin: 1 0;
    }

    Checkbox {
        margin: 0 0 1 0;
    }

    Input {
        margin: 1 0;
    }

    ProgressBar {
        margin: 1 0;
    }

    RichLog {
        height: 20;
        border: solid $secondary;
        margin: 1 0;
    }
    """

    def __init__(self, state: WizardState | None = None, **kwargs):
        super().__init__(**kwargs)
        self.wizard_state = state or WizardState()

    async def on_mount(self) -> None:
        await self.push_screen(WelcomeScreen(), callback=self._on_welcome_done)

    def _on_welcome_done(self, result) -> None:
        if result is None:
            self.exit()
            return
        self.push_screen(HardwareScreen(self.wizard_state), callback=self._on_hardware_done)

    def _on_hardware_done(self, result) -> None:
        if result is None:
            self.push_screen(WelcomeScreen(), callback=self._on_welcome_done)
            return
        self.push_screen(EngineScreen(self.wizard_state), callback=self._on_engine_done)

    def _on_engine_done(self, result) -> None:
        if result is None:
            self.push_screen(HardwareScreen(self.wizard_state), callback=self._on_hardware_done)
            return
        self.push_screen(ModelScreen(self.wizard_state), callback=self._on_model_done)

    def _on_model_done(self, result) -> None:
        if result is None:
            self.push_screen(EngineScreen(self.wizard_state), callback=self._on_engine_done)
            return
        self.push_screen(OptionsScreen(self.wizard_state), callback=self._on_options_done)

    def _on_options_done(self, result) -> None:
        if result is None:
            self.push_screen(ModelScreen(self.wizard_state), callback=self._on_model_done)
            return
        self.push_screen(ConfirmScreen(self.wizard_state), callback=self._on_confirm_done)

    def _on_confirm_done(self, result) -> None:
        if result is None:
            self.push_screen(OptionsScreen(self.wizard_state), callback=self._on_options_done)
            return
        self.push_screen(InstallScreen(self.wizard_state), callback=self._on_install_done)

    def _on_install_done(self, result) -> None:
        self.exit(self.wizard_state)
