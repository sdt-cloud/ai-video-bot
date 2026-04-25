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
- İLK SAHNE (ilk 3 saniye) videonun HOOK (kanca) kısmı olmalıdır. İzleyiciyi anında yakalayacak, 'Bunu biliyor muydunuz?' veya 'İşte %99 insanın bilmediği gerçek...' tarzı çok çarpıcı bir cümle ile başla.
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

# Dil bazlı system prompt'lar
SYSTEM_PROMPTS = {
    "tr": SYSTEM_PROMPT,
    "en": """
You are a YouTube Shorts and Instagram Reels content creator.
You will write an extremely engaging, informative {duration}-second video script about the given topic.
MANDATORY RULES:
- The FIRST SCENE (first 3 seconds) must be the HOOK. Start with an extremely catchy sentence like 'Did you know?' or 'Here is a fact 99% of people don\\'t know...' to immediately grab the viewer's attention.
- Total narration word count MUST be AT LEAST {min_words} words.
- Generate at least {min_scenes} scenes.
- Each scene's narration must be 1-2 sentences and must NOT repeat a previous scene.
- Do NOT produce short text; write enough content to fill the target duration.
Each sentence or sentence group should have an 'image_prompt' describing the visual for that scene.
Image prompts must ALWAYS be written in ENGLISH (AI image tools work better in English).
Add terms like realistic, cinematic, or high-quality. Narrations must be in ENGLISH.

Return ONLY a JSON object (containing a 'scenes' list) as shown below.
Do NOT add any explanation or markdown, return only raw JSON:
{
  "scenes": [
    {
        "narration": "The coldest place in the universe is not in Antarctica, but in the Boomerang Nebula, 5000 light-years away from us.",
        "image_prompt": "A cinematic hyperrealistic image of a freezing cold nebula in deep space glowing slowly, dark space background, 8k resolution"
    }
  ]
}
""",
    "es": """
Eres un creador de contenido de YouTube Shorts e Instagram Reels.
Escribirás un guion de video extremadamente atractivo e informativo de {duration} segundos sobre el tema dado.
REGLAS OBLIGATORIAS:
- La PRIMERA ESCENA (los primeros 3 segundos) debe ser el GANCHO (hook). Comienza con una frase extremadamente llamativa como '¿Sabías que...?' o 'Aquí hay un hecho que el 99% de las personas no sabe...' para captar inmediatamente la atención.
- El número total de palabras de narración DEBE ser AL MENOS {min_words} palabras.
- Genera al menos {min_scenes} escenas.
- La narración de cada escena debe tener 1-2 oraciones y NO debe repetir una escena anterior.
- NO produzcas texto corto; escribe suficiente contenido para llenar la duración objetivo.
Cada oración o grupo de oraciones debe tener un 'image_prompt' que describa el visual de esa escena.
Los image prompts deben SIEMPRE estar escritos en INGLÉS (las herramientas de IA funcionan mejor en inglés).
Añade términos como realista, cinematográfico o alta calidad. Las narraciones deben ser en ESPAÑOL.

Devuelve SOLO un objeto JSON (que contenga una lista 'scenes') como se muestra a continuación.
NO agregues ninguna explicación o markdown, devuelve solo JSON puro:
{
  "scenes": [
    {
        "narration": "El lugar más frío del universo no está en la Antártida, sino en la Nebulosa Boomerang, a 5000 años luz de nosotros.",
        "image_prompt": "A cinematic hyperrealistic image of a freezing cold nebula in deep space glowing slowly, dark space background, 8k resolution"
    }
  ]
}
""",
}

# Dil bazlı user prompt şablonları
USER_PROMPTS = {
    "tr": "Lütfen şu konuda ilginç ve tam olarak {duration} saniye sürecek bir senaryo yaz: {topic}. Toplam narration metni en az {min_words} kelime ve en az {min_scenes} sahne olsun.",
    "en": "Please write an interesting script about the following topic that will last exactly {duration} seconds: {topic}. Total narration text must be at least {min_words} words and at least {min_scenes} scenes.",
    "es": "Por favor, escribe un guion interesante sobre el siguiente tema que dure exactamente {duration} segundos: {topic}. El texto de narración total debe tener al menos {min_words} palabras y al menos {min_scenes} escenas.",
}

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


