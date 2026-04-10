import os
import json
import logging
import re
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
Sen bir YouTube Shorts ve Instagram Reels içerik üreticisisin.
Verilen konu hakkında aşırı ilgi çekici, bilgilendirici, {duration} saniyelik bir video senaryosu yazacaksın.
ZORUNLU KURALLAR:
- Toplam narration kelime sayısı EN AZ {min_words} kelime olmalıdır.
- En az {min_scenes} sahne üret.
- Her sahnede narration metni 1-2 cümle olmalı ve bir önceki sahneyi tekrar etmemeli.
- Kısa metin üretme, hedef süreyi dolduracak içerik yaz.
Her cümlenin veya cümle grubunun ekranda kalma süresinde gösterilecek bir 'görsel promptu (image_prompt)' olmalıdır.
Image prompt'lar her zaman İNGİLİZCE yazılmalıdır çünkü yapay zeka resim araçları İngilizce daha iyi anlar. 
Gerçekçi, sinematik veya yüksek kaliteli gibi terimler ekle. Metinler ise TÜRKÇE olacaktır.

Cevabını sadece ve sadece aşağıdaki gibi bir JSON objesi ('scenes' listesi içeren) formatında döndür.
Başka hiçbir açıklama veya markdown ekleme, sadece saf JSON döndür:
{
  "scenes": [
    {
        "narration": "Evrenin en soğuk yeri Antarktika'da değil, bizden 5000 ışık yılı uzaktaki Bumerang Bulutsusu'dur.",
        "image_prompt": "A cinematic hyperrealistic image of a freezing cold nebula in deep space glowing slowly, dark space background, 8k resolution"
    }
  ]
}
"""

# Konuşma hızına göre minimum metin uzunluğu kontrolü.
# .env üzerinden SCRIPT_MIN_WORDS_PER_MINUTE ile değiştirilebilir.
MIN_WORDS_PER_MINUTE = int(os.environ.get("SCRIPT_MIN_WORDS_PER_MINUTE", "120"))
MAX_SCRIPT_RETRIES = 3


def _count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))


def _calculate_min_words(duration_seconds: int) -> int:
    return max(30, int((duration_seconds / 60) * MIN_WORDS_PER_MINUTE))


def _calculate_min_scenes(duration_seconds: int) -> int:
    # Ortalama 12-15 saniye/sahne temposu
    return max(3, int(duration_seconds / 15))


def _build_system_prompt(duration: int, min_words: int, min_scenes: int) -> str:
    return (
        SYSTEM_PROMPT
        .replace("{duration}", str(duration))
        .replace("{min_words}", str(min_words))
        .replace("{min_scenes}", str(min_scenes))
    )


def _build_user_prompt(topic: str, duration: int, min_words: int, min_scenes: int, extra_instructions: str = "") -> str:
    prompt = (
        f"Lütfen şu konuda ilginç ve tam olarak {duration} saniye sürecek bir senaryo yaz: {topic}. "
        f"Toplam narration metni en az {min_words} kelime ve en az {min_scenes} sahne olsun."
    )
    if extra_instructions:
        prompt += f"\nEk düzeltme talimatı: {extra_instructions}"
    return prompt


def _script_stats(script_data: dict) -> dict:
    scenes = script_data.get("scenes", [])
    if not isinstance(scenes, list):
        scenes = []

    narrations = [scene.get("narration", "") for scene in scenes if isinstance(scene, dict)]
    full_text = " ".join([n for n in narrations if isinstance(n, str)])
    word_count = _count_words(full_text)
    estimated_seconds = int((word_count / MIN_WORDS_PER_MINUTE) * 60) if word_count > 0 else 0

    return {
        "scene_count": len(scenes),
        "word_count": word_count,
        "estimated_seconds": estimated_seconds,
    }

def generate_script_openai(topic, duration=30, min_words=60, min_scenes=3, extra_instructions=""):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    formatted_system_prompt = _build_system_prompt(duration, min_words, min_scenes)
    user_prompt = _build_user_prompt(topic, duration, min_words, min_scenes, extra_instructions)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": formatted_system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def generate_script_gemini(topic, model_name="gemini-2.5-pro", duration=30, min_words=60, min_scenes=3, extra_instructions=""):
    try:
        import google.genai as genai
    except ImportError:
        # Yeni paket yüklü değilse eski paketi kullan
        import google.generativeai as genai
    
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel(model_name)
    
    formatted_system_prompt = _build_system_prompt(duration, min_words, min_scenes)
    prompt = formatted_system_prompt + "\n\n" + _build_user_prompt(topic, duration, min_words, min_scenes, extra_instructions)
    
    response = model.generate_content(prompt)
    return response.text

def _is_openai_quota_or_rate_error(error: Exception) -> bool:
    """OpenAI kota/rate-limit hatalarını tespit eder (429 ve insufficient_quota)."""
    text = str(error).lower()
    status_code = getattr(error, "status_code", None)

    return (
        status_code == 429
        or "insufficient_quota" in text
        or "429" in text
        or "rate limit" in text
        or "quota" in text
    )

def generate_script(topic, ai_provider="Gemini", duration=30):
    print(f"[+] '{topic}' konusu için {duration} saniyelik senaryo üretiliyor... (AI: {ai_provider})")
    min_words = _calculate_min_words(duration)
    min_scenes = _calculate_min_scenes(duration)
    print(f"[i] Minimum senaryo hedefi: {min_words} kelime, {min_scenes} sahne (min {MIN_WORDS_PER_MINUTE} kelime/dk)")
    
    try:
        fallback_provider = None
        extra_instructions = ""
        last_valid_script = None

        for attempt in range(1, MAX_SCRIPT_RETRIES + 1):
            provider_lower = ai_provider.lower()
            if "openai" in provider_lower or "gpt" in provider_lower:
                try:
                    raw_content = generate_script_openai(
                        topic,
                        duration,
                        min_words=min_words,
                        min_scenes=min_scenes,
                        extra_instructions=extra_instructions,
                    )
                except Exception as openai_error:
                    if _is_openai_quota_or_rate_error(openai_error):
                        print("[!] OpenAI kota/rate-limit hatası alındı. Otomatik olarak Gemini'ye geçiliyor...")
                        logger.warning(f"OpenAI hatası sonrası Gemini fallback devreye girdi: {openai_error}")
                        fallback_provider = "Gemini"
                        raw_content = generate_script_gemini(
                            topic,
                            model_name="gemini-2.5-pro",
                            duration=duration,
                            min_words=min_words,
                            min_scenes=min_scenes,
                            extra_instructions=extra_instructions,
                        )
                    else:
                        raise
            elif "3.1-flash" in provider_lower or "3.1 flash" in provider_lower:
                # Not: Google API'sinde şu an en güncel flaş model 2.5-flash'dir. 3.1 UI ismidir.
                raw_content = generate_script_gemini(
                    topic,
                    model_name="gemini-2.5-flash",
                    duration=duration,
                    min_words=min_words,
                    min_scenes=min_scenes,
                    extra_instructions=extra_instructions,
                )
            elif "3.1-pro" in provider_lower or "3.1 pro" in provider_lower:
                # Not: Google API'sinde şu an en güncel pro model 2.5-pro'dur.
                raw_content = generate_script_gemini(
                    topic,
                    model_name="gemini-2.5-pro",
                    duration=duration,
                    min_words=min_words,
                    min_scenes=min_scenes,
                    extra_instructions=extra_instructions,
                )
            else:
                raw_content = generate_script_gemini(
                    topic,
                    model_name="gemini-2.5-pro",
                    duration=duration,
                    min_words=min_words,
                    min_scenes=min_scenes,
                    extra_instructions=extra_instructions,
                )

            # JSON temizle (bazen ```json ... ``` ile sarılıyor)
            content = raw_content.strip()
            if content.startswith("```"):
                # İlk ve son ``` satırlarını kaldır
                lines = content.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                content = "\n".join(lines)

            try:
                script_data = json.loads(content)
            except json.JSONDecodeError as parse_error:
                if attempt == MAX_SCRIPT_RETRIES:
                    print(f"[-] JSON Parse Hatası: {parse_error}")
                    print(f"    Gelen Yanıt: {raw_content[:300]}")
                    return None

                extra_instructions = (
                    "Yalnızca geçerli JSON döndür. Markdown, açıklama veya başlık ekleme. "
                    "Sadece {\"scenes\":[...]} formatını kullan."
                )
                continue

            stats = _script_stats(script_data)
            last_valid_script = script_data

            if stats["word_count"] >= min_words and stats["scene_count"] >= min_scenes:
                meta = script_data.get("_meta", {})
                if fallback_provider:
                    meta["fallback_provider"] = fallback_provider
                meta["word_count"] = stats["word_count"]
                meta["estimated_duration_seconds"] = stats["estimated_seconds"]
                meta["target_duration_seconds"] = duration
                script_data["_meta"] = meta

                print(
                    f"[+] Senaryo başarıyla üretildi! ({stats['scene_count']} sahne, "
                    f"{stats['word_count']} kelime, tahmini {stats['estimated_seconds']} sn)"
                )
                return script_data

            if attempt < MAX_SCRIPT_RETRIES:
                print(
                    f"[!] Senaryo kısa kaldı (deneme {attempt}/{MAX_SCRIPT_RETRIES}): "
                    f"{stats['word_count']} kelime / {stats['scene_count']} sahne. Yeniden üretiliyor..."
                )
                extra_instructions = (
                    f"Önceki yanıt çok kısaydı ({stats['word_count']} kelime, {stats['scene_count']} sahne). "
                    f"Bu kez narration toplamı en az {min_words} kelime ve sahne sayısı en az {min_scenes} olsun. "
                    "Bilgi yoğunluğunu artır, kısa cümlelerle daha çok sahne ekle."
                )

        # Son denemede de minimumu tutturamazsa en son geçerli script'i yine döndür.
        if last_valid_script:
            stats = _script_stats(last_valid_script)
            meta = last_valid_script.get("_meta", {})
            if fallback_provider:
                meta["fallback_provider"] = fallback_provider
            meta["word_count"] = stats["word_count"]
            meta["estimated_duration_seconds"] = stats["estimated_seconds"]
            meta["target_duration_seconds"] = duration
            meta["length_warning"] = "Script minimum uzunluk hedefini tam karşılamadı."
            last_valid_script["_meta"] = meta

            print(
                f"[!] Senaryo minimum hedefin altında kaldı ancak kullanılabilir: "
                f"{stats['word_count']} kelime, {stats['scene_count']} sahne"
            )
            return last_valid_script

        return None
        
    except json.JSONDecodeError as e:
        print(f"[-] JSON Parse Hatası: {e}")
        print(f"    Gelen Yanıt: {raw_content[:300]}")
        return None
    except Exception as e:
        print(f"[-] Hata oluştu: {e}")
        return None

# Kodu test etmek için
if __name__ == "__main__":
    test_topic = "Piramitlerin yapılışıyla ilgili bilinmeyen 3 sır"
    script = generate_script(test_topic, "Gemini")
    
    if script:
        with open("test_script.json", "w", encoding="utf-8") as f:
            json.dump(script, f, ensure_ascii=False, indent=4)
        print("[+] Başarılı! Senaryo test_script.json dosyasına kaydedildi.")
        print(json.dumps(script, ensure_ascii=False, indent=2))
