"""
Groq Whisper API model information for Vocalinux.

This module provides model metadata for Groq's hosted Whisper API models.
No local model downloads are needed — inference runs on Groq's servers.
"""

# Groq Whisper API models
# Pricing: ~$0.03/hour of audio (as of 2025)
GROQ_MODEL_INFO = {
    "whisper-large-v3": {
        "desc": "Highest accuracy, hosted API",
        "speed": "Fast",
        "notes": "OpenAI Whisper large-v3 on Groq hardware",
    },
    "whisper-large-v3-turbo": {
        "desc": "Best speed/quality balance, hosted API",
        "speed": "Fastest",
        "notes": "Optimized large-v3 for lower latency",
    },
    "distil-whisper-large-v3-en": {
        "desc": "English-only, fastest, hosted API",
        "speed": "Fastest",
        "notes": "Distilled model, English only",
    },
}

DEFAULT_GROQ_MODEL = "whisper-large-v3-turbo"
