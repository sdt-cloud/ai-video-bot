import edge_tts
import os
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Ses seçenekleri (Örn: tr-TR-AhmetNeural, tr-TR-EmelNeural)
VOICE = "tr-TR-AhmetNeural"

# ElevenLabs Türkçe ses seçenekleri
TURKISH_VOICES = {
    "erkek": "pNInz6obpgDQGcFmaJgB",      # Adam
    "kadin": "pFZgXZQz1YIz16BleZ",      # Bella  
    "cocuk": "TX3LPQmX4UJuhhS52t",      # Domi
    "dramatik": "pNInz6obpgDQGcFmaJgB",     # Adam (dramatik)
    "gulucu": "pFZgXZQz1YIz16BleZ",       # Bella (gülücü)
    "profesyonel": "pNInz6obpgDQGcFmaJgB",    # Adam (profesyonel)
    "sakin": "pFZgXZQz1YIz16BleZ",          # Bella (sakin)
}

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
        
        response = requests.post(url, json=data, headers=headers)
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

async def generate_voice_edge(text, output_filename):
    print(f"[+] '{output_filename}' için ses sentezleniyor (Edge-TTS)...")
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_filename)
        print(f"[+] Ses dosyası kaydedildi: {output_filename}")
        return True
    except Exception as e:
        print(f"[-] Ses üretilirken hata oluştu: {e}")
        return False

async def generate_voice_async(text, output_filename, ai_provider="Edge-TTS", voice_type="erkek"):
    """Async ortamdan (FastAPI gibi) çağrılacak versiyon."""
    if "elevenlabs" in ai_provider.lower():
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, generate_voice_elevenlabs, text, output_filename, voice_type)
    else:
        return await generate_voice_edge(text, output_filename)

def generate_voice(text, output_filename, ai_provider="Edge-TTS", voice_type="erkek"):
    """Senkron ortamdan çağrılacak versiyon (test için)."""
    if "elevenlabs" in ai_provider.lower():
        return generate_voice_elevenlabs(text, output_filename, voice_type)
    else:
        return asyncio.run(generate_voice_edge(text, output_filename))

if __name__ == "__main__":
    test_text = "Dünya sadece bir kum tanesi mi yoksa sonsuz bir okyanus mu?"
    generate_voice(test_text, "test_voice.mp3", ai_provider="ElevenLabs")
