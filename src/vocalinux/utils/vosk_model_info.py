# VOSK model metadata for display
# The large option uses the same model as medium, because 0.42 seems unavailable
# TODO @violog: specify correct size for each model
VOSK_MODEL_INFO = {
    "small": {
        "size_mb": 40,
        "desc": "Lightweight, fast",
        "languages": {
            "en-us": "vosk-model-small-en-us-0.15",
            "fr": "vosk-model-small-fr-0.22",
            "de": "vosk-model-small-de-0.15",
            "ru": "vosk-model-small-ru-0.22",
        }
    },
    "medium": {
        "size_mb": 1800,
        "desc": "Balanced accuracy/speed",
        "languages": {
            "en-us": "vosk-model-en-us-0.22",
            "fr": "vosk-model-fr-0.22",
            "de": "vosk-model-de-0.21",
            "ru": "vosk-model-ru-0.22",
        }
    },
    "large": {
        "size_mb": 1800,
        "desc": "Same as medium (best available)",
        "languages": {
            "en-us": "vosk-model-en-us-0.22",
            "fr": "vosk-model-fr-0.22",
            "de": "vosk-model-de-0.21",
            "ru": "vosk-model-ru-0.22",
        }
    },
}
