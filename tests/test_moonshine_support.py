"""Focused tests for Moonshine helper/config support."""

from vocalinux.ui.config_manager import DEFAULT_CONFIG
from vocalinux.utils.moonshine_model_info import (
    get_moonshine_default_model_size,
    get_moonshine_supported_model_sizes,
    is_moonshine_language_supported,
    resolve_moonshine_language,
    resolve_moonshine_model_arch_name,
)


def test_default_config_has_moonshine_model_size():
    sr = DEFAULT_CONFIG["speech_recognition"]
    assert sr["moonshine_model_size"] == "auto"


def test_moonshine_language_mapping():
    assert resolve_moonshine_language("auto") == ("en", True)
    assert resolve_moonshine_language("en-us") == ("en", False)
    assert resolve_moonshine_language("en-in") == ("en", False)
    assert resolve_moonshine_language("es") == ("es", False)
    assert resolve_moonshine_language("fr") == ("en", True)


def test_moonshine_language_support():
    assert is_moonshine_language_supported("auto") is True
    assert is_moonshine_language_supported("en-us") is True
    assert is_moonshine_language_supported("ja") is True
    assert is_moonshine_language_supported("fr") is False


def test_moonshine_supported_model_sizes():
    assert get_moonshine_supported_model_sizes("en-us") == ["tiny", "base", "small", "medium"]
    assert get_moonshine_supported_model_sizes("es") == ["base"]
    assert get_moonshine_supported_model_sizes("ko") == ["tiny"]


def test_moonshine_default_model_size():
    assert get_moonshine_default_model_size("en-us") == "medium"
    assert get_moonshine_default_model_size("es") == "base"
    assert get_moonshine_default_model_size("ko") == "tiny"


def test_moonshine_model_arch_auto():
    assert resolve_moonshine_model_arch_name("auto", "en-us") == (None, False)


def test_moonshine_model_arch_direct():
    assert resolve_moonshine_model_arch_name("medium", "en-us") == ("MEDIUM_STREAMING", False)
    assert resolve_moonshine_model_arch_name("tiny", "ja") == ("TINY", False)


def test_moonshine_model_arch_fallback():
    assert resolve_moonshine_model_arch_name("large", "en-us") == ("MEDIUM_STREAMING", True)
    assert resolve_moonshine_model_arch_name("tiny", "es") == ("BASE", True)
