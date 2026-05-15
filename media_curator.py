import os
import re
import random
import requests
import time
from config import PIXABAY_API_KEY, VideoConfig

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; VortexEngine/2.0)"
}

def _sanitize_keyword(raw: str) -> str:
    if not raw or not raw.strip():
        return "cinematic"
    cleaned = re.sub(r'[^\w\s]', '', raw.strip())
    parts = cleaned.split()
    if not parts:
        return "cinematic"
    last = parts[-1].lower()
    return last if len(last) >= 3 else parts[0].lower()

def _search_pixabay(keyword: str, count: int = 5) -> list:
    if not PIXABAY_API_KEY:
        return []
    
    items = []
    clean_key = PIXABAY_API_KEY.strip()
    
    # Search videos
    try:
        url = f"https://pixabay.com/api/videos/?key={clean_key}&q={keyword}&per_page={min(count, 10)}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        for hit in resp.json().get("hits", []):
            videos = hit["videos"]
            for qual in ["large", "medium", "small"]:
                if qual in videos:
                    items.append((videos[qual]["url"], "video"))
                    break
    except Exception as e:
        print(f"   ⚠️  Pixabay video search failed: {e}")
    
    # Fill with images
    needed = count - len(items)
    if needed > 0:
        try:
            url = f"https://pixabay.com/api/?key={clean_key}&q={keyword}&image_type=photo&per_page={needed}"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            for hit in resp.json().get("hits", []):
                items.append((hit["webformatURL"], "image"))
        except Exception as e:
            print(f"   ⚠️  Pixabay image search failed: {e}")
    
    return items[:count]

def _download_media(url: str, media_type: str, job_id: str, idx: int, temp_dir: str) -> str:
    ext = ".mp4" if media_type == "video" else ".jpg"
    path = os.path.join(temp_dir, f"media_{job_id}_{idx}{ext}")
    
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"   ⏳ Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            with open(path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            return path
        except Exception as e:
            if attempt == 2:
                print(f"   ❌ Download failed: {e}")
                return os.path.join(temp_dir, f"media_{job_id}_{idx}_placeholder.jpg")
            time.sleep(1)
    
    return os.path.join(temp_dir, f"media_{job_id}_{idx}_placeholder.jpg")

def _get_local_fallback(video_config: VideoConfig) -> str:
    folder = video_config.fallback_dir
    if not os.path.isdir(folder):
        return None
    videos = [f for f in os.listdir(folder) if f.lower().endswith(('.mp4', '.webm', '.mov'))]
    return os.path.join(folder, random.choice(videos)) if videos else None

def curate_media(script: str, video_config: VideoConfig, job_id: str) -> list:
    # Split into paragraphs
    paragraphs = [p.strip() for p in script.split('. ') if p.strip()]
    if not paragraphs:
        paragraphs = [script]
    
    media_map = []
    used_urls = set()
    clips_needed = 3 if video_config.video_type == "shorts" else 5
    
    for para_idx, para in enumerate(paragraphs):
        keyword = _sanitize_keyword(para)
        print(f"   🔍 Paragraph {para_idx+1}: keyword='{keyword}'")
        
        candidates = _search_pixabay(keyword, clips_needed * 2)
        para_media = []
        
        for url, mtype in candidates:
            if url in used_urls:
                continue
            used_urls.add(url)
            path = _download_media(url, mtype, job_id, f"{para_idx}_{len(para_media)}", video_config.temp_dir)
            if path and not path.endswith("_placeholder.jpg"):
                para_media.append(path)
            if len(para_media) >= clips_needed:
                break
        
        # Fill with local fallback
        while len(para_media) < clips_needed:
            local = _get_local_fallback(video_config)
            if local and local not in para_media:
                para_media.append(local)
            else:
                break
        
        # Ensure at least 1 clip
        if not para_media:
            local = _get_local_fallback(video_config)
            para_media.append(local if local else os.path.join(video_config.temp_dir, f"black_{job_id}.mp4"))
        
        media_map.append(para_media)
        time.sleep(0.3)  # Rate limit protection
    
    return media_map