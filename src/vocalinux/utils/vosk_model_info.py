# Language definitions with display names and Whisper/VOSK codes
# Supported languages for speech recognition
SUPPORTED_LANGUAGES = {
    "auto": {
        "name": "Auto-detect",
        "whisper": None,
        "vosk": None,
        "warning": "Slower, may be less accurate",
    },
    "en-us": {
        "name": "English (US)",
        "whisper": "en",
        "vosk": "vosk-model-small-en-us-0.15",
    },
    "hi": {
        "name": "Hindi",
        "whisper": "hi",
        "vosk": "vosk-model-small-hi-0.22",
    },
    "es": {
        "name": "Spanish",
        "whisper": "es",
        "vosk": "vosk-model-small-es-0.42",
    },
    "fr": {
        "name": "French",
        "whisper": "fr",
        "vosk": "vosk-model-small-fr-0.22",
    },
    "de": {
        "name": "German",
        "whisper": "de",
        "vosk": "vosk-model-small-de-0.15",
    },
    "it": {
        "name": "Italian",
        "whisper": "it",
        "vosk": "vosk-model-small-it-0.22",
    },
    "pt": {
        "name": "Portuguese",
        "whisper": "pt",
        "vosk": "vosk-model-small-pt-0.3",
    },
    "ru": {
        "name": "Russian",
        "whisper": "ru",
        "vosk": "vosk-model-small-ru-0.22",
    },
    "zh": {
        "name": "Chinese",
        "whisper": "zh",
        "vosk": "vosk-model-small-cn-0.22",
    },
}


# VOSK model metadata for display
# The large option uses the same model as medium, because 0.42 seems unavailable
# TODO @violog: specify correct size for each model
VOSK_MODEL_INFO = {
    "small": {
        "size_mb": 40,
        "desc": "Lightweight, fast",
        "languages": {
            "en-us": "vosk-model-small-en-us-0.15",
            "en-in": "vosk-model-small-en-in-0.4",
            "hi": "vosk-model-small-hi-0.22",
            "es": "vosk-model-small-es-0.42",
            "fr": "vosk-model-small-fr-0.22",
            "de": "vosk-model-small-de-0.15",
            "it": "vosk-model-small-it-0.22",
            "pt": "vosk-model-small-pt-0.3",
            "ru": "vosk-model-small-ru-0.22",
            "zh": "vosk-model-small-cn-0.22",
        },
    },
    "medium": {
        "size_mb": 1800,
        "desc": "Balanced accuracy/speed",
        "languages": {
            "en-us": "vosk-model-en-us-0.22",
            "fr": "vosk-model-fr-0.22",
            "de": "vosk-model-de-0.21",
            "ru": "vosk-model-ru-0.22",
            "hi": "vosk-model-hi-0.22",
            "es": "vosk-model-es-0.42",
            "pt": "vosk-model-pt-0.4",
            "zh": "vosk-model-cn-0.22",
        },
    },
    "large": {
        "size_mb": 1800,
        "desc": "Same as medium (best available)",
        "languages": {
            "en-us": "vosk-model-en-us-0.22",
            "fr": "vosk-model-fr-0.22",
            "de": "vosk-model-de-0.21",
            "ru": "vosk-model-ru-0.22",
            "hi": "vosk-model-hi-0.22",
            "es": "vosk-model-es-0.42",
            "pt": "vosk-model-pt-0.4",
            "zh": "vosk-model-cn-0.22",
        },
    },
}
