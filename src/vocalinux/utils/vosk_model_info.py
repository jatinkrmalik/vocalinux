# Language definitions with display names and Whisper/VOSK codes
# Supported languages for speech recognition
#
# Whisper / whisper.cpp / remote_api use the catalog key (or the "whisper"
# code for English-only model checks). VOSK uses per-language model zips from
# VOSK_MODEL_INFO; set "vosk" to None when no official Alphacephei model exists.
# Medium/large must cover every language present in small (see issue #550).
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
    "en-in": {
        "name": "English (India)",
        "whisper": "en",
        "vosk": "vosk-model-small-en-in-0.4",
    },
    "ar": {
        "name": "Arabic",
        "whisper": "ar",
        "vosk": "vosk-model-small-ar-0.3",
    },
    "bn": {
        "name": "Bengali",
        "whisper": "bn",
        "vosk": None,
    },
    "ca": {
        "name": "Catalan",
        "whisper": "ca",
        "vosk": "vosk-model-small-ca-0.4",
    },
    "zh": {
        "name": "Chinese",
        "whisper": "zh",
        "vosk": "vosk-model-small-cn-0.22",
    },
    "cs": {
        "name": "Czech",
        "whisper": "cs",
        "vosk": "vosk-model-small-cs-0.4-rhasspy",
    },
    "da": {
        "name": "Danish",
        "whisper": "da",
        "vosk": None,
    },
    "nl": {
        "name": "Dutch",
        "whisper": "nl",
        "vosk": "vosk-model-small-nl-0.22",
    },
    "fi": {
        "name": "Finnish",
        "whisper": "fi",
        "vosk": None,
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
    "el": {
        "name": "Greek",
        "whisper": "el",
        "vosk": None,
    },
    "he": {
        "name": "Hebrew",
        "whisper": "he",
        "vosk": None,
    },
    "hi": {
        "name": "Hindi",
        "whisper": "hi",
        "vosk": "vosk-model-small-hi-0.22",
    },
    "hu": {
        "name": "Hungarian",
        "whisper": "hu",
        "vosk": None,
    },
    "id": {
        "name": "Indonesian",
        "whisper": "id",
        "vosk": None,
    },
    "it": {
        "name": "Italian",
        "whisper": "it",
        "vosk": "vosk-model-small-it-0.22",
    },
    "ja": {
        "name": "Japanese",
        "whisper": "ja",
        "vosk": "vosk-model-small-ja-0.22",
    },
    "ko": {
        "name": "Korean",
        "whisper": "ko",
        "vosk": "vosk-model-small-ko-0.22",
    },
    "no": {
        "name": "Norwegian",
        "whisper": "no",
        "vosk": None,
    },
    "fa": {
        "name": "Persian",
        "whisper": "fa",
        "vosk": "vosk-model-small-fa-0.42",
    },
    "pl": {
        "name": "Polish",
        "whisper": "pl",
        "vosk": "vosk-model-small-pl-0.22",
    },
    "pt": {
        "name": "Portuguese",
        "whisper": "pt",
        "vosk": "vosk-model-small-pt-0.3",
    },
    "ro": {
        "name": "Romanian",
        "whisper": "ro",
        "vosk": None,
    },
    "ru": {
        "name": "Russian",
        "whisper": "ru",
        "vosk": "vosk-model-small-ru-0.22",
    },
    "es": {
        "name": "Spanish",
        "whisper": "es",
        "vosk": "vosk-model-small-es-0.42",
    },
    "sv": {
        "name": "Swedish",
        "whisper": "sv",
        "vosk": "vosk-model-small-sv-rhasspy-0.15",
    },
    "ta": {
        "name": "Tamil",
        "whisper": "ta",
        "vosk": None,
    },
    "th": {
        "name": "Thai",
        "whisper": "th",
        "vosk": None,
    },
    "tr": {
        "name": "Turkish",
        "whisper": "tr",
        "vosk": "vosk-model-small-tr-0.3",
    },
    "uk": {
        "name": "Ukrainian",
        "whisper": "uk",
        "vosk": "vosk-model-small-uk-v3-small",
    },
    "vi": {
        "name": "Vietnamese",
        "whisper": "vi",
        "vosk": "vosk-model-small-vn-0.4",
    },
}


