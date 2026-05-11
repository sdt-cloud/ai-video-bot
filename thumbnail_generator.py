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
        prompt = f"Şu konu hakkında YouTube Shorts/TikTok/Reels için EN FAZLA TEK CÜMLE ve MAKSİMUM 4 KELİME süren, MUAZZAM derecede merak uyandırıcı, tıklama tuzağı (clickbait) bir kapak yazısı üret. Örneğin: 'BUNU BİLMİYORDUN!', 'GİZLİ GERÇEK!', 'YOK ARTIK!'. Asla uzun cümle kurma. Sadece yazıyı ver, tırnak işareti kullanma.\nKonu: {topic}"
        response = model.generate_content(prompt)
        title = response.text.strip().replace('"', '').replace('.', '').upper()
        
        # Eğer yapay zeka dinlemeyip uzun bir metin verirse zorla kırp
        words = title.split()
        if len(words) > 4:
            title = " ".join(words[:4])
            
        return title
    except Exception:
        # Fallback
        words = topic.split()
        return " ".join(words[:3]).upper() + "!"

def _find_bold_font(font_size=150):
    """Cross-platform kalın font arayıcı."""
    # 1. Öncelik: Sistemimizde indirdiğimiz fontu kullan
    try:
        from video_maker import ensure_font
        font_path = ensure_font("tiktok") # Montserrat-ExtraBold indirir
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"[*] Font yüklenirken hata: {e}")
        pass

    # 2. Alternatif Sistem Fontları
    font_paths = [
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        # Windows
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, font_size)
            except Exception:
                continue
                
    print("[-] DİKKAT: Hiçbir kalın font bulunamadı. Default (küçük) font kullanılıyor!")
    return ImageFont.load_default()


def select_best_thumbnail_scene(scenes, image_paths):
    """En dikkat çekici sahneyi thumbnail için seçer (en uzun narration = en çok bilgi)."""
    if not scenes or not image_paths:
        return image_paths[0] if image_paths else None
    
    best_idx = 0
    best_score = 0
    hook_keywords = ["şok", "inanılmaz", "sır", "gizli", "bilmiyordun", "amazing", "secret", "shocking"]
    
    for i, scene in enumerate(scenes):
        if i >= len(image_paths):
            break
        narration = scene.get("narration", "").lower()
        score = len(narration)  # Daha uzun = daha bilgilendirici
        for kw in hook_keywords:
            if kw in narration:
                score += 50  # Clickbait kelimesi varsa bonus
        if i == 0:
            score += 30  # Hook sahnesi genelde en dikkat çekici
        if score > best_score:
            best_score = score
            best_idx = i
    
    return image_paths[best_idx]


def create_thumbnail(image_path: str, topic: str, output_path: str, aspect_ratio="9:16"):
    """
    Profesyonel thumbnail üretir:
    - Gradient karartma (üstten aşağı)
    - Otomatik renk iyileştirme
    - Devasa clickbait başlık + 3D gölge
    """
    print(f"[+] '{output_path}' için kapak fotoğrafı (Thumbnail) üretiliyor...")
    if not os.path.exists(image_path):
        print(f"[-] Thumbnail kaynağı bulunamadı: {image_path}")
        return False
        
    try:
        title = generate_clickbait_title(topic)
        print(f"[+] Kapak Başlığı: {title}")
        
        # Boyut belirle
        sizes = {"9:16": (1080, 1920), "1:1": (1080, 1080), "16:9": (1920, 1080)}
        target_w, target_h = sizes.get(aspect_ratio, (1080, 1920))
        
        img = Image.open(image_path).convert("RGBA")
        img = img.resize((target_w, target_h), Image.LANCZOS)
        
        # Renk iyileştirme
        img = ImageEnhance.Contrast(img).enhance(1.35)
        img = ImageEnhance.Color(img).enhance(1.20)
        img = ImageEnhance.Sharpness(img).enhance(1.15)
        
        # Gradient overlay (üstten aşağı karartma — metin için)
        gradient = Image.new("RGBA", img.size, (0, 0, 0, 0))
        for y in range(target_h):
            # Üst %20: hafif, orta: çok hafif, alt %30: koyu
            if y < target_h * 0.3:
                alpha = int(80 * (1 - y / (target_h * 0.3)))  # Üst: hafif koyu
            elif y > target_h * 0.65:
                progress = (y - target_h * 0.65) / (target_h * 0.35)
                alpha = int(40 + 100 * progress)  # Alt: giderek koyu
            else:
                alpha = 20  # Orta: çok hafif
            for x in range(target_w):
                gradient.putpixel((x, y), (0, 0, 0, alpha))
        img = Image.alpha_composite(img, gradient)
        
        draw = ImageDraw.Draw(img)
        
        # Font
        font_size = int(target_h * 0.078)  # Orantılı font boyutu
        font = _find_bold_font(font_size)
        
        wrapped_title = textwrap.fill(title, width=10)
        lines = wrapped_title.split("\n")
        
        line_height = font_size + 14
        total_height = len(lines) * line_height
        start_y = (target_h - total_height) // 2 - int(target_h * 0.08)
        
        # Renk paleti
        text_color = (255, 220, 0, 255)  # Altın sarı
        stroke_color = (0, 0, 0, 255)
        stroke_width = max(6, font_size // 15)
        
        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (target_w - text_width) // 2
            
            # Dış çizgi (stroke)
            for dx in range(-stroke_width, stroke_width + 1, 3):
                for dy in range(-stroke_width, stroke_width + 1, 3):
                    draw.text((x + dx, y + dy), line, font=font, fill=stroke_color)
            
            # 3D gölge efekti
            draw.text((x + 12, y + 12), line, font=font, fill=(0, 0, 0, 180))
            draw.text((x + 6, y + 6), line, font=font, fill=(0, 0, 0, 120))
            
            # Ana metin
            draw.text((x, y), line, font=font, fill=text_color)
            
        img = img.convert("RGB")
        img.save(output_path, quality=95, optimize=True)
        print(f"[+] ŞAHANE! Thumbnail hazır: {output_path}")
        return True
    except Exception as e:
        print(f"[-] Thumbnail üretilemedi: {e}")
        return False

if __name__ == "__main__":
    # Test
    # create_thumbnail("assets/test.jpg", "Evrenin sırları ve karadelikler", "assets/thumb_test.jpg")
    pass
