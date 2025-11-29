"""
Gemini TTS - Text-to-Speech using Google Gemini API
Supports multilingual audio generation with voice presets and emotion control

Environment variables:
- GOOGLE_GENAI_API_KEY: Google AI Studio API key (required)
- GOOGLE_TTS_MODEL: TTS model (default: gemini-2.5-flash-preview-tts)
- GOOGLE_TTS_AUDIO_ENCODING: Audio format (default: mp3)
- GOOGLE_TTS_MAX_CHARS_PER_SEGMENT: Max chars per request (default: 2800)
"""

import os
import logging
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from functools import lru_cache

logger = logging.getLogger(__name__)


class TTSSynthesisError(Exception):
    """Raised when TTS synthesis fails"""
    pass


@dataclass
class VoicePreset:
    """Voice preset configuration"""
    id: str                    # Internal ID, e.g. "narrator_female_soft"
    label: str                 # Human-friendly name
    description: str           # Shown in UI
    voice_name: str            # Gemini prebuilt voice name, e.g. "Kore"
    default_language_code: str # e.g. "en-US"
    gender: str               # "male", "female", "neutral"
    style: str                # Default style/emotion


# Gemini 2.5 Flash TTS Prebuilt Voices
# Reference: https://ai.google.dev/gemini-api/docs/speech-generation
# Available voices: Aoede, Charon, Fenrir, Kore, Puck, Zephyr, etc.
VOICE_PRESETS: Dict[str, VoicePreset] = {
    # English - US
    "narrator_female_warm": VoicePreset(
        id="narrator_female_warm",
        label="Warm Female Narrator",
        description="Warm, engaging female narrator - perfect for fiction and storytelling",
        voice_name="Kore",
        default_language_code="en-US",
        gender="female",
        style="warm, engaging",
    ),
    "narrator_male_calm": VoicePreset(
        id="narrator_male_calm",
        label="Calm Male Narrator",
        description="Calm, professional male narrator - great for non-fiction and documentaries",
        voice_name="Charon",
        default_language_code="en-US",
        gender="male",
        style="calm, professional",
    ),
    "storyteller_expressive": VoicePreset(
        id="storyteller_expressive",
        label="Expressive Storyteller",
        description="Dynamic, expressive voice for fantasy and adventure stories",
        voice_name="Puck",
        default_language_code="en-US",
        gender="neutral",
        style="expressive, dynamic",
    ),
    "studio_neutral": VoicePreset(
        id="studio_neutral",
        label="Studio Narrator",
        description="Neutral, studio-quality voice for general audiobook narration",
        voice_name="Zephyr",
        default_language_code="en-US",
        gender="neutral",
        style="neutral, clear",
    ),

    # English - UK
    "narrator_british_female": VoicePreset(
        id="narrator_british_female",
        label="British Female Narrator",
        description="Elegant British female voice for literary fiction",
        voice_name="Aoede",
        default_language_code="en-GB",
        gender="female",
        style="elegant, refined",
    ),
    "narrator_british_male": VoicePreset(
        id="narrator_british_male",
        label="British Male Narrator",
        description="Distinguished British male voice for classics and period pieces",
        voice_name="Fenrir",
        default_language_code="en-GB",
        gender="male",
        style="distinguished, classic",
    ),

    # Spanish
    "narrator_spanish_female": VoicePreset(
        id="narrator_spanish_female",
        label="Spanish Female Narrator",
        description="Warm Spanish female voice for Latin American and Spanish content",
        voice_name="Kore",
        default_language_code="es-ES",
        gender="female",
        style="warm, expressive",
    ),
    "narrator_spanish_male": VoicePreset(
        id="narrator_spanish_male",
        label="Spanish Male Narrator",
        description="Clear Spanish male voice for Spanish language audiobooks",
        voice_name="Charon",
        default_language_code="es-ES",
        gender="male",
        style="clear, engaging",
    ),

    # French
    "narrator_french_female": VoicePreset(
        id="narrator_french_female",
        label="French Female Narrator",
        description="Elegant French female voice for French content",
        voice_name="Aoede",
        default_language_code="fr-FR",
        gender="female",
        style="elegant, melodic",
    ),
    "narrator_french_male": VoicePreset(
        id="narrator_french_male",
        label="French Male Narrator",
        description="Sophisticated French male voice",
        voice_name="Fenrir",
        default_language_code="fr-FR",
        gender="male",
        style="sophisticated, cultured",
    ),

    # German
    "narrator_german_female": VoicePreset(
        id="narrator_german_female",
        label="German Female Narrator",
        description="Clear German female voice",
        voice_name="Kore",
        default_language_code="de-DE",
        gender="female",
        style="clear, precise",
    ),
    "narrator_german_male": VoicePreset(
        id="narrator_german_male",
        label="German Male Narrator",
        description="Authoritative German male voice",
        voice_name="Charon",
        default_language_code="de-DE",
        gender="male",
        style="authoritative, clear",
    ),

    # Hindi
    "narrator_hindi_female": VoicePreset(
        id="narrator_hindi_female",
        label="Hindi Female Narrator",
        description="Warm Hindi female voice for Indian content",
        voice_name="Kore",
        default_language_code="hi-IN",
        gender="female",
        style="warm, melodic",
    ),
    "narrator_hindi_male": VoicePreset(
        id="narrator_hindi_male",
        label="Hindi Male Narrator",
        description="Clear Hindi male voice for Indian audiobooks",
        voice_name="Charon",
        default_language_code="hi-IN",
        gender="male",
        style="clear, expressive",
    ),

    # Marathi (using Hindi/Indian English voices as Gemini may not have dedicated Marathi)
    "narrator_marathi_female": VoicePreset(
        id="narrator_marathi_female",
        label="Marathi Female Narrator",
        description="Female narrator for Marathi content (Indian multilingual voice)",
        voice_name="Kore",
        default_language_code="mr-IN",
        gender="female",
        style="warm, traditional",
    ),
    "narrator_marathi_male": VoicePreset(
        id="narrator_marathi_male",
        label="Marathi Male Narrator",
        description="Male narrator for Marathi content (Indian multilingual voice)",
        voice_name="Charon",
        default_language_code="mr-IN",
        gender="male",
        style="clear, traditional",
    ),

    # Japanese
    "narrator_japanese_female": VoicePreset(
        id="narrator_japanese_female",
        label="Japanese Female Narrator",
        description="Soft Japanese female voice for Japanese content",
        voice_name="Aoede",
        default_language_code="ja-JP",
        gender="female",
        style="soft, polite",
    ),
    "narrator_japanese_male": VoicePreset(
        id="narrator_japanese_male",
        label="Japanese Male Narrator",
        description="Clear Japanese male voice",
        voice_name="Fenrir",
        default_language_code="ja-JP",
        gender="male",
        style="clear, professional",
    ),

    # Portuguese (Brazil)
    "narrator_portuguese_female": VoicePreset(
        id="narrator_portuguese_female",
        label="Portuguese Female Narrator",
        description="Warm Brazilian Portuguese female voice",
        voice_name="Kore",
        default_language_code="pt-BR",
        gender="female",
        style="warm, expressive",
    ),
    "narrator_portuguese_male": VoicePreset(
        id="narrator_portuguese_male",
        label="Portuguese Male Narrator",
        description="Clear Brazilian Portuguese male voice",
        voice_name="Charon",
        default_language_code="pt-BR",
        gender="male",
        style="clear, engaging",
    ),

    # Romantic/Intimate style
    "romantic_female": VoicePreset(
        id="romantic_female",
        label="Romantic Female",
        description="Soft, intimate female voice for romance novels",
        voice_name="Aoede",
        default_language_code="en-US",
        gender="female",
        style="soft, intimate, romantic",
    ),
    "romantic_male": VoicePreset(
        id="romantic_male",
        label="Romantic Male",
        description="Deep, passionate male voice for romance novels",
        voice_name="Fenrir",
        default_language_code="en-US",
        gender="male",
        style="deep, passionate, romantic",
    ),
}