# VOSK model metadata for display and download path resolution.
# When Alphacephei only ships a small model, medium/large point at that same
# zip so size selection never resolves to None (issue #550).
VOSK_MODEL_INFO = {
    "small": {
        "size_mb": 40,
        "desc": "Lightweight, fast",
        "languages": {
            "en-us": "vosk-model-small-en-us-0.15",
            "en-in": "vosk-model-small-en-in-0.4",
            "ar": "vosk-model-small-ar-0.3",
            "ca": "vosk-model-small-ca-0.4",
            "zh": "vosk-model-small-cn-0.22",
            "cs": "vosk-model-small-cs-0.4-rhasspy",
            "nl": "vosk-model-small-nl-0.22",
            "fr": "vosk-model-small-fr-0.22",
            "de": "vosk-model-small-de-0.15",
            "hi": "vosk-model-small-hi-0.22",
            "it": "vosk-model-small-it-0.22",
            "ja": "vosk-model-small-ja-0.22",
            "ko": "vosk-model-small-ko-0.22",
            "fa": "vosk-model-small-fa-0.42",
            "pl": "vosk-model-small-pl-0.22",
            "pt": "vosk-model-small-pt-0.3",
            "ru": "vosk-model-small-ru-0.22",
            "es": "vosk-model-small-es-0.42",
            "sv": "vosk-model-small-sv-rhasspy-0.15",
            "tr": "vosk-model-small-tr-0.3",
            "uk": "vosk-model-small-uk-v3-small",
            "vi": "vosk-model-small-vn-0.4",
        },
    },
    "medium": {
        "size_mb": 1500,
        "desc": "Balanced accuracy/speed",
        "languages": {
            "en-us": "vosk-model-en-us-0.22",
            "en-in": "vosk-model-en-in-0.5",
            "ar": "vosk-model-ar-0.22-linto-1.1.0",
            "ca": "vosk-model-small-ca-0.4",
            "zh": "vosk-model-cn-0.22",
            "cs": "vosk-model-small-cs-0.4-rhasspy",
            "nl": "vosk-model-nl-spraakherkenning-0.6",
            "fr": "vosk-model-fr-0.22",
            "de": "vosk-model-de-0.21",
            "hi": "vosk-model-hi-0.22",
            "it": "vosk-model-it-0.22",
            "ja": "vosk-model-ja-0.22",
            "ko": "vosk-model-small-ko-0.22",
            "fa": "vosk-model-fa-0.42",
            "pl": "vosk-model-small-pl-0.22",
            "pt": "vosk-model-pt-0.4",
            "ru": "vosk-model-ru-0.22",
            "es": "vosk-model-es-0.42",
            "sv": "vosk-model-small-sv-rhasspy-0.15",
            "tr": "vosk-model-small-tr-0.3",
            "uk": "vosk-model-uk-v3",
            "vi": "vosk-model-vn-0.4",
        },
    },
    "large": {
        "size_mb": 1500,
        "desc": "Same as medium (best available)",
        "languages": {
            "en-us": "vosk-model-en-us-0.22",
            "en-in": "vosk-model-en-in-0.5",
            "ar": "vosk-model-ar-0.22-linto-1.1.0",
            "ca": "vosk-model-small-ca-0.4",
            "zh": "vosk-model-cn-0.22",
            "cs": "vosk-model-small-cs-0.4-rhasspy",
            "nl": "vosk-model-nl-spraakherkenning-0.6",
            "fr": "vosk-model-fr-0.22",
            "de": "vosk-model-de-0.21",
            "hi": "vosk-model-hi-0.22",
            "it": "vosk-model-it-0.22",
            "ja": "vosk-model-ja-0.22",
            "ko": "vosk-model-small-ko-0.22",
            "fa": "vosk-model-fa-0.42",
            "pl": "vosk-model-small-pl-0.22",
            "pt": "vosk-model-pt-0.4",
            "ru": "vosk-model-ru-0.22",
            "es": "vosk-model-es-0.42",
            "sv": "vosk-model-small-sv-rhasspy-0.15",
            "tr": "vosk-model-small-tr-0.3",
            "uk": "vosk-model-uk-v3",
            "vi": "vosk-model-vn-0.4",
        },
    },
}
