"""Hardware table widget."""

from textual.widgets import DataTable


class HardwareTable(DataTable[None]):
    """DataTable specialized for hardware info display."""

    DEFAULT_CSS = """
    HardwareTable {
        height: auto;
        max-height: 20;
    }
    """
