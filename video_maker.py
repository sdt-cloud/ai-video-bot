from moviepy import AudioFileClip, ImageClip, VideoFileClip, concatenate_videoclips, CompositeAudioClip
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import requests
import numpy as np
import video_effects
from subtitle_enhancer import subtitle_enhancer
from bgm_manager import get_bgm_path


def is_target_resolution_image(image_path, target_size=(1080, 1920)):
    """Gorsel zaten hedef cozumlukteyse ekstra resize maliyetinden kacin."""
    try:
        with Image.open(image_path) as img:
            return img.size == target_size
    except Exception:
        return False
        
def generate_karaoke_subtitle_clips(text, duration, temp_files, subtitle_style="tiktok"):
    """Kelimelerin zamanlamasını hesaplar ve karaoke stili PNG'lerden oluşan bir klip döner."""
    from subtitle_enhancer import subtitle_enhancer
    from moviepy import ImageClip, concatenate_videoclips
    import uuid
    
    timings = subtitle_enhancer.generate_subtitle_timing(text, duration)
    if not timings:
        return None
        
    wrapped = textwrap.fill(text, width=18 if subtitle_style == "tiktok" else 24)
    lines = wrapped.split("\n")
    
    font_size = 58 if subtitle_style == "tiktok" else 50
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
        
    line_height = font_size + 10
    total_text_height = len(lines) * line_height
    start_y = 1920 - total_text_height - (200 if subtitle_style == "tiktok" else 260)
    
    box_padding = 25 if subtitle_style == "tiktok" else 18
    box_top = start_y - box_padding
    box_bottom = start_y + total_text_height + box_padding
    
    overlay_height = int(box_bottom - box_top + 20)
    y_offset = box_top
    
    base_color = (255, 255, 255, 255)
    highlight_color = (255, 255, 80, 255) if subtitle_style == "tiktok" else (255, 200, 0, 255)
    
    clips = []
    
    for t_idx, timing in enumerate(timings):
        word_duration = timing['duration']
        highlight_idx = t_idx
        
        overlay = Image.new("RGBA", (1080, overlay_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        local_box_top = 0
        local_box_bottom = box_bottom - box_top
        
        if subtitle_style == "tiktok":
            draw.rounded_rectangle([40, local_box_top, 1040, local_box_bottom], radius=15, fill=(0, 0, 0, 120))
        elif subtitle_style == "netflix":
            draw.rounded_rectangle([40, local_box_top, 1040, local_box_bottom], radius=12, fill=(0, 0, 0, 70))
            
        shadow_offset = 2
        word_counter = 0
        
        for i, line in enumerate(lines):
            y = (start_y + (i * line_height)) - y_offset
            
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            current_x = (1080 - line_width) // 2
            
            line_words = line.split()
            for lw in line_words:
                is_highlight = (word_counter == highlight_idx)
                
                # Gölge
                for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, -shadow_offset), 
                               (-shadow_offset, shadow_offset), (shadow_offset, shadow_offset)]:
                    draw.text((current_x + dx, y + dy), lw, font=font, fill=(0, 0, 0, 255))
                    
                # Text
                color = highlight_color if is_highlight else base_color
                draw.text((current_x, y), lw, font=font, fill=color)
                
                # Space width
                lw_bbox = draw.textbbox((0, 0), lw + " ", font=font)
                current_x += (lw_bbox[2] - lw_bbox[0])
                word_counter += 1
                
        out_name = f"assets/dyn_sub_{uuid.uuid4().hex[:6]}.png"
        # Optimize PNG for faster disk write/read
        overlay.save(out_name, "PNG", optimize=False)
        temp_files.append(out_name)
        
        c = ImageClip(out_name)
        if hasattr(c, 'with_duration'):
            c = c.with_duration(word_duration)
        else:
            c = c.set_duration(word_duration)
        clips.append(c)
        
    if clips:
        seq = concatenate_videoclips(clips, method="compose")
        if hasattr(seq, 'with_position'):
            return seq.with_position(("center", y_offset))
        else:
            return seq.set_position(("center", y_offset))
    return None


def get_render_settings(video_mode, total_duration):
    """Süreye ve moda gore hiz/kalite dengesini otomatik ayarla."""
    cpu_threads = max(2, min(8, (os.cpu_count() or 4)))

    # Varsayilan kalite profili (mevcut davranisa yakin)
    settings = {
        "fps": 20,
        "preset": "superfast",
        "threads": cpu_threads,
        "ffmpeg_params": ["-movflags", "+faststart", "-crf", "24", "-pix_fmt", "yuv420p"],
    }

    # Uzun videolarda encode suresi ciddi uzadigi icin daha agresif hiz profili
    if total_duration >= 180:
        settings.update({
            "fps": 16,
            "preset": "ultrafast",
            "ffmpeg_params": ["-movflags", "+faststart", "-crf", "30", "-pix_fmt", "yuv420p"],
        })

    # AI video modu en maliyetli mod oldugu icin ek hizlandirma
    if video_mode == "ai_video":
        settings.update({
            "fps": 15,
            "preset": "ultrafast",
            "ffmpeg_params": ["-movflags", "+faststart", "-crf", "32", "-pix_fmt", "yuv420p"],
        })

    return settings

