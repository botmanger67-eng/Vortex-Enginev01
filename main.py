import os
import threading
import traceback
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template
from config import VideoConfig
import database
from script_engine import generate_script
from voiceover_engine import create_voiceover
from media_curator import curate_media
from video_editor import build_video
from audio_mixer import mix_audio
from moviepy.audio.io.AudioFileClip import AudioFileClip

app = Flask(__name__)
database.init_db()

def run_pipeline(job_id: str, prompt: str, duration: int, video_type: str):
    def progress(pct, msg):
        database.update_job(job_id, progress=pct, status=msg)
    
    try:
        vcfg = VideoConfig(video_type, duration)
        
        # 1. Script
        progress(10, "Generating script...")
        script = generate_script(prompt, vcfg)
        database.update_job(job_id, script=script)
        
        # 2. Voiceover
        progress(25, "Creating voiceover...")
        voice_path = os.path.join(vcfg.temp_dir, f"voice_{job_id}.mp3")
        create_voiceover(script, voice_path, vcfg)
        
        # 3. Audio duration
        audio_clip = AudioFileClip(voice_path)
        total_dur = audio_clip.duration
        audio_clip.close()
        
        # 4. Segments
        num_seg = 5 if video_type == "shorts" else 10
        seg_dur = total_dur / num_seg
        segments = [{"duration": seg_dur} for _ in range(num_seg)]
        
        # 5. Media
        progress(40, "Curating media...")
        media_map = curate_media(script, vcfg, job_id)
        
        # 6. Video compose
        progress(60, "Assembling video...")
        video_path = build_video(segments, media_map, voice_path, vcfg)
        
        # 7. Audio mix & reattach
        progress(85, "Mixing audio...")
        mixed_audio = mix_audio(voice_path, output_path=os.path.join(vcfg.temp_dir, f"mixed_{job_id}.mp3"))
        
        from moviepy.video.io.VideoFileClip import VideoFileClip as VFC
        vid = VFC(video_path)
        aud = AudioFileClip(mixed_audio)
        final_vid = vid.set_audio(aud)
        
        final_path = os.path.join(vcfg.output_dir, f"final_{job_id}.mp4")
        final_vid.write_videofile(
            final_path, fps=vcfg.fps,
            codec=vcfg.video_codec,
            audio_codec=vcfg.audio_codec,
            preset=vcfg.preset, threads=2, logger=None
        )
        
        vid.close()
        aud.close()
        final_vid.close()
        os.remove(video_path)
        
        progress(100, "Completed")
        database.update_job(job_id, status="completed", progress=100, video_path=final_path)
        
    except Exception as e:
        traceback.print_exc()
        database.update_job(job_id, status="failed", error_msg=str(e))

# ==================== ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create', methods=['POST'])
def api_create():
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({"error": "Missing prompt"}), 400
    
    prompt = data['prompt']
    duration = int(data.get('duration', 15))
    video_type = data.get('video_type', 'shorts')
    
    if video_type not in ('shorts', 'long'):
        return jsonify({"error": "video_type must be shorts or long"}), 400
    
    job_id = database.create_job(prompt, duration, video_type)
    thread = threading.Thread(target=run_pipeline, args=(job_id, prompt, duration, video_type), daemon=True)
    thread.start()
    
    return jsonify({"job_id": job_id, "status": "processing"})

@app.route('/api/status/<job_id>')
def api_status(job_id):
    job = database.get_job(job_id)
    if not job:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "status": job['status'],
        "progress": job['progress'],
        "video_path": job.get('video_path')
    })

@app.route('/api/videos')
def api_videos():
    return jsonify(database.list_videos())

@app.route('/api/delete/<job_id>', methods=['DELETE'])
def api_delete(job_id):
    database.delete_video(job_id)
    return jsonify({"success": True})

@app.route('/api/download/<job_id>')
def api_download(job_id):
    job = database.get_job(job_id)
    if not job or not job.get('video_path') or not os.path.exists(job['video_path']):
        return "Not found", 404
    directory = os.path.dirname(job['video_path'])
    filename = os.path.basename(job['video_path'])
    return send_from_directory(directory, filename, as_attachment=True)

if __name__ == '__main__':
    print("🔮 Vortex Engine Pro — Starting on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)