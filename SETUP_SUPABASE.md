# Supabase Kurulum Rehberi

Bu rehber, AI Video Bot projesini SQLite'dan Supabase'e geçirmek için adım adım talimatlar içerir.

## Gereksinimler

- Supabase hesabı (ücretsiz tier yeterli)
- Python 3.10+
- İnternet bağlantısı

---

## Adım 1: Supabase Projesi Oluştur

1. **Supabase'e Kaydol:**
   - https://supabase.com adresine git
   - "Start your project" → Sign up (GitHub ile giriş yapabilirsiniz)

2. **Yeni Proje Oluştur:**
   - Dashboard'da "New project" butonuna tıkla
   - **Project name:** ai-video-bot (istediğiniz ismi verebilirsiniz)
   - **Database Password:** Güçlü bir şifre belirleyin (kaydedin!)
   - **Region:** Size en yakın bölgeyi seçin (örn: Frankfurt, eu-central-1)
   - "Create new project" butonuna tıkla
   - Proje hazırlanırken 1-2 dakika bekleyin

3. **API Credentials'ı Kopyala:**
   - Sol menüden "Settings" → "API"
   - **Project URL** ve **Anon Public Key**'i kopyalayın

---

## Adım 2: Environment Variables

1. **`.env` Dosyası Oluştur:**

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

2. **Supabase Credentials Ekle:**

`.env` dosyasını düzenleyin:

```env
# === SUPABASE (VERİTABANI) ===
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Kopyaladığınız değerleri buraya yapıştırın.

---

## Adım 3: Database Schema Oluştur

Supabase Dashboard'da SQL Editor kullanarak migration'ları çalıştıracağız.

### Migration 1: Videos Tablosu

1. Supabase Dashboard → Sol menü → **SQL Editor**
2. "New query" butonuna tıkla
3. Aşağıdaki SQL'i yapıştır:

```sql
/*
  # Video Üretim Sistemi - Ana Tablo
*/

-- Videos tablosunu oluştur
CREATE TABLE IF NOT EXISTS videos (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    category TEXT DEFAULT 'Genel',
    tone TEXT DEFAULT 'Enerjik',
    duration INTEGER DEFAULT 30,
    language TEXT DEFAULT 'tr',
    script_ai TEXT DEFAULT 'Gemini',
    voice_ai TEXT DEFAULT 'Edge-TTS',
    voice_type TEXT DEFAULT 'erkek',
    image_ai TEXT DEFAULT 'Pollinations',
    subtitle_style TEXT DEFAULT 'tiktok',
    status TEXT DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    video_mode TEXT DEFAULT 'slideshow',
    error_message TEXT,
    video_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- updated_at otomatik güncelleme trigger'ı
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_videos_updated_at
    BEFORE UPDATE ON videos
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- RLS'yi etkinleştir
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;

-- Herkes okuyabilir
CREATE POLICY "Anyone can view videos"
    ON videos FOR SELECT
    TO public
    USING (true);

-- Herkes ekleyebilir
CREATE POLICY "Anyone can insert videos"
    ON videos FOR INSERT
    TO public
    WITH CHECK (true);

-- Herkes güncelleyebilir
CREATE POLICY "Anyone can update videos"
    ON videos FOR UPDATE
    TO public
    USING (true)
    WITH CHECK (true);

-- Herkes silebilir
CREATE POLICY "Anyone can delete videos"
    ON videos FOR DELETE
    TO public
    USING (true);
```

4. "Run" butonuna tıkla
5. "Success. No rows returned" mesajını görmelisiniz

### Migration 2: Indexes

1. Yeni bir query oluştur (New query)
2. Aşağıdaki SQL'i yapıştır:

```sql
/*
  # Performans İndexleri
*/

-- Status index
CREATE INDEX IF NOT EXISTS idx_videos_status
    ON videos(status);

-- Created_at index
CREATE INDEX IF NOT EXISTS idx_videos_created_at
    ON videos(created_at DESC);

-- Composite index
CREATE INDEX IF NOT EXISTS idx_videos_status_created
    ON videos(status, created_at DESC);

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_videos_topic
    ON videos USING gin(to_tsvector('turkish', topic));

-- Analyze table
ANALYZE videos;
```

3. "Run" butonuna tıkla

### Migration 3: Stats Views

1. Yeni bir query oluştur
2. Aşağıdaki SQL'i yapıştır:

```sql
/*
  # İstatistik View'ları
*/

-- Video istatistikleri view
CREATE OR REPLACE VIEW video_stats AS
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'pending') as pending,
    COUNT(*) FILTER (WHERE status IN ('scripting', 'media', 'rendering')) as processing,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    CASE
        WHEN COUNT(*) FILTER (WHERE status IN ('completed', 'failed')) > 0
        THEN ROUND(
            100.0 * COUNT(*) FILTER (WHERE status = 'completed') /
            COUNT(*) FILTER (WHERE status IN ('completed', 'failed'))
        )
        ELSE 0
    END as success_rate
FROM videos;

-- Kategori bazlı istatistikler
CREATE OR REPLACE VIEW video_stats_by_category AS
SELECT
    category,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    ROUND(AVG(duration)) as avg_duration
