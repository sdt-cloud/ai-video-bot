import sqlite3
from datetime import datetime

DB_NAME = "aivid_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            category TEXT,
            tone TEXT,
            duration INTEGER,
            language TEXT,
            script_ai TEXT,
            voice_ai TEXT,
            image_ai TEXT,
            subtitle_style TEXT DEFAULT 'tiktok',
            status TEXT DEFAULT 'pending',
            progress INTEGER DEFAULT 0,
            video_mode TEXT DEFAULT 'slideshow',
            error_message TEXT,
            video_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Geçmiş veritabanına sütun ekleme (varsa hata verir, ignore edilir)
    try:
        cursor.execute("ALTER TABLE videos ADD COLUMN subtitle_style TEXT DEFAULT 'tiktok'")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE videos ADD COLUMN video_mode TEXT DEFAULT 'slideshow'")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

def add_video_task(topic, category, tone, duration, language, script_ai, voice_ai, image_ai, subtitle_style="tiktok", video_mode="slideshow"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO videos (topic, category, tone, duration, language, script_ai, voice_ai, image_ai, subtitle_style, video_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (topic, category, tone, duration, language, script_ai, voice_ai, image_ai, subtitle_style, video_mode))
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def update_status(task_id, status, progress=None, error_message=None, video_path=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "UPDATE videos SET status = ?, updated_at = CURRENT_TIMESTAMP"
    params = [status]
    
    if progress is not None:
        query += ", progress = ?"
        params.append(progress)
    if error_message is not None:
        query += ", error_message = ?"
        params.append(error_message)
    if video_path is not None:
        query += ", video_path = ?"
        params.append(video_path)
        
    query += " WHERE id = ?"
    params.append(task_id)
    
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def get_pending_task():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1")
    task = cursor.fetchone()
    conn.close()
    return dict(task) if task else None

def get_all_tasks():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
    tasks = cursor.fetchall()
    conn.close()
    return [dict(t) for t in tasks]

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM videos")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM videos WHERE status NOT IN ('pending', 'completed', 'failed')")
    processing = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'failed'")
    failed = cursor.fetchone()[0]
    
    conn.close()
    
    success_rate = 0
    if (completed + failed) > 0:
        success_rate = int((completed / (completed + failed)) * 100)
        
    return {
        "total": total,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "success_rate": success_rate
    }

def get_existing_topics():
    """Daha önce kuyruğa eklenmiş veya tamamlanmış tüm konu başlıklarını döndürür (tekrar eklemeyi önlemek için)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT LOWER(topic) FROM videos")
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}

def delete_tasks(task_ids):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # It's better to use parameter binding
    placeholders = ','.join(['?'] * len(task_ids))
    
    # We could also fetch video_paths to delete files, but keeping it simple for DB first
    # Or fetch them before deletion
    cursor.execute(f"SELECT video_path FROM videos WHERE id IN ({placeholders}) AND video_path IS NOT NULL", task_ids)
    paths = cursor.fetchall()
    
    cursor.execute(f"DELETE FROM videos WHERE id IN ({placeholders})", task_ids)
    conn.commit()
    conn.close()
    
    return [p[0] for p in paths]

# Tabloyu oluştur
init_db()
