import os
import json
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
Sen bir YouTube Shorts ve Instagram Reels içerik üreticisisin.
Verilen konu hakkında aşırı ilgi çekici, bilgilendirici, {duration} saniyelik bir video senaryosu yazacaksın.
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

def generate_script_openai(topic, duration=30):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    formatted_system_prompt = SYSTEM_PROMPT.replace("{duration}", str(duration))
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": formatted_system_prompt},
            {"role": "user", "content": f"Lütfen şu konuda ilginç ve tam olarak {duration} saniye sürecek bir senaryo yaz: {topic}"}
        ],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def generate_script_gemini(topic, model_name="gemini-2.5-pro", duration=30):
    import google.generativeai as genai
    
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel(model_name)
    
    formatted_system_prompt = SYSTEM_PROMPT.replace("{duration}", str(duration))
    prompt = formatted_system_prompt + f"\n\nLütfen şu konuda ilginç ve tam olarak {duration} saniye sürecek bir senaryo yaz: {topic}"
    
    response = model.generate_content(prompt)
    return response.text

def generate_script(topic, ai_provider="Gemini", duration=30):
    print(f"[+] '{topic}' konusu için {duration} saniyelik senaryo üretiliyor... (AI: {ai_provider})")
    
    try:
        provider_lower = ai_provider.lower()
        if "openai" in provider_lower or "gpt" in provider_lower:
            raw_content = generate_script_openai(topic, duration)
        elif "3.1-flash" in provider_lower or "3.1 flash" in provider_lower:
            # Not: Google API'sinde şu an en güncel flaş model 2.5-flash'dir. 3.1 UI ismidir.
            raw_content = generate_script_gemini(topic, model_name="gemini-2.5-flash", duration=duration)
        elif "3.1-pro" in provider_lower or "3.1 pro" in provider_lower:
            # Not: Google API'sinde şu an en güncel pro model 2.5-pro'dur.
            raw_content = generate_script_gemini(topic, model_name="gemini-2.5-pro", duration=duration)
        else:
            raw_content = generate_script_gemini(topic, model_name="gemini-2.5-pro", duration=duration)
        
        # JSON temizle (bazen ```json ... ``` ile sarılıyor)
        content = raw_content.strip()
        if content.startswith("```"):
            # İlk ve son ``` satırlarını kaldır
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)
        
        script_data = json.loads(content)
        print(f"[+] Senaryo başarıyla üretildi! ({len(script_data.get('scenes', []))} sahne)")
        return script_data
        
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
