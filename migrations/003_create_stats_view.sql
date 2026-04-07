/*
  # İstatistik View'ları

  1. View'lar
    - `video_stats` - Anlık istatistikler (total, pending, processing, completed, failed)
    - Performans için materialized view kullanılabilir (opsiyonel)

  2. Kullanım
    - SELECT * FROM video_stats; → Anlık istatistikler
    - Frontend /api/stats endpoint'inde kullanılacak
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
