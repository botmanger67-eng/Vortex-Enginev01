import requests
import re
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL, VideoConfig
)

def generate_script(prompt: str, video_config: VideoConfig) -> str:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("❌ DEEPSEEK_API_KEY not set in environment")

    if video_config.video_type == "shorts":
        system_prompt = f"""
You are a viral short-form video scriptwriter.
Write a powerful, high-energy, cinematic narration for exactly {video_config.duration} seconds.

CRITICAL RULES (MUST FOLLOW):
1. Write EXACTLY between {video_config.min_words} and {video_config.max_words} words. NO EXCEPTIONS.
2. ONE continuous flowing paragraph. NO line breaks, NO bullet points, NO section headers.
3. Use LONG, connected, fluid sentences — this will be spoken by AI voice.
4. NO visual directions, NO timestamps, NO markdown formatting.
5. Output ONLY the pure narration text. Nothing else before or after.
6. Make every word count. Punch hard. Zero filler.
"""
    else:
        system_prompt = f"""
You are a professional cinematic video scriptwriter.
Write an engaging, fluid narration for a {video_config.duration}-second video.

RULES:
1. ONE continuous flowing paragraph. NO line breaks.
2. LONG, connected sentences for natural TTS reading.
3. NO visual directions, NO timestamps, NO formatting.
4. Output ONLY the pure narration text.
"""

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 400 if video_config.video_type == "shorts" else 1500
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=45)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"DeepSeek API failed: {e}")

    # Clean response
    content = content.strip()
    content = re.sub(r'```[a-zA-Z]*\n?', '', content)
    content = content.replace('```', '')
    content = re.sub(r'^\[.*?\]\s*', '', content)
    content = content.strip('"\'')

    # Word count enforcement for shorts
    wc = len(content.split())
    if video_config.video_type == "shorts":
        if wc > video_config.max_words:
            print(f"⚠️  Script ({wc} words) exceeds limit. Truncating to {video_config.max_words}.")
            content = " ".join(content.split()[:video_config.max_words])
        elif wc < video_config.min_words:
            print(f"⚠️  Script ({wc} words) below minimum. Regenerating...")
            # Retry once with stronger prompt
            return generate_script(prompt + " (MUST be at least 35 words)", video_config)

    print(f"📝 Generated script ({len(content.split())} words): {content[:100]}...")
    return content