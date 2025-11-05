"""
Inworld TTS Synthesizer
-----------------------
Converts text to high-quality speech using Inworld's latest TTS API.

Requires:
- `requests`
- `python-dotenv`
- `.env` file containing:
      INWORLD_API_KEY=<your base64 runtime key from Inworld console>
"""

import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()


def synthesize_with_inworld(text: str, part_num: int, voice_id: str = "Deborah"):
    """
    Convert text to speech using Inworld's REST TTS endpoint and save as MP3 in /output.
    """
    api_key = os.getenv("INWORLD_API_KEY")
    if not api_key:
        raise EnvironmentError("❌ Missing INWORLD_API_KEY in .env")

    # ✅ Latest Inworld TTS endpoint (2025)
    url = "https://api.inworld.ai/tts/v1/voice"

    payload = {
        "text": text,
        "voiceId": voice_id,
        "modelId": "inworld-tts-1-max",   # Recommended model for natural voice
        "encoding": "mp3",
    }

    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"❌ API error {response.status_code}: {response.text}")

    data = response.json()

    # Inworld returns Base64 audio data
    audio_b64 = data.get("audioContent") or data.get("audio", {}).get("data")
    if not audio_b64:
        raise ValueError(f"⚠️ Unexpected API response: {data}")

    audio_bytes = base64.b64decode(audio_b64)

    # ✅ Save directly to output directory
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"output_part_{part_num:03}.mp3")
    with open(output_path, "wb") as f:
        f.write(audio_bytes)

    print(f"🎧 Saved audio chunk {part_num} → {output_path}")
    return output_path


if __name__ == "__main__":
    try:
        synthesize_with_inworld("Testing one two three.", 1)
    except Exception as e:
        print(f"🚨 Error: {e}")