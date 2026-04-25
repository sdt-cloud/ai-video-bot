import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import google.generativeai as genai

def generate_clickbait_title(topic: str) -> str:
    """Konudan 2-4 kelimelik devasa kapak yazısı üretir."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        words = topic.split()
        return " ".join(words[:3]).upper() + "!"
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"Şu konu hakkında YouTube Shorts/TikTok/Reels için maksimum 3-4 kelimelik, MUAZZAM derecede merak uyandırıcı, tıklama tuzağı (clickbait) bir kapak yazısı üret. Örneğin: 'BUNU BİLMİYORDUN!', 'GİZLİ GERÇEK!', 'YOK ARTIK!'. Sadece yazıyı ver, tırnak işareti veya noktalama kullanma.\nKonu: {topic}"
        response = model.generate_content(prompt)
        return response.text.strip().replace('"', '').replace('.', '').upper()
    except Exception:
        # Fallback
        words = topic.split()
        return " ".join(words[:3]).upper() + "!"

def create_thumbnail(image_path: str, topic: str, output_path: str):
    """
    Görseli alır, karartır/kontrast ekler, ortasına devasa clickbait yazısı koyar.
    """
    print(f"[+] '{output_path}' için kapak fotoğrafı (Thumbnail) üretiliyor...")
    if not os.path.exists(image_path):
        print(f"[-] Thumbnail kaynağı bulunamadı: {image_path}")
        return False
        
    try:
        title = generate_clickbait_title(topic)
        print(f"[+] Kapak Başlığı: {title}")
        
        # Resmi yükle
        img = Image.open(image_path).convert("RGBA")
        img = img.resize((1080, 1920), Image.LANCZOS)
        
        # Efektler: Kontrastı artır
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.3) # Kontrastı %30 artır
        
        # Arkaplanı hafif karart (metin okunsun diye)
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 110)) # %45 siyah
        img = Image.alpha_composite(img, overlay)
        
        draw = ImageDraw.Draw(img)
        
        # Font seçimi (Büyük ve kalın)
        font_size = 150
        font = None
        bold_fonts = [
            "C:/Windows/Fonts/impact.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        for f in bold_fonts:
            if os.path.exists(f):
                font = ImageFont.truetype(f, font_size)
                break
        if font is None:
            font = ImageFont.load_default()
            
        # Metni dar bir kutuya sığdır (ortalama 10-12 karakter yan yana)
        wrapped_title = textwrap.fill(title, width=10)
        lines = wrapped_title.split("\n")
        
        line_height = font_size + 10
        total_height = len(lines) * line_height
        
        # Metni dikeyde tam merkezin azıcık yukarısına koyalım
        start_y = (1920 - total_height) // 2 - 150 
        
        # Yazı renkleri (Tiktok sarısı / Kırmızı)
        text_color = (255, 220, 0, 255) # Altın / Canlı Sarı
        stroke_color = (0, 0, 0, 255)
        stroke_width = 10
        
        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (1080 - text_width) // 2
            
            # Dış Çizgi (Stroke) ve kalın gölge
            for dx in range(-stroke_width, stroke_width+1, 3):
                for dy in range(-stroke_width, stroke_width+1, 3):
                    draw.text((x + dx, y + dy), line, font=font, fill=stroke_color)
            
            # Alt gölge efekti (3d effect)
            draw.text((x + 15, y + 15), line, font=font, fill=(0, 0, 0, 200))
            
            # Ana Metin
            draw.text((x, y), line, font=font, fill=text_color)
            
        # JPEG olarak kaydet
        img = img.convert("RGB")
        img.save(output_path, quality=95)
        print(f"[+] ŞAHANE! Thumbnail hazır: {output_path}")
        return True
    except Exception as e:
        print(f"[-] Thumbnail üretilemedi: {e}")
        return False

if __name__ == "__main__":
    # Test
    # create_thumbnail("assets/test.jpg", "Evrenin sırları ve karadelikler", "assets/thumb_test.jpg")
    pass
