import os
import json
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
Sen bir YouTube Shorts ve Instagram Reels içerik üreticisisin.
Verilen konu hakkında aşırı ilgi çekici, bilgilendirici, 45-60 saniyelik bir video senaryosu yazacaksın.
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

def generate_script_openai(topic):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Lütfen şu konuda ilginç bir senaryo yaz: {topic}"}
        ],
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content

def generate_script_gemini(topic):
    import google.generativeai as genai
    
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.5-pro")
    
    prompt = SYSTEM_PROMPT + f"\n\nLütfen şu konuda ilginç bir senaryo yaz: {topic}"
    
    response = model.generate_content(prompt)
    return response.text

def generate_script(topic, ai_provider="Gemini"):
    print(f"[+] '{topic}' konusu için senaryo üretiliyor... (AI: {ai_provider})")
    
    try:
        if "openai" in ai_provider.lower() or "gpt" in ai_provider.lower():
            raw_content = generate_script_openai(topic)
        else:
            raw_content = generate_script_gemini(topic)
        
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
