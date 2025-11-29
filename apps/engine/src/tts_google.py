"""
Google Cloud Text-to-Speech Provider

⚠️ DEPRECATED: This module uses the OLD Google Cloud TTS API (Neural2/Studio voices).
   For new development, use the Gemini TTS module at: apps/engine/tts/gemini_tts.py

   The new Gemini TTS module:
   - Uses GOOGLE_GENAI_API_KEY (not service account)
   - Supports 30+ voices with emotion/style control
   - Integrates translation for multilingual audiobooks
   - Is actively maintained

   This file is kept for backwards compatibility only.

Supports both:
1. Google Cloud TTS (service account authentication)
2. Google AI Studio TTS via REST API (API key authentication)

Features:
- Higher character limits than OpenAI (5000 chars vs 4096)
- SSML support for prosody, pauses, emphasis
- 40+ languages with native speakers
- Multiple voice qualities (Standard, WaveNet, Neural2, Studio)
"""

import os
import json
import base64
import logging
from typing import Dict, List, Optional
from pathlib import Path

import requests

from src.tts_provider import TTSProvider

logger = logging.getLogger(__name__)

# Google Cloud TTS voices - popular selections
GOOGLE_VOICES = {
    # English (US) - Neural2 voices (highest quality)
    "en-US-Neural2-A": {"gender": "male", "language": "en-US", "description": "Male, professional"},
    "en-US-Neural2-C": {"gender": "female", "language": "en-US", "description": "Female, warm"},
    "en-US-Neural2-D": {"gender": "male", "language": "en-US", "description": "Male, authoritative"},
    "en-US-Neural2-E": {"gender": "female", "language": "en-US", "description": "Female, friendly"},
    "en-US-Neural2-F": {"gender": "female", "language": "en-US", "description": "Female, expressive"},
    "en-US-Neural2-G": {"gender": "female", "language": "en-US", "description": "Female, storyteller"},
    "en-US-Neural2-H": {"gender": "female", "language": "en-US", "description": "Female, calm"},
    "en-US-Neural2-I": {"gender": "male", "language": "en-US", "description": "Male, narrative"},
    "en-US-Neural2-J": {"gender": "male", "language": "en-US", "description": "Male, conversational"},

    # English (US) - Studio voices (premium)
    "en-US-Studio-M": {"gender": "male", "language": "en-US", "description": "Male, studio quality"},
    "en-US-Studio-O": {"gender": "female", "language": "en-US", "description": "Female, studio quality"},

    # English (UK)
    "en-GB-Neural2-A": {"gender": "female", "language": "en-GB", "description": "British female"},
    "en-GB-Neural2-B": {"gender": "male", "language": "en-GB", "description": "British male"},
    "en-GB-Neural2-C": {"gender": "female", "language": "en-GB", "description": "British female, warm"},
    "en-GB-Neural2-D": {"gender": "male", "language": "en-GB", "description": "British male, narrative"},

    # English (Australia)
    "en-AU-Neural2-A": {"gender": "female", "language": "en-AU", "description": "Australian female"},
    "en-AU-Neural2-B": {"gender": "male", "language": "en-AU", "description": "Australian male"},

    # Spanish
    "es-US-Neural2-A": {"gender": "female", "language": "es-US", "description": "Spanish (US) female"},
    "es-US-Neural2-B": {"gender": "male", "language": "es-US", "description": "Spanish (US) male"},
    "es-ES-Neural2-A": {"gender": "female", "language": "es-ES", "description": "Spanish (Spain) female"},
    "es-ES-Neural2-B": {"gender": "male", "language": "es-ES", "description": "Spanish (Spain) male"},

    # French
    "fr-FR-Neural2-A": {"gender": "female", "language": "fr-FR", "description": "French female"},
    "fr-FR-Neural2-B": {"gender": "male", "language": "fr-FR", "description": "French male"},

    # German
    "de-DE-Neural2-A": {"gender": "female", "language": "de-DE", "description": "German female"},
    "de-DE-Neural2-B": {"gender": "male", "language": "de-DE", "description": "German male"},

    # Italian
    "it-IT-Neural2-A": {"gender": "female", "language": "it-IT", "description": "Italian female"},
    "it-IT-Neural2-B": {"gender": "male", "language": "it-IT", "description": "Italian male"},

    # Portuguese
    "pt-BR-Neural2-A": {"gender": "female", "language": "pt-BR", "description": "Portuguese (Brazil) female"},
    "pt-BR-Neural2-B": {"gender": "male", "language": "pt-BR", "description": "Portuguese (Brazil) male"},

    # Japanese
    "ja-JP-Neural2-B": {"gender": "female", "language": "ja-JP", "description": "Japanese female"},
    "ja-JP-Neural2-C": {"gender": "male", "language": "ja-JP", "description": "Japanese male"},

    # Chinese (Mandarin)
    "cmn-CN-Neural2-A": {"gender": "female", "language": "cmn-CN", "description": "Mandarin female"},
    "cmn-CN-Neural2-B": {"gender": "male", "language": "cmn-CN", "description": "Mandarin male"},

    # Korean
    "ko-KR-Neural2-A": {"gender": "female", "language": "ko-KR", "description": "Korean female"},
    "ko-KR-Neural2-B": {"gender": "male", "language": "ko-KR", "description": "Korean male"},

    # Hindi
    "hi-IN-Neural2-A": {"gender": "female", "language": "hi-IN", "description": "Hindi female"},
    "hi-IN-Neural2-B": {"gender": "male", "language": "hi-IN", "description": "Hindi male"},
}

