"""
Inworld TTS Provider
"""
from src.tts_provider import TTSProvider
import requests
import base64
from typing import Dict

class InworldProvider(TTSProvider):
    VOICES = {
        "deborah": "Female, warm narrator",
        "michael": "Male, professional",
        "emma": "Female, young adult"
    }
    
    def __init__(self, api_key: str, workspace_id: str = None):
        self.api_key = api_key
        self.workspace_id = workspace_id
    
    def synthesize(self, text: str, voice_id: str = "deborah") -> bytes:
        url = "https://api.inworld.ai/tts/v1/voice"
        
        payload = {
            "text": text,
            "voiceId": voice_id.capitalize(),
            "modelId": "inworld-tts-1-max",
            "encoding": "mp3",
        }
        
        headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise RuntimeError(f"Inworld API error {response.status_code}: {response.text}")
        
        data = response.json()
        audio_b64 = data.get("audioContent") or data.get("audio", {}).get("data")
        
        if not audio_b64:
            raise ValueError(f"No audio in response: {data}")
        
        return base64.b64decode(audio_b64)
    
    def get_available_voices(self) -> Dict[str, str]:
        return self.VOICES
    
    def estimate_cost(self, text: str) -> float:
        # Inworld pricing: ~$0.15 per 1K characters
        return (len(text) / 1000) * 0.15
