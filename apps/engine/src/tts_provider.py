"""
TTS Provider Abstraction Layer
Multi-provider TTS with automatic fallback

⚠️ NOTE: This module is part of the LEGACY TTS system.
   The primary TTS for AuthorFlow is now Gemini TTS at: apps/engine/tts/gemini_tts.py

   The new Gemini TTS module:
   - Uses GOOGLE_GENAI_API_KEY (not service account)
   - Supports 21+ voice presets with emotion/style control
   - Integrates translation for multilingual audiobooks
   - Handles audio format conversion automatically

   This abstraction layer is kept for fallback scenarios only.

Legacy supported providers (in priority order):
1. Google Cloud TTS (deprecated - use Gemini instead)
2. OpenAI TTS (fallback when Gemini unavailable)
3. ElevenLabs (premium voices)
4. Inworld (experimental)
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import os
import logging

logger = logging.getLogger(__name__)


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    def synthesize(self, text: str, voice_id: str) -> bytes:
        """Synthesize speech from text."""
        pass

    @abstractmethod
    def get_available_voices(self) -> Dict[str, str]:
        """Get available voices with descriptions."""
        pass

    @abstractmethod
    def estimate_cost(self, text: str) -> float:
        """Estimate cost for synthesis."""
        pass


class TTSManager:
    """
    Multi-provider TTS manager with automatic fallback.

    Priority order:
    1. Google Cloud TTS (if configured) - Best for long books
    2. OpenAI TTS (if configured) - Good default
    3. ElevenLabs (if configured) - Premium voices
    4. Inworld (if configured) - Experimental
    """

    def __init__(self, config: dict, primary_provider: Optional[str] = None):
        """
        Initialize TTS manager.

        Args:
            config: Dictionary with API keys
            primary_provider: Force a specific provider ('google', 'openai', 'elevenlabs')
        """
        self.providers = []
        self.provider_names = []
        self.config = config
        self.primary_provider = primary_provider

        # Initialize providers in priority order
        # Google Cloud TTS first (best for long books, multilingual)
        if config.get('google_api_key') or config.get('google_credentials_json') or os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            try:
                from .tts_google import GoogleCloudTTSProvider
                provider = GoogleCloudTTSProvider(
                    api_key=config.get('google_api_key'),
                    credentials_json=config.get('google_credentials_json'),
                )
                self.providers.append(provider)
                self.provider_names.append('google')
                logger.info("Google Cloud TTS provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google TTS: {e}")

        # OpenAI TTS (good default)
        if config.get('openai_api_key'):
            try:
                from .tts_openai import OpenAIProvider
                self.providers.append(OpenAIProvider(config['openai_api_key']))
                self.provider_names.append('openai')
                logger.info("OpenAI TTS provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI TTS: {e}")

        # ElevenLabs (premium voices)
        if config.get('elevenlabs_api_key'):
            try:
                from .tts_elevenlabs import ElevenLabsProvider
                self.providers.append(ElevenLabsProvider(config['elevenlabs_api_key']))
                self.provider_names.append('elevenlabs')
                logger.info("ElevenLabs TTS provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize ElevenLabs TTS: {e}")

        # Inworld (experimental)
        if config.get('inworld_api_key'):
            try:
                from .tts_inworld import InworldProvider
                self.providers.append(InworldProvider(config['inworld_api_key']))
                self.provider_names.append('inworld')
                logger.info("Inworld TTS provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Inworld TTS: {e}")

        if not self.providers:
            raise ValueError("No TTS providers configured. Set at least one of: GOOGLE_GENAI_API_KEY, OPENAI_API_KEY, ELEVENLABS_API_KEY")

        logger.info(f"TTS Manager initialized with {len(self.providers)} providers: {self.provider_names}")

    def get_provider(self, name: str) -> Optional[TTSProvider]:
        """Get a specific provider by name."""
        try:
            idx = self.provider_names.index(name)
            return self.providers[idx]
        except ValueError:
            return None

    def synthesize_with_fallback(self, text: str, voice_id: str) -> bytes:
        """
        Synthesize with automatic fallback on failure.

        Args:
            text: Text to synthesize
            voice_id: Voice ID

        Returns:
            Audio bytes
        """
        errors = []

        # If primary provider is set, try it first
        if self.primary_provider:
            provider = self.get_provider(self.primary_provider)
            if provider:
                try:
                    return provider.synthesize(text, voice_id)
                except Exception as e:
                    errors.append(f"{self.primary_provider}: {e}")
                    logger.warning(f"Primary provider {self.primary_provider} failed: {e}")

        # Try all providers in order
        for i, provider in enumerate(self.providers):
            provider_name = self.provider_names[i]

            # Skip if already tried as primary
            if provider_name == self.primary_provider:
                continue

            try:
                return provider.synthesize(text, voice_id)
            except Exception as e:
                errors.append(f"{provider_name}: {e}")
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue

        raise Exception(f"All TTS providers failed: {'; '.join(errors)}")
