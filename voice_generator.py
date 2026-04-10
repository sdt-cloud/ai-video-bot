import edge_tts
import os
import asyncio
import re
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests

load_dotenv()

# Session for ElevenLabs API with connection pooling
_elevenlabs_session = None

def get_elevenlabs_session():
    """ElevenLabs API için connection pooling session"""
    global _elevenlabs_session
    if _elevenlabs_session is None:
        _elevenlabs_session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=5,
            pool_maxsize=10
        )
        
        _elevenlabs_session.mount("https://", adapter)
    
    return _elevenlabs_session

# Ses seçenekleri - Edge TTS
EDGE_TTS_VOICES = {
    "erkek": "tr-TR-AhmetNeural",
    "kadin": "tr-TR-EmelNeural",
    "cocuk": "tr-TR-EmelNeural",  # Çocuk sesi için Emel kullan (daha yumuşak)
    "dramatik": "tr-TR-AhmetNeural",
    "gulucu": "tr-TR-EmelNeural",
    "profesyonel": "tr-TR-AhmetNeural",
    "sakin": "tr-TR-EmelNeural",
}

# Varsayılan ses
DEFAULT_VOICE = EDGE_TTS_VOICES["erkek"]

# Edge-TTS otomatik hız ayarı için temel değerler
EDGE_BASE_WPM = int(os.environ.get("EDGE_BASE_WPM", "145"))
EDGE_RATE_MIN_PERCENT = int(os.environ.get("EDGE_RATE_MIN_PERCENT", "-35"))
EDGE_RATE_MAX_PERCENT = int(os.environ.get("EDGE_RATE_MAX_PERCENT", "40"))

# ElevenLabs Türkçe ses seçenekleri - Free Tier erişilebilir sesler
TURKISH_VOICES = {
    "erkek": "pNInz6obpgDQGcFmaJgB",      # Adam - Multilingual
    "kadin": "XrExE9yKIg1WjnnlVkGX",      # Matilda - Multilingual (kadın)
    "cocuk": "TX3LPQmX4UJuhhS52t",        # Domi - Multilingual
    "dramatik": "ZQe5CxyNwgrlbJ1iI0zB",   # Lewis - Dramatik erkek
    "gulucu": "XrExE9yKIg1WjnnlVkGX",     # Matilda - Neşeli kadın
    "profesyonel": "pNInz6obpgDQGcFmaJgB", # Adam - Profesyonel erkek
    "sakin": "JBFqnCBsd6RMkjVDRZzb",      # Daniel - Sakin erkek
}


def _count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def _calculate_edge_rate(text: str, target_duration_seconds: int) -> str:
    """Hedef süreye göre Edge rate değeri üretir (örn: +12% / -8%)."""
    if target_duration_seconds <= 0:
        return "+0%"

    words = _count_words(text)
    if words == 0:
        return "+0%"

    target_wpm = words / (target_duration_seconds / 60)
    rate_percent = int(round(((target_wpm / EDGE_BASE_WPM) - 1) * 100))
    rate_percent = max(EDGE_RATE_MIN_PERCENT, min(EDGE_RATE_MAX_PERCENT, rate_percent))

    sign = "+" if rate_percent >= 0 else ""
    return f"{sign}{rate_percent}%"

def generate_voice_elevenlabs(text, output_filename, voice_type="erkek"):
    print(f"[+] '{output_filename}' için ses sentezleniyor (AI: ElevenLabs)...")
    try:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            print("[-] ELEVENLABS_API_KEY bulunamadı!")
            return False
            
        # Ses tipine göre voice ID'si seç
        voice_id = TURKISH_VOICES.get(voice_type, TURKISH_VOICES["erkek"])
        print(f"[+] Ses tipi: {voice_type} (Voice ID: {voice_id})")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            }
        }
        
        # Session kullanarak istek gönder
        session = get_elevenlabs_session()
        response = session.post(url, json=data, headers=headers, timeout=60)
        
        if response.status_code == 200:
            with open(output_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"[+] Ses dosyası kaydedildi: {output_filename}")
            return True
        else:
            print(f"[-] ElevenLabs Hatası: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"[-] Ses üretilirken hata oluştu: {e}")
        return False

async def generate_voice_edge(text, output_filename, voice_type="erkek", target_duration_seconds=None):
    print(f"[+] '{output_filename}' için ses sentezleniyor (Edge-TTS)...")
    try:
        # Ses tipine göre voice seç
        voice = EDGE_TTS_VOICES.get(voice_type, DEFAULT_VOICE)
        print(f"[+] Edge-TTS ses tipi: {voice_type} (Voice: {voice})")

        rate = "+0%"
        if target_duration_seconds is not None:
            rate = _calculate_edge_rate(text, int(target_duration_seconds))
            print(f"[i] Otomatik TTS hızı: hedef {target_duration_seconds} sn için rate={rate}")
        
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(output_filename)
        print(f"[+] Ses dosyası kaydedildi: {output_filename}")
        return True
    except Exception as e:
        print(f"[-] Ses üretilirken hata oluştu: {e}")
        return False

async def generate_voice_async(text, output_filename, ai_provider="Edge-TTS", voice_type="erkek", target_duration_seconds=None):
    """Async ortamdan (FastAPI gibi) çağrılacak versiyon."""
    if "elevenlabs" in ai_provider.lower():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, generate_voice_elevenlabs, text, output_filename, voice_type)
    else:
        return await generate_voice_edge(text, output_filename, voice_type, target_duration_seconds)

def generate_voice(text, output_filename, ai_provider="Edge-TTS", voice_type="erkek", target_duration_seconds=None):
    """Senkron ortamdan çağrılacak versiyon (test için)."""
    if "elevenlabs" in ai_provider.lower():
        return generate_voice_elevenlabs(text, output_filename, voice_type)
    else:
        return asyncio.run(generate_voice_edge(text, output_filename, voice_type, target_duration_seconds))

if __name__ == "__main__":
    test_text = "Dünya sadece bir kum tanesi mi yoksa sonsuz bir okyanus mu?"
    generate_voice(test_text, "test_voice.mp3", ai_provider="ElevenLabs")
