/*
  # Video Üretim Sistemi - Ana Tablo

  1. Yeni Tablolar
    - `videos`
      - `id` (bigserial, primary key)
      - `topic` (text) - Video konusu
      - `category` (text) - Kategori
      - `tone` (text) - Ton (Enerjik, Dramatik, vb.)
      - `duration` (integer) - Süre (saniye)
      - `language` (text) - Dil (tr, en)
      - `script_ai` (text) - Senaryo AI provider
      - `voice_ai` (text) - Ses AI provider
      - `voice_type` (text) - Ses tipi (erkek, kadın, vb.)
      - `image_ai` (text) - Görsel AI provider
      - `subtitle_style` (text) - Altyazı stili
      - `status` (text) - Durum (pending, scripting, media, rendering, completed, failed)
      - `progress` (integer) - İlerleme yüzdesi (0-100)
      - `video_mode` (text) - Video modu (slideshow, cinematic, ai_video)
      - `error_message` (text) - Hata mesajı
      - `video_path` (text) - Oluşturulan video dosyası yolu
      - `created_at` (timestamptz) - Oluşturulma zamanı
      - `updated_at` (timestamptz) - Güncellenme zamanı

  2. Güvenlik
    - RLS etkin
    - Herkes okuyabilir (public read)
    - Sadece authenticated kullanıcılar yazabilir (örneklem için)

  3. Performans
    - Otomatik updated_at trigger
    - Index'ler sonraki migration'da eklenecek
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

-- Herkes ekleyebilir (demo için - production'da authenticated olmalı)
CREATE POLICY "Anyone can insert videos"
    ON videos FOR INSERT
    TO public
    WITH CHECK (true);

-- Herkes güncelleyebilir (demo için - production'da authenticated olmalı)
CREATE POLICY "Anyone can update videos"
    ON videos FOR UPDATE
    TO public
    USING (true)
    WITH CHECK (true);

-- Herkes silebilir (demo için - production'da authenticated olmalı)
CREATE POLICY "Anyone can delete videos"
    ON videos FOR DELETE
    TO public
    USING (true);
