import os
from dotenv import load_dotenv

load_dotenv()

# ==================== API Keys ====================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")

# ==================== Video Presets ====================
class VideoConfig:
    def __init__(self, video_type: str, duration: int):
        self.video_type = video_type
        self.duration = duration
        
        if video_type == "shorts":
            self.width = 1080
            self.height = 1920
            self.fps = 30
            self.max_words = 45
            self.min_words = 35
        else:
            self.width = 1920
            self.height = 1080
            self.fps = 30
            self.max_words = None
            self.min_words = None
        
        # Paths
        base = os.path.dirname(__file__)
        self.output_dir = os.path.join(base, "storage", "outputs")
        self.fallback_dir = os.path.join(base, "storage", "fallbacks")
        self.temp_dir = os.path.join(base, "temp")
        
        for d in [self.output_dir, self.fallback_dir, self.temp_dir]:
            os.makedirs(d, exist_ok=True)
        
        # Encoding
        self.video_codec = "libx264"
        self.audio_codec = "aac"
        self.preset = "medium"
        self.audio_bitrate = "192k"
        self.crossfade_dur = 0.5

# ==================== API Endpoints ====================
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
ELEVENLABS_MODEL = "eleven_monolingual_v1"

EDGE_TTS_VOICE = "en-US-AriaNeural"
PIXABAY_BASE_URL = "https://pixabay.com/api"