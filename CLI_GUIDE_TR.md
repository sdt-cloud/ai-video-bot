# 🎬 AI Video Bot — Profesyonel CLI Otomasyon Klavuzu

**AI Video Bot CLI Klavuzuna** hoş geldiniz. Bu kapsamlı rehber, terminal arayüzünü (`main.py`) kullanarak video üretim kuyruklarını nasıl tamamen otomatikleştireceğinizi, zamanlanmış video üretim hatları kuracağınızı, toplu video üretim scriptleri çalıştıracağınızı ve entegrasyon senaryolarını detaylandırmaktadır.

---

## 🚀 1. CLI Kullanımı ve Temel Sözdizimi

Botu CLI modunda çalıştırmak için kök dizinde Python kullanarak `main.py` dosyasını tetikleyin:
```bash
python main.py [argümanlar]
```
> [!TIP]
> Eğer `python main.py` komutunu **hiçbir argüman vermeden** çalıştırırsanız, CLI otomatik olarak eski etkileşimli terminal moduna geçiş yapar!

---

## 📊 2. Argüman Özellikleri ve Parametreler

| Kısa Bayrak | Uzun Bayrak | Tip | İzin Verilen Değerler | Varsayılan | Açıklama |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `-t` | `--topic` | `string` | Herhangi bir konu başlığı | `None` | Senaryo üretilecek video konusu. |
| `-cs` | `--custom-script` | `string` | Metin veya dosya yolu | `None` | Önceden yazılmış özel senaryo metni veya txt dosya yolu. |
| `-d` | `--duration` | `int` | `15` - `300` | `30` | Saniye cinsinden hedef video süresi. |
| `-l` | `--language` | `string` | `tr`, `en`, `es` | `tr` | Seslendirme ve senaryo dili. |
| `-q` | `--quality` | `string` | `low`, `medium`, `high` | `medium` | Video üretim kalite seviyesi. |
| `-ar` | `--aspect-ratio` | `string` | `9:16`, `16:9`, `1:1` | `9:16` | Video çözünürlük oranı. |
| `-sa` | `--script-ai` | `string` | `Gemini`, `OpenAI` | `Gemini` | Senaryo yazıcı yapay zeka motoru. |
| `-va` | `--voice-ai` | `string` | `Edge-TTS`, `ElevenLabs` | `Edge-TTS` | Ses sentezleyici motoru. |
| `-vt` | `--voice-type` | `string` | `erkek`, `kadin` | `erkek` | Seslendirme karakter cinsiyeti. |
| `-ia` | `--image-ai` | `string` | `Stock-Auto`, `Pollinations`, `OpenAI`, `Flux`, `SDXL`, `Pexels`, `Pixabay`, `Unsplash` | `Pollinations` | Görsel varlık üretici/sağlayıcı motoru. |
| `-ap` | `--animation-provider` | `string` | `none`, `stability_ai`, `runway`, `replicate`, `luma` | `none` | Görselden videoya animasyon motoru. |
| `-ss` | `--subtitle-style` | `string` | `tiktok`, `classic`, `minimal` | `tiktok` | Altyazı tasarım şablonu. |
| `-sd` | `--subtitle-delay` | `float` | `0.1` - `3.0` | `0.75` | Altyazı hızı çarpan gecikmesi. |
| `-vm` | `--video-mode` | `string` | `slideshow`, `zoom_motion` | `slideshow` | Sahne geçiş/hareket animasyonu modu. |
| `-tr` | `--transition` | `string` | `none`, `fade`, `crossfade`, `zoom`, `spin`, `glitch`, `auto` | `none` | Sahneler arası geçiş efekti. |
| `--bgm` | *Bayrak* | *Yok* | Aktif / Pasif | `False` | Tona uygun otomatik arka plan müziği ekler. |
| `--bgm-tone` | `string` | `dramatic`, `epic`, `happy`, `energetic`, `auto` | `auto` | Arka plan müzik tonu seçimi. |
| `-sp` | `--sentence-pause` | `float` | `0.0` - `2.5` | `0.0` | Cümleler arası sessizlik/bekleme süresi. |
| `--watermark` | *Bayrak* | *Yok* | Aktif / Pasif | `False` | Varsayılan AI Video Bot filigranını ekler. |
| `-cg` | `--color-grade` | `string` | `none`, `auto_enhance`, `warm`, `cool`, `vintage`, `cinematic` | `auto_enhance` | Renk derecelendirme filtre stili. |
| `--letterbox` | *Bayrak* | *Yok* | Aktif / Pasif | `False` | Sinematik siyah kenar sınırları ekler. |
| `--light-leak` | *Bayrak* | *Yok* | Aktif / Pasif | `False` | Organik ışık sızması film kaplamaları ekler. |
| `--no-thumbnail` | *Bayrak* | *Yok* | Aktif / Pasif | `False` | Otomatik kapak (thumbnail) üretimini kapatır. |
| `-o` | `--output` | `string` | Özel dosya yolu (Örn: `exports/v.mp4`) | `None` | Çıktı video dosyasının kaydedileceği yer. |

---

## 💡 3. Hızlı Başlangıç Örnekleri

### 📱 TikTok / YouTube Shorts (Dikey Mod)
Roma Gladyatörleri hakkında 30 saniyelik, enerjik, müzikli ve filigranlı bir video üretin:
```bash
python main.py -t "İnanılmaz Roma Gladyatör Gerçekleri" -d 30 -l tr -q high --bgm --bgm-tone energetic --watermark
```

### 🎬 YouTube Uzun Video (Yatay Sinematik)
Rönesans üzerine 2 dakikalık, yatay, zoom geçişli, sinematik siyah şeritli ve ışık sızmalı bir belgesel hazırlayın:
```bash
python main.py -t "Rönesans Sanatının Gizli Dehası" -d 120 -ar 16:9 -vm zoom_motion -tr crossfade --letterbox --light-leak -o exports/ronesans_belgeseli.mp4
```

### 🧠 Hazır Özel Senaryolu Video Üretimi
Kendi yazdığınız bir senaryo metnini kullanarak otomatik seslendirme, altyazı ve görselleştirme akışını tetikleyin:
```bash
python main.py -cs "scripts/ozel_metin.txt" -d 45 -l tr --bgm -o exports/ozel_anlatim.mp4
```

---

## ⚙️ 4. İleri Seviye Otomasyon ve Geliştirici Bash Reçeteleri

CLI arayüzü paralel kuyrukları tek bir komutla arka planda yönettiği için, shell scriptleri, cron görevleri ve mikroservislerle saniyeler içinde bütünleştirilebilir.

### Reçete A: Metin Dosyasından Toplu Video Üretimi
Her satırında bir konu başlığı barındıran bir `topics.txt` dosyanız varsa, sırayla hepsini üreten bir bash script (`toplu_uretici.sh`) hazırlayabilirsiniz:

```bash
#!/bin/bash
# toplu_uretici.sh

TOPIC_FILE="topics.txt"

if [ ! -f "$TOPIC_FILE" ]; then
    echo "[-] Hata: $TOPIC_FILE bulunamadı!"
    exit 1
fi

echo "[+] Toplu Video Üretim Kuyruğu Başlatılıyor..."
while IFS= read -r topic || [ -n "$topic" ]; do
    # Boş satırları veya yorum satırlarını atla
    [[ -z "$topic" || "$topic" =~ ^# ]] && continue
    
    echo "=========================================================="
    echo "🚀 İşlenen Konu: $topic"
    echo "=========================================================="
    
    python main.py -t "$topic" -d 30 -l tr --bgm --watermark
    
    echo "[+] Tamamlandı: $topic"
    sleep 5 # API limitlerine takılmamak için kısa bekleme süresi
done < "$TOPIC_FILE"

echo "[🎉] Toplu video üretimi başarıyla tamamlandı!"
```

### Reçete B: Cron Görevleri ile Otomatik Günlük Video Üretimi
Sunucunuzun veya bilgisayarınızın her sabah saat 09:00'da otomatik olarak popüler bilim üzerine dikey bir Short/TikTok videosu üretmesini sağlayabilirsiniz.

Cron yöneticisini açın:
```bash
crontab -e
```

En alta şu satırı ekleyin (venv ortamını yükler, komutu çalıştırır ve günlük logları kaydeder):
```cron
0 9 * * * cd /home/sedat/Masaüstü/Projeler/scratch/ai-video-bot && ./venv/bin/python main.py -t "Günün Akıl Almaz Bilimsel Gerçeği" -d 35 -l tr --bgm > logs/cron_gunluk.log 2>&1
```

---

## 🏆 5. CLI Üzerindeki Paralel Güçler
Terminal üzerinden tetiklenen bu CLI motoru, web arayüzünde kullanılan tüm performans optimizasyonlarını birebir kullanır:
*   **Paralel Stok Klipleri:** Pexels ve Pixabay üzerinden videoları paralel thread'lerde sorgular ve indirir.
*   **Paralel Görsel Üretimi:** Yapay zeka görsellerini tek tek beklemek yerine eş zamanlı isteklerle üretir.
*   **Otomatik Tıklama Tuzağı (Clickbait) Kapak Resmi:** Video üretimi bittiğinde, montaja uygun Montserrat fontları ve altın sarısı parlamalarla devasa boyutlarda ilgi çekici bir kapak görselini (`_thumbnail.jpg`) otomatik hazırlar.
