import os
import random
from moviepy import AudioFileClip

class SFXManager:
    def __init__(self, sfx_dir="assets/sfx"):
        self.sfx_dir = sfx_dir
        os.makedirs(self.sfx_dir, exist_ok=True)
        
        # Eğer sfx klasörü boşsa, matematiksel olarak ses üret
        self._ensure_default_sfx()
        
        # Kategorize edilmiş efektler (Dosya isimleri bu kelimeleri içeriyorsa otomatik tanınır)
        self.categories = {
            "transition": ["whoosh", "swoosh", "whip", "transition", "pass"],
            "hook": ["boom", "impact", "dramatic", "hit", "bass"],
            "pop": ["pop", "click", "bubble", "ding"]
        }
        
    def generate_sfx_elevenlabs(self, prompt, output_filename, duration_seconds=1.0):
        """ElevenLabs Sound Effects API'sini kullanarak ses üretir."""
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not api_key:
            return False
            
        url = "https://api.elevenlabs.io/v1/sound-generation"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        data = {
            "text": prompt,
            "duration_seconds": duration_seconds,
            "prompt_influence": 0.3
        }
        
        try:
            import requests
            resp = requests.post(url, json=data, headers=headers, timeout=30)
            if resp.status_code == 200:
                with open(output_filename, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                print(f"[-] ElevenLabs SFX API hatası: {resp.status_code}")
                return False
        except Exception as e:
            print(f"[-] ElevenLabs SFX istek hatası: {e}")
            return False

    def _ensure_default_sfx(self):
        """Klasör boşsa önce ElevenLabs ile, başarısız olursa NumPy ile ses üretir."""
        files = os.listdir(self.sfx_dir)
        has_audio = any(f.endswith(('.mp3', '.wav', '.ogg')) for f in files)
        
        if not has_audio:
            # Önce ElevenLabs SFX API dene
            api_key = os.environ.get("ELEVENLABS_API_KEY")
            if api_key:
                print("[SFX] Klasör boş. ElevenLabs AI ile premium ses efektleri üretiliyor...")
                boom_success = self.generate_sfx_elevenlabs(
                    "A deep, cinematic bass boom impact sound, heavy and dramatic",
                    os.path.join(self.sfx_dir, "elevenlabs_boom.mp3"),
                    duration_seconds=1.5
                )
                whoosh_success = self.generate_sfx_elevenlabs(
                    "A fast, cinematic wind swoosh transition sound effect",
                    os.path.join(self.sfx_dir, "elevenlabs_whoosh.mp3"),
                    duration_seconds=1.0
                )
                
                if boom_success or whoosh_success:
                    print("[SFX] ElevenLabs AI sesleri başarıyla oluşturuldu!")
                    return

            print("[SFX] ElevenLabs kullanılamadı. Matematiksel yedek (NumPy) sentezleyici devreye giriyor...")
            try:
                import numpy as np
                import wave
                
                def save_wav(filename, data, sr=44100):
                    data = np.clip(data, -1.0, 1.0)
                    audio_data = np.int16(data * 32767)
                    with wave.open(filename, 'w') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)
                        wav_file.setframerate(sr)
                        wav_file.writeframes(audio_data.tobytes())
                
                sr = 44100
                
                # --- 1. Whoosh Efekti ---
                t = np.linspace(0, 0.8, int(sr * 0.8), False)
                noise = np.random.normal(0, 1, len(t))
                envelope = (t / 0.2) * (t <= 0.2) + np.exp(-(t - 0.2) * 5) * (t > 0.2)
                whoosh = noise * envelope
                # Basit Low-pass filter ile rüzgar hissiyatı
                whoosh_filtered = np.zeros_like(whoosh)
                for i in range(1, len(whoosh)):
                    whoosh_filtered[i] = whoosh_filtered[i-1] * 0.85 + whoosh[i] * 0.15
                whoosh_filtered = whoosh_filtered / np.max(np.abs(whoosh_filtered))
                save_wav(os.path.join(self.sfx_dir, "synthetic_whoosh.wav"), whoosh_filtered)
                
                # --- 2. Boom/Impact Efekti ---
                t = np.linspace(0, 1.5, int(sr * 1.5), False)
                # Frekans hızlıca 150Hz'den 30Hz'e düşer (Pitch drop)
                freqs = 30 + 120 * np.exp(-t * 8)
                phase = np.cumsum(freqs) * 2 * np.pi / sr
                boom = np.sin(phase)
                # Çarpma hissi için başlangıca distorsiyon/gürültü ekle
                impact_noise = np.random.normal(0, 1, len(t)) * np.exp(-t * 20)
                boom = boom + impact_noise * 0.5
                envelope = np.exp(-t * 3)
                boom = boom * envelope
                boom = boom / np.max(np.abs(boom))
                save_wav(os.path.join(self.sfx_dir, "synthetic_boom.wav"), boom)
                
                print("[SFX] Sentezlenen sesler 'assets/sfx' klasörüne kaydedildi!")
            except ImportError:
                print("[SFX] Numpy bulunamadı, otomatik ses üretimi atlandı.")
            except Exception as e:
                print(f"[SFX] Ses üretilirken hata: {e}")
        
    def get_sfx_path(self, category):
        """Kategoriye uygun rastgele bir ses dosyasının yolunu bulur."""
        if not os.path.exists(self.sfx_dir):
            return None
            
        valid_files = []
        keywords = self.categories.get(category, [category])
        
        for file in os.listdir(self.sfx_dir):
            if file.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                name_lower = file.lower()
                for kw in keywords:
                    if kw in name_lower:
                        valid_files.append(os.path.join(self.sfx_dir, file))
                        break
                        
        if valid_files:
            return random.choice(valid_files)
            
        return None
        
    def get_clip(self, category, start_time, volume=0.5):
        """İstenen kategoride AudioFileClip oluşturur ve zaman/ses ayarlar."""
        path = self.get_sfx_path(category)
        if not path:
            return None
            
        try:
            clip = AudioFileClip(path)
            
            if hasattr(clip, 'with_start'):
                clip = clip.with_start(start_time)
            elif hasattr(clip, 'set_start'):
                clip = clip.set_start(start_time)
                
            if hasattr(clip, 'with_volume_scaled'):
                clip = clip.with_volume_scaled(volume)
            elif hasattr(clip, 'volumex'):
                clip = clip.volumex(volume)
                
            return clip
        except Exception as e:
            print(f"[SFX] {path} yüklenemedi: {e}")
            return None

sfx_manager = SFXManager()
