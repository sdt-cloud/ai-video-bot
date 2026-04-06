@echo off
title AI Video Bot Sunucusu
echo =======================================
echo    AI Video Bot Sunucusu Baslatiliyor
echo =======================================
echo.

:: Sanal ortami baslat
call .\venv\Scripts\activate

:: Gerekli kutuphanelerin kurulu oldugundan emin ol
echo Kutuphaneler kontrol ediliyor...
pip install fastapi uvicorn pydantic google-generativeai requests psutil -q

:: Sunucuyu baslat
echo.
echo =======================================
echo  Sunucu hazir! Tarayicidan acin:
echo  http://localhost:8000
echo =======================================
echo  (Bu pencereyi kapatirsaniz sunucu durur)
echo.
python -m uvicorn app:app --host 0.0.0.0 --port 8000

pause