# Supported languages with display names
SUPPORTED_LANGUAGES: Dict[str, str] = {
    "auto": "Auto-detect",
    "en-US": "English (US)",
    "en-GB": "English (UK)",
    "es-ES": "Spanish (Spain)",
    "es-MX": "Spanish (Mexico)",
    "fr-FR": "French",
    "de-DE": "German",
    "it-IT": "Italian",
    "pt-BR": "Portuguese (Brazil)",
    "pt-PT": "Portuguese (Portugal)",
    "ja-JP": "Japanese",
    "ko-KR": "Korean",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "hi-IN": "Hindi",
    "mr-IN": "Marathi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "bn-IN": "Bengali",
    "ar-SA": "Arabic",
    "ru-RU": "Russian",
    "nl-NL": "Dutch",
    "pl-PL": "Polish",
    "tr-TR": "Turkish",
    "vi-VN": "Vietnamese",
    "th-TH": "Thai",
    "id-ID": "Indonesian",
    "ms-MY": "Malay",
    "sv-SE": "Swedish",
    "da-DK": "Danish",
    "no-NO": "Norwegian",
    "fi-FI": "Finnish",
}


def get_config() -> Dict[str, Any]:
    """Get TTS configuration from environment"""
    return {
        "api_key": os.getenv("GOOGLE_GENAI_API_KEY"),
        "model": os.getenv("GOOGLE_TTS_MODEL", "gemini-2.5-flash-preview-tts"),
        "audio_encoding": os.getenv("GOOGLE_TTS_AUDIO_ENCODING", "mp3"),
        "max_chars_per_segment": int(os.getenv("GOOGLE_TTS_MAX_CHARS_PER_SEGMENT", "2800")),
    }


