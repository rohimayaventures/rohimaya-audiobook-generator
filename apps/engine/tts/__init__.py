"""
AuthorFlow TTS Module
Gemini-based Text-to-Speech with multilingual support
"""

from .gemini_tts import (
    GeminiTTS,
    VoicePreset,
    VOICE_PRESETS,
    SUPPORTED_LANGUAGES,
    synthesize_segment,
    get_voice_presets,
    get_supported_languages,
    TTSSynthesisError,
)

from .translator import (
    translate_text,
    detect_language,
    TranslationError,
)

__all__ = [
    "GeminiTTS",
    "VoicePreset",
    "VOICE_PRESETS",
    "SUPPORTED_LANGUAGES",
    "synthesize_segment",
    "get_voice_presets",
    "get_supported_languages",
    "TTSSynthesisError",
    "translate_text",
    "detect_language",
    "TranslationError",
]
