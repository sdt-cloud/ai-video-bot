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
- İLK SAHNE (ilk 3 saniye) videonun HOOK (kanca) kısmı olmalıdır. İzleyiciyi aninda yakalayacak kişisel veya çarpıcı bir giriş yap ("Denedim ve şok oldum", "Sırrı buldum" gibi).
- Hikaye yapısı kullan: Problem → Çatışma → Çözüm. Bilgi aktarımı değil, olay/deneyim anlatımı yap.
- Metin DİLİ: Aşırı doğal, kişisel ve konuşma dilinde olmalı. Ansiklopedik 'beyan'lardan kaçın. "Yani", "hmm", "açıkçası" gibi doğal dolgu kelimeleri ve duraklamalar ("...") kullan.
- Kısa video algoritması dinamik bir yapı sever! GÖRSELLER HER 3-4 SANİYEDE BİR DEĞİŞELİ.
- En az {min_scenes} sahne üret.
- Toplam narration kelime sayısı EN AZ {min_words} kelime olmalıdır.
- Her sahnede narration metni kısa bir cümle olmalı ve bir önceki sahneyi tekrar etmemeli.
- SON SAHNE mutlaka bir Call to Action (CTA) olmalıdır.

GÖRSEL PROMPT KURALLARI:
- Image prompt'lar her zaman İNGİLİZCE yazılmalıdır.
- Her prompt'ta şu terimleri MUTLAKA ekle: "cinematic stock photo, 35mm film, film grain, subtle motion blur, realistic human touch" (Yapay zeka gibi görünmemesi çok önemli).
- Her prompt'a MUTLAKA bir kamera açısı belirt: "close-up", "wide angle", "low angle" gibi
- ART ARDA İKİ SAHNEDE AYNI KAMERA AÇISINI KULLANMA.
- ASLA şunları içerme: blurry, low quality, watermark, text overlay, ugly, deformed, cartoon, illustration
- RENK TUTARLIĞI: TÜM sahnelerdeki görseller AYNI renk paleti ve atmosferde olmalıdır. Her prompt'un sonuna 'style_anchor' metnini MUTLAKA ekle.

Her sahne için bir 'media_type' alanı belirle:
- "image" → normal statik görsel (çoğu sahne bu olmalı)
- "video_clip" → kısa GIF veya video klip (sahnelerin %20-30'u bunu kullanabilir, özellikle aksiyon, hareket veya komik sahnelerde)
Video clip sahneleri için ayrıca bir 'clip_search_query' alanı da ekle (İngilizce, konuyla çok alakalı kısa arama kelimesi, max 4 kelime).

Her sahne için bir 'pacing' alanı belirle:
- "fast" → hızlı tempo (hook, şok bilgiler, heyecan)
- "normal" → normal tempo (açıklama, bilgi aktarma)
- "slow" → yavaş tempo (dramatik an, final, CTA)

Her sahne için bir 'mood' alanı belirle:
- "tense" → gerilimli, karanlık
- "inspiring" → ilham verici, sıcak
- "shocking" → şok edici, dikkat çekici
- "calm" → sakin, huzurlu
- "funny" → komik, eğlenceli

JSON'un en üst seviyesine bir 'style_anchor' alanı ekle. Bu alan TÜM sahnelerin görsel stilini tanımlar.
Style anchor şu kriterleri karşılamalıdır:
1. Konuya özel renk paleti: Konu ile duygusal bağ kuran renkler seç (uzay → koyu lacivert/mor, doğa → yeşil/toprak, teknoloji → neon/siyan)
2. Sinematik üslup: "dark moody cinematic", "warm golden hour", "cool futuristic neon" gibi tutarlı bir atmosfer
3. Aydınlatma: Sahneye uygun ışık tanımı ("dramatic rim lighting", "soft diffused light", "harsh neon glow")
Her image_prompt'un SONUNA bu style_anchor metnini MUTLAKA ekle.

Cevabını sadece ve sadece aşağıdaki gibi bir JSON objesi formatında döndür.
Başka hiçbir açıklama veya markdown ekleme, sadece saf JSON döndür:
{
  "style_anchor": "dark moody cinematic, deep navy and electric purple tones, dramatic rim lighting, atmospheric haze",
  "scenes": [
    {
        "narration": "Evrenin en soğuk yeri Antarktika'da değil, bizden 5000 ışık yılı uzaktaki Bumerang Bulutsusu'dur.",
        "image_prompt": "A cinematic hyperrealistic wide-angle shot of a freezing cold nebula in deep space, glowing blue and purple, dark space background, cinematic lighting, sharp focus, 8k resolution, cinematic stock photo, 35mm film, film grain, subtle motion blur, realistic human touch, dark moody cinematic, deep navy and electric purple tones, dramatic rim lighting, atmospheric haze",
        "media_type": "image",
        "pacing": "fast",
        "mood": "shocking"
    },
    {
        "narration": "Bu bulutsu, eksi 272 derece ile mutlak sıfıra en yakın doğal ortamdır.",
        "image_prompt": "Extreme close-up of frozen ice crystals forming in deep space environment, macro photography, cinematic lighting, 8k, cinematic stock photo, 35mm film, film grain, subtle motion blur, realistic human touch, dark moody cinematic, deep navy and electric purple tones, dramatic rim lighting, atmospheric haze",
        "media_type": "video_clip",
        "clip_search_query": "ice crystals space frozen",
        "pacing": "normal",
        "mood": "tense"
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
- The FIRST SCENE (first 3 seconds) must be the HOOK. Start with a personal, extremely catchy sentence like "I tried this and was shocked" or "Here is the secret I found".
- Use storytelling: Problem -> Conflict -> Solution. Tell an experience or story, do not just state encyclopedic facts.
- TONE: Highly conversational, personal, and natural. Use filler words like "well", "hmm", "you know", and pauses ("...") to make it sound human.
- Visuals MUST CHANGE EVERY 3-4 SECONDS.
- Generate at least {min_scenes} scenes (CRITICAL). Keep scenes short.
- Total narration word count MUST be AT LEAST {min_words} words.
- Each scene's narration must be short and not repeat the previous scene.
Each sentence should have an 'image_prompt' describing the visual for that scene.
Image prompts must ALWAYS be written in ENGLISH.
Narrations must be in ENGLISH.

IMAGE PROMPT RULES:
- Include these terms in EVERY prompt to avoid the "AI look": "cinematic stock photo, 35mm film, film grain, subtle motion blur, realistic human touch".
- NEVER use the same camera angle in two consecutive scenes!
- ALL scenes must share the SAME COLOR PALETTE and STYLE.
- NEVER include: blurry, text overlay, cartoon, illustration, deformed.

For each scene, specify a 'media_type' field:
- "image" → normal static image (most scenes should use this)
- "video_clip" → short GIF or video clip (20-30% of scenes can use this, especially for action, movement, or funny scenes)
For video_clip scenes, also add a 'clip_search_query' field (short English search keyword).

For each scene, specify a 'pacing' field:
- "fast" → fast tempo (hook, shocking facts, excitement)
- "normal" → normal tempo (explanation, information)
- "slow" → slow tempo (dramatic moment, finale, CTA)

For each scene, specify a 'mood' field:
- "tense" → suspenseful, dark
- "inspiring" → uplifting, warm
- "shocking" → attention-grabbing
- "calm" → peaceful, serene
- "funny" → humorous, playful

Add a 'style_anchor' field at the TOP LEVEL of the JSON. This defines the visual style for ALL scenes.
Example: "dark moody cinematic, teal and orange color grading, dramatic shadows"
You MUST append this style_anchor text to the END of every image_prompt.

Return ONLY a JSON object as shown below. Do NOT add any explanation or markdown:
{
  "style_anchor": "dark moody cinematic, teal and orange color grading, dramatic shadows",
  "scenes": [
    {
        "narration": "The coldest place in the universe is not in Antarctica, but in the Boomerang Nebula, 5000 light-years away from us.",
        "image_prompt": "A cinematic hyperrealistic wide-angle shot of a freezing cold nebula in deep space glowing slowly, dark space background, 8k resolution, dark moody cinematic, teal and orange color grading, dramatic shadows",
        "media_type": "image",
        "pacing": "fast",
        "mood": "shocking"
    },
    {
        "narration": "This nebula, at minus 272 degrees, is the closest natural environment to absolute zero.",
        "image_prompt": "Extreme close-up of frozen ice crystals forming in extreme cold deep space environment, 8k, dark moody cinematic, teal and orange color grading, dramatic shadows",
        "media_type": "video_clip",
        "clip_search_query": "ice crystals forming timelapse",
        "pacing": "normal",
        "mood": "tense"
    }
  ]
}
""",
    "es": """
ERES un creador de contenido de YouTube Shorts e Instagram Reels.
Escribirás un guion de video extremadamente atractivo e informativo de {duration} segundos sobre el tema dado.
REGLAS OBLIGATORIAS:
- La PRIMERA ESCENA (los primeros 3 segundos) debe ser el GANCHO. Comienza con una frase personal y muy llamativa como "Probé esto y me sorprendió" o "Aquí está el secreto que descubrí".
- Usa una estructura narrativa: Problema -> Conflicto -> Solución. Cuenta una experiencia, no des datos enciclopédicos.
- TONO: Muy natural, personal y conversacional. Usa palabras de relleno como "bueno", "hmm", "ya sabes" y pausas ("...") para que suene humano.
- ¡Las imágenes DEBEN CAMBIAR CADA 3-4 SEGUNDOS!
- Genera al menos {min_scenes} escenas.
- El número total de palabras de narración DEBE ser AL MENOS {min_words} palabras.
- La narración de cada escena debe ser corta y no debe repetir una escena anterior.
Cada oración debe tener un 'image_prompt' que describa el visual de esa escena.
Los image prompts deben SIEMPRE estar escritos en INGLÉS. Las narraciones en ESPAÑOL.

REGLAS DE IMAGE PROMPT:
- Incluye estos términos en CADA prompt para evitar el "aspecto de IA": "cinematic stock photo, 35mm film, film grain, subtle motion blur, realistic human touch".
- NUNCA uses el mismo ángulo de cámara en dos escenas consecutivas.
- TODAS las escenas deben compartir la MISMA PALETA DE COLORES y ESTILO.
- NUNCA incluyas: blurry, text overlay, cartoon, illustration, deformed.

Para cada escena, especifica un campo 'media_type':
- "image" → imagen estática normal (la mayoría de escenas deben usar esto)
- "video_clip" → GIF corto o clip de video (20-30% de escenas pueden usar esto, especialmente para acción, movimiento o escenas divertidas)
Para escenas video_clip, también agrega un campo 'clip_search_query' (palabra clave corta en inglés).

Para cada escena, especifica un campo 'pacing':
- "fast" → ritmo rápido (gancho, datos impactantes, emoción)
- "normal" → ritmo normal (explicación, información)
- "slow" → ritmo lento (momento dramático, final, CTA)

Para cada escena, especifica un campo 'mood':
- "tense" → suspenso, oscuro
- "inspiring" → inspirador, cálido
- "shocking" → impactante
- "calm" → tranquilo, sereno
- "funny" → humorístico, divertido

Agrega un campo 'style_anchor' en el NIVEL SUPERIOR del JSON. Define el estilo visual para TODAS las escenas.
Ejemplo: "dark moody cinematic, teal and orange color grading, dramatic shadows"
DEBES añadir este texto style_anchor al FINAL de cada image_prompt.

Devuelve SOLO un objeto JSON como se muestra a continuación. NO agregues explicación o markdown:
{
  "style_anchor": "dark moody cinematic, teal and orange color grading, dramatic shadows",
  "scenes": [
    {
        "narration": "El lugar más frío del universo no está en la Antártida, sino en la Nebulosa Boomerang, a 5000 años luz de nosotros.",
        "image_prompt": "A cinematic hyperrealistic wide-angle shot of a freezing cold nebula in deep space glowing slowly, dark space background, 8k resolution, dark moody cinematic, teal and orange color grading, dramatic shadows",
        "media_type": "image",
        "pacing": "fast",
        "mood": "shocking"
    },
    {
        "narration": "Esta nebulosa, a menos 272 grados, es el entorno natural más cercano al cero absoluto.",
        "image_prompt": "Extreme close-up of frozen ice crystals forming in extreme cold deep space environment, 8k, dark moody cinematic, teal and orange color grading, dramatic shadows",
        "media_type": "video_clip",
        "clip_search_query": "ice crystals forming timelapse",
        "pacing": "normal",
        "mood": "tense"
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


# Kalite düzeyine göre sahne çarpanları
QUALITY_SCENE_MULTIPLIERS = {
    "low": 0.55,      # Düşük kalite → az sahne (6-8)
    "medium": 1.0,    # Orta kalite → normal sahne (12-15)
    "high": 1.6,      # Yüksek kalite → çok sahne (18-22)
}

def _calculate_min_scenes(duration_seconds: int, quality_level: str = "medium") -> int:
    """Kalite düzeyine göre minimum sahne sayısını hesaplar."""
    # Temel hesap: ortalama 3-4 saniye/sahne temposu
    base_scenes = max(6, int(duration_seconds / 3.5))
    multiplier = QUALITY_SCENE_MULTIPLIERS.get(quality_level, 1.0)
    return max(4, int(base_scenes * multiplier))


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


def generate_script_from_custom_text(topic, custom_script, ai_provider="Gemini", duration=30, quality_level="medium"):
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

# Kamera açısı çeşitliliğini zorunlu kılan post-validation
CAMERA_ANGLES = [
    "close-up", "wide angle", "bird's eye view", "low angle",
    "macro", "over-the-shoulder", "extreme close-up", "medium shot",
    "aerial view", "dutch angle"
]


# ─────────────────────────────────────────────────────────────
# TOPIC-AWARE STYLE ANCHOR SEÇİCİ
# ─────────────────────────────────────────────────────────────

# Konu kategorisine göre önceden tanımlanmış sinematik stiller
_TOPIC_STYLE_ANCHORS = [
    # (anahtar kelimeler, style_anchor)
    (["uzay", "evren", "gezegen", "star", "space", "cosmos", "astronot", "nasa", "roket", "mars", "galaksi"],
     "dark moody cinematic, deep navy and electric purple tones, dramatic rim lighting, atmospheric cosmic haze, teal and violet color grading"),
    (["doğa", "orman", "hayvan", "bitki", "okyanus", "deniz", "dığ", "nature", "forest", "ocean", "wildlife"],
     "natural cinematic, rich earth tones and emerald greens, soft diffused golden hour lighting, organic film grain, warm and cool contrast"),
    (["tarih", "antik", "piramit", "rönesans", "savaş", "history", "ancient", "pyramid", "medieval", "empire"],
     "vintage cinematic, sepia amber tones, aged film grain, dramatic chiaroscuro lighting, desaturated warm palette"),
    (["teknoloji", "yapay zeka", "bilgisayar", "siber", "robot", "ai", "tech", "cyber", "digital", "future"],
     "futuristic cinematic, neon cyan and electric blue tones, hard neon glow, dark background, high contrast cyberpunk aesthetic"),
    (["sağlık", "beyin", "tıp", "hastalık", "vücud", "health", "brain", "medicine", "medical", "science"],
     "clinical cinematic, cool blue and white tones, clean modern lighting, precise shallow depth of field, sterile yet dramatic"),
    (["para", "ekonomi", "iş", "finans", "girişim", "money", "finance", "business", "success", "wealth"],
     "premium cinematic, rich gold and deep charcoal tones, dramatic moody lighting, sharp contrast, luxury aesthetic"),
    (["spor", "antrenman", "fitness", "futbol", "başarı", "sport", "training", "athlete", "competition"],
     "high energy cinematic, vibrant orange and black tones, dynamic motion blur, intense dramatic lighting, powerful athletic aesthetic"),
    (["psikoloji", "beyin", "duygu", "zihin", "bilinç", "psychology", "mind", "emotion", "mental"],
     "introspective cinematic, deep teal and muted purple tones, soft rim lighting, shallow depth of field, atmospheric haze"),
    (["yemek", "mutfak", "tarif", "food", "cooking", "recipe", "cuisine"],
     "warm culinary cinematic, rich amber and terracotta tones, soft golden light, shallow depth of field, appetizing warm palette"),
    (["müzik", "sanat", "dans", "tiyatro", "music", "art", "dance", "creative"],
     "artistic cinematic, vibrant jewel tones, dramatic stage lighting, bold color contrast, expressive visual style"),
]

_DEFAULT_STYLE_ANCHOR = "dark moody cinematic, teal and orange color grading, dramatic shadows, film grain, atmospheric depth"


def _select_style_anchor(topic: str) -> str:
    """
    Konuya göre en uygun style_anchor'ı seçer.
    Eşleşme bulunamazsa genel sinematik varsayılanı döndürür.
    """
    topic_lower = topic.lower()
    for keywords, anchor in _TOPIC_STYLE_ANCHORS:
        if any(kw in topic_lower for kw in keywords):
            return anchor
    return _DEFAULT_STYLE_ANCHOR


def _enforce_style_anchor(script_data: dict, topic: str = "") -> dict:
    """
    Script'teki tüm image_prompt'ların sonuna style_anchor'ı ekler.
    style_anchor yoksa konuya göre otomatik üretir.
    Tutarsız veya eksik style_anchor kullanımını düzenler.
    """
    scenes = script_data.get("scenes", [])
    if not scenes:
        return script_data

    # style_anchor al veya üret
    style_anchor = script_data.get("style_anchor", "").strip()
    if not style_anchor:
        style_anchor = _select_style_anchor(topic) if topic else _DEFAULT_STYLE_ANCHOR
        script_data["style_anchor"] = style_anchor
        print(f"[+] Style anchor konuya göre belirlendi: '{style_anchor[:60]}...'")
    else:
        print(f"[+] Style anchor kullanılıyor: '{style_anchor[:60]}...'")

    fixes = 0
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        prompt = scene.get("image_prompt", "")
        if not prompt:
            continue
        # style_anchor zaten eklenmiş mi kontrol et
        anchor_fragment = style_anchor[:30].lower()
        if anchor_fragment not in prompt.lower():
            scene["image_prompt"] = f"{prompt.rstrip(', ')} {style_anchor}"
            fixes += 1

    if fixes > 0:
        print(f"[+] Style anchor {fixes} sahnenin görsel prompt'una eklendi/düzeltildi.")

    return script_data

def _detect_camera_angle(prompt: str) -> str | None:
    """Prompt'tan kamera açısını tespit eder."""
    prompt_lower = prompt.lower()
    for angle in CAMERA_ANGLES:
        if angle in prompt_lower:
            return angle
    return None

def _enforce_camera_angle_diversity(script_data: dict) -> dict:
    """
    Ardışık sahnelerde aynı kamera açısı kullanılmışsa otomatik düzeltir.
    AI bazen kurala uymayabilir, bu fonksiyon garanti sağlar.
    """
    scenes = script_data.get("scenes", [])
    if len(scenes) < 2:
        return script_data
    
    angle_pool = list(CAMERA_ANGLES)  # Kullanılabilir açılar havuzu
    prev_angle = None
    fixes_made = 0
    
    for i, scene in enumerate(scenes):
        prompt = scene.get("image_prompt", "")
        current_angle = _detect_camera_angle(prompt)
        
        if current_angle and current_angle == prev_angle:
            # Ardışık aynı açı bulundu — değiştir
            available = [a for a in angle_pool if a != current_angle]
            if available:
                new_angle = available[i % len(available)]
                scene["image_prompt"] = prompt.replace(current_angle, new_angle)
                fixes_made += 1
                current_angle = new_angle
        
        prev_angle = current_angle
    
    if fixes_made > 0:
        print(f"[+] Kamera açısı çeşitliliği düzeltildi: {fixes_made} sahne güncellendi.")
    
    return script_data


def generate_script(topic, ai_provider="Gemini", duration=30, language="tr", quality_level="medium"):
    lang_name = {"tr": "Türkçe", "en": "English", "es": "Español"}.get(language, language)
    quality_labels = {"low": "Düşük", "medium": "Orta", "high": "Yüksek"}
    print(f"[+] '{topic}' konusu için {duration} saniyelik {lang_name} senaryo üretiliyor... (AI: {ai_provider}, Kalite: {quality_labels.get(quality_level, quality_level)})")
    min_words = _calculate_min_words(duration)
    min_scenes = _calculate_min_scenes(duration, quality_level)
    print(f"[i] Minimum senaryo hedefi: {min_words} kelime, {min_scenes} sahne (kalite: {quality_level}, min {MIN_WORDS_PER_MINUTE} kelime/dk)")
    
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
                # Kamera açısı çeşitliliğini zorla
                script_data = _enforce_camera_angle_diversity(script_data)
                # Style anchor tutarlılığını garanti et
                script_data = _enforce_style_anchor(script_data, topic)
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
            # Style anchor'ı fallback için de uygula
            last_valid_script = _enforce_style_anchor(last_valid_script, topic)
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
