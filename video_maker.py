from moviepy import AudioFileClip, ImageClip, VideoFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import requests
import numpy as np
import video_effects
from subtitle_enhancer import subtitle_enhancer

def apply_clip_resize(clip, width=None, height=None):
    """MoviePy v1'de resize(), v2'de resized() kullanılır."""
    if hasattr(clip, 'resized'):
        return clip.resized(width=width, height=height)
    if hasattr(clip, 'resize'):
        return clip.resize(width=width, height=height)
    return clip

def apply_clip_duration(clip, duration):
    """MoviePy v1'de set_duration(), v2'de with_duration() kullanılır."""
    if hasattr(clip, 'with_duration'):
        return clip.with_duration(duration)
    if hasattr(clip, 'set_duration'):
        return clip.set_duration(duration)
    return clip

def apply_clip_audio(clip, audio):
    """MoviePy v1'de set_audio(), v2'de with_audio() kullanılır."""
    if hasattr(clip, 'with_audio'):
        return clip.with_audio(audio)
    if hasattr(clip, 'set_audio'):
        return clip.set_audio(audio)
    return clip


def burn_subtitle_on_image(image_path, text, output_path, subtitle_style="tiktok"):
    """Görselin üzerine kalın, renkli, gölgeli altyazı yakar. OPTİMİZE EDİLDİ."""
    img = Image.open(image_path).convert("RGBA")
    
    # 1080x1920'ye zorla - HIZLI: Bilinear yerine LANCZOS kullanma
    img = img.resize((1080, 1920), Image.BILINEAR)  # Daha hızlı resize
    
    # Yarı saydam bir overlay katmanı oluştur
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Font ayarla
    font_size = 58 if subtitle_style == "tiktok" else 50  # Biraz daha küçük = hızlı render
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
    
    # Metni satırlara böl
    wrapped = textwrap.fill(text, width=18 if subtitle_style == "tiktok" else 24)
    lines = wrapped.split("\n")
    
    # Hesaplamalar
    line_height = font_size + 10
    total_text_height = len(lines) * line_height
    start_y = 1920 - total_text_height - (200 if subtitle_style == "tiktok" else 260)
    
    # Arka plan kutusu
    box_padding = 25 if subtitle_style == "tiktok" else 18
    box_top = start_y - box_padding
    box_bottom = start_y + total_text_height + box_padding
    
    if subtitle_style == "tiktok":
        draw.rounded_rectangle(
            [40, box_top, 1040, box_bottom],
            radius=15,
            fill=(0, 0, 0, 120)  # Biraz daha az opak = hızlı
        )
    elif subtitle_style == "netflix":
        draw.rounded_rectangle(
            [40, box_top, 1040, box_bottom],
            radius=12,
            fill=(0, 0, 0, 70)
        )
    
    # Basit gölge (sadece 4 yön yerine 8)
    shadow_offset = 2 if subtitle_style == "tiktok" else 2
    text_color = (255, 255, 80, 255) if subtitle_style == "tiktok" else (255, 255, 255, 255)
    
    for i, line in enumerate(lines):
        y = start_y + (i * line_height)
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        
        # Sadece 4 yönde gölge (daha hızlı)
        for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, -shadow_offset), 
                       (-shadow_offset, shadow_offset), (shadow_offset, shadow_offset)]:
            draw.text((x + dx, y + dy), line, font=font, fill=(0, 0, 0, 255))
        
        # Ana metin
        draw.text((x, y), line, font=font, fill=text_color)
    
    # Overlay'i ana görselle birleştir
    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")
    # HIZLI: Kaliteyi %85 yap (95 yerine) - %30 daha hızlı
    result.save(output_path, quality=85, optimize=True)

