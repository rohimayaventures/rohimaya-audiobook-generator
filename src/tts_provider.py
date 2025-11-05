"""
TTS Provider Abstraction Layer
Multi-provider TTS with automatic fallback
"""

from abc import ABC, abstractmethod
from typing import Dict
import os

class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, voice_id: str) -> bytes:
        pass
    
    @abstractmethod
    def get_available_voices(self) -> Dict[str, str]:
        pass
    
    @abstractmethod
    def estimate_cost(self, text: str) -> float:
        pass

class TTSManager:
    def __init__(self, config: dict):
        self.providers = []
        self.config = config
        
        # Initialize providers
        if config.get('inworld_api_key'):
            from src.tts_inworld import InworldProvider
            self.providers.append(InworldProvider(config['inworld_api_key']))
        
        if config.get('openai_api_key'):
            from src.tts_openai import OpenAIProvider
            self.providers.append(OpenAIProvider(config['openai_api_key']))
        
        if not self.providers:
            raise ValueError("No TTS providers configured")
    
    def synthesize_with_fallback(self, text: str, voice_id: str) -> bytes:
        for provider in self.providers:
            try:
                return provider.synthesize(text, voice_id)
            except Exception as e:
                print(f"Provider failed: {e}")
                continue
        raise Exception("All TTS providers failed")
