"""
OpenAI TTS Provider

⚠️ NOTE: This module is part of the LEGACY TTS system.
   The primary TTS for AuthorFlow is now Gemini TTS at: apps/engine/tts/gemini_tts.py

   OpenAI TTS is still used as a fallback when Gemini is unavailable.
   For new development, prefer the new Gemini TTS module.
"""

from src.tts_provider import TTSProvider
from openai import OpenAI
from typing import Dict

class OpenAIProvider(TTSProvider):
    VOICES = {
        "alloy": "Neutral, balanced",
        "echo": "Male, clear",
        "fable": "British, expressive",
        "onyx": "Deep male",
        "nova": "Female, warm",
        "shimmer": "Female, soft"
    }
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def synthesize(self, text: str, voice_id: str = "alloy") -> bytes:
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice_id,
            input=text
        )
        return response.content
    
    def get_available_voices(self) -> Dict[str, str]:
        return self.VOICES
    
    def estimate_cost(self, text: str) -> float:
        return (len(text) / 1000) * 0.015