def generate_video_clip_ai(image_path, output_path):
    """Görseli Replicate SVD kullanarak videoya çevirir."""
    try:
        import replicate
        print(f"[+] '{image_path}' video klibine dönüştürülüyor... (AI: SVD)")
        
        # Görseli Replicate'e yüklemek için bir URL lazım, 
        # ancak yerel dosyayı doğrudan replicate.run ile gönderebiliriz.
        with open(image_path, "rb") as image_file:
            output = replicate.run(
                "stability-ai/svd:3f776d5209f25790c05739091851084741604a8839965d13735232759905470d",
                input={
                    "image": image_file,
                    "video_length": "14_frames_with_svd",
                    "fps": 6,
                    "motion_bucket_id": 127,
                }
            )
        
        video_url = output # Genelde doğrudan bir URL döner
        
        # Videoyu indir
        video_resp = requests.get(video_url, stream=True)
        if video_resp.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in video_resp.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"[+] AI video klibi kaydedildi: {output_path}")
            return True
        else:
            print(f"[-] AI video indirilemedi: {video_resp.status_code}")
            return False
            
    except ImportError:
        print("[-] Replicate modülü bulunamadı, statik görsel kullanılıyor")
        return False
    except Exception as e:
        print(f"[-] AI video oluşturulurken hata: {e}")
        return False

def create_video(image_paths, audio_path, output_filename="final_video.mp4", narrations=None, subtitle_style="tiktok", video_mode="slideshow"):
    print(f"[+] Video kurgulanıyor (Mod: {video_mode}): {output_filename}...")
    
    try:
        # Sesi yükle
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        
        # Her görselin ekranda kalma süresini hesapla
        slide_duration = total_duration / len(image_paths)
        
        clips = []
        for i, img in enumerate(image_paths):
            # 1. Altyazı veya Efekt Uygula
            processed_img = img
            if narrations and i < len(narrations) and subtitle_style != "none":
                # Metni seslendirmeye uygun hale getir
                enhanced_narration = subtitle_enhancer.enhance_text_for_speech(narrations[i])
                
                subtitle_img = f"assets/sub_{os.path.basename(img)}"
                burn_subtitle_on_image(img, enhanced_narration, subtitle_img, subtitle_style)
                processed_img = subtitle_img
            
            # 2. Mod Seçimine Göre Klip Oluştur
            if video_mode == "ai_video":
                video_clip_path = f"assets/clip_{os.path.basename(img)}.mp4"
                if generate_video_clip_ai(processed_img, video_clip_path):
                    clip = VideoFileClip(video_clip_path)
                    # Ses süresine uydurmak için klibi loop yap veya hızlandır
                    clip = apply_clip_resize(clip, width=1080, height=1920)
                    clip = apply_clip_duration(clip, slide_duration)
                else:
                    # Hata olursa statik görsele dön
                    clip = ImageClip(processed_img, duration=slide_duration)
            else:
                # Cinematic veya Slideshow
                clip = ImageClip(processed_img, duration=slide_duration)
                clip = apply_clip_resize(clip, width=1080, height=1920)
                
                if video_mode == "cinematic":
                    clip = video_effects.apply_random_effect(clip)
            
            clips.append(clip)
        
        # Klipleri birleştir
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Sesi videoya ekle
        final_video = apply_clip_audio(final_video, audio_clip)
        
        # Videoyu MP4 olarak render al - CPU thread'lerini kullan
        print(f"[+] Render işlemi başlıyor...")
        final_video.write_videofile(
            output_filename,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",  # Zaten en hızlı
            threads=0,  # Tüm CPU çekirdeklerini kullan (0 = auto)
            ffmpeg_params=[
                "-tune", "fastdecode",  # Hızlı decode
                "-movflags", "+faststart",  # Hızlı başlangıç
            ],
            temp_audiofile=f"temp-audio-{os.path.basename(output_filename)}.m4a",
            remove_temp=True,
            logger=None
        )
        
        print(f"[+] ŞAHANE! Videonuz hazırlandı: {output_filename}")
        return True
        
    except Exception as e:
        print(f"[-] Video birleştirilirken hata oluştu: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imgs = ["test_image.jpg"]