def _build_system_prompt(duration: int, min_words: int, min_scenes: int, language: str = "tr") -> str:
    template = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["tr"])
    return (
        template
        .replace("{duration}", str(duration))
        .replace("{min_words}", str(min_words))
        .replace("{min_scenes}", str(min_scenes))
    )


def _build_user_prompt(topic: str, duration: int, min_words: int, min_scenes: int, extra_instructions: str = "", language: str = "tr") -> str:
    template = USER_PROMPTS.get(language, USER_PROMPTS["tr"])
    prompt = (
        template
        .replace("{topic}", topic)
        .replace("{duration}", str(duration))
        .replace("{min_words}", str(min_words))
        .replace("{min_scenes}", str(min_scenes))
    )
    if extra_instructions:
        prompt += f"\nAdditional instruction: {extra_instructions}"
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


def _clean_json_response(raw_content: str) -> str:
    """Model yanıtındaki markdown codeblock sarmalayıcılarını temizler."""
    content = raw_content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines)
    return content


def _split_custom_script_to_narrations(custom_script: str, target_scene_count: int) -> list[str]:
    """Kullanıcının script metnini sahnelere böl."""
    raw_lines = [line.strip() for line in custom_script.replace("\r", "").split("\n") if line.strip()]
    if len(raw_lines) >= 3:
        return raw_lines

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", custom_script.strip()) if s.strip()]
    if not sentences:
        return [custom_script.strip()]

    total_words = sum(_count_words(s) for s in sentences)
    target_scene_count = max(3, target_scene_count)
    target_words_per_scene = max(10, int(total_words / target_scene_count))

    chunks = []
    buffer = []
    buffer_words = 0
    for sentence in sentences:
        sentence_words = _count_words(sentence)
        if buffer and (buffer_words + sentence_words > target_words_per_scene):
            chunks.append(" ".join(buffer).strip())
            buffer = [sentence]
            buffer_words = sentence_words
        else:
            buffer.append(sentence)
            buffer_words += sentence_words

    if buffer:
        chunks.append(" ".join(buffer).strip())

    return [c for c in chunks if c]


def _select_gemini_model(ai_provider: str) -> str:
    provider_lower = ai_provider.lower()
    if "3.1-flash" in provider_lower or "3.1 flash" in provider_lower:
        return "gemini-2.5-flash"
    return "gemini-2.5-pro"


