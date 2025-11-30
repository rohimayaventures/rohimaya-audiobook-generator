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
    sample_text: str = ""     # Genre-appropriate preview text for this narrator


# Gemini 2.5 Flash TTS Prebuilt Voices
# Reference: https://ai.google.dev/gemini-api/docs/speech-generation
# Available voices: Aoede, Charon, Fenrir, Kore, Puck, Zephyr, etc.
VOICE_PRESETS: Dict[str, VoicePreset] = {
    # =========================================================================
    # ENGLISH - US (Main collection with diverse, creative personas)
    # =========================================================================
    "narrator_female_warm": VoicePreset(
        id="narrator_female_warm",
        label="Celeste Monroe",
        description="Warm, captivating voice that draws you into every story. Perfect for fiction and emotional narratives.",
        voice_name="Kore",
        default_language_code="en-US",
        gender="female",
        style="warm, engaging",
        sample_text="My heart found its home in your hands. Every whisper between us tells a story of forever, a promise written in the stars.",
    ),
    "narrator_female_soft": VoicePreset(
        id="narrator_female_soft",
        label="Violet Sinclair",
        description="Soft, intimate whispers for your heart. The perfect companion for romance and tender moments.",
        voice_name="Achernar",
        default_language_code="en-US",
        gender="female",
        style="soft, gentle",
        sample_text="He traced the curve of her cheek with trembling fingers. 'Stay,' he whispered. 'Stay, and let me prove my heart belongs to you.'",
    ),
    "narrator_female_smooth": VoicePreset(
        id="narrator_female_smooth",
        label="Isabella Cruz",
        description="Smooth as silk with timeless elegance. Made for literary fiction and classics.",
        voice_name="Despina",
        default_language_code="en-US",
        gender="female",
        style="smooth, flowing",
        sample_text="The garden held its breath as autumn descended, each leaf a whispered memory of summers past, each shadow a story waiting to unfold.",
    ),
    "narrator_female_youthful": VoicePreset(
        id="narrator_female_youthful",
        label="Mia Brightwell",
        description="Fresh, vibrant energy that captures youth and adventure. Ideal for YA and coming-of-age stories.",
        voice_name="Leda",
        default_language_code="en-US",
        gender="female",
        style="youthful, fresh",
        sample_text="I never expected summer camp to change everything. But then again, I never expected to discover I had powers, either. Awkward.",
    ),
    "narrator_female_clear": VoicePreset(
        id="narrator_female_clear",
        label="Dr. Evelyn Reed",
        description="Crystal-clear articulation with intellectual warmth. Perfect for non-fiction and educational content.",
        voice_name="Erinome",
        default_language_code="en-US",
        gender="female",
        style="clear, articulate",
        sample_text="The human brain processes eleven million bits of information every second. Yet we're only consciously aware of about forty.",
    ),
    "narrator_male_calm": VoicePreset(
        id="narrator_male_calm",
        label="Marcus Blackwood",
        description="Calm, authoritative presence that commands attention. Great for non-fiction and documentaries.",
        voice_name="Charon",
        default_language_code="en-US",
        gender="male",
        style="calm, professional",
        sample_text="In eighteen forty-eight, gold was discovered at Sutter's Mill. Within months, three hundred thousand prospectors flooded into California.",
    ),
    "narrator_male_smooth": VoicePreset(
        id="narrator_male_smooth",
        label="James Hartley",
        description="Smooth, magnetic voice that keeps you on edge. Perfect for thrillers and mysteries.",
        voice_name="Algieba",
        default_language_code="en-US",
        gender="male",
        style="smooth, rich",
        sample_text="The file landed on my desk at midnight. Three people were dead, and the only witness had just gone missing. This was going to be a long night.",
    ),
    "narrator_male_warm": VoicePreset(
        id="narrator_male_warm",
        label="Benjamin Stone",
        description="Warm, inviting voice like a fireside chat. Great for memoirs and heartfelt stories.",
        voice_name="Sulafat",
        default_language_code="en-US",
        gender="male",
        style="warm, inviting",
        sample_text="My grandfather always said, 'The best stories aren't in books—they're in the lines on an old man's face.' I finally understand what he meant.",
    ),
    "narrator_male_gravelly": VoicePreset(
        id="narrator_male_gravelly",
        label="Vincent Malone",
        description="Deep, gravelly tones straight from a noir film. Ideal for crime fiction and gritty narratives.",
        voice_name="Algenib",
        default_language_code="en-US",
        gender="male",
        style="gravelly, deep",
        sample_text="Rain hammered the pavement like bullets. She walked out of my life that night, taking nothing but my trust and leaving nothing but questions.",
    ),
    "narrator_male_mature": VoicePreset(
        id="narrator_male_mature",
        label="Theodore Wellington",
        description="Distinguished and refined with decades of wisdom. Perfect for historical fiction and classics.",
        voice_name="Gacrux",
        default_language_code="en-US",
        gender="male",
        style="mature, seasoned",
        sample_text="The manor had stood for three centuries, its walls bearing witness to revolution, scandal, and the quiet tragedies of ordinary lives.",
    ),
    "narrator_male_knowledgeable": VoicePreset(
        id="narrator_male_knowledgeable",
        label="Professor Arthur Hayes",
        description="Authoritative expertise that makes complex topics accessible. Ideal for science and history.",
        voice_name="Sadaltager",
        default_language_code="en-US",
        gender="male",
        style="knowledgeable, authoritative",
        sample_text="Quantum entanglement suggests particles can communicate instantly across vast distances. Einstein called it 'spooky action at a distance.'",
    ),
    "storyteller_expressive": VoicePreset(
        id="storyteller_expressive",
        label="Phoenix Starling",
        description="Dynamic, theatrical flair that brings fantasy worlds to life. Perfect for epic adventures.",
        voice_name="Puck",
        default_language_code="en-US",
        gender="neutral",
        style="expressive, dynamic",
        sample_text="The dragon unfurled its wings, shadow stretching across the valley. 'You dare enter my domain, little warrior? Then let us see what courage you carry!'",
    ),
    "storyteller_lively": VoicePreset(
        id="storyteller_lively",
        label="Jamie Whimsy",
        description="Boundless energy and playful charm. Made for children's books and animated stories.",
        voice_name="Sadachbia",
        default_language_code="en-US",
        gender="neutral",
        style="lively, energetic",
        sample_text="Benny the bunny bounced through the meadow. 'Today,' he declared, 'is going to be the best adventure ever!' And oh boy, was he right!",
    ),
    "storyteller_friendly": VoicePreset(
        id="storyteller_friendly",
        label="Sam Riverside",
        description="Your best friend telling a story. Approachable and natural for casual content.",
        voice_name="Achird",
        default_language_code="en-US",
        gender="neutral",
        style="friendly, approachable",
        sample_text="So there I was, standing in the middle of the airport, with no luggage and a plane ticket to the wrong country. Let me tell you how that happened.",
    ),
    "studio_neutral": VoicePreset(
        id="studio_neutral",
        label="Alex Sterling",
        description="Studio-quality precision with versatile appeal. The reliable choice for any audiobook.",
        voice_name="Zephyr",
        default_language_code="en-US",
        gender="neutral",
        style="neutral, clear",
        sample_text="Welcome to your audiobook. I'll be guiding you through this story with clarity and care, bringing each word to life as the author intended.",
    ),
    "studio_bright": VoicePreset(
        id="studio_bright",
        label="Jordan Brooks",
        description="Bright, motivational energy that inspires action. Perfect for business and self-help.",
        voice_name="Autonoe",
        default_language_code="en-US",
        gender="neutral",
        style="bright, clear",
        sample_text="Today is the day you stop waiting and start doing. Your potential is unlimited—it's time to unlock it. Are you ready to transform your life?",
    ),
    "studio_even": VoicePreset(
        id="studio_even",
        label="Morgan Everett",
        description="Perfectly balanced and precise. Ideal for technical guides and instructional content.",
        voice_name="Schedar",
        default_language_code="en-US",
        gender="neutral",
        style="even, balanced",
        sample_text="Step one: open the application. Step two: navigate to settings. Step three: select your preferences. These simple steps will optimize your workflow.",
    ),
    "casual_narrator": VoicePreset(
        id="casual_narrator",
        label="Riley Cooper",
        description="Laid-back vibes like chatting over coffee. Great for casual and conversational audiobooks.",
        voice_name="Zubenelgenubi",
        default_language_code="en-US",
        gender="neutral",
        style="casual, relaxed",
        sample_text="You know what? Life's too short for perfect plans. Sometimes you just gotta grab your bag and go. That's exactly what I did last summer.",
    ),
    "gentle_narrator": VoicePreset(
        id="gentle_narrator",
        label="Sage Meadows",
        description="Tranquil and soothing like a gentle stream. Perfect for meditation and wellness content.",
        voice_name="Vindemiatrix",
        default_language_code="en-US",
        gender="neutral",
        style="gentle, soothing",
        sample_text="Close your eyes and breathe deeply. Feel the tension leaving your body with each exhale. You are safe. You are calm. You are exactly where you need to be.",
    ),

    # =========================================================================
    # ENGLISH - UK (British accents with unique personas)
    # =========================================================================
    "narrator_british_female": VoicePreset(
        id="narrator_british_female",
        label="Lady Victoria Ashworth",
        description="Elegant British refinement with aristocratic charm. Perfect for literary fiction and period dramas.",
        voice_name="Aoede",
        default_language_code="en-GB",
        gender="female",
        style="elegant, refined",
        sample_text="One must always maintain composure, even when the world around us crumbles. Tea, my dear? It's frightfully good for steadying the nerves.",
    ),
    "narrator_british_male": VoicePreset(
        id="narrator_british_male",
        label="Sir Edmund Fairfax",
        description="Distinguished British gentleman's voice. Ideal for classics and period pieces.",
        voice_name="Fenrir",
        default_language_code="en-GB",
        gender="male",
        style="distinguished, classic",
        sample_text="It was the sort of evening that reminded one of better days—when honour meant something, and a gentleman's word was his bond.",
    ),
    "narrator_british_clear": VoicePreset(
        id="narrator_british_clear",
        label="Elliot Clarke",
        description="Clear, precise British articulation. Perfect for documentaries and non-fiction.",
        voice_name="Iapetus",
        default_language_code="en-GB",
        gender="neutral",
        style="clear, precise",
        sample_text="The Thames has witnessed two thousand years of London's history. Its waters carry secrets from Roman invaders to modern-day traders.",
    ),

    # Spanish (with culturally appropriate names)
    "narrator_spanish_female": VoicePreset(
        id="narrator_spanish_female",
        label="Lucia Fernandez",
        description="Warm, passionate Spanish voice. Perfect for Latin American and Spanish content.",
        voice_name="Kore",
        default_language_code="es-ES",
        gender="female",
        style="warm, expressive",
        sample_text="El amor es como el viento: no puedes verlo, pero puedes sentirlo. Y cuando llega, lo cambia todo en su camino.",
    ),
    "narrator_spanish_male": VoicePreset(
        id="narrator_spanish_male",
        label="Alejandro Rivera",
        description="Rich, engaging Spanish voice. Ideal for Spanish language audiobooks.",
        voice_name="Charon",
        default_language_code="es-ES",
        gender="male",
        style="clear, engaging",
        sample_text="La aventura comenzó cuando menos lo esperaba. Un mapa antiguo, una promesa olvidada, y el destino esperando al final del camino.",
    ),

    # French (with culturally appropriate names)
    "narrator_french_female": VoicePreset(
        id="narrator_french_female",
        label="Camille Beaumont",
        description="Elegant, melodic French voice. Made for French literary content.",
        voice_name="Aoede",
        default_language_code="fr-FR",
        gender="female",
        style="elegant, melodic",
        sample_text="Paris s'éveillait doucement sous la lumière dorée du matin. Les rues pavées gardaient encore les secrets de la nuit.",
    ),
    "narrator_french_male": VoicePreset(
        id="narrator_french_male",
        label="Jean-Pierre Moreau",
        description="Sophisticated French voice with cultured charm.",
        voice_name="Fenrir",
        default_language_code="fr-FR",
        gender="male",
        style="sophisticated, cultured",
        sample_text="L'art de vivre, c'est comprendre que chaque moment est précieux. Le café du matin, la conversation avec un ami, le silence de la nuit.",
    ),

    # German (with culturally appropriate names)
    "narrator_german_female": VoicePreset(
        id="narrator_german_female",
        label="Anna Schmidt",
        description="Clear, precise German voice. Perfect for German audiobooks.",
        voice_name="Kore",
        default_language_code="de-DE",
        gender="female",
        style="clear, precise",
        sample_text="Die Berge erhoben sich majestätisch vor uns, ihre Gipfel in Wolken gehüllt. Hier begann unsere Reise ins Unbekannte.",
    ),
    "narrator_german_male": VoicePreset(
        id="narrator_german_male",
        label="Klaus Weber",
        description="Authoritative German voice with commanding presence.",
        voice_name="Charon",
        default_language_code="de-DE",
        gender="male",
        style="authoritative, clear",
        sample_text="Die Geschichte lehrt uns, dass Veränderung unvermeidlich ist. Doch wie wir damit umgehen, definiert, wer wir werden.",
    ),

    # Hindi (with culturally appropriate names)
    "narrator_hindi_female": VoicePreset(
        id="narrator_hindi_female",
        label="Priya Sharma",
        description="Warm, melodic Hindi voice. Perfect for Indian stories and content.",
        voice_name="Kore",
        default_language_code="hi-IN",
        gender="female",
        style="warm, melodic",
    ),
    "narrator_hindi_male": VoicePreset(
        id="narrator_hindi_male",
        label="Arjun Patel",
        description="Clear, expressive Hindi voice. Ideal for Indian audiobooks.",
        voice_name="Charon",
        default_language_code="hi-IN",
        gender="male",
        style="clear, expressive",
    ),

    # Marathi (with culturally appropriate names)
    "narrator_marathi_female": VoicePreset(
        id="narrator_marathi_female",
        label="Meera Joshi",
        description="Warm, traditional Marathi voice. Perfect for Marathi content.",
        voice_name="Kore",
        default_language_code="mr-IN",
        gender="female",
        style="warm, traditional",
    ),
    "narrator_marathi_male": VoicePreset(
        id="narrator_marathi_male",
        label="Vikram Deshmukh",
        description="Authentic Marathi voice for regional content.",
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
        audio_format: str = "mp3",
    ) -> bytes:
        """
        Synthesize speech from text using Gemini TTS.

        Args:
            text: Text to synthesize
            preset_id: Voice preset ID
            language_code: Override language code (optional)
            emotion_style_prompt: Style/emotion instructions (e.g., "soft, romantic, intimate")
            audio_format: Output audio format (mp3, wav, flac, m4b). Default: mp3

        Returns:
            Audio bytes in requested format (MP3 by default)

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

        # Retry configuration for rate limits
        max_retries = 5
        base_delay = 2.0  # Start with 2 seconds

        for attempt in range(max_retries):
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
                # Gemini returns raw PCM audio (linear16, 24kHz, mono)
                # IMPORTANT: The SDK may return base64-encoded data as string OR bytes
                # See: https://github.com/googleapis/python-genai/issues/837
                import base64

                if response.candidates and response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            raw_audio_data = part.inline_data.data

                            # Debug: Log data type and first bytes
                            data_type = type(raw_audio_data).__name__
                            logger.info(f"[TTS] Raw audio data type: {data_type}")
                            logger.info(f"[TTS] Raw audio length: {len(raw_audio_data)}")

                            # Handle base64 encoding - SDK behavior varies!
                            # Sometimes returns str, sometimes bytes that are actually base64 text
                            if isinstance(raw_audio_data, str):
                                # Data is base64 encoded string - decode it
                                logger.info("[TTS] Data is base64 string, decoding...")
                                raw_audio_data = base64.b64decode(raw_audio_data)
                                logger.info(f"[TTS] Decoded to {len(raw_audio_data)} bytes")
                            elif isinstance(raw_audio_data, bytes):
                                # Check if bytes look like base64 text (common issue!)
                                # Base64 typically starts with letters/numbers, not binary
                                first_bytes = raw_audio_data[:20]
                                try:
                                    # If it decodes as ASCII and looks like base64, decode it
                                    first_str = first_bytes.decode('ascii')
                                    if first_str.replace('+', '').replace('/', '').replace('=', '').isalnum():
                                        logger.info("[TTS] Bytes appear to be base64 text, decoding...")
                                        raw_audio_data = base64.b64decode(raw_audio_data)
                                        logger.info(f"[TTS] Decoded base64 bytes to {len(raw_audio_data)} bytes")
                                except (UnicodeDecodeError, ValueError):
                                    # Not base64 text, use as-is
                                    pass

                            # Log first 20 bytes for debugging
                            if len(raw_audio_data) > 20:
                                header_hex = raw_audio_data[:20].hex()
                                logger.info(f"[TTS] Audio header (hex): {header_hex}")

                            # Convert to requested format (default: MP3 for browser compatibility)
                            converted_audio = self._convert_to_mp3(raw_audio_data, audio_format)
                            logger.info(f"[TTS] Converted to {audio_format.upper()}: {len(converted_audio)} bytes")
                            return converted_audio

                raise TTSSynthesisError("No audio data in response")

            except Exception as e:
                error_str = str(e)
                # Check if it's a rate limit error (429)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries - 1:
                        # Extract retry delay from error if available
                        import re
                        delay_match = re.search(r'retry in (\d+\.?\d*)s', error_str.lower())
                        if delay_match:
                            delay = float(delay_match.group(1)) + 1.0  # Add 1s buffer
                        else:
                            delay = base_delay * (2 ** attempt)  # Exponential backoff

                        logger.warning(f"[TTS] Rate limited (attempt {attempt + 1}/{max_retries}), waiting {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        continue
                # Not a rate limit error, or we've exhausted retries
                error_msg = f"TTS synthesis failed: {str(e)}"
                logger.error(error_msg)
                raise TTSSynthesisError(error_msg) from e

        # Should never reach here, but just in case
        raise TTSSynthesisError("TTS synthesis failed after all retries")

    def _convert_to_mp3(self, raw_audio: bytes, output_format: str = "mp3") -> bytes:
        """
        Convert raw audio to the desired output format.

        Gemini TTS API returns audio data that may be in various formats.
        We auto-detect the format and convert to the requested output format.

        Supported output formats: mp3, wav, flac, m4a/m4b

        Args:
            raw_audio: Raw audio bytes from Gemini API
            output_format: Target format (default: mp3)

        Returns:
            Audio bytes in requested format
        """
        import io

        # Normalize format name
        output_format = output_format.lower()
        if output_format == "m4b":
            output_format = "mp4"  # m4b is just mp4 container with audiobook flag

        try:
            from pydub import AudioSegment

            audio_stream = io.BytesIO(raw_audio)
            audio = None

            # Log the first few bytes to help debug format issues
            header = raw_audio[:20] if len(raw_audio) > 20 else raw_audio
            logger.info(f"Audio header bytes: {header.hex()}")

            # Try to auto-detect format using pydub's from_file with format hints
            # The order matters - try most common formats first

            # Check for WAV header (RIFF....WAVE)
            if raw_audio[:4] == b'RIFF' and raw_audio[8:12] == b'WAVE':
                logger.info("Detected WAV format")
                audio_stream.seek(0)
                audio = AudioSegment.from_wav(audio_stream)

            # Check for MP3 header (ID3 or 0xFF 0xFB/0xFF 0xFA sync bytes)
            elif raw_audio[:3] == b'ID3' or (raw_audio[0] == 0xFF and raw_audio[1] in (0xFB, 0xFA, 0xF3, 0xF2)):
                logger.info("Detected MP3 format")
                audio_stream.seek(0)
                audio = AudioSegment.from_mp3(audio_stream)

            # Check for OGG header (OggS)
            elif raw_audio[:4] == b'OggS':
                logger.info("Detected OGG format")
                audio_stream.seek(0)
                audio = AudioSegment.from_ogg(audio_stream)

            # Check for FLAC header (fLaC)
            elif raw_audio[:4] == b'fLaC':
                logger.info("Detected FLAC format")
                audio_stream.seek(0)
                audio = AudioSegment.from_file(audio_stream, format="flac")

            else:
                # Gemini TTS typically returns raw PCM (linear16 at 24kHz mono)
                # Try raw PCM FIRST before auto-detection, since Gemini rarely returns
                # any format with headers
                logger.info("No recognized format header, trying as raw PCM first (Gemini default)")
                audio_stream.seek(0)
                try:
                    audio = AudioSegment.from_raw(
                        audio_stream,
                        sample_width=2,  # 16-bit (linear16)
                        frame_rate=24000,  # Gemini TTS outputs at 24kHz
                        channels=1,  # Mono
                    )
                    logger.info(f"Loaded as raw PCM: duration={len(audio)}ms")
                except Exception as e1:
                    logger.warning(f"Raw PCM failed: {e1}, trying auto-detection...")
                    # Fallback to auto-detection via ffmpeg
                    audio_stream.seek(0)
                    try:
                        audio = AudioSegment.from_file(audio_stream)
                        logger.info("Auto-detection succeeded")
                    except Exception as e2:
                        logger.error(f"All format detection failed: raw PCM={e1}, auto={e2}")
                        raise ValueError(f"Could not load audio: {e2}")

            if audio is None:
                raise ValueError("Could not load audio data")

            # Export to requested format
            output_buffer = io.BytesIO()

            if output_format == "mp3":
                audio.export(output_buffer, format="mp3", bitrate="192k")
            elif output_format == "wav":
                audio.export(output_buffer, format="wav")
            elif output_format == "flac":
                audio.export(output_buffer, format="flac")
            elif output_format in ("m4a", "mp4", "m4b"):
                audio.export(output_buffer, format="mp4", codec="aac", bitrate="192k")
            else:
                # Default to MP3 for unknown formats
                logger.warning(f"Unknown output format '{output_format}', defaulting to MP3")
                audio.export(output_buffer, format="mp3", bitrate="192k")

            output_buffer.seek(0)
            result = output_buffer.read()
            logger.info(f"Converted {len(raw_audio)} bytes -> {len(result)} bytes ({output_format})")
            return result

        except ImportError:
            logger.warning("pydub not available, returning raw audio (may not play in browsers)")
            return raw_audio
        except Exception as e:
            logger.error(f"Audio conversion to {output_format} failed: {e}, returning raw audio")
            return raw_audio

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
    audio_format: str = "mp3",
) -> bytes:
    """
    Synthesize a text segment with proper multilingual support.

    IMPORTANT: This implements a 3-step pipeline for multilingual TTS:
    1. Detect input language (if auto or unknown)
    2. Translate text if input != output language (with emotion preservation)
    3. Send TRANSLATED text to TTS with correct output language code

    DO NOT send English text to a Marathi/Hindi/etc voice - this produces static!

    Args:
        text: Text to synthesize
        preset_id: Voice preset ID
        input_language_code: Language of the input text (None or "auto" to detect)
        output_language_code: Desired output language (None to use input language)
        emotion_style_prompt: Style/emotion instructions (e.g., "soft, romantic, intimate")
        audio_format: Output audio format (mp3, wav, flac, m4b). Default: mp3

    Returns:
        Audio bytes

    Raises:
        TTSSynthesisError: If synthesis fails
    """
    from .translator import translate_text, detect_language

    tts = get_tts()

    # ========================================================================
    # STEP 1: Detect input language
    # ========================================================================
    detected_input_language = input_language_code

    if input_language_code == "auto" or not input_language_code:
        logger.info("[TTS] Step 1: Detecting input language...")
        detected_input_language = await detect_language(text)
        logger.info(f"[TTS] Detected input language: {detected_input_language}")
    else:
        logger.info(f"[TTS] Input language specified: {input_language_code}")

    # ========================================================================
    # STEP 2: Translate if needed (input language != output language)
    # ========================================================================
    final_text = text

    # Normalize language codes for comparison
    # IMPORTANT: Compare against output_language_code directly, NOT the fallback value!
    input_base = detected_input_language.split("-")[0].lower() if detected_input_language else "en"
    output_base = output_language_code.split("-")[0].lower() if output_language_code else None

    # Translation is needed if:
    # 1. output_language_code is explicitly provided AND
    # 2. It's different from the input language
    needs_translation = output_base is not None and input_base != output_base

    # Determine final language for TTS (after potential translation)
    final_language = output_language_code or detected_input_language or "en-US"

    # Log the decision logic for debugging
    logger.info(f"[TTS] Step 2: Translation check:")
    logger.info(f"[TTS]   - input_language_code param: {input_language_code}")
    logger.info(f"[TTS]   - output_language_code param: {output_language_code}")
    logger.info(f"[TTS]   - detected_input_language: {detected_input_language}")
    logger.info(f"[TTS]   - input_base: {input_base}, output_base: {output_base}")
    logger.info(f"[TTS]   - needs_translation: {needs_translation}")
    logger.info(f"[TTS]   - final_language (for TTS): {final_language}")

    if needs_translation:
        logger.info(f"[TTS] Step 2: ✅ Translation WILL happen ({input_base} -> {output_base})")
        logger.info(f"[TTS] Translating with emotion preservation: {emotion_style_prompt or 'natural'}")

        # Translate with emotion/style preservation
        final_text = await translate_text(
            text=text,
            source_lang=detected_input_language or "en-US",
            target_lang=output_language_code,
            preserve_formatting=True,
            emotion_style=emotion_style_prompt,
        )

        # Log translation preview
        preview = final_text[:300] + "..." if len(final_text) > 300 else final_text
        logger.info(f"[TTS] Translation preview: {preview}")

        # The TTS language code MUST be the output language
        final_language = output_language_code
    else:
        # No translation - either same language or no output_language_code specified
        if output_language_code:
            logger.info(f"[TTS] Step 2: No translation needed (same language: {input_base})")
        else:
            logger.info(f"[TTS] Step 2: No translation requested (output_language_code not specified)")

    # ========================================================================
    # STEP 3: Synthesize with TTS
    # ========================================================================
    logger.info(f"[TTS] Step 3: Synthesizing audio")
    logger.info(f"[TTS]   - Preset: {preset_id}")
    logger.info(f"[TTS]   - Language code: {final_language}")
    logger.info(f"[TTS]   - Style: {emotion_style_prompt or 'default'}")
    logger.info(f"[TTS]   - Text length: {len(final_text)} chars")

    # Log final text preview (what will be sent to TTS)
    final_preview = final_text[:200] + "..." if len(final_text) > 200 else final_text
    logger.info(f"[TTS]   - Final TTS text preview: {final_preview}")

    # Synthesize - the text should now be in the OUTPUT language
    return await tts.synthesize(
        text=final_text,
        preset_id=preset_id,
        language_code=final_language,
        emotion_style_prompt=emotion_style_prompt,
        audio_format=audio_format,
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
            "sample_text": preset.sample_text,
        }
        for preset in VOICE_PRESETS.values()
    ]


def get_supported_languages() -> Dict[str, str]:
    """Get supported languages with display names"""
    return SUPPORTED_LANGUAGES.copy()