def apply_clip_resize(clip, width=None, height=None):
    """MoviePy v1'de resize(), v2'de resized() kullanılır."""
    if width is not None and height is not None:
        if hasattr(clip, 'resized'):
            return clip.resized((width, height))
        if hasattr(clip, 'resize'):
            return clip.resize((width, height))
            
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

def apply_watermark(image_path, output_path, opacity=0.35, padding=30, max_size=180):
    """Görselin sağ üst köşesine şeffaf logo watermark uygular."""
    watermark_path = "assets/watermark/logo.png"
    if not os.path.exists(watermark_path):
        # Logo yoksa görseli olduğu gibi kopyala
        import shutil
        shutil.copy2(image_path, output_path)
        return

    try:
        base = Image.open(image_path).convert("RGBA")
        wm = Image.open(watermark_path).convert("RGBA")

        # Watermark boyutunu sınırla (max max_size x max_size)
        wm_ratio = min(max_size / wm.width, max_size / wm.height)
        new_wm_size = (int(wm.width * wm_ratio), int(wm.height * wm_ratio))
        wm = wm.resize(new_wm_size, Image.LANCZOS)

        # Opacity uygula — alpha kanalını ölçekle
        r, g, b, a = wm.split()
        a = a.point(lambda x: int(x * opacity))
        wm = Image.merge("RGBA", (r, g, b, a))

        # Sağ üst köşeye yerleştir
        x = base.width - new_wm_size[0] - padding
        y = padding
        base.paste(wm, (x, y), wm)

        base.convert("RGB").save(output_path, quality=85, optimize=True)
    except Exception as e:
        print(f"[-] Watermark uygulama hatası: {e}")
        import shutil
        shutil.copy2(image_path, output_path)


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

def create_video(image_paths, audio_path, output_filename="final_video.mp4", narrations=None,
                 subtitle_style="tiktok", video_mode="slideshow",
                 watermark_enabled=False, transition_style="none",
                 bgm_enabled=False, bgm_tone="auto"):
    print(f"[+] Video kurgulanıyor (Mod: {video_mode}): {output_filename}...")
    temp_files = []
    clips = []
    audio_clip = None
    try:
        # Sesi yükle
        audio_clip = AudioFileClip(audio_path)
        total_duration = audio_clip.duration
        
        if not image_paths:
            raise ValueError("image_paths listesi boş olamaz")
        
        # Slayt sürelerini kelime/harf sayısına göre orantılı hesapla
        slide_durations = []
        if narrations and len(narrations) == len(image_paths):
            total_chars = sum(max(1, len(n)) for n in narrations)
            for n in narrations:
                dur = total_duration * (max(1, len(n)) / total_chars)
                slide_durations.append(dur)
        else:
            slide_durations = [total_duration / len(image_paths)] * len(image_paths)
        
        for i, img in enumerate(image_paths):
            slide_duration = slide_durations[i]
            processed_img = img

            # Watermark uygula
            if watermark_enabled:
                wm_img = f"assets/wm_{os.path.basename(processed_img)}"
                apply_watermark(processed_img, wm_img)
                temp_files.append(wm_img)
                processed_img = wm_img
            
            if video_mode == "ai_video":
                video_clip_path = f"assets/clip_{os.path.basename(img)}.mp4"
                if generate_video_clip_ai(processed_img, video_clip_path):
                    clip = VideoFileClip(video_clip_path)
                    clip = apply_clip_resize(clip, width=1080, height=1920)
                    clip = apply_clip_duration(clip, slide_duration)
                    temp_files.append(video_clip_path)
                else:
                    clip = ImageClip(processed_img)
                    clip = apply_clip_duration(clip, slide_duration)
            else:
                clip = ImageClip(processed_img)
                clip = apply_clip_duration(clip, slide_duration)
                if not is_target_resolution_image(processed_img):
                    clip = apply_clip_resize(clip, width=1080, height=1920)
                if video_mode == "cinematic":
                    clip = video_effects.apply_random_effect(clip)

            # Dinamik Karaoke Altyazı Ekleme
            if narrations and i < len(narrations) and subtitle_style != "none":
                enhanced_narration = subtitle_enhancer.enhance_text_for_speech(narrations[i])
                try:
                    from moviepy import CompositeVideoClip
                    dynamic_sub_clip = generate_karaoke_subtitle_clips(enhanced_narration, slide_duration, temp_files, subtitle_style)
                    if dynamic_sub_clip:
                        clip = CompositeVideoClip([clip, dynamic_sub_clip])
                    else:
                        # Fallback to static if dynamic fails
                        subtitle_img = f"assets/sub_{os.path.basename(img)}"
                        burn_subtitle_on_image(processed_img, enhanced_narration, subtitle_img, subtitle_style)
                        clip = ImageClip(subtitle_img)
                        clip = apply_clip_duration(clip, slide_duration)
                        temp_files.append(subtitle_img)
                except Exception as sub_err:
                    print(f"[-] Dinamik altyazı hatası (devam ediliyor): {sub_err}")

            # Geçiş efektleri (crossfade / fade)
            transition_dur = 0.4
            if transition_style in ("crossfade", "fade") and clip.duration > transition_dur * 2:
                clip = video_effects.apply_fade_in(clip, transition_dur)
                clip = video_effects.apply_fade_out(clip, transition_dur)
            
            clips.append(clip)
        
        if transition_style == "crossfade" and len(clips) > 1:
            # Crossfade: klipleri 0.4 saniye overlap ile birleştir
            final_video = concatenate_videoclips(clips, method="compose", padding=-0.4)
        else:
            final_video = concatenate_videoclips(clips, method="compose")

        # --- BGM Karıştırma ---
        if bgm_enabled:
            bgm_path = get_bgm_path(bgm_tone)
            if bgm_path and os.path.exists(bgm_path):
                try:
                    print(f"[BGM] Müzik ekleniyor: {bgm_path} (ton: {bgm_tone})")
                    bgm_clip = AudioFileClip(bgm_path)

                    # BGM'i video süresine göre loop veya kırp
                    if bgm_clip.duration < total_duration:
                        from math import ceil
                        repeat_count = ceil(total_duration / bgm_clip.duration)
                        loops = []
                        t = 0.0
                        for _ in range(repeat_count):
                            lp = bgm_clip
                            if hasattr(lp, 'with_start'):
                                lp = lp.with_start(t)
                            elif hasattr(lp, 'set_start'):
                                lp = lp.set_start(t)
                            loops.append(lp)
                            t += bgm_clip.duration
                        bgm_looped = CompositeAudioClip(loops)
                    else:
                        bgm_looped = bgm_clip

                    if hasattr(bgm_looped, 'with_duration'):
                        bgm_looped = bgm_looped.with_duration(total_duration)
                    elif hasattr(bgm_looped, 'set_duration'):
                        bgm_looped = bgm_looped.set_duration(total_duration)

                    bgm_volume = 0.12
                    if hasattr(bgm_looped, 'with_volume_scaled'):
                        bgm_looped = bgm_looped.with_volume_scaled(bgm_volume)
                    elif hasattr(bgm_looped, 'volumex'):
                        bgm_looped = bgm_looped.volumex(bgm_volume)

                    mixed_audio = CompositeAudioClip([audio_clip, bgm_looped])
                    final_video = apply_clip_audio(final_video, mixed_audio)
                    print("[BGM] Arka plan müzik başarıyla eklendi!")
                except Exception as bgm_err:
                    print(f"[BGM] Müzik eklenirken hata (devam ediliyor): {bgm_err}")
                    final_video = apply_clip_audio(final_video, audio_clip)
            else:
                print("[BGM] Müzik dosyası bulunamadı, sözsüz devam ediliyor.")
                final_video = apply_clip_audio(final_video, audio_clip)
        else:
            final_video = apply_clip_audio(final_video, audio_clip)

        # --- Intro / Outro Ekleme (Son Aşama) ---
        try:
            intro_path = "assets/intro.mp4"
            outro_path = "assets/outro.mp4"
            sequence = []
            
            if os.path.exists(intro_path):
                print(f"[+] Intro videosu algılandı: {intro_path}")
                intro_clip = VideoFileClip(intro_path)
                intro_clip = apply_clip_resize(intro_clip, width=1080, height=1920)
                sequence.append(intro_clip)
                clips.append(intro_clip) # Cleanup için listeye ekle
                
            sequence.append(final_video)
            
            if os.path.exists(outro_path):
                print(f"[+] Outro videosu algılandı: {outro_path}")
                outro_clip = VideoFileClip(outro_path)
                outro_clip = apply_clip_resize(outro_clip, width=1080, height=1920)
                sequence.append(outro_clip)
                clips.append(outro_clip) # Cleanup için listeye ekle
                
            if len(sequence) > 1:
                final_video = concatenate_videoclips(sequence, method="compose")
                total_duration = final_video.duration
        except Exception as io_err:
            print(f"[-] Intro/Outro birleştirme hatası: {io_err}")

        # H264 codec requires even dimensions
        w, h = final_video.size
        if w % 2 != 0 or h % 2 != 0:
            final_video = apply_clip_resize(final_video, width=w - (w % 2), height=h - (h % 2))
            
        render_settings = get_render_settings(video_mode, total_duration)
        print(
            f"[+] Render işlemi başlıyor... "
            f"(fps={render_settings['fps']}, preset={render_settings['preset']}, threads={render_settings['threads']})"
        )
        final_video.write_videofile(
            output_filename,
            fps=render_settings["fps"],
            codec="libx264",
            audio_codec="aac",
            preset=render_settings["preset"],
            threads=render_settings["threads"],
            ffmpeg_params=render_settings["ffmpeg_params"],
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
    finally:
        for clip in clips:
            try:
                clip.close()
            except Exception:
                pass
        if audio_clip is not None:
            try:
                audio_clip.close()
            except Exception:
                pass
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

if __name__ == "__main__":
    test_imgs = ["test_image.jpg"]