def _generate_image_prompts_openai(topic: str, narrations: list[str]) -> list[str]:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    list_text = "\n".join([f"{i+1}. {n}" for i, n in enumerate(narrations)])
    system_prompt = (
        "You generate English image prompts for video scenes. "
        "Return JSON only with this schema: {\"prompts\": [{\"image_prompt\": \"...\"}]}"
    )
    user_prompt = (
        f"Topic: {topic}\n"
        f"Generate exactly {len(narrations)} cinematic, high-detail image prompts for these narrations. "
        "Each prompt must be English and visual-only (no on-screen text).\n"
        f"Narrations:\n{list_text}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    content = _clean_json_response(response.choices[0].message.content)
    data = json.loads(content)
    prompts = data.get("prompts", [])
    return [p.get("image_prompt", "") for p in prompts if isinstance(p, dict)]


def _generate_image_prompts_gemini(topic: str, narrations: list[str], model_name: str) -> list[str]:
    try:
        import google.genai as genai
    except ImportError:
        import google.generativeai as genai

    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel(model_name)
    list_text = "\n".join([f"{i+1}. {n}" for i, n in enumerate(narrations)])
    prompt = (
        "You generate English image prompts for video scenes. "
        "Return only valid JSON with schema {\"prompts\": [{\"image_prompt\": \"...\"}]}.\n"
        f"Topic: {topic}\n"
        f"Generate exactly {len(narrations)} prompts, one per narration. "
        "Prompts must be cinematic, visual-only, no text overlays.\n"
        f"Narrations:\n{list_text}"
    )
    response = model.generate_content(prompt)
    content = _clean_json_response(response.text)
    data = json.loads(content)
    prompts = data.get("prompts", [])
    return [p.get("image_prompt", "") for p in prompts if isinstance(p, dict)]


def _build_fallback_image_prompt(topic: str, narration: str) -> str:
    short = narration.strip()[:140]
    return (
        f"A cinematic, highly detailed scene about {topic}, illustrating: {short}, "
        "dramatic lighting, realistic composition, 9:16 portrait frame, 8k"
    )


def generate_script_from_custom_text(topic, custom_script, ai_provider="Gemini", duration=30):
    """Kullanıcının yazdığı script'i koruyup sadece sahne/görsel promptlarını hazırlar."""
    print(f"[+] Özel script işleniyor... (AI: {ai_provider})")
    try:
        cleaned_script = (custom_script or "").strip()
        if not cleaned_script:
            return None

        target_scenes = _calculate_min_scenes(duration)
        narrations = _split_custom_script_to_narrations(cleaned_script, target_scenes)
        narrations = [n for n in narrations if n.strip()]
        if not narrations:
            return None

        image_prompts = []
        provider_lower = ai_provider.lower()
        try:
            if "openai" in provider_lower or "gpt" in provider_lower:
                image_prompts = _generate_image_prompts_openai(topic, narrations)
            else:
                image_prompts = _generate_image_prompts_gemini(topic, narrations, _select_gemini_model(ai_provider))
        except Exception as prompt_error:
            logger.warning(f"Özel script için image_prompt üretimi AI ile başarısız oldu, fallback kullanılacak: {prompt_error}")

        scenes = []
        for i, narration in enumerate(narrations):
            image_prompt = ""
            if i < len(image_prompts):
                image_prompt = (image_prompts[i] or "").strip()
            if not image_prompt:
                image_prompt = _build_fallback_image_prompt(topic, narration)

            scenes.append({
                "narration": narration,
                "image_prompt": image_prompt,
            })

        script_data = {
            "scenes": scenes,
            "_meta": {
                "source": "custom_script",
                "target_duration_seconds": duration,
                "word_count": _count_words(cleaned_script),
            },
        }

        print(f"[+] Özel script sahnelere dönüştürüldü! ({len(scenes)} sahne)")
        return script_data
    except Exception as e:
        print(f"[-] Özel script işlenirken hata oluştu: {e}")
        return None

def generate_script_openai(topic, duration=30, min_words=60, min_scenes=3, extra_instructions="", language="tr"):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    formatted_system_prompt = _build_system_prompt(duration, min_words, min_scenes, language)
    user_prompt = _build_user_prompt(topic, duration, min_words, min_scenes, extra_instructions, language)
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": formatted_system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def generate_script_gemini(topic, model_name="gemini-2.5-pro", duration=30, min_words=60, min_scenes=3, extra_instructions="", language="tr"):
    try:
        import google.genai as genai
    except ImportError:
        import google.generativeai as genai
    
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel(model_name)
    
    formatted_system_prompt = _build_system_prompt(duration, min_words, min_scenes, language)
    prompt = formatted_system_prompt + "\n\n" + _build_user_prompt(topic, duration, min_words, min_scenes, extra_instructions, language)
    
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

def generate_script(topic, ai_provider="Gemini", duration=30, language="tr"):
    lang_name = {"tr": "Türkçe", "en": "English", "es": "Español"}.get(language, language)
    print(f"[+] '{topic}' konusu için {duration} saniyelik {lang_name} senaryo üretiliyor... (AI: {ai_provider})")
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
                        language=language,
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
                            language=language,
                        )
                    else:
                        raise
            elif "3.1-flash" in provider_lower or "3.1 flash" in provider_lower:
                raw_content = generate_script_gemini(
                    topic,
                    model_name="gemini-2.5-flash",
                    duration=duration,
                    min_words=min_words,
                    min_scenes=min_scenes,
                    extra_instructions=extra_instructions,
                    language=language,
                )
            elif "3.1-pro" in provider_lower or "3.1 pro" in provider_lower:
                raw_content = generate_script_gemini(
                    topic,
                    model_name="gemini-2.5-pro",
                    duration=duration,
                    min_words=min_words,
                    min_scenes=min_scenes,
                    extra_instructions=extra_instructions,
                    language=language,
                )
            else:
                raw_content = generate_script_gemini(
                    topic,
                    model_name="gemini-2.5-pro",
                    duration=duration,
                    min_words=min_words,
                    min_scenes=min_scenes,
                    extra_instructions=extra_instructions,
                    language=language,
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