class GeminiTTS:
    """
    Gemini TTS client for speech synthesis.

    Usage:
        tts = GeminiTTS()
        audio_bytes = await tts.synthesize(
            text="Hello world",
            preset_id="narrator_female_warm",
            emotion_style="warm, engaging"
        )
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini TTS client.

        Args:
            api_key: Google AI API key (defaults to GOOGLE_GENAI_API_KEY env var)
        """
        self.config = get_config()
        self.api_key = api_key or self.config["api_key"]

        if not self.api_key:
            raise ValueError(
                "GOOGLE_GENAI_API_KEY is required. "
                "Get one at https://aistudio.google.com/apikey"
            )

        self._client = None
        self._initialized = False

    def _ensure_client(self):
        """Lazily initialize the Gemini client"""
        if not self._initialized:
            try:
                from google import genai
                from google.genai import types

                self._client = genai.Client(api_key=self.api_key)
                self._types = types
                self._initialized = True
                logger.info(f"Gemini TTS initialized with model: {self.config['model']}")
            except ImportError:
                raise ImportError(
                    "google-genai package not installed. "
                    "Run: pip install google-genai"
                )

    def _get_preset(self, preset_id: str) -> VoicePreset:
        """Get voice preset by ID"""
        if preset_id not in VOICE_PRESETS:
            # Default to studio narrator if preset not found
            logger.warning(f"Voice preset '{preset_id}' not found, using 'studio_neutral'")
            return VOICE_PRESETS["studio_neutral"]
        return VOICE_PRESETS[preset_id]

    async def synthesize(
        self,
        text: str,
        preset_id: str = "studio_neutral",
        language_code: Optional[str] = None,
        emotion_style_prompt: Optional[str] = None,
    ) -> bytes:
        """
        Synthesize speech from text using Gemini TTS.

        Args:
            text: Text to synthesize
            preset_id: Voice preset ID
            language_code: Override language code (optional)
            emotion_style_prompt: Style/emotion instructions (e.g., "soft, romantic, intimate")

        Returns:
            Audio bytes in configured format (MP3 by default)

        Raises:
            TTSSynthesisError: If synthesis fails
        """
        self._ensure_client()

        # Get voice preset
        preset = self._get_preset(preset_id)

        # Validate text length
        max_chars = self.config["max_chars_per_segment"]
        if len(text) > max_chars:
            raise TTSSynthesisError(
                f"Text exceeds maximum length ({len(text)} > {max_chars}). "
                "Split text into smaller segments."
            )

        # Build the speech prompt
        speech_prompt = self._build_speech_prompt(text, preset, emotion_style_prompt)

        # Determine language
        lang = language_code or preset.default_language_code

        try:
            # Configure speech generation
            voice_config = self._types.VoiceConfig(
                prebuilt_voice_config=self._types.PrebuiltVoiceConfig(
                    voice_name=preset.voice_name
                )
            )

            speech_config = self._types.SpeechConfig(
                voice_config=voice_config,
            )

            # Generate speech using Gemini
            # Run in thread pool since the client may be synchronous
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._client.models.generate_content(
                    model=self.config["model"],
                    contents=speech_prompt,
                    config=self._types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=speech_config,
                    ),
                )
            )

            # Extract audio data from response
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        audio_data = part.inline_data.data
                        logger.info(f"Generated {len(audio_data)} bytes of audio")
                        return audio_data

            raise TTSSynthesisError("No audio data in response")

        except Exception as e:
            error_msg = f"TTS synthesis failed: {str(e)}"
            logger.error(error_msg)
            raise TTSSynthesisError(error_msg) from e

    def _build_speech_prompt(
        self,
        text: str,
        preset: VoicePreset,
        emotion_style_prompt: Optional[str] = None,
    ) -> str:
        """
        Build the prompt for Gemini TTS with style instructions.

        Gemini TTS supports natural language style control via the prompt.
        """
        style = emotion_style_prompt or preset.style

        # Build prompt with style instructions
        prompt = f"""Read the following text aloud with a {style} tone.

{text}"""

        return prompt


