import sqlite3
import threading
from datetime import datetime
from typing import List
from contextlib import contextmanager

DB_NAME = "aivid_data.db"

# Thread-local connection pool
_local = threading.local()

def get_connection():
    """Thread-local bağlantı al veya oluştur"""
    if not hasattr(_local, 'connection') or _local.connection is None:
        _local.connection = sqlite3.connect(DB_NAME, check_same_thread=False)
        _local.connection.row_factory = sqlite3.Row
    return _local.connection

@contextmanager
def get_db():
    """Context manager for database operations with automatic commit/rollback"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
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
                voice_type TEXT DEFAULT 'erkek',
                image_ai TEXT,
                custom_script TEXT,
                subtitle_style TEXT DEFAULT 'tiktok',
                subtitle_delay REAL DEFAULT 0.5,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                video_mode TEXT DEFAULT 'slideshow',
                sentence_pause REAL DEFAULT 0.0,
                watermark_enabled INTEGER DEFAULT 0,
                transition_style TEXT DEFAULT 'none',
                bgm_enabled INTEGER DEFAULT 0,
                bgm_tone TEXT DEFAULT 'auto',
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
            cursor.execute("ALTER TABLE videos ADD COLUMN subtitle_delay REAL DEFAULT 0.5")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE videos ADD COLUMN video_mode TEXT DEFAULT 'slideshow'")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE videos ADD COLUMN voice_type TEXT DEFAULT 'erkek'")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE videos ADD COLUMN custom_script TEXT")
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute("ALTER TABLE videos ADD COLUMN sentence_pause REAL DEFAULT 0.0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE videos ADD COLUMN watermark_enabled INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE videos ADD COLUMN transition_style TEXT DEFAULT 'none'")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE videos ADD COLUMN bgm_enabled INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE videos ADD COLUMN bgm_tone TEXT DEFAULT 'auto'")
        except sqlite3.OperationalError:
            pass
        
        # Index oluştur - performans için
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON videos(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON videos(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic ON videos(topic)")

def add_video_task(topic, category, tone, duration, language, script_ai, voice_ai, image_ai,
                   subtitle_style="tiktok", video_mode="slideshow", voice_type="erkek",
                   custom_script=None, sentence_pause=0.0,
                   watermark_enabled=False, transition_style="none",
                   bgm_enabled=False, bgm_tone="auto", subtitle_delay=0.5):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO videos (topic, category, tone, duration, language, script_ai, voice_ai,
                                voice_type, image_ai, subtitle_style, video_mode, custom_script,
                                sentence_pause, watermark_enabled, transition_style,
                                bgm_enabled, bgm_tone, subtitle_delay)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (topic, category, tone, duration, language, script_ai, voice_ai, voice_type,
               image_ai, subtitle_style, video_mode, custom_script,
               sentence_pause, int(watermark_enabled), transition_style,
               int(bgm_enabled), bgm_tone, subtitle_delay))
        return cursor.lastrowid

def update_status(task_id, status, progress=None, error_message=None, video_path=None):
    with get_db() as conn:
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

def get_pending_tasks(limit: int = 10) -> List[dict]:
    """Bekleyen görevleri alır"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, topic, category, tone, duration, language, script_ai, voice_ai,
                   voice_type, image_ai, subtitle_style, video_mode, custom_script,
                   sentence_pause, watermark_enabled, transition_style,
                   bgm_enabled, bgm_tone, subtitle_delay
            FROM videos 
            WHERE status = 'pending' 
            ORDER BY created_at ASC 
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

def get_pending_tasks_count() -> int:
    """Bekleyen görev sayısını döndürür"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM videos WHERE status = 'pending'")
        return cursor.fetchone()[0]

def get_pending_task():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE status = 'pending' ORDER BY created_at ASC LIMIT 1")
        task = cursor.fetchone()
        return dict(task) if task else None

def get_all_tasks():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

def get_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tek sorguda tüm istatistikleri al
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status NOT IN ('pending', 'completed', 'failed') THEN 1 ELSE 0 END) as processing,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM videos
        """)
        
        row = cursor.fetchone()
        total, pending, processing, completed, failed = row
        
        success_rate = 0
        if (completed + failed) > 0:
            success_rate = int((completed / (completed + failed)) * 100)
            
        return {
            "total": total or 0,
            "pending": pending or 0,
            "processing": processing or 0,
            "completed": completed or 0,
            "failed": failed or 0,
            "success_rate": success_rate
        }

def get_existing_topics():
    """Daha önce kuyruğa eklenmiş veya tamamlanmış tüm konu başlıklarını döndürür (tekrar eklemeyi önlemek için)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT LOWER(topic) FROM videos")
        return {row[0] for row in cursor.fetchall()}

def delete_tasks(task_ids):
    with get_db() as conn:
        cursor = conn.cursor()
        placeholders = ','.join(['?'] * len(task_ids))
        
        cursor.execute(f"SELECT video_path FROM videos WHERE id IN ({placeholders}) AND video_path IS NOT NULL", task_ids)
        paths = cursor.fetchall()
        
        cursor.execute(f"DELETE FROM videos WHERE id IN ({placeholders})", task_ids)
        
        return [p[0] for p in paths]


def get_tasks_by_status(status: str, limit: int = 100) -> List[dict]:
    """Belirli durumdaki görevleri alır"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM videos 
            WHERE status = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (status, limit))
        return [dict(row) for row in cursor.fetchall()]


def cleanup_old_tasks(days: int = 30):
    """Belirli günden eski tamamlanmış/başarısız görevleri temizler"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM videos 
            WHERE status IN ('completed', 'failed') 
            AND updated_at < datetime('now', '-{} days')
        """.format(days))
        return cursor.rowcount

# Tabloyu oluştur
init_db()
