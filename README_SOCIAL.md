# Sosyal Medya Entegrasyonu - AI Video Bot

AI Video Bot projeniz için oluşturulan sosyal medya yönetim sistemi ile videolarınızı tek bir yerden tüm platformlarda yayınlayabilirsiniz.

## 🚀 Özellikler

- **Çoklu Platform Desteği**: Facebook, X (Twitter), Instagram, TikTok, YouTube, LinkedIn, Threads, Pinterest, Bluesky
- **3 Farklı API Provider**: Ayrshare, Outstand, PostForMe
- **Zamanlanmış Gönderiler**: İstediğiniz zamanında otomatik yayın
- **Video Önizleme**: Gönderim öncesi videoları izleyin
- **Gönderi Geçmişi**: Tüm sosyal medya gönderilerinizi takip edin
- **Otomatik Metin Oluşturma**: AI destekli gönderi metinleri

## 📋 Kurulum

### 1. Gerekli Dosyalar

Sosyal medya yönetimi için aşağıdaki dosyalar oluşturuldu:

- `social_media_manager.py` - Sosyal medya yönetimi sınıfı
- `social_api.py` - FastAPI endpoint'leri
- `social_dashboard.html` - Yönetim paneli arayüzü
- `social_routes.py` - Flask alternatif route'ları

### 2. API Provider Seçimi

Üç farklı provider arasından seçim yapabilirsiniz:

#### Ayrshare
- **Platformlar**: 13+ platform (Facebook, X, Instagram, LinkedIn, TikTok, YouTube, Threads, Pinterest, Snapchat, Reddit, Telegram, Bluesky, Google Business)
- **Fiyat**: $49/ay (Business plan)
- **Özellikler**: Analytics, comment management, auto hashtags
- **Website**: https://www.ayrshare.com/

#### Outstand
- **Platformlar**: 10 platform (X, LinkedIn, Instagram, Facebook, Threads, TikTok, YouTube, Bluesky, Pinterest)
- **Fiyat**: $5/ay + $0.01 gönderi başına
- **Özellikler**: Developer odaklı, hızlı kurulum
- **Website**: https://www.outstand.so/

#### PostForMe
- **Platformlar**: 5 platform (TikTok, Instagram, YouTube, Facebook, X)
- **Fiyat**: $10/ay
- **Özellikler**: Basit kullanım, white label seçeneği
- **Website**: https://www.postforme.dev/

### 3. API Anahtarları

1. Seçtiğiniz provider'ın web sitesine gidin
2. Hesap oluşturun ve API anahtarı alın
3. Video bot panelinde `/social` adresine gidin
4. API yapılandırma bölümünden anahtarınızı girin

## 🎯 Kullanım

### 1. Panel Erişimi

Video botunuz çalışırken:
```
http://localhost:8000/social
```

### 2. Adım Adım Gönderi

1. **API Yapılandırma**: Provider seçin ve API anahtarını girin
2. **Video Seçme**: Tamamlanmış videolardan birini seçin
3. **Platform Seçimi**: Yayınlamak istediğiniz platformları işaretleyin
4. **Metin Hazırlama**: Gönderi metnini yazın (otomatik oluşturulabilir)
5. **Zamanlama**: İsteğe bağlı olarak yayın zamanını ayarlayın
6. **Gönder**: "Gönder" butonuna tıklayın

### 3. API ile Kullanım

```python
from social_media_manager import SocialMediaManager

manager = SocialMediaManager()

# API anahtarını yapılandır
manager.configure_api("ayrshare", "your_api_key_here", True)

# Videoyu gönder
result = manager.post_video_to_social_media(
    video_id=1,
    platforms=["instagram", "tiktok", "youtube"],
    content="Yeni AI videom yayında! 🚀",
    provider="ayrshare"
)
```

## 📊 Veritabanı Yapısı

Sosyal medya gönderileri için yeni tablo oluşturulur:

```sql
CREATE TABLE social_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id INTEGER,
    platforms TEXT,
    content TEXT,
    provider TEXT,
    result TEXT,
    status TEXT DEFAULT 'posted',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos (id)
);
```

## 🔧 API Endpoint'leri

### Yapılandırma
- `GET /social/config` - Mevcut yapılandırmayı al
- `POST /social/config` - API yapılandırmasını güncelle

### Gönderi Yönetimi
- `POST /social/post` - Videoyu sosyal medyada paylaş
- `GET /social/history` - Gönderi geçmişini al
- `GET /social/post/{id}` - Belirli gönderinin detayları

### Platform Bilgileri
- `GET /social/platforms` - Desteklenen platformları listele

## 🎨 Arayüz Özellikleri

- **Modern Tasarım**: Bootstrap 5 tabanlı responsive arayüz
- **Platform Kartları**: Görsel platform seçimi
- **Video Önizleme**: Seçilen videoyu izleyebilme
- **Karakter Sayacı**: Twitter limitleri için karakter takibi
- **Toast Bildirimleri**: İşlem sonuçlarını anında bildirim
- **Modal Pencereler**: Detaylı bilgi gösterimi

## 🛡️ Güvenlik

- API anahtarları şifreli olarak saklanır
- Her kullanıcı kendi hesaplarını bağlar
- Token yenileme otomatik yönetilir

## 📱 Desteklenen Platformlar

| Platform | Ayrshare | Outstand | PostForMe |
|----------|----------|----------|-----------|
| Facebook | ✅ | ✅ | ✅ |
| X (Twitter) | ✅ | ✅ | ✅ |
| Instagram | ✅ | ✅ | ✅ |
| TikTok | ✅ | ✅ | ✅ |
| YouTube | ✅ | ✅ | ✅ |
| LinkedIn | ✅ | ✅ | ❌ |
| Threads | ✅ | ✅ | ❌ |
| Pinterest | ✅ | ✅ | ❌ |
| Bluesky | ✅ | ✅ | ❌ |

## 🔥 İpuçları

1. **İlk Gönderi**: Test etmek için önce tek bir platformda deneyin
2. **Metin Optimizasyonu**: Her platformun karakter limitlerine dikkat edin
3. **Zamanlama**: En yüksek etkileşim zamanlarında yayın yapın
4. **Hashtag Kullanımı**: Otomatik hashtag özelliğini kullanın
5. **Video Formatları**: Platformların video format gereksinimlerini kontrol edin

## 🐞 Sorun Giderme

### API Hataları
- API anahtarının doğru olduğundan emin olun
- Provider hesabınızın aktif olduğunu kontrol edin
- Platform bağlantılarının yapılandırıldığını doğrulayın

### Video Yükleme Hataları
- Video dosyasının var olduğunu kontrol edin
- Video formatının desteklendiğinden emin olun
- Dosya boyutunun platform limitlerini aşıp aşmadığını kontrol edin

### Platform Bağlantı Hataları
- Sosyal medya hesaplarınızın bağlı olduğunu doğrulayın
- API izinlerinin güncel olduğundan emin olun
- Provider'ın platform desteğini kontrol edin

## 📞 Destek

Sorun yaşarsanız:
1. Provider'ın dokümantasyonunu kontrol edin
2. API anahtarınızı yenileyin
3. Video bot loglarını inceleyin

---

**Not**: Bu entegrasyon ile AI videolarınızı profesyonel bir şekilde tüm sosyal medya platformlarında kolayca yayınlayabilirsiniz!
