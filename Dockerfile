# Python 3.10 tabanlı hafif imaj
FROM python:3.10-slim

# FFmpeg ve temel derleme araçlarını kur
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Çalışma dizinini ayarla
WORKDIR /app

# Bağımlılıkları kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kaynak kodlarını kopyala
COPY . .

# Çıkış portunu tanımla (FastAPI 8001 portunda çalışıyor)
EXPOSE 8001

# Uygulamayı başlat
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
