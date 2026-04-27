"""Moonshine language and model compatibility helpers for Vocalinux."""

from __future__ import annotations

from typing import Optional

MOONSHINE_LANGUAGE_MAP = {
    "auto": "en",
    "en": "en",
    "en-us": "en",
    "en-in": "en",
    "es": "es",
    "zh": "zh",
    "ja": "ja",
    "ko": "ko",
    "ar": "ar",
}

_LANGUAGE_MODEL_ARCHES = {
    "en": {
        "tiny": "TINY_STREAMING",
        "base": "BASE",
        "small": "SMALL_STREAMING",
        "medium": "MEDIUM_STREAMING",
    },
    "es": {
        "base": "BASE",
    },
    "zh": {
        "base": "BASE",
    },
    "ja": {
        "tiny": "TINY",
        "base": "BASE",
    },
    "ko": {
        "tiny": "TINY",
    },
    "ar": {
        "base": "BASE",
    },
}

_DEFAULT_MODEL_SIZE = {
    "en": "medium",
    "es": "base",
    "zh": "base",
    "ja": "base",
    "ko": "tiny",
    "ar": "base",
}


def is_moonshine_available() -> bool:
    """Return True when moonshine_voice is importable."""
    try:
        import moonshine_voice  # noqa: F401
    except ImportError:
        return False
    return True


def resolve_moonshine_language(language: Optional[str]) -> tuple[str, bool]:
    """Map Vocalinux language values to Moonshine-compatible language codes."""
    normalized = (language or "auto").strip().lower()
    resolved = MOONSHINE_LANGUAGE_MAP.get(normalized)
    if resolved is None:
        return "en", True
    return resolved, normalized == "auto"


def is_moonshine_language_supported(language: Optional[str]) -> bool:
    """Return True if the provided Vocalinux language can be used without fallback."""
    normalized = (language or "auto").strip().lower()
    return normalized in MOONSHINE_LANGUAGE_MAP


def get_moonshine_supported_model_sizes(language: Optional[str]) -> list[str]:
    """Return valid Moonshine model-size labels for the resolved language."""
    resolved_language, _ = resolve_moonshine_language(language)
    arches = _LANGUAGE_MODEL_ARCHES.get(resolved_language, _LANGUAGE_MODEL_ARCHES["en"])
    return list(arches.keys())


def get_moonshine_default_model_size(language: Optional[str]) -> str:
    """Return the safest default model-size label for the resolved language."""
    resolved_language, _ = resolve_moonshine_language(language)
    return _DEFAULT_MODEL_SIZE.get(resolved_language, "medium")


def resolve_moonshine_model_arch_name(
    model_size: Optional[str], language: Optional[str]
) -> tuple[Optional[str], bool]:
    """Resolve a Vocalinux model-size label to a Moonshine ModelArch enum name.

    Returns:
        (arch_name, used_fallback)

        arch_name is None when Moonshine should choose the default arch itself.
    """
    resolved_language, _ = resolve_moonshine_language(language)
    valid_arches = _LANGUAGE_MODEL_ARCHES.get(
        resolved_language, _LANGUAGE_MODEL_ARCHES["en"]
    )

    normalized = (model_size or "auto").strip().lower()
    if normalized in ("", "auto"):
        return None, False

    if normalized in valid_arches:
        return valid_arches[normalized], False

    fallback_aliases = {
        "large": "medium",
    }
    aliased = fallback_aliases.get(normalized)
    if aliased and aliased in valid_arches:
        return valid_arches[aliased], True

    default_size = get_moonshine_default_model_size(language)
    return valid_arches[default_size], True
