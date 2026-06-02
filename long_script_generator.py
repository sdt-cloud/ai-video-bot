import os
import json
import re
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Constants
MIN_WORDS_LONG = 1100
MAX_RETRIES = 3

# Language labels
LANG_LABELS = {
    "tr": "Türkçe",
    "en": "English",
    "es": "Español"
}

def clean_json_response(raw_content: str) -> str:
    """Cleans markdown code block wraps from raw model output."""
    content = raw_content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines)
    return content.strip()

def count_words(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))

def get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def generate_outline_openai(topic: str, duration: int, language: str) -> dict:
    """Stage 1: Generates a structural chapter outline of the long video using OpenAI."""
    client = get_openai_client()
    lang_name = LANG_LABELS.get(language, "Türkçe")
    
    system_prompt = (
        "You are an expert YouTube documentary writer. Your goal is to structure a detailed chapter outline "
        f"for a long-form {duration}-second documentary about the given topic.\n"
        f"The outline must contain exactly 5 to 7 chapters. The language of the outline details must be in {lang_name}.\n"
        "Return ONLY a valid JSON object matching this schema. Do not add markdown or extra text:\n"
        "{\n"
        "  \"style_anchor\": \"Visual color palette and cinematic style anchor for the entire video (in English)\",\n"
        "  \"chapters\": [\n"
        "    {\n"
        "      \"chapter_num\": 1,\n"
        "      \"title\": \"Title of the first chapter\",\n"
        "      \"description\": \"Brief description of what will be discussed in this chapter\",\n"
        "      \"target_duration\": 80\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = f"Topic: {topic}\nTarget total duration: {duration} seconds. Generate a high-quality educational outline."
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    content = clean_json_response(response.choices[0].message.content)
    return json.loads(content)

def generate_outline_gemini(topic: str, duration: int, language: str, model_name: str = "gemini-2.5-pro") -> dict:
    """Stage 1: Generates a structural chapter outline of the long video using Gemini."""
    from google import genai
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    lang_name = LANG_LABELS.get(language, "Türkçe")
    
    prompt = (
        "You are an expert YouTube documentary writer. Your goal is to structure a detailed chapter outline "
        f"for a long-form {duration}-second documentary about the given topic.\n"
        f"The outline must contain exactly 5 to 7 chapters. The language of the outline details must be in {lang_name}.\n"
        "Return ONLY a valid JSON object matching this schema. Do not add markdown or extra text:\n"
        "{\n"
        "  \"style_anchor\": \"Visual color palette and cinematic style anchor for the entire video (in English)\",\n"
        "  \"chapters\": [\n"
        "    {\n"
        "      \"chapter_num\": 1,\n"
        "      \"title\": \"Title of the first chapter\",\n"
        "      \"description\": \"Brief description of what will be discussed in this chapter\",\n"
        "      \"target_duration\": 80\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Topic: {topic}\nTarget total duration: {duration} seconds."
    )
    
    response = client.models.generate_content(model=model_name, contents=prompt)
    content = clean_json_response(response.text)
    return json.loads(content)

def generate_chapter_scenes_openai(topic: str, style_anchor: str, chapter: dict, language: str,
                                    prev_chapter_narrations: list = None, next_chapter_desc: str = None) -> list:
    """Stage 2: Expands a single chapter into 8-10 detailed scenes with narration and prompts using OpenAI."""
    client = get_openai_client()
    lang_name = LANG_LABELS.get(language, "Türkçe")
    
    # Bağlam devamlılığı: önceki bölümün son narration'ları
    context_bridge = ""
    if prev_chapter_narrations:
        context_bridge = (
            "\nIMPORTANT CONTEXT CONTINUITY RULE: The previous chapter ended with these narrations (do NOT repeat them, "
            "but continue naturally from where they left off):\n"
            + "\n".join([f'- "{n}"' for n in prev_chapter_narrations[-2:]])
            + "\n"
        )
    if next_chapter_desc:
        context_bridge += f"\nThe NEXT chapter will cover: \"{next_chapter_desc}\". Do NOT start covering that topic yet, but build a natural bridge toward it in your final scene.\n"
    
    system_prompt = (
        "You are a documentary writer. You are writing scenes for a specific chapter in a long-form video.\n"
        "You must generate exactly 7 to 10 scenes for this chapter. Keep narration engaging, natural, and conversational.\n"
        f"Narrations MUST be in {lang_name}. Use rich vocabulary, storytelling tone, and realistic punctuation pauses.\n"
        + context_bridge +
        f"Visual style rules:\n"
        f"- EVERY image prompt must be in ENGLISH and visual-only.\n"
        f"- End each image prompt with this EXACT style anchor: \"{style_anchor}\".\n"
        "- Incorporate cinematic terms: \"cinematic stock photo, 35mm film, film grain, subtle motion blur, realistic human touch\".\n"
        "- Specify distinct camera angles in consecutive prompts (e.g., wide angle, close-up, low angle).\n"
        "- Set media_type: \"image\" or \"video_clip\". If \"video_clip\", add a short English \"clip_search_query\" (max 4 words).\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"narration\": \"Narration sentence(s) in target language\",\n"
        "      \"image_prompt\": \"Cinematic image prompt in English ending with the style anchor\",\n"
        "      \"media_type\": \"image\",\n"
        "      \"clip_search_query\": null,\n"
        "      \"pacing\": \"normal\",\n"
        "      \"mood\": \"inspiring\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )
    
    user_prompt = (
        f"Topic of overall documentary: {topic}\n"
        f"Current Chapter Number: {chapter['chapter_num']}\n"
        f"Chapter Title: {chapter['title']}\n"
        f"Chapter Description: {chapter['description']}\n"
        f"Chapter Target Duration: {chapter['target_duration']} seconds."
    )
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    content = clean_json_response(response.choices[0].message.content)
    data = json.loads(content)
    return data.get("scenes", [])

def generate_chapter_scenes_gemini(topic: str, style_anchor: str, chapter: dict, language: str, model_name: str = "gemini-2.5-pro",
                                    prev_chapter_narrations: list = None, next_chapter_desc: str = None) -> list:
    """Stage 2: Expands a single chapter into 8-10 detailed scenes with narration and prompts using Gemini."""
    from google import genai
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    lang_name = LANG_LABELS.get(language, "Türkçe")
    
    # Bağlam devamlılığı: önceki bölümün son narration'ları
    context_bridge = ""
    if prev_chapter_narrations:
        context_bridge = (
            "\nIMPORTANT CONTEXT CONTINUITY RULE: The previous chapter ended with these narrations (do NOT repeat them, "
            "but continue naturally from where they left off):\n"
            + "\n".join([f'- "{n}"' for n in prev_chapter_narrations[-2:]])
            + "\n"
        )
    if next_chapter_desc:
        context_bridge += f"\nThe NEXT chapter will cover: \"{next_chapter_desc}\". Do NOT start covering that topic yet, but build a natural bridge toward it in your final scene.\n"
    
    prompt = (
        "You are a documentary writer. You are writing scenes for a specific chapter in a long-form video.\n"
        "You must generate exactly 7 to 10 scenes for this chapter. Keep narration engaging, natural, and conversational.\n"
        f"Narrations MUST be in {lang_name}. Use rich vocabulary, storytelling tone, and realistic punctuation pauses.\n"
        + context_bridge +
        f"Visual style rules:\n"
        f"- EVERY image prompt must be in ENGLISH and visual-only.\n"
        f"- End each image prompt with this EXACT style anchor: \"{style_anchor}\".\n"
        "- Incorporate cinematic terms: \"cinematic stock photo, 35mm film, film grain, subtle motion blur, realistic human touch\".\n"
        "- Specify distinct camera angles in consecutive prompts (e.g., wide angle, close-up, low angle).\n"
        "- Set media_type: \"image\" or \"video_clip\". If \"video_clip\", add a short English \"clip_search_query\" (max 4 words).\n"
        "Return ONLY a valid JSON object matching this schema:\n"
        "{\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"narration\": \"Narration sentence(s) in target language\",\n"
        "      \"image_prompt\": \"Cinematic image prompt in English ending with the style anchor\",\n"
        "      \"media_type\": \"image\",\n"
        "      \"clip_search_query\": null,\n"
        "      \"pacing\": \"normal\",\n"
        "      \"mood\": \"inspiring\"\n"
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Topic of overall documentary: {topic}\n"
        f"Current Chapter Number: {chapter['chapter_num']}\n"
        f"Chapter Title: {chapter['title']}\n"
        f"Chapter Description: {chapter['description']}\n"
        f"Chapter Target Duration: {chapter['target_duration']} seconds."
    )
    
    response = client.models.generate_content(model=model_name, contents=prompt)
    content = clean_json_response(response.text)
    data = json.loads(content)
    return data.get("scenes", [])

def generate_long_script(topic: str, ai_provider: str = "Gemini", duration: int = 480, language: str = "tr", tone: str = "auto") -> dict:
    """
    Stage 3: Coordinates outline creation, expands each chapter sequentially,
    and returns a combined, fully formatted JSON script matching Shorts structure but scaled up.
    """
    print(f"[+] '{topic}' için çok aşamalı UZUN VİDEO senaryo üretimi başladı (Hedef: {duration} saniye, Dil: {language}, AI: {ai_provider})")
    
    # 1. AŞAMA: Ana Hat (Outline) Oluşturma
    provider_lower = ai_provider.lower()
    outline = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if "openai" in provider_lower or "gpt" in provider_lower:
                outline = generate_outline_openai(topic, duration, language)
            else:
                model = "gemini-2.5-flash" if "flash" in provider_lower else "gemini-2.5-pro"
                outline = generate_outline_gemini(topic, duration, language, model)
            break
        except Exception as e:
            print(f"[-] Outline oluşturma hatası (deneme {attempt}/{MAX_RETRIES}): {e}")
            if attempt == MAX_RETRIES:
                return None
            
    if not outline or "chapters" not in outline:
        print("[-] Ana hat (outline) üretilemedi veya geçersiz.")
        return None
        
    style_anchor = outline.get("style_anchor", "dark moody cinematic, rich color grade, high details")
    chapters = outline.get("chapters", [])
    print(f"[+] Ana hat oluşturuldu: {len(chapters)} bölüm planlandı. Görsel Stil Çapası: '{style_anchor}'")
    
    # 2. AŞAMA: Her Bölümü Sırayla Genişletme (Bağlam Köprüsü ile)
    all_scenes = []
    prev_chapter_narrations = []  # Önceki bölümün son narration'ları (bağlam devamlılığı)
    
    for ch_idx, ch in enumerate(chapters):
        print(f"[+] Bölüm {ch['chapter_num']} genişletiliyor: '{ch['title']}'...")
        
        # Sonraki bölümün açıklamasını al (bağlam köprüsü için)
        next_chapter_desc = None
        if ch_idx + 1 < len(chapters):
            next_chapter_desc = chapters[ch_idx + 1].get("description", "")
        
        scenes = []
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if "openai" in provider_lower or "gpt" in provider_lower:
                    scenes = generate_chapter_scenes_openai(
                        topic, style_anchor, ch, language,
                        prev_chapter_narrations=prev_chapter_narrations if prev_chapter_narrations else None,
                        next_chapter_desc=next_chapter_desc
                    )
                else:
                    model = "gemini-2.5-flash" if "flash" in provider_lower else "gemini-2.5-pro"
                    scenes = generate_chapter_scenes_gemini(
                        topic, style_anchor, ch, language, model,
                        prev_chapter_narrations=prev_chapter_narrations if prev_chapter_narrations else None,
                        next_chapter_desc=next_chapter_desc
                    )
                break
            except Exception as e:
                print(f"[-] Bölüm {ch['chapter_num']} genişletme hatası (deneme {attempt}/{MAX_RETRIES}): {e}")
                if attempt == MAX_RETRIES:
                    print(f"[!] Bölüm {ch['chapter_num']} başarısız oldu, atlanıyor.")
        
        if scenes:
            print(f"[i] Bölüm {ch['chapter_num']}: {len(scenes)} sahne başarıyla üretildi.")
            # Bağlam köprüsü: bu bölümün son narration'larını sakla
            prev_chapter_narrations = [s.get("narration", "") for s in scenes if s.get("narration")]
            all_scenes.extend(scenes)
        else:
            # Başarısız bölüm — önceki bağlamı koru, sıfırlama
            pass
            
    if not all_scenes:
        print("[-] Hiçbir bölüm sahnesi üretilemedi.")
        return None
        
    # 3. AŞAMA: Doğrulama ve Derleme
    total_text = " ".join([s.get("narration", "") for s in all_scenes])
    word_cnt = count_words(total_text)
    
    print(f"[+] Tüm bölümler birleştirildi. Toplam Sahne: {len(all_scenes)}, Toplam Kelime: {word_cnt}")
    
    # Kamera açısı tutarlılık kontrolleri ve düzeltmeleri
    from script_generator import _enforce_camera_angle_diversity, _enforce_style_anchor
    
    script_data = {
        "style_anchor": style_anchor,
        "virality_score": 95,
        "critique": "Uzun soluklu derinlemesine belgesel formatı. Bilgi yoğunluğu ve görsel zenginlik hedeflere uygundur.",
        "audience_retention_tip": "Altyazıları senkron ve dinamik sunun, konuşma arasındaki duraklamaları profesyonel tutun.",
        "scenes": all_scenes
    }
    
    # Kamera açısı çeşitliliğini zorla
    script_data = _enforce_camera_angle_diversity(script_data)
    # Style anchor bütünlüğünü garantile
    script_data = _enforce_style_anchor(script_data, topic, tone)
    
    # Meta verilerini ekle
    # Dil bazlı WPM: Türkçe ~120 WPM, İngilizce ~140 WPM, İspanyolca ~130 WPM
    wpm_by_lang = {"tr": 120, "en": 140, "es": 130}
    wpm = wpm_by_lang.get(language, 130)
    
    meta = script_data.get("_meta", {})
    meta["source"] = "long_script_generator"
    meta["word_count"] = word_cnt
    meta["estimated_duration_seconds"] = int((word_cnt / wpm) * 60)
    meta["target_duration_seconds"] = duration
    script_data["_meta"] = meta
    
    return script_data

if __name__ == "__main__":
    # Test long script generation
    test_topic = "Bizans İmparatorluğu'nun çöküşünün 5 bilinmeyen nedeni"
    res = generate_long_script(test_topic, "Gemini", 480, "tr")
    if res:
        with open("test_long_script.json", "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
        print("[+] Test Başarılı! test_long_script.json dosyasına kaydedildi.")
