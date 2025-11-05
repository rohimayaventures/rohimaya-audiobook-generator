"""
ElevenLabs TTS Provider
"""
from src.tts_provider import TTSProvider
import requests
from typing import Dict

class ElevenLabsProvider(TTSProvider):
    VOICES = {
        "rachel": "Female, calm narrator",
        "adam": "Male, deep",
        "domi": "Female, strong",
        "elli": "Female, emotional",
        "josh": "Male, warm",
        "arnold": "Male, crisp"
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def synthesize(self, text: str, voice_id: str = "rachel") -> bytes:
        # Use default Rachel voice ID if not provided
        voice_map = {
            "rachel": "21m00Tcm4TlvDq8ikWAM",
            "adam": "pNInz6obpgDQGcFmaJgB",
            "domi": "AZnzlk1XvdvUeBnXmlld",
            "elli": "MF3mGyEYCl7XYWbV9V6O",
            "josh": "TxGEqnHWrfWFTfGW9XjX",
            "arnold": "VR6AewLTigWG4xSOukaG"
        }
        
        actual_voice_id = voice_map.get(voice_id.lower(), voice_map["rachel"])
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{actual_voice_id}"
        
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise RuntimeError(f"ElevenLabs API error {response.status_code}: {response.text}")
        
        return response.content
    
    def get_available_voices(self) -> Dict[str, str]:
        return self.VOICES
    
    def estimate_cost(self, text: str) -> float:
        # ElevenLabs pricing varies by plan, estimate for standard
        characters = len(text)
        return (characters / 1000) * 0.30
