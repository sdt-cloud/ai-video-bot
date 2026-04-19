"""
Arka Plan Müziği (BGM) Yönetim Modülü

Ton bazlı telifsiz müzik seçer ve indirir.
Önce yerel assets/bgm/ dizinine bakar, yoksa Pixabay Music API'sinden indirir.
"""

import os
import random
import requests
from dotenv import load_dotenv

load_dotenv()

BGM_DIR = "assets/bgm"

# Ton → Pixabay arama sorgusu eşleşmesi
TONE_TO_QUERY = {
    "enerjik":     "energetic upbeat",
    "neşeli":      "happy cheerful",
    "komik":       "funny playful",
    "dramatik":    "dramatic cinematic",
    "gizemli":     "mysterious ambient",
    "sakin":       "calm relaxing",
    "bilimsel":    "ambient electronic",
    "eğitici":     "calm background music",
    "profesyonel": "corporate background",
    "romantik":    "romantic soft",
    "otomatik":    "background ambient",
    "auto":        "background ambient",
}

# Ton → yerel dosya ismi eşleşmesi
TONE_TO_FILENAME = {
    "enerjik":     "energetic.mp3",
    "neşeli":      "happy.mp3",
    "komik":       "funny.mp3",
    "dramatik":    "dramatic.mp3",
    "gizemli":     "mysterious.mp3",
    "sakin":       "calm.mp3",
    "bilimsel":    "ambient.mp3",
    "eğitici":     "calm.mp3",
    "profesyonel": "corporate.mp3",
    "romantik":    "romantic.mp3",
    "otomatik":    "calm.mp3",
    "auto":        "calm.mp3",
}


def _normalize_tone(tone: str) -> str:
    """Tonu normalize eder (küçük harf, Türkçe karakter toleransı)."""
    return (tone or "auto").strip().lower()


def _get_local_bgm(tone: str) -> str | None:
    """Yerel BGM dosyasını arar. Bulursa yolunu döndürür."""
    os.makedirs(BGM_DIR, exist_ok=True)
    tone_key = _normalize_tone(tone)

    # Önce ton-spesifik dosyayı dene
    filename = TONE_TO_FILENAME.get(tone_key, "calm.mp3")
    path = os.path.join(BGM_DIR, filename)
    if os.path.exists(path) and os.path.getsize(path) > 1024:
        print(f"[BGM] Yerel dosya bulundu: {path}")
        return path

    # Dizinde herhangi bir mp3 varsa onu kullan
    try:
        mp3_files = [
            f for f in os.listdir(BGM_DIR)
            if f.endswith(".mp3") and os.path.getsize(os.path.join(BGM_DIR, f)) > 1024
        ]
        if mp3_files:
            chosen = random.choice(mp3_files)
            print(f"[BGM] Rastgele yerel dosya seçildi: {chosen}")
            return os.path.join(BGM_DIR, chosen)
    except Exception:
        pass

    return None


