import sqlite3
import uuid
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "vortex.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            prompt TEXT NOT NULL,
            duration INTEGER NOT NULL,
            video_type TEXT NOT NULL DEFAULT 'shorts',
            status TEXT DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            script TEXT,
            video_path TEXT,
            error_msg TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database initialized")

def create_job(prompt: str, duration: int, video_type: str = "shorts") -> str:
    job_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO videos (id, prompt, duration, video_type) VALUES (?, ?, ?, ?)",
        (job_id, prompt, duration, video_type)
    )
    conn.commit()
    conn.close()
    return job_id

def update_job(job_id: str, **kwargs):
    if not kwargs:
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [job_id]
    c.execute(f"UPDATE videos SET {fields} WHERE id = ?", values)
    conn.commit()
    conn.close()

def get_job(job_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM videos WHERE id = ?", (job_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def list_videos() -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM videos ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_video(job_id: str) -> bool:
    job = get_job(job_id)
    if job and job.get("video_path") and os.path.exists(job["video_path"]):
        try:
            os.remove(job["video_path"])
        except:
            pass
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM videos WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    return True