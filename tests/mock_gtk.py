"""Mock GTK objects for testing."""

from unittest.mock import MagicMock


class MockGtk:
    """Mock GTK implementation for testing."""

    def __init__(self):
        self.main_called = False
        self.main_quit = MagicMock()

    def main(self):
        """Mock main loop."""
        self.main_called = True

    # License enum
    class License:
        GPL_3_0 = "GPL-3.0"

    # Interface and base classes
    class Buildable:
        """Mock Buildable interface."""

        def __init__(self):
            self._name = ""

        def get_name(self):
            """Get widget name."""
            return self._name

        def set_name(self, name):
            """Set widget name."""
            self._name = name

        def add_child(self, builder, child, type=None):
            """Add a child widget."""
            pass

    class Widget(Buildable):
        """Mock Widget base class."""

        def __init__(self):
            super().__init__()
            self.visible = False
            self.sensitive = True
            self.parent = None

        def show(self):
            """Show the widget."""
            self.visible = True

        def hide(self):
            """Hide the widget."""
            self.visible = False

        def set_sensitive(self, sensitive):
            """Set widget sensitivity."""
            self.sensitive = sensitive

        def get_parent(self):
            """Get widget parent."""
            return self.parent

    class Dialog(Widget):
        """Mock dialog base class."""

        def __init__(self):
            super().__init__()

        def run(self):
            """Run the dialog."""
            return 0

        def destroy(self):
            """Destroy the dialog."""
            pass

    class AboutDialog:
        """Mock AboutDialog implementation."""

        @staticmethod
        def new():
            """Create a new AboutDialog."""
            return MockGtk.AboutDialog()

        def __init__(self):
            self._program_name = None
            self._version = None
            self._copyright = None
            self._authors = None
            self._comments = None
            self._website = None
            self._website_label = None
            self._license_type = None
            self._logo = None

        def set_program_name(self, name):
            """Set program name."""
            self._program_name = name

        def set_version(self, version):
            """Set version."""
            self._version = version

        def set_copyright(self, copyright):
            """Set copyright."""
            self._copyright = copyright

        def set_authors(self, authors):
            """Set authors."""
            self._authors = authors

        def set_comments(self, comments):
            """Set comments."""
            self._comments = comments

        def set_website(self, website):
            """Set website."""
            self._website = website

        def set_website_label(self, label):
            """Set website label."""
            self._website_label = label

        def set_license_type(self, license_type):
            """Set license type."""
            self._license_type = license_type

        def set_logo(self, logo):
            """Set logo."""
            self._logo = logo

        @property
        def program_name(self):
            """Get program name."""
            return self._program_name

        @property
        def version(self):
            """Get version."""
            return self._version

        @property
        def copyright(self):
            """Get copyright."""
            return self._copyright

        @property
        def authors(self):
            """Get authors."""
            return self._authors

        @property
        def comments(self):
            """Get comments."""
            return self._comments

        @property
        def website(self):
            """Get website."""
            return self._website

        @property
        def website_label(self):
            """Get website label."""
            return self._website_label

        @property
        def license_type(self):
            """Get license type."""
            return self._license_type

        def get_logo(self):
            """Get logo."""
            return self._logo

        def run(self):
            """Run the dialog."""
            return 0

        def destroy(self):
            """Destroy the dialog."""
            pass

    class Image:
        """Mock image implementation."""

        def __init__(self):
            self.icon_name = None
            self.size = None

        def set_from_icon_name(self, icon_name, size):
            """Set image from icon name."""
            self.icon_name = icon_name
            self.size = size

    class ImageMenuItem:
        """Mock image menu item implementation."""

        def __init__(self, label=None):
            self.label = label
            self.callback = None
            self.sensitive = True
            self.submenu = None
            self.image = None

        def set_image(self, image):
            """Set menu item image."""
            self.image = image

        def set_always_show_image(self, show):
            """Set whether to always show image."""
            self.always_show_image = show

        def connect(self, signal, callback):
            """Connect a signal handler."""
            self.callback = callback

        def get_label(self):
            """Get the menu item label."""
            return self.label

        def set_sensitive(self, sensitive):
            """Set menu item sensitivity."""
            self.sensitive = sensitive

        def set_submenu(self, submenu):
            """Set submenu for this menu item."""
            self.submenu = submenu

    class MenuItem:
        """Mock menu item implementation."""

        @staticmethod
        def new_with_label(label):
            """Create a new menu item with label."""
            return MockGtk.MenuItem(label)

        def __init__(self, label=None):
            self.label = label
            self.callback = None
            self.sensitive = True
            self.submenu = None

        def connect(self, signal, callback):
            """Connect a signal handler."""
            self.callback = callback

        def get_label(self):
            """Get the menu item label."""
            return self.label

        def set_sensitive(self, sensitive):
            """Set menu item sensitivity."""
            self.sensitive = sensitive

        def set_submenu(self, submenu):
            """Set submenu for this menu item."""
            self.submenu = submenu

    class SeparatorMenuItem:
        """Mock separator menu item implementation."""

        def __init__(self):
            pass

    class Menu:
        """Mock menu implementation."""

        def __init__(self):
            self.items = []

        def append(self, item):
            """Append a menu item."""
            self.items.append(item)

        def show_all(self):
            """Show all menu items."""
            pass

        def get_children(self):
            """Get all menu items."""
            return self.items


class MockGLib:
    """Mock GLib implementation."""

    @staticmethod
    def idle_add(func, *args):
        """Execute function immediately for testing."""
        if args:
            return func(*args)
        return func()


class MockAppIndicator:
    """Mock AppIndicator implementation."""

    class IndicatorCategory:
        APPLICATION_STATUS = 0

    class IndicatorStatus:
        ACTIVE = 0
        ATTENTION = 1
        PASSIVE = 2

    class Indicator:
        """Mock Indicator implementation."""

        @staticmethod
        def new_with_path(app_id, icon_name, category, path):
            """Create new indicator with path."""
            return MockAppIndicator.Indicator(app_id, icon_name, category, path)

        def __init__(self, app_id=None, icon_name=None, category=None, path=None):
            self.app_id = app_id
            self.icon_name = icon_name
            self.category = category
            self.path = path
            self.menu = None
            self.status = MockAppIndicator.IndicatorStatus.PASSIVE

        def set_status(self, status):
            """Set indicator status."""
            self.status = status

        def set_menu(self, menu):
            """Set indicator menu."""
            self.menu = menu

        def set_icon(self, icon_name):
            """Set indicator icon."""
            self.icon_name = icon_name

        def set_icon_full(self, icon_name, description):
            """Set indicator icon with description."""
            self.icon_name = icon_name
            self.description = description
