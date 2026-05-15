import os
import requests
import asyncio
from config import (
    ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL,
    EDGE_TTS_VOICE, VideoConfig
)

def create_voiceover(script: str, output_path: str, video_config: VideoConfig):
    """
    Generate MP3 voiceover.
    Priority: ElevenLabs → Edge-TTS fallback
    """
    # Try ElevenLabs first
    if ELEVENLABS_API_KEY:
        try:
            _elevenlabs_tts(script, output_path)
            print("✅ Voiceover created with ElevenLabs (Premium)")
            return
        except Exception as e:
            print(f"⚠️  ElevenLabs failed: {e}")

    # Fallback to Edge-TTS
    try:
        asyncio.run(_edge_tts(script, output_path))
        print("✅ Voiceover created with Edge-TTS (Free)")
    except Exception as e:
        raise RuntimeError(f"Voiceover generation failed: {e}")

def _elevenlabs_tts(text: str, output_path: str):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": text,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)

async def _edge_tts(text: str, output_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)
    await communicate.save(output_path)