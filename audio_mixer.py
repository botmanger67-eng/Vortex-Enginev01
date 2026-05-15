import os
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip

DEFAULT_BGM = os.path.join(os.path.dirname(__file__), "storage", "bgm.mp3")

def mix_audio(voice_path: str, bgm_path: str = None, output_path: str = None, duration: float = None) -> str:
    voice = AudioFileClip(voice_path)
    if duration is None:
        duration = voice.duration
    
    out = output_path or voice_path.replace(".mp3", "_mixed.mp3")
    
    # Check for BGM
    bgm = None
    if bgm_path and os.path.exists(bgm_path):
        bgm = AudioFileClip(bgm_path)
    elif os.path.exists(DEFAULT_BGM):
        bgm = AudioFileClip(DEFAULT_BGM)
    
    if bgm is None:
        voice.write_audiofile(out, codec='libmp3lame', verbose=False, logger=None)
        voice.close()
        return out
    
    # Loop BGM if needed
    if bgm.duration < duration:
        loops = int(duration / bgm.duration) + 1
        bgm = bgm.loop(n=loops)
    bgm = bgm.subclip(0, duration)
    
    # Duck volume & fade
    bgm = bgm.volumex(0.15)
    if duration > 2:
        bgm = bgm.audio_fadeout(2)
    
    mixed = CompositeAudioClip([voice, bgm])
    mixed.write_audiofile(out, codec='libmp3lame', verbose=False, logger=None)
    
    voice.close()
    bgm.close()
    mixed.close()
    
    return out