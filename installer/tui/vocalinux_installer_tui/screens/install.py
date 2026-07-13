"""Installation screen — invokes the built install.sh with CLI flags."""

import asyncio
import os

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Label, ProgressBar, RichLog

from ..state import WizardState


class InstallScreen(Screen[bool | None]):
    """Installation progress screen."""

    def __init__(self, wizard_state: WizardState, **kwargs):
        super().__init__(**kwargs)
        self.wizard_state = wizard_state

    def compose(self) -> ComposeResult:
        with Container(id="install-container"):
            yield Label("Installing Vocalinux...", id="title")
            yield ProgressBar(total=100, show_eta=False, id="progress")
            yield RichLog(id="log", wrap=True, highlight=True)
            yield Button("Exit", variant="default", id="exit-btn", disabled=True)

    async def on_mount(self) -> None:
        self.run_worker(self._run_installation(), name="install")

    def _build_cli_args(self) -> list[str]:
        """Build install.sh CLI args from wizard state."""
        args = ["--auto", f"--engine={self.wizard_state.engine}"]
        if self.wizard_state.dev_mode:
            args.append("--dev")
        if self.wizard_state.skip_models:
            args.append("--skip-models")
        if self.wizard_state.rebuild_whispercpp == "yes":
            args.append("--rebuild-whispercpp")
        elif self.wizard_state.rebuild_whispercpp == "no":
            args.append("--no-rebuild-whispercpp")
        return args

    async def _run_installation(self) -> None:
        progress_bar = self.query_one("#progress", ProgressBar)
        log_widget = self.query_one("#log", RichLog)

        install_sh = os.path.join(os.path.dirname(__file__), "..", "..", "..", "install.sh")
        install_sh = os.path.normpath(install_sh)

        if not os.path.exists(install_sh):
            log_widget.write("[bold red]install.sh not found.[/bold red]")
            log_widget.write("The built installer must exist at the repository root.")
            self._enable_exit()
            return

        cli_args = self._build_cli_args()
        log_widget.write(f"[bold]Running: bash install.sh {' '.join(cli_args)}[/bold]\n")
        progress_bar.update(progress=10)

        proc = await asyncio.create_subprocess_exec(
            "bash", install_sh, *cli_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        line_count = 0
        if proc.stdout:
            async for line in proc.stdout:
                decoded = line.decode("utf-8", errors="replace").rstrip()
                log_widget.write(decoded)
                line_count += 1
                progress = min(10 + (line_count / max(line_count + 50, 100)) * 80, 90)
                progress_bar.update(progress=progress)

        rc = await proc.wait()
        if rc == 0:
            log_widget.write("\n[bold green]Installation complete![/bold green]")
            progress_bar.update(progress=100)
        else:
            log_widget.write(f"\n[bold red]Installation failed (exit code {rc}).[/bold red]")

        self._enable_exit()

    def _enable_exit(self) -> None:
        exit_btn = self.query_one("#exit-btn", Button)
        exit_btn.disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "exit-btn":
            self.dismiss(True)