def _generate_ambient_tone(output_path: str, tone: str = "calm", duration_secs: int = 45) -> str | None:
    """
    Numpy ile basit bir ambient arka plan müziği üretir.
    İnternet yoksa veya API başarısız olursa bu devreye girer.
    Tamamen ücretsiz ve telifsizdir.
    """
    try:
        import numpy as np
        import wave, struct
        print(f"[BGM] Ambient ton üretiliyor (ton={tone}, {duration_secs}sn)...")

        sample_rate = 44100

        # Ton bazlı frekans ve ayar seçimi
        tone_profiles = {
            "calm":       {"freqs": [110.0, 165.0, 220.0], "vol": 0.06, "mod_rate": 0.08},
            "sakin":      {"freqs": [110.0, 165.0, 220.0], "vol": 0.06, "mod_rate": 0.08},
            "enerjik":    {"freqs": [174.6, 261.6, 349.2], "vol": 0.09, "mod_rate": 0.25},
            "dramatik":   {"freqs": [98.0,  130.8, 196.0], "vol": 0.10, "mod_rate": 0.12},
            "gizemli":    {"freqs": [92.5,  138.6, 185.0], "vol": 0.07, "mod_rate": 0.06},
            "neşeli":     {"freqs": [261.6, 329.6, 392.0], "vol": 0.08, "mod_rate": 0.20},
            "profesyonel":{"freqs": [130.8, 196.0, 261.6], "vol": 0.06, "mod_rate": 0.10},
            "bilimsel":   {"freqs": [144.0, 192.0, 288.0], "vol": 0.06, "mod_rate": 0.07},
            "eğitici":    {"freqs": [110.0, 165.0, 220.0], "vol": 0.05, "mod_rate": 0.08},
            "romantik":   {"freqs": [196.0, 246.9, 293.7], "vol": 0.07, "mod_rate": 0.09},
        }
        profile = tone_profiles.get(tone.lower(), tone_profiles["calm"])

        t = np.linspace(0, duration_secs, int(sample_rate * duration_secs), endpoint=False)

        # Her frekans için sinüs dalgası üret ve karıştır
        signal = np.zeros_like(t)
        for i, freq in enumerate(profile["freqs"]):
            amplitude = profile["vol"] * (1.0 / (i + 1))  # Harmonikler azalan amplitüd ile
            signal += amplitude * np.sin(2 * np.pi * freq * t)

        # Yavaş titreşim (tremolo) — müziği daha canlı hissettirir
        mod_rate = profile["mod_rate"]
        tremolo = 0.85 + 0.15 * np.sin(2 * np.pi * mod_rate * t)
        signal *= tremolo

        # Fade in/out (başında ve sonunda 3sn yumuşama)
        fade_samples = int(sample_rate * 3)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        signal[:fade_samples] *= fade_in
        signal[-fade_samples:] *= fade_out

        # 16-bit PCM WAV olarak kaydet
        wav_path = output_path.replace(".mp3", ".wav")
        with wave.open(wav_path, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            pcm_data = (signal * 32767).astype(np.int16)
            wav_file.writeframes(struct.pack(f'<{len(pcm_data)}h', *pcm_data))

        print(f"[BGM] Ambient WAV oluşturuldu: {wav_path}")
        return wav_path

    except ImportError:
        print("[BGM] numpy bulunamadı, ambient ton üretilemiyor.")
        return None
    except Exception as e:
        print(f"[BGM] Ambient ton üretme hatası: {e}")
        return None


def _fetch_jamendo_music(query: str, tone_filename: str) -> str | None:
    """Jamendo API'sinden telifsiz müzik indirir (API key gerektirmez, client_id public)."""
    try:
        print(f"[BGM] Jamendo'dan müzik aranıyor: '{query}'")
        # Jamendo public demo client_id (sadece demo amaçlı, kayıtsız kullanım)
        url = "https://api.jamendo.com/v3.0/tracks/"
        params = {
            "client_id": "b6747d04",  # Jamendo demo public client_id
            "format": "json",
            "limit": 10,
            "search": query,
            "audioformat": "mp32",
            "include": "musicinfo",
            "ccsa": "true",           # Creative Commons Share-Alike lisanslılar
        }
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[BGM] Jamendo API hatası: {resp.status_code}")
            return None

        data = resp.json()
        results = data.get("results", [])
        if not results:
            print(f"[BGM] Jamendo'da '{query}' için sonuç bulunamadı.")
            return None

        track = random.choice(results[:5])
        audio_url = track.get("audio") or track.get("audiodownload")
        if not audio_url:
            print("[BGM] Jamendo ses URL'si boş.")
            return None

        os.makedirs(BGM_DIR, exist_ok=True)
        output_path = os.path.join(BGM_DIR, tone_filename)

        print(f"[BGM] İndiriliyor ({track.get('name', '?')}): {audio_url[:80]}...")
        music_resp = requests.get(audio_url, timeout=45, stream=True)
        if music_resp.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in music_resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            if os.path.getsize(output_path) > 10240:  # En az 10KB
                print(f"[BGM] Müzik kaydedildi: {output_path} ({track.get('name', '?')})")
                return output_path
            else:
                print("[BGM] İndirilen dosya çok küçük, geçersiz.")
                os.remove(output_path)
                return None
        else:
            print(f"[BGM] Jamendo indirme hatası: {music_resp.status_code}")
            return None

    except Exception as e:
        print(f"[BGM] Jamendo müzik hatası: {e}")
        return None


def get_bgm_path(tone: str = "auto") -> str | None:
    """
    Verilen tona uygun bir BGM dosyası yolu döndürür.
    
    Öncelik sırası:
    1. Yerel assets/bgm/ dizininde hazır dosya
    2. Jamendo API'sinden indir (telifsiz, ücretsiz)
    3. Numpy ile ambient ton üret (internet olmasa da çalışır)
    4. None (BGM olmadan devam et)
    """
    tone_key = _normalize_tone(tone)
    query = TONE_TO_QUERY.get(tone_key, TONE_TO_QUERY["auto"])
    tone_filename = TONE_TO_FILENAME.get(tone_key, "calm.mp3")

    # 1. Önce yerel dosya
    local = _get_local_bgm(tone_key)
    if local:
        return local

    # 2. Jamendo API dene
    jamendo_path = _fetch_jamendo_music(query, tone_filename)
    if jamendo_path:
        return jamendo_path

    # 3. Fallback: numpy ile ambient ton üret
    print("[BGM] Online müzik alınamadı, yerel ambient ton üretiliyor...")
    os.makedirs(BGM_DIR, exist_ok=True)
    fallback_path = os.path.join(BGM_DIR, tone_filename.replace(".mp3", "_generated.wav"))
    generated = _generate_ambient_tone(fallback_path, tone_key)
    if generated:
        return generated

    print("[BGM] BGM eklenemiyor, video müziksiz devam edecek.")
    return None


if __name__ == "__main__":
    # Test
    path = get_bgm_path("dramatik")
    print(f"BGM yolu: {path}")
