#!/bin/bash
echo "======================================="
echo "   AI Video Bot Sunucusu Baslatiliyor  "
echo "======================================="
echo ""

# Sanal ortamı başlat
source venv/bin/activate

# Gerekli kütüphaneleri kontrol et ve kur
echo "Kutuphaneler kontrol ediliyor..."
pip install fastapi uvicorn pydantic google-generativeai requests psutil -q

# Sunucuyu başlat
echo ""
echo "======================================="
echo " Sunucu hazir! Tarayicidan acin:"
echo " http://localhost:8001"
echo "======================================="
echo " (Bu terminal penceresini kapatırsanız veya CTRL+C yaparsanız sunucu durur)"
echo ""

python -m uvicorn app:app --host 0.0.0.0 --port 8001
