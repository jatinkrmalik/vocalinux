"""
Tests for the version module.
"""

import unittest


class TestVersion(unittest.TestCase):
    """Test cases for version information."""

    def test_version_exists(self):
        """Test that version string exists and is valid."""
        from vocalinux.version import __version__

        self.assertIsInstance(__version__, str)
        self.assertTrue(len(__version__) > 0)
        # Version should follow semver-like pattern
        parts = __version__.replace("-", ".").split(".")
        self.assertTrue(len(parts) >= 3)

    def test_version_info_tuple(self):
        """Test that version info tuple exists and is valid."""
        from vocalinux.version import __version_info__

        self.assertIsInstance(__version_info__, tuple)
        self.assertTrue(len(__version_info__) >= 3)
        # First three elements should be integers
        self.assertIsInstance(__version_info__[0], int)
        self.assertIsInstance(__version_info__[1], int)
        self.assertIsInstance(__version_info__[2], int)

    def test_author_info(self):
        """Test that author information exists."""
        from vocalinux.version import __author__, __email__

        self.assertIsInstance(__author__, str)
        self.assertTrue(len(__author__) > 0)
        self.assertIsInstance(__email__, str)
        self.assertIn("@", __email__)

    def test_license_info(self):
        """Test that license information exists."""
        from vocalinux.version import __copyright__, __license__

        self.assertIsInstance(__license__, str)
        self.assertTrue(len(__license__) > 0)
        self.assertIsInstance(__copyright__, str)
        self.assertIn("Copyright", __copyright__)

    def test_url_and_description(self):
        """Test that URL and description exist."""
        from vocalinux.version import __description__, __url__

        self.assertIsInstance(__url__, str)
        self.assertTrue(__url__.startswith("http"))
        self.assertIsInstance(__description__, str)
        self.assertTrue(len(__description__) > 0)
