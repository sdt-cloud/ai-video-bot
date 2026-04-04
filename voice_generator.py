import edge_tts
import os

# Ses seçenekleri (Örn: tr-TR-AhmetNeural, tr-TR-EmelNeural)
VOICE = "tr-TR-AhmetNeural"

async def generate_voice_async(text, output_filename):
    """Async ortamdan (FastAPI gibi) çağrılacak versiyon."""
    print(f"[+] '{output_filename}' için ses sentezleniyor (Edge-TTS)...")
    try:
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(output_filename)
        print(f"[+] Ses dosyası kaydedildi: {output_filename}")
        return True
    except Exception as e:
        print(f"[-] Ses üretilirken hata oluştu: {e}")
        return False

def generate_voice(text, output_filename):
    """Senkron ortamdan çağrılacak versiyon (test için)."""
    import asyncio
    print(f"[+] '{output_filename}' için ses sentezleniyor (Edge-TTS)...")
    try:
        asyncio.run(edge_tts.Communicate(text, VOICE).save(output_filename))
        print(f"[+] Ses dosyası kaydedildi: {output_filename}")
        return True
    except Exception as e:
        print(f"[-] Ses üretilirken hata oluştu: {e}")
        return False

if __name__ == "__main__":
    test_text = "Dünya sadece bir kum tanesi mi yoksa sonsuz bir okyanus mu?"
    generate_voice(test_text, "test_voice.mp3")