# Module-level singleton
_tts_instance: Optional[GeminiTTS] = None


def get_tts() -> GeminiTTS:
    """Get or create the global TTS instance"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = GeminiTTS()
    return _tts_instance


async def synthesize_segment(
    text: str,
    preset_id: str = "studio_neutral",
    input_language_code: Optional[str] = None,
    output_language_code: Optional[str] = None,
    emotion_style_prompt: Optional[str] = None,
) -> bytes:
    """
    Convenience function to synthesize a text segment.

    If output_language_code differs from input_language_code,
    the text will be translated first.

    Args:
        text: Text to synthesize
        preset_id: Voice preset ID
        input_language_code: Language of the input text (None or "auto" to detect)
        output_language_code: Desired output language (None to use input language)
        emotion_style_prompt: Style/emotion instructions

    Returns:
        Audio bytes

    Raises:
        TTSSynthesisError: If synthesis fails
    """
    from .translator import translate_text, detect_language

    tts = get_tts()

    # Handle translation if needed
    final_text = text
    final_language = output_language_code or input_language_code

    if output_language_code and input_language_code:
        # Normalize language codes for comparison
        input_base = input_language_code.split("-")[0].lower() if input_language_code != "auto" else None
        output_base = output_language_code.split("-")[0].lower()

        if input_language_code == "auto":
            # Detect language first
            detected = await detect_language(text)
            input_base = detected.split("-")[0].lower() if detected else None

        # Translate if languages differ
        if input_base and input_base != output_base:
            logger.info(f"Translating from {input_language_code} to {output_language_code}")
            final_text = await translate_text(
                text=text,
                source_lang=input_language_code,
                target_lang=output_language_code,
            )
            final_language = output_language_code

    # Synthesize
    return await tts.synthesize(
        text=final_text,
        preset_id=preset_id,
        language_code=final_language,
        emotion_style_prompt=emotion_style_prompt,
    )


def get_voice_presets() -> List[Dict[str, Any]]:
    """Get all available voice presets as dictionaries"""
    return [
        {
            "id": preset.id,
            "label": preset.label,
            "description": preset.description,
            "voice_name": preset.voice_name,
            "default_language_code": preset.default_language_code,
            "gender": preset.gender,
            "style": preset.style,
        }
        for preset in VOICE_PRESETS.values()
    ]


def get_supported_languages() -> Dict[str, str]:
    """Get supported languages with display names"""
    return SUPPORTED_LANGUAGES.copy()
