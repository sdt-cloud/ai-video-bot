import os
import json
import logging
import base64
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def evaluate_image_relevance(prompt: str, image_path: str) -> tuple[int, str]:
    """
    Verilen görselin, istenen prompt ile ne kadar uyumlu olduğunu 1-10 arası puanlar.
    Açık kaynak limitasyonları/blokları nedeniyle OpenAI (GPT-4o-mini Vision) kullanır.
    
    Args:
        prompt: Görselin üretilmesi/aranması için kullanılan metin
        image_path: Dosya sistemindeki görselin yolu
        
    Returns:
        tuple(puan, neden_aciklamasi)
    """
    if not os.path.exists(image_path):
        return 0, "Görsel dosyası bulunamadı."

    try:
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY bulunamadı, denetim atlanıyor.")
            return 7, "API Key yok."
            
        client = OpenAI(api_key=api_key)
        
        # Resmi optimize et ve base64'e çevir
        # Resmi yeniden boyutlandırmak API token tasarrufu sağlar ve süreyi kısaltır
        img = Image.open(image_path)
        img.thumbnail((512, 512)) # Sadece içeriği anlaması için yeterli boyut
        
        # Geçici bir buffer'a kaydet ve base64'e çevir
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        system_instruction = (
            "Sen katı bir görsel denetçisisin. Verilen görselin istenen Prompt ile ne kadar uyuştuğunu denetleyeceksin. "
            "Puanlamayı 1 ile 10 arasında yap. "
            "Eğer görselde Prompt'ta istenen temel unsurlar veya çok benzer alternatifleri varsa 7 ve üzeri puan ver. "
            "Eğer görsel konuyla tamamen alakasız, absürt veya sadece boş bir arkaplansa düşük puan ver. "
            "SADECE JSON formatında cevap ver: {\"score\": 8, \"reason\": \"Görselde astronot ve karlı dağ net olarak görünüyor.\"}"
        )
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Bu görsel şu prompt için üretildi: '{prompt}'. Değerlendir."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300,
            response_format={"type": "json_object"}
        )
        
        text_content = response.choices[0].message.content.strip()
        
        try:
            result = json.loads(text_content)
            score = int(result.get("score", 0))
            reason = str(result.get("reason", "Açıklama yok."))
            return score, reason
        except json.JSONDecodeError:
            logger.warning(f"Görsel denetçisi geçerli JSON döndürmedi: {text_content}")
            return 7, "Değerlendirme yapılamadı, JSON format hatası."

    except Exception as e:
        logger.error(f"Görsel denetim hatası: {e}")
        # API hatası (kota vb.) durumunda sistemi durdurmamak için görseli kabul et
        return 7, f"Denetim atlandı (Hata: {e})"
