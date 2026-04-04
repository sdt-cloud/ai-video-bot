# 🤝 Katkıda Bulunma Rehberi

AI Video Bot projesine katkıda bulunmak istediğiniz için teşekkürler! 🎉

## 🚀 Nasıl Katkıda Bulunabilirim?

### 1. Bug Raporlama
- GitHub Issues sayfasından yeni bir issue oluşturun
- Hatanın detaylı bir şekilde açıklayın
- Mümkünse ekran görüntüsü veya hata logları ekleyin

### 2. Yeni Özellik Önerme
- Issues sayfasında `enhancement` etiketi ile yeni bir issue açın
- Özelliğin ne işe yarayacağını ve neden gerekli olduğunu açıklayın

### 3. Kod Katkısı
1. Bu repoyu **fork** edin
2. Yeni bir **branch** oluşturun: `git checkout -b yeni-ozellik`
3. Değişikliklerinizi yapın ve **commit** edin: `git commit -m "Yeni özellik: XYZ eklendi"`
4. Branch'inizi **push** edin: `git push origin yeni-ozellik`
5. Bir **Pull Request** açın

## 📋 Geliştirme Ortamı Kurulumu

```bash
# Repoyu klonlayın
git clone https://github.com/KULLANICI_ADINIZ/ai-video-bot.git
cd ai-video-bot

# Sanal ortam oluşturun
python -m venv venv
.\venv\Scripts\activate  # Windows

# Bağımlılıkları kurun
pip install -r requirements.txt

# .env dosyasını oluşturun
cp .env.example .env
# API anahtarlarınızı .env dosyasına ekleyin
```

## 📝 Kod Standartları

- Python kodu için **PEP 8** standartlarına uyun
- Fonksiyonlara açıklayıcı docstring'ler ekleyin
- Türkçe yorumlar kullanın (proje dili Türkçe)
- Commit mesajları anlamlı ve açıklayıcı olsun

## 🙏 Teşekkürler

Her türlü katkı, ister bir bug raporu, ister bir özellik önerisi, ister bir pull request olsun, proje için çok değerlidir!
