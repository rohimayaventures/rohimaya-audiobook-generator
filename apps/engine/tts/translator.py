"""
Translation Helper using Gemini
Handles text translation for multilingual audiobook generation

Uses the same GOOGLE_GENAI_API_KEY as the TTS module.
"""

import os
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)


class TranslationError(Exception):
    """Raised when translation fails"""
    pass


# Cache for the Gemini client
_translation_client = None


def _get_client():
    """Get or create the Gemini client for translation"""
    global _translation_client
    if _translation_client is None:
        try:
            from google import genai

            api_key = os.getenv("GOOGLE_GENAI_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_GENAI_API_KEY is required for translation")

            _translation_client = genai.Client(api_key=api_key)
            logger.info("Gemini translation client initialized")
        except ImportError:
            raise ImportError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )
    return _translation_client


# Language display names for better prompts
LANGUAGE_NAMES = {
    "en": "English",
    "en-US": "English (American)",
    "en-GB": "English (British)",
    "es": "Spanish",
    "es-ES": "Spanish (Spain)",
    "es-MX": "Spanish (Mexico)",
    "fr": "French",
    "fr-FR": "French",
    "de": "German",
    "de-DE": "German",
    "it": "Italian",
    "it-IT": "Italian",
    "pt": "Portuguese",
    "pt-BR": "Portuguese (Brazilian)",
    "pt-PT": "Portuguese (European)",
    "ja": "Japanese",
    "ja-JP": "Japanese",
    "ko": "Korean",
    "ko-KR": "Korean",
    "zh": "Chinese",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "hi": "Hindi",
    "hi-IN": "Hindi",
    "mr": "Marathi",
    "mr-IN": "Marathi",
    "ta": "Tamil",
    "ta-IN": "Tamil",
    "te": "Telugu",
    "te-IN": "Telugu",
    "bn": "Bengali",
    "bn-IN": "Bengali",
    "ar": "Arabic",
    "ar-SA": "Arabic",
    "ru": "Russian",
    "ru-RU": "Russian",
    "nl": "Dutch",
    "nl-NL": "Dutch",
    "pl": "Polish",
    "pl-PL": "Polish",
    "tr": "Turkish",
    "tr-TR": "Turkish",
    "vi": "Vietnamese",
    "vi-VN": "Vietnamese",
    "th": "Thai",
    "th-TH": "Thai",
    "id": "Indonesian",
    "id-ID": "Indonesian",
    "ms": "Malay",
    "ms-MY": "Malay",
    "sv": "Swedish",
    "sv-SE": "Swedish",
    "da": "Danish",
    "da-DK": "Danish",
    "no": "Norwegian",
    "no-NO": "Norwegian",
    "fi": "Finnish",
    "fi-FI": "Finnish",
}


def _get_language_name(code: str) -> str:
    """Get display name for language code"""
    if code in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[code]

    # Try base code
    base = code.split("-")[0].lower()
    if base in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[base]

    return code


async def detect_language(text: str) -> str:
    """
    Detect the language of the given text using Gemini.

    Args:
        text: Text to analyze

    Returns:
        Language code (e.g., "en-US", "es-ES", "hi-IN")

    Raises:
        TranslationError: If detection fails
    """
    client = _get_client()

    # Use a short sample for detection
    sample = text[:500] if len(text) > 500 else text

    prompt = f"""Analyze the following text and determine its language.
Respond with ONLY the language code in the format: language-COUNTRY
Examples: en-US, es-ES, fr-FR, de-DE, hi-IN, mr-IN, ja-JP

Text:
{sample}

Language code:"""

    try:
        logger.info("[DETECT] Detecting language from text sample...")
        sample_preview = sample[:100] + "..." if len(sample) > 100 else sample
        logger.info(f"[DETECT] Sample: {sample_preview}")

        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
        )

        if response.text:
            # Parse the response to get just the language code
            lang_code = response.text.strip().split()[0].strip()
            # Validate it looks like a language code
            if "-" in lang_code and len(lang_code) <= 10:
                logger.info(f"[DETECT] Detected language: {lang_code}")
                return lang_code

        # Default fallback
        logger.warning("[DETECT] Could not detect language, defaulting to en-US")
        return "en-US"

    except Exception as e:
        logger.error(f"[DETECT] Language detection failed: {e}")
        raise TranslationError(f"Failed to detect language: {str(e)}") from e


async def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    preserve_formatting: bool = True,
    emotion_style: Optional[str] = None,
) -> str:
    """
    Translate text from source language to target language using Gemini.

    Args:
        text: Text to translate
        source_lang: Source language code (or "auto" to detect)
        target_lang: Target language code
        preserve_formatting: If True, preserves paragraph breaks and structure
        emotion_style: Optional emotion/style to preserve (e.g., "romantic, intimate, soft")

    Returns:
        Translated text

    Raises:
        TranslationError: If translation fails
    """
    client = _get_client()

    # Handle auto-detect
    if source_lang == "auto":
        source_lang = await detect_language(text)
        logger.info(f"[TRANSLATE] Auto-detected source language: {source_lang}")

    source_name = _get_language_name(source_lang)
    target_name = _get_language_name(target_lang)

    # Build translation prompt with emotional preservation
    formatting_instruction = ""
    if preserve_formatting:
        formatting_instruction = """
IMPORTANT: Preserve all paragraph breaks, line breaks, and text structure.
Do not add any explanations or notes. Only output the translated text."""

    # Add emotion/style preservation instructions
    emotion_instruction = ""
    if emotion_style:
        emotion_instruction = f"""
CRITICAL: Preserve the emotional tone and style throughout the translation.
The translation should feel: {emotion_style}
Keep romantic nuances intact, use natural phrasing, and maintain soft intimate style where present."""

    prompt = f"""Translate the following text from {source_name} to {target_name}.

Produce a natural, fluent translation suitable for audiobook narration.
Maintain the original tone, style, and meaning.{emotion_instruction}{formatting_instruction}

Original text ({source_name}):
{text}

Translation ({target_name}):"""

    try:
        logger.info(f"[TRANSLATE] Translating from {source_name} to {target_name}")
        if emotion_style:
            logger.info(f"[TRANSLATE] Preserving emotion/style: {emotion_style}")

        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
        )

        if response.text:
            translated = response.text.strip()
            # Log preview of translation
            preview = translated[:200] + "..." if len(translated) > 200 else translated
            logger.info(f"[TRANSLATE] Translation complete: {len(text)} -> {len(translated)} chars")
            logger.info(f"[TRANSLATE] Preview: {preview}")
            return translated

        raise TranslationError("No translation in response")

    except Exception as e:
        error_msg = f"Translation failed: {str(e)}"
        logger.error(error_msg)
        raise TranslationError(error_msg) from e


async def translate_segments(
    segments: list[str],
    source_lang: str,
    target_lang: str,
    max_concurrent: int = 5,
) -> list[str]:
    """
    Translate multiple text segments in parallel.

    Args:
        segments: List of text segments
        source_lang: Source language code
        target_lang: Target language code
        max_concurrent: Maximum concurrent translations

    Returns:
        List of translated segments

    Raises:
        TranslationError: If any translation fails
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def translate_with_limit(text: str) -> str:
        async with semaphore:
            return await translate_text(text, source_lang, target_lang)

    tasks = [translate_with_limit(seg) for seg in segments]
    results = await asyncio.gather(*tasks)

    return list(results)
