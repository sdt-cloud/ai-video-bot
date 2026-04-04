from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import numpy as np


def burn_subtitle_on_image(image_path, text, output_path):
    """Görselin üzerine kalın, renkli, gölgeli altyazı yakar."""
    img = Image.open(image_path).convert("RGBA")
    
    # 1080x1920'ye zorla
    img = img.resize((1080, 1920), Image.LANCZOS)
    
    # Yarı saydam bir overlay katmanı oluştur (altyazı arka planı için)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Font ayarla - Windows'ta Impact veya Arial Black kullan
    font_size = 62
    font = None
    bold_fonts = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/Arial.ttf",
    ]
    for f in bold_fonts:
        if os.path.exists(f):
            font = ImageFont.truetype(f, font_size)
            break
    if font is None:
        font = ImageFont.load_default()
    
    # Metni satırlara böl (max 20 karakter/satır)
    wrapped = textwrap.fill(text, width=18)
    lines = wrapped.split("\n")
    
    # Toplam metin yüksekliğini hesapla
    line_height = font_size + 12
    total_text_height = len(lines) * line_height
    
    # Altyazı konumu: ekranın alt 1/3'ünde
    start_y = 1920 - total_text_height - 220
    
    # Arka plan kutusu çiz (yarı saydam siyah)
    box_padding = 30
    box_top = start_y - box_padding
    box_bottom = start_y + total_text_height + box_padding
    draw.rounded_rectangle(
        [40, box_top, 1040, box_bottom],
        radius=20,
        fill=(0, 0, 0, 140)
    )
    
    # Her satırı ortala ve yaz
    for i, line in enumerate(lines):
        y = start_y + (i * line_height)
        
        # Metin genişliğini hesapla (ortalamak için)
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        
        # 1. Siyah gölge/kontur (4 yönde)
        shadow_offset = 3
        for dx in [-shadow_offset, 0, shadow_offset]:
            for dy in [-shadow_offset, 0, shadow_offset]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
        
        # 2. Sarı ana metin (TikTok tarzı parlak renk)
        draw.text((x, y), line, font=font, fill=(255, 255, 80, 255))
    
    # Overlay'i ana görselle birleştir
    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")
    result.save(output_path, quality=95)


def create_video(image_paths, audio_path, output_filename="final_video.mp4", narrations=None):
    print(f"[+] Video kurgulanıyor: {output_filename}...")
    
    try:
        # Sesi yükle
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        
        # Her görselin ekranda kalma süresini hesapla
        slide_duration = total_duration / len(image_paths)
        
        clips = []
        for i, img in enumerate(image_paths):
            # Eğer narrations varsa, altyazıyı görsele yak
            if narrations and i < len(narrations):
                subtitle_img = f"assets/sub_{os.path.basename(img)}"
                burn_subtitle_on_image(img, narrations[i], subtitle_img)
                clip = ImageClip(subtitle_img, duration=slide_duration)
            else:
                clip = ImageClip(img, duration=slide_duration)
            
            clip = clip.resized(width=1080, height=1920)
            clips.append(clip)
        
        # Klipleri birleştir
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Sesi videoya ekle
        final_video = final_video.with_audio(audio_clip)
        
        # Videoyu MP4 olarak render al
        print(f"[+] Render işlemi başlıyor...")
        final_video.write_videofile(
            output_filename,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            logger=None
        )
        
        print(f"[+] ŞAHANE! Videonuz hazırlandı: {output_filename}")
        return True
        
    except Exception as e:
        print(f"[-] Video birleştirilirken hata oluştu: {e}")
        return False

if __name__ == "__main__":
    test_imgs = ["test_image.jpg"]
