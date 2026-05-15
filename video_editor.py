import os
import random
import numpy as np
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import ImageClip, ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx.all import resize, speedx
from moviepy.audio.io.AudioFileClip import AudioFileClip
from PIL import Image as PILImage
from config import VideoConfig

def _fit_to_aspect(clip, target_w: int, target_h: int):
    """Center-crop to fit target aspect ratio without distortion."""
    clip_w, clip_h = clip.size
    target_ratio = target_w / target_h
    clip_ratio = clip_w / clip_h
    
    if clip_ratio > target_ratio:
        new_h = target_h
        new_w = int(new_h * clip_ratio)
        clip = clip.resize(newsize=(new_w, new_h))
        x1 = (new_w - target_w) // 2
        clip = clip.crop(x1=x1, y1=0, x2=x1+target_w, y2=target_h)
    else:
        new_w = target_w
        new_h = int(new_w / clip_ratio)
        clip = clip.resize(newsize=(new_w, new_h))
        y1 = (new_h - target_h) // 2
        clip = clip.crop(x1=0, y1=y1, x2=new_w, y2=y1+target_h)
    
    return clip

def _ken_burns(clip, duration: float, size=(1920,1080)):
    """Smooth Ken Burns zoom/pan effect."""
    if duration <= 0:
        return clip.set_duration(0)
    
    start_scale = random.uniform(1.0, 1.15)
    end_scale = start_scale + random.uniform(-0.03, 0.1)
    end_scale = max(0.95, min(end_scale, 1.4))
    
    max_dx = (size[0] * (start_scale - 1)) / 2 if start_scale > 1 else 0
    max_dy = (size[1] * (start_scale - 1)) / 2 if start_scale > 1 else 0
    
    start_x = random.uniform(-max_dx, max_dx) if max_dx > 0 else 0
    start_y = random.uniform(-max_dy, max_dy) if max_dy > 0 else 0
    end_x = random.uniform(-max_dx, max_dx) if max_dx > 0 else 0
    end_y = random.uniform(-max_dy, max_dy) if max_dy > 0 else 0
    
    def scale_func(t):
        return start_scale + (end_scale - start_scale) * t / duration
    
    def pos_func(t):
        x = start_x + (end_x - start_x) * t / duration
        y = start_y + (end_y - start_y) * t / duration
        return (x, y)
    
    resized = clip.resize(scale_func)
    canvas = ColorClip(size=size, color=(0,0,0), duration=duration)
    result = CompositeVideoClip([canvas, resized.set_position(pos_func)], size=size)
    return result.set_duration(duration)

def _adjust_duration(clip, target_dur: float):
    """Trim or loop to match exact duration."""
    if clip.duration >= target_dur:
        return clip.subclip(0, target_dur)
    factor = clip.duration / target_dur
    if factor >= 0.3:
        return clip.fx(speedx, factor)
    loops = int(np.ceil(target_dur / clip.duration))
    return concatenate_videoclips([clip] * loops).subclip(0, target_dur)

def build_video(segments: list, media_map: list, audio_path: str, video_config: VideoConfig) -> str:
    tw, th = video_config.width, video_config.height
    scene_clips = []
    
    for i, seg in enumerate(segments):
        seg_dur = seg["duration"]
        media_list = media_map[i] if i < len(media_map) else media_map[-1]
        media_path = media_list[0] if media_list else None
        
        if not media_path:
            clip = ColorClip(size=(tw, th), color=(10,10,20), duration=seg_dur)
        else:
            is_vid = media_path.lower().endswith(('.mp4','.webm','.mov'))
            try:
                if is_vid:
                    raw = VideoFileClip(media_path)
                    raw = _fit_to_aspect(raw, tw, th)
                    raw = _adjust_duration(raw, seg_dur)
                else:
                    pil_img = PILImage.open(media_path).convert("RGB")
                    raw = ImageClip(np.array(pil_img)).resize(newsize=(tw, th)).set_duration(seg_dur)
            except Exception as e:
                print(f"⚠️  Media error: {e}")
                raw = ColorClip(size=(tw, th), color=(0,0,0), duration=seg_dur)
            
            clip = _ken_burns(raw, seg_dur, (tw, th))
        
        if i > 0:
            clip = clip.crossfadein(video_config.crossfade_dur)
        if i < len(segments) - 1:
            clip = clip.crossfadeout(video_config.crossfade_dur)
        
        scene_clips.append(clip)
    
    video = concatenate_videoclips(scene_clips, method="compose")
    audio = AudioFileClip(audio_path)
    final = video.set_audio(audio).set_duration(audio.duration)
    
    output_path = os.path.join(video_config.output_dir, f"vortex_output.mp4")
    final.write_videofile(
        output_path, fps=video_config.fps,
        codec=video_config.video_codec,
        audio_codec=video_config.audio_codec,
        preset=video_config.preset,
        threads=2, logger=None
    )
    
    for c in scene_clips:
        c.close()
    video.close()
    final.close()
    audio.close()
    
    return output_path