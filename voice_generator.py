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

# Ses seçenekleri - Edge TTS (Dil bazlı)
EDGE_TTS_VOICES = {
    "tr": {
        "erkek": "tr-TR-AhmetNeural",
        "kadin": "tr-TR-EmelNeural",
        "cocuk": "tr-TR-EmelNeural",
        "dramatik": "tr-TR-AhmetNeural",
        "gulucu": "tr-TR-EmelNeural",
        "profesyonel": "tr-TR-AhmetNeural",
        "sakin": "tr-TR-EmelNeural",
    },
    "en": {
        "erkek": "en-US-GuyNeural",
        "kadin": "en-US-JennyNeural",
        "cocuk": "en-US-AnaNeural",
        "dramatik": "en-US-GuyNeural",
        "gulucu": "en-US-JennyNeural",
        "profesyonel": "en-US-GuyNeural",
        "sakin": "en-US-JennyNeural",
    },
    "es": {
        "erkek": "es-ES-AlvaroNeural",
        "kadin": "es-ES-ElviraNeural",
        "cocuk": "es-ES-ElviraNeural",
        "dramatik": "es-ES-AlvaroNeural",
        "gulucu": "es-ES-ElviraNeural",
        "profesyonel": "es-ES-AlvaroNeural",
        "sakin": "es-ES-ElviraNeural",
    },
}

# Varsayılan ses
DEFAULT_VOICE = "tr-TR-AhmetNeural"


def _get_edge_voice(voice_type: str = "erkek", language: str = "tr") -> str:
    """Dil ve ses tipine göre uygun Edge TTS sesini döndürür."""
    lang_voices = EDGE_TTS_VOICES.get(language, EDGE_TTS_VOICES["tr"])
    return lang_voices.get(voice_type, lang_voices.get("erkek", DEFAULT_VOICE))

# Edge-TTS otomatik hız ayarı için temel değerler
EDGE_BASE_WPM = int(os.environ.get("EDGE_BASE_WPM", "145"))
EDGE_RATE_MIN_PERCENT = int(os.environ.get("EDGE_RATE_MIN_PERCENT", "-35"))
EDGE_RATE_MAX_PERCENT = int(os.environ.get("EDGE_RATE_MAX_PERCENT", "40"))

# ElevenLabs Türkçe ses seçenekleri - Free Tier erişilebilir sesler
TURKISH_VOICES = {
    "erkek": "HGokgaAG6y586a3fAmcA",      # Kullanıcı tarafından sağlanan erkek ses ID
    "kadin": "TASY7VCrU29rEMoYFTGG",      # Kullanıcı tarafından sağlanan kadın ses ID
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

# ElevenLabs ses tonu presetleri — her mod farklı stability/style değerleri kullanır
ELEVENLABS_VOICE_PRESETS = {
    "dramatik":     {"stability": 0.30, "similarity_boost": 0.85, "style": 0.70},
    "profesyonel":  {"stability": 0.70, "similarity_boost": 0.80, "style": 0.30},
    "enerjik":      {"stability": 0.40, "similarity_boost": 0.75, "style": 0.80},
    "sakin":        {"stability": 0.80, "similarity_boost": 0.70, "style": 0.20},
    "gulucu":       {"stability": 0.35, "similarity_boost": 0.75, "style": 0.90},
    "default":      {"stability": 0.50, "similarity_boost": 0.75, "style": 0.50},
}

def generate_voice_elevenlabs(text, output_filename, voice_type="erkek", voice_tone="default"):
    print(f"[+] '{output_filename}' için ses sentezleniyor (AI: ElevenLabs, ton: {voice_tone})...")
    try:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            print("[-] ELEVENLABS_API_KEY bulunamadı!")
            return False
            
        # Ses tipine göre voice ID'si seç (Doğrudan Voice ID veya preset)
        if len(voice_type) > 15 and voice_type not in TURKISH_VOICES:
            voice_id = voice_type
        else:
            voice_id = TURKISH_VOICES.get(voice_type, TURKISH_VOICES["erkek"])
        print(f"[+] Ses tipi: {voice_type} (Voice ID: {voice_id})")
        
        # Ton preset'ini seç
        preset = ELEVENLABS_VOICE_PRESETS.get(voice_tone, ELEVENLABS_VOICE_PRESETS["default"])
        print(f"[+] Ses tonu preset: {voice_tone} → stability={preset['stability']}, style={preset['style']}")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        voice_settings = {
            "stability": preset["stability"],
            "similarity_boost": preset["similarity_boost"],
        }
        # Style parametresi sadece multilingual_v2'de aktif
        if "style" in preset:
            voice_settings["style"] = preset["style"]
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": voice_settings
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

def _apply_ssml_enhancements(text: str) -> str:
    """
    Edge TTS SSML desteği ile dramatik duraklamalar ve vurgular ekler.
    - '...' → 800ms duraklama
    - '!' → 400ms duraklama
    - '?' → 300ms duraklama  
    - '--' → 500ms duraklama (dramatik geçiş)
    """
    # Üç nokta → uzun dramatik duraklama
    text = text.replace("...", '<break time="800ms"/>')
    # Çift tire → orta duraklama
    text = text.replace("--", '<break time="500ms"/>')
    # Ünlem → kısa duraklama (vurgu sonrası)
    text = re.sub(r'!\s+', '!<break time="400ms"/> ', text)
    # Soru işareti → kısa duraklama
    text = re.sub(r'\?\s+', '?<break time="300ms"/> ', text)
    
    return text


async def generate_voice_edge(text, output_filename, voice_type="erkek", target_duration_seconds=None, language="tr"):
    print(f"[+] '{output_filename}' için ses sentezleniyor (Edge-TTS, dil: {language})...")
    try:
        # Dil ve ses tipine göre voice seç
        voice = _get_edge_voice(voice_type, language)
        print(f"[+] Edge-TTS ses tipi: {voice_type} (Voice: {voice})")

        rate = "+0%"
        if target_duration_seconds is not None:
            rate = _calculate_edge_rate(text, int(target_duration_seconds))
            print(f"[i] Otomatik TTS hızı: hedef {target_duration_seconds} sn için rate={rate}")
        
        # Word boundaries dosya yolunu belirle
        task_id = None
        match = re.search(r'narration_(\d+)\.mp3', output_filename)
        if match:
            task_id = match.group(1)
            
        import json
        from subtitle_sync import generate_voice_and_timestamps_edge
        
        # SSML etiketleri WordBoundary callback'lerini bozduğu için
        # ORİJİNAL metni kullanarak ses ve kelime zamanlamalarını üretiyoruz.
        # Edge-TTS zaten kendi doğal duraklamalarını ekliyor.
        word_boundaries = await generate_voice_and_timestamps_edge(text, voice, rate, output_filename)
        
        if task_id and word_boundaries:
            boundaries_path = f"assets/word_boundaries_{task_id}.json"
            with open(boundaries_path, "w", encoding="utf-8") as bf:
                json.dump(word_boundaries, bf, ensure_ascii=False, indent=4)
            print(f"[+] Kelime zaman damgaları kaydedildi: {boundaries_path} ({len(word_boundaries)} kelime)")
            
        return True
    except Exception as e:
        print(f"[-] Ses üretilirken hata oluştu: {e}")
        # Düz metin ile tekrar dene
        try:
            print("[i] Tekrar deneniyor (basit mod)...")
            voice = _get_edge_voice(voice_type, language)
            rate_val = "+0%"
            if target_duration_seconds is not None:
                rate_val = _calculate_edge_rate(text, int(target_duration_seconds))
            communicate = edge_tts.Communicate(text, voice, rate=rate_val)
            await communicate.save(output_filename)
            print(f"[+] Ses dosyası kaydedildi (fallback): {output_filename}")
            
            # Fallback'te de heuristik kelime zamanlamaları oluştur
            if task_id:
                try:
                    import json
                    from subtitle_sync import generate_heuristic_timestamps
                    from moviepy import AudioFileClip
                    fallback_audio = AudioFileClip(output_filename)
                    audio_dur = fallback_audio.duration
                    fallback_audio.close()
                    heuristic_bounds = generate_heuristic_timestamps(text, audio_dur)
                    boundaries_path = f"assets/word_boundaries_{task_id}.json"
                    with open(boundaries_path, "w", encoding="utf-8") as bf:
                        json.dump(heuristic_bounds, bf, ensure_ascii=False, indent=4)
                    print(f"[+] Heuristik kelime zamanlamaları kaydedildi: {boundaries_path}")
                except Exception as heur_err:
                    print(f"[-] Heuristik zamanlama oluşturulamadı: {heur_err}")
            
            return True
        except Exception as e2:
            print(f"[-] Fallback deneme de başarısız: {e2}")
            return False

async def generate_voice_async(text, output_filename, ai_provider="Edge-TTS", voice_type="erkek", target_duration_seconds=None, sentence_pause=0.0, language="tr"):
    """Çoklu dil destekli async ses üretici."""
    if sentence_pause <= 0.0:
        if "elevenlabs" in ai_provider.lower():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, generate_voice_elevenlabs, text, output_filename, voice_type)
        else:
            return await generate_voice_edge(text, output_filename, voice_type, target_duration_seconds, language)
            
    # --- Cümle Arası Boşluk Mantığı ---
    print(f"[i] Cümle arası {sentence_pause}s boşluk eklenecek. Cümleler ayrılıyor...")
    
    # Basit cümle bölme kalıbı, kısaltmalarda vs ufak hatalar yapabilir ama genel olarak iyi çalışır
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    if not sentences:
        print("[-] Parçalanacak cümle bulunamadı.")
        return False
        
    temp_files = []
    clips = []
    success = True
    
    try:
        from moviepy import AudioFileClip, CompositeAudioClip
        import uuid
        
        current_time = 0.0
        
        # Hedef süre oranını parçalara dağıtmak yerine otomatik hızlandırma kullanmıyoruz
        # (cümle parse ederken tek tek ayarlamak zor, Edge TTS varsayılan rate kullanacak)
        
        for i, sentence in enumerate(sentences):
            tmp_name = f"temp_voice_{uuid.uuid4().hex[:8]}_{i}.mp3"
            temp_files.append(tmp_name)
            
            print(f"[i] Cümle {i+1}/{len(sentences)} sentezleniyor...")
            if "elevenlabs" in ai_provider.lower():
                loop = asyncio.get_event_loop()
                cur_success = await loop.run_in_executor(None, generate_voice_elevenlabs, sentence, tmp_name, voice_type)
                await asyncio.sleep(0.5)
            else:
                cur_success = await generate_voice_edge(sentence, tmp_name, voice_type, None, language)
                
            if not cur_success or not os.path.exists(tmp_name):
                print(f"[-] Hata: {i+1}. cümle üretilemedi.")
                success = False
                break
                
            try:
                # Klibi yükle
                clip = AudioFileClip(tmp_name)
                
                # moviepy v1 ve v2 uyumlulugu icin start time ayarla
                if hasattr(clip, 'with_start'):
                    clip = clip.with_start(current_time)
                elif hasattr(clip, 'set_start'):
                    clip = clip.set_start(current_time)
                    
                clips.append(clip)
                
                # Sonraki klibin baslangic zamanini guncelle
                current_time += clip.duration + sentence_pause
                
            except Exception as clip_err:
                print(f"[-] Klip oluşturma hatası: {clip_err}")
                success = False
                break
                
        if success and clips:
            print("[i] Ses klipsleri birleştiriliyor...")
            final_audio = CompositeAudioClip(clips)
            final_audio.write_audiofile(output_filename, fps=44100, logger=None)
            print(f"[+] Özel boşluklu ses başarıyla oluşturuldu: {output_filename}")
            return True
            
        return False
    except Exception as e:
        print(f"[-] Cümle arası boşluk eklenirken beklenmedik hata: {e}")
        return False
    finally:
        for c in clips:
            try:
                c.close()
            except:
                pass
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception as del_err:
                    print(f"[-] Gecici dosya silinemedi: {f} - {del_err}")

def generate_voice(text, output_filename, ai_provider="Edge-TTS", voice_type="erkek", target_duration_seconds=None, sentence_pause=0.0, language="tr"):
    """Senkron ortamdan çağrılacak versiyon (test için)."""
    return asyncio.run(generate_voice_async(text, output_filename, ai_provider, voice_type, target_duration_seconds, sentence_pause, language))

if __name__ == "__main__":
    test_text = "Dünya sadece bir kum tanesi mi yoksa sonsuz bir okyanus mu?"
    generate_voice(test_text, "test_voice.mp3", ai_provider="ElevenLabs")