FROM videos
GROUP BY category
ORDER BY total DESC;
```

3. "Run" butonuna tıkla

---

## Adım 4: Bağlantıyı Test Et

1. **Python Paketlerini Yükle:**

```bash
pip install supabase
```

2. **Test Script Çalıştır:**

```python
# test_supabase.py
from supabase_client import SupabaseClient
import asyncio

async def test_connection():
    try:
        client = SupabaseClient.get_client()
        print("✅ Supabase bağlantısı başarılı!")

        # Health check
        is_healthy = await SupabaseClient.health_check()
        if is_healthy:
            print("✅ Health check başarılı!")
        else:
            print("❌ Health check başarısız!")

        # Test insert
        response = client.table('videos').insert({
            'topic': 'Test Video',
            'status': 'pending'
        }).execute()

        if response.data:
            print(f"✅ Test video oluşturuldu: ID {response.data[0]['id']}")

            # Test select
            videos = client.table('videos').select("*").execute()
            print(f"✅ {len(videos.data)} video bulundu")

            # Test delete
            client.table('videos').delete().eq('topic', 'Test Video').execute()
            print("✅ Test video silindi")

    except Exception as e:
        print(f"❌ Hata: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

```bash
python test_supabase.py
```

Çıktı:
```
✅ Supabase bağlantısı başarılı!
✅ Health check başarılı!
✅ Test video oluşturuldu: ID 1
✅ 1 video bulundu
✅ Test video silindi
```

---

## Adım 5: Mevcut SQLite Verisini Migrate Et (Opsiyonel)

Eğer mevcut SQLite veritabanınızda video kayıtları varsa:

```python
# migrate_sqlite_to_supabase.py
import sqlite3
from supabase_client import SupabaseClient

def migrate_data():
    # SQLite'dan veriyi oku
    conn = sqlite3.connect('aivid_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM videos")
    rows = cursor.fetchall()

    print(f"📦 {len(rows)} video kaydı bulundu")

    # Supabase'e aktar
    client = SupabaseClient.get_client()

    for row in rows:
        data = dict(row)
        # id'yi çıkar (otomatik üretilecek)
        data.pop('id', None)

        try:
            client.table('videos').insert(data).execute()
            print(f"✅ Video migrated: {data['topic']}")
        except Exception as e:
            print(f"❌ Hata: {e}")

    conn.close()
    print("✅ Migration tamamlandı!")

if __name__ == "__main__":
    migrate_data()
```

```bash
python migrate_sqlite_to_supabase.py
```

---

## Adım 6: Database Layer'ı Güncelle (Gelecek Çalışma)

`database.py` dosyasını Supabase kullanacak şekilde refactor etmek gerekiyor. Bu adım için teknik bilgi gerekir.

**Örnek Fonksiyon Dönüşümü:**

**Öncesi (SQLite):**
```python
def add_video_task(topic, ...):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO videos (topic, ...) VALUES (?, ...)
        """, (topic, ...))
        return cursor.lastrowid
```

**Sonrası (Supabase):**
```python
def add_video_task(topic, ...):
    client = SupabaseClient.get_client()
    response = client.table('videos').insert({
        'topic': topic,
        ...
    }).execute()
    return response.data[0]['id']
```

---

## Sorun Giderme

### Hata: "relation 'videos' does not exist"

**Çözüm:** Migration'ları tekrar çalıştırın (Adım 3)

### Hata: "Invalid API key"

**Çözüm:** `.env` dosyasındaki `SUPABASE_ANON_KEY`'i kontrol edin

### Hata: "Unable to connect"

**Çözüm:** İnternet bağlantınızı ve `SUPABASE_URL`'i kontrol edin

### Hata: "Permission denied"

**Çözüm:** RLS policy'leri kontrol edin (Migration 1'de oluşturulmuş olmalı)

---

## Güvenlik Notları

### Production'da RLS Politikalarını Sıkılaştırın

**Şu anki durum:** Herkes her şeyi yapabilir (demo için)

**Production önerisi:** Authenticated kullanıcılar için kısıtla

```sql
-- Mevcut policy'leri sil
DROP POLICY "Anyone can insert videos" ON videos;
DROP POLICY "Anyone can update videos" ON videos;
DROP POLICY "Anyone can delete videos" ON videos;

-- Yeni restrictive policy'ler
CREATE POLICY "Authenticated users can insert videos"
    ON videos FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Authenticated users can update videos"
    ON videos FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

CREATE POLICY "Authenticated users can delete videos"
    ON videos FOR DELETE
    TO authenticated
    USING (true);
```

---

## Faydalı Supabase Komutları

### Tüm Videoları Görüntüle
```sql
SELECT * FROM videos ORDER BY created_at DESC LIMIT 10;
```

### İstatistikleri Görüntüle
```sql
SELECT * FROM video_stats;
```

### Kategori Bazlı İstatistikler
```sql
SELECT * FROM video_stats_by_category;
```

### Bekleyen Videoları Görüntüle
```sql
SELECT * FROM videos WHERE status = 'pending' ORDER BY created_at ASC;
```

### Başarısız Videoları Sil
```sql
DELETE FROM videos WHERE status = 'failed' AND created_at < NOW() - INTERVAL '7 days';
```

---

## Kaynaklar

- Supabase Docs: https://supabase.com/docs
- Python Client: https://supabase.com/docs/reference/python
- Row Level Security: https://supabase.com/docs/guides/auth/row-level-security

---

**Son Güncelleme:** 2026-04-07