# Default voice mappings (similar to OpenAI voices)
VOICE_ALIASES = {
    "alloy": "en-US-Neural2-D",      # Neutral male
    "echo": "en-US-Neural2-J",       # Clear male
    "fable": "en-GB-Neural2-D",      # British narrative
    "onyx": "en-US-Neural2-A",       # Deep male
    "nova": "en-US-Neural2-C",       # Warm female
    "shimmer": "en-US-Neural2-F",    # Soft female
    "sage": "en-US-Neural2-G",       # Storyteller female
}


class GoogleCloudTTSProvider(TTSProvider):
    """
    Google Cloud Text-to-Speech provider.

    Supports authentication via:
    1. Service account JSON file (GOOGLE_APPLICATION_CREDENTIALS)
    2. Service account JSON content (GOOGLE_APPLICATION_CREDENTIALS_JSON)
    3. API key for REST API (GOOGLE_GENAI_API_KEY or GOOGLE_CLOUD_API_KEY)
    """

    # Google Cloud TTS limits
    MAX_CHARS_PER_REQUEST = 5000  # 5000 characters per request
    MAX_BYTES_PER_REQUEST = 5000  # 5000 bytes for Neural2/Studio voices

    def __init__(
        self,
        api_key: Optional[str] = None,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
        default_language: str = "en-US",
        audio_encoding: str = "MP3",
        speaking_rate: float = 1.0,
        pitch: float = 0.0,
    ):
        """
        Initialize Google Cloud TTS provider.

        Args:
            api_key: Google Cloud API key (for REST API)
            credentials_json: Service account JSON content
            credentials_path: Path to service account JSON file
            default_language: Default language code
            audio_encoding: Audio format (MP3, LINEAR16, OGG_OPUS)
            speaking_rate: Speaking rate (0.25 to 4.0, default 1.0)
            pitch: Pitch adjustment (-20.0 to 20.0, default 0.0)
        """
        self.api_key = api_key or os.getenv("GOOGLE_CLOUD_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
        self.credentials_json = credentials_json or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.default_language = default_language
        self.audio_encoding = audio_encoding
        self.speaking_rate = speaking_rate
        self.pitch = pitch

        # Try to initialize the client
        self.client = None
        self.use_rest_api = False

        self._initialize_client()

    def _initialize_client(self):
        """Initialize the TTS client based on available credentials."""
        # Try service account authentication first (preferred)
        try:
            from google.cloud import texttospeech

            if self.credentials_json:
                # Use JSON content directly
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(self.credentials_json)
                    temp_path = f.name
                self.client = texttospeech.TextToSpeechClient.from_service_account_json(temp_path)
                os.unlink(temp_path)
                logger.info("Google Cloud TTS initialized with service account JSON")
                return

            if self.credentials_path and os.path.exists(self.credentials_path):
                self.client = texttospeech.TextToSpeechClient.from_service_account_json(
                    self.credentials_path
                )
                logger.info(f"Google Cloud TTS initialized with service account file: {self.credentials_path}")
                return

            # Try default credentials (ADC)
            self.client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud TTS initialized with default credentials")
            return

        except ImportError:
            logger.warning("google-cloud-texttospeech not installed, falling back to REST API")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Cloud client: {e}, falling back to REST API")

        # Fallback to REST API with API key
        if self.api_key:
            self.use_rest_api = True
            logger.info("Google Cloud TTS initialized with REST API (API key)")
        else:
            raise ValueError(
                "No Google Cloud TTS credentials found. Set one of:\n"
                "- GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON)\n"
                "- GOOGLE_APPLICATION_CREDENTIALS_JSON (JSON content)\n"
                "- GOOGLE_CLOUD_API_KEY or GOOGLE_GENAI_API_KEY (for REST API)"
            )

    def _resolve_voice_id(self, voice_id: str) -> tuple[str, str]:
        """
        Resolve voice ID to actual Google voice name and language.

        Args:
            voice_id: Voice ID (can be alias like 'alloy' or full name like 'en-US-Neural2-A')

        Returns:
            Tuple of (voice_name, language_code)
        """
        # Check if it's an alias
        if voice_id in VOICE_ALIASES:
            voice_id = VOICE_ALIASES[voice_id]

        # Check if it's a known voice
        if voice_id in GOOGLE_VOICES:
            return voice_id, GOOGLE_VOICES[voice_id]["language"]

        # Assume it's a valid Google voice name, extract language
        # Format: {language}-{voice_type}-{letter}
        parts = voice_id.split("-")
        if len(parts) >= 2:
            language = f"{parts[0]}-{parts[1]}"
            return voice_id, language

        # Default to US English
        logger.warning(f"Unknown voice ID '{voice_id}', using default")
        return "en-US-Neural2-D", "en-US"

    def synthesize(self, text: str, voice_id: str = "en-US-Neural2-D") -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize (max 5000 characters)
            voice_id: Voice ID (alias or full Google voice name)

        Returns:
            Audio bytes (MP3 format by default)
        """
        if len(text) > self.MAX_CHARS_PER_REQUEST:
            raise ValueError(
                f"Text exceeds maximum length ({len(text)} > {self.MAX_CHARS_PER_REQUEST}). "
                "Split text into smaller chunks."
            )

        voice_name, language_code = self._resolve_voice_id(voice_id)

        if self.use_rest_api:
            return self._synthesize_rest_api(text, voice_name, language_code)
        else:
            return self._synthesize_client(text, voice_name, language_code)

    def _synthesize_client(self, text: str, voice_name: str, language_code: str) -> bytes:
        """Synthesize using google-cloud-texttospeech client."""
        from google.cloud import texttospeech

        # Build synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Build voice parameters
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
        )

        # Build audio config
        audio_encoding_map = {
            "MP3": texttospeech.AudioEncoding.MP3,
            "LINEAR16": texttospeech.AudioEncoding.LINEAR16,
            "OGG_OPUS": texttospeech.AudioEncoding.OGG_OPUS,
        }

        audio_config = texttospeech.AudioConfig(
            audio_encoding=audio_encoding_map.get(self.audio_encoding, texttospeech.AudioEncoding.MP3),
            speaking_rate=self.speaking_rate,
            pitch=self.pitch,
        )

        # Perform synthesis
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        return response.audio_content

    def _synthesize_rest_api(self, text: str, voice_name: str, language_code: str) -> bytes:
        """Synthesize using REST API with API key."""
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"

        # Build request body
        body = {
            "input": {"text": text},
            "voice": {
                "languageCode": language_code,
                "name": voice_name,
            },
            "audioConfig": {
                "audioEncoding": self.audio_encoding,
                "speakingRate": self.speaking_rate,
                "pitch": self.pitch,
            }
        }

        response = requests.post(url, json=body)

        if response.status_code != 200:
            error_msg = response.json().get("error", {}).get("message", response.text)
            raise Exception(f"Google TTS API error: {error_msg}")

        # Response contains base64-encoded audio
        audio_content = response.json().get("audioContent")
        if not audio_content:
            raise Exception("No audio content in response")

        return base64.b64decode(audio_content)

    def synthesize_ssml(self, ssml: str, voice_id: str = "en-US-Neural2-D") -> bytes:
        """
        Synthesize speech from SSML.

        SSML allows fine control over:
        - Pauses: <break time="500ms"/>
        - Emphasis: <emphasis level="strong">word</emphasis>
        - Prosody: <prosody rate="slow" pitch="+2st">text</prosody>
        - Say-as: <say-as interpret-as="characters">ABC</say-as>

        Args:
            ssml: SSML-formatted text
            voice_id: Voice ID

        Returns:
            Audio bytes
        """
        voice_name, language_code = self._resolve_voice_id(voice_id)

        if self.use_rest_api:
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"

            body = {
                "input": {"ssml": ssml},
                "voice": {
                    "languageCode": language_code,
                    "name": voice_name,
                },
                "audioConfig": {
                    "audioEncoding": self.audio_encoding,
                    "speakingRate": self.speaking_rate,
                    "pitch": self.pitch,
                }
            }

            response = requests.post(url, json=body)

            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", response.text)
                raise Exception(f"Google TTS API error: {error_msg}")

            audio_content = response.json().get("audioContent")
            return base64.b64decode(audio_content)
        else:
            from google.cloud import texttospeech

            synthesis_input = texttospeech.SynthesisInput(ssml=ssml)

            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=self.speaking_rate,
                pitch=self.pitch,
            )

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
            )

            return response.audio_content

    def get_available_voices(self) -> Dict[str, str]:
        """Get available voices with descriptions."""
        voices = {}
        for voice_id, info in GOOGLE_VOICES.items():
            voices[voice_id] = f"{info['description']} ({info['language']})"
        return voices

    def get_voices_by_language(self, language_code: str) -> Dict[str, str]:
        """Get voices filtered by language."""
        voices = {}
        for voice_id, info in GOOGLE_VOICES.items():
            if info["language"].startswith(language_code.split("-")[0]):
                voices[voice_id] = f"{info['description']} ({info['language']})"
        return voices

    def estimate_cost(self, text: str, voice_type: str = "Neural2") -> float:
        """
        Estimate cost for synthesis.

        Pricing (as of 2024):
        - Standard voices: $4 per 1M characters
        - WaveNet voices: $16 per 1M characters
        - Neural2 voices: $16 per 1M characters
        - Studio voices: $160 per 1M characters

        Args:
            text: Text to synthesize
            voice_type: Voice type (Standard, WaveNet, Neural2, Studio)

        Returns:
            Estimated cost in USD
        """
        char_count = len(text)

        rates = {
            "Standard": 4.0,
            "WaveNet": 16.0,
            "Neural2": 16.0,
            "Studio": 160.0,
        }

        rate = rates.get(voice_type, 16.0)  # Default to Neural2 rate
        return (char_count / 1_000_000) * rate


def generate_audio_google_tts(
    text: str,
    output_path: Path,
    voice_id: str = "en-US-Neural2-D",
    api_key: Optional[str] = None,
) -> bool:
    """
    Convenience function to generate audio file using Google Cloud TTS.

    Args:
        text: Text to synthesize
        output_path: Output file path
        voice_id: Voice ID
        api_key: Optional API key

    Returns:
        True if successful
    """
    try:
        provider = GoogleCloudTTSProvider(api_key=api_key)
        audio_bytes = provider.synthesize(text, voice_id)

        with open(output_path, "wb") as f:
            f.write(audio_bytes)

        return True
    except Exception as e:
        logger.error(f"Google TTS generation failed: {e}")
        return False
