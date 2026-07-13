"""Entry point for the TUI installer."""

from .app import InstallWizardApp


def main():
    app = InstallWizardApp()
    app.run()


if __name__ == "__main__":
    main()
