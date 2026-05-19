from moviepy import AudioFileClip, ImageClip, VideoFileClip, concatenate_videoclips, CompositeAudioClip
from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import requests
import numpy as np
import video_effects
from subtitle_enhancer import subtitle_enhancer
from bgm_manager import get_bgm_path
import urllib.request


# ─────────────────────────────────────────────────────────────
# ASPECT RATIO YARDIMCISI
# ─────────────────────────────────────────────────────────────

ASPECT_RATIO_MAP = {
    "9:16": (1080, 1920),   # Dikey (TikTok, Reels, Shorts)
    "1:1":  (1080, 1080),   # Kare (Instagram Feed, X)
    "16:9": (1920, 1080),   # Yatay (YouTube, Web)
}

def get_resolution(aspect_ratio: str = "9:16") -> tuple:
    """Aspect ratio'ya göre (width, height) döner."""
    return ASPECT_RATIO_MAP.get(aspect_ratio, (1080, 1920))

def ensure_font(style="tiktok"):
    """Sistemde font yoksa otomatik indirir ve yolunu döner."""
    os.makedirs("assets/fonts", exist_ok=True)
    if style == "tiktok":
        font_name = "Montserrat-ExtraBold.ttf"
        url = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-ExtraBold.ttf"
    else:
        font_name = "Montserrat-Medium.ttf"
        url = "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Medium.ttf"
        
    font_path = f"assets/fonts/{font_name}"
    if not os.path.exists(font_path):
        print(f"[*] Font eksik, indiriliyor: {font_name}")
        try:
            urllib.request.urlretrieve(url, font_path)
        except Exception as e:
            print(f"[-] Font indirilemedi: {e}")
    return font_path

def make_ducking_volume_func(audio_clip, base_vol=0.15, duck_vol=0.035, threshold=0.015,
                              attack_time=0.3, release_time=0.5):
    """
    Smooth attack/release ile profesyonel ducking zarf fonksiyonu.
    
    - attack_time: Konuşma başladığında müziğin kısılma süresi (saniye)
    - release_time: Konuşma bittiğinde müziğin geri açılma süresi (saniye)
    - Bu, ani ses değişimlerini engelleyerek doğal bir geçiş sağlar.
    """
    import numpy as np
    try:
        print("[BGM] Auto-Ducking için ana ses (TTS) analiz ediliyor (smooth envelope)...")
        fps = 20  # Daha yüksek çözünürlük (20 örnek/s) — pürüzsüz geçiş için
        audio_array = audio_clip.to_soundarray(fps=fps)
        if audio_array.ndim == 2:
            rms = np.sqrt(np.mean(audio_array**2, axis=1))
        else:
            rms = np.sqrt(audio_array**2)
            
        # Pürüzsüzleştirme (smoothing) - ani ses değişimlerini engellemek için
        window = 6
        smoothed_rms = np.convolve(rms, np.ones(window)/window, mode='same')
        
        # Konuşma aktif mi? (binary maske)
        is_speaking = (smoothed_rms > threshold).astype(np.float32)
        
        # Smooth envelope oluştur: attack (kısılma) ve release (açılma) süreleri
        attack_samples = max(1, int(attack_time * fps))
        release_samples = max(1, int(release_time * fps))
        
        envelope = np.zeros_like(is_speaking)
        current_level = 0.0  # 0=konuşma yok, 1=konuşma var
        
        for i in range(len(is_speaking)):
            target = is_speaking[i]
            if target > current_level:
                # Attack: konuşma başlıyor, hızlıca kıs
                current_level = min(1.0, current_level + 1.0 / attack_samples)
            else:
                # Release: konuşma bitiyor, yavaşça aç
                current_level = max(0.0, current_level - 1.0 / release_samples)
            envelope[i] = current_level
        
        # Envelope'u volume çarpanına dönüştür: 
        # envelope=0 → base_vol (müzik açık), envelope=1 → duck_vol (müzik kısık)
        vol_envelope = base_vol - (base_vol - duck_vol) * envelope
        
        def volume_multiplier(t):
            idx = int(t * fps)
            if idx < len(vol_envelope):
                return float(vol_envelope[idx])
            return base_vol
        
        print(f"[BGM] Smooth ducking hazır (attack: {attack_time}s, release: {release_time}s)")
        return volume_multiplier
    except Exception as e:
        print(f"[-] Ducking analizi başarısız: {e}")
        return base_vol


def is_target_resolution_image(image_path, target_size=None, aspect_ratio="9:16"):
    """Gorsel zaten hedef cozumlukteyse ekstra resize maliyetinden kacin."""
    if target_size is None:
        target_size = get_resolution(aspect_ratio)
    try:
        with Image.open(image_path) as img:
            return img.size == target_size
    except Exception:
        return False
        
def generate_karaoke_subtitle_clips(text, duration, temp_files, subtitle_style="tiktok", subtitle_delay=0.0, aspect_ratio="9:16"):
    """Kelimelerin zamanlamasını hesaplar ve karaoke stili bellekten oluşan bir klip döner."""
    from subtitle_enhancer import subtitle_enhancer
    from moviepy import ImageClip, concatenate_videoclips
    
    target_w, target_h = get_resolution(aspect_ratio)
    
    timings = subtitle_enhancer.generate_subtitle_timing(text, duration, delay=subtitle_delay)
    if not timings:
        return None
        
    wrapped = textwrap.fill(text, width=18 if subtitle_style == "tiktok" else 24)
    lines = wrapped.split("\n")
    
    font_path = ensure_font(subtitle_style)
    font_size = 52 if subtitle_style == "tiktok" else 46
    font = None
    pop_font = None
    bold_fonts = [font_path]
    for f in bold_fonts:
        if os.path.exists(f):
            font = ImageFont.truetype(f, font_size)
            pop_font = ImageFont.truetype(f, int(font_size * 1.15))  # %15 pop-in (overlap önlemek için küçültüldü)
            break
    if font is None:
        font = ImageFont.load_default()
        pop_font = font
        
    line_height = int(font_size * 1.15) + 12  # Pop fontuna göre boşluk bırak, üst üste binmesin
    total_text_height = len(lines) * line_height
    start_y = target_h - total_text_height - (200 if subtitle_style == "tiktok" else 260)
    
    box_padding = 25 if subtitle_style == "tiktok" else 18
    box_top = start_y - box_padding
    box_bottom = start_y + total_text_height + box_padding
    
    overlay_height = int(box_bottom - box_top + 20)
    y_offset = box_top
    
    if subtitle_style == "tiktok":
        base_color = (255, 255, 255, 255)
        highlight_color = (255, 255, 80, 255)
    elif subtitle_style == "mrbeast":
        base_color = (255, 200, 200, 255)
        highlight_color = (255, 80, 80, 255)
    else:
        base_color = (255, 255, 255, 255)
        highlight_color = (255, 200, 0, 255)
    
    clips = []
    
    for t_idx, timing in enumerate(timings):
        word_duration = timing['duration']
        highlight_idx = timing.get('index', -1)
        
        overlay = Image.new("RGBA", (target_w, overlay_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        local_box_top = 0
        local_box_bottom = box_bottom - box_top
        
        if subtitle_style == "tiktok":
            draw.rounded_rectangle([40, local_box_top, target_w - 40, local_box_bottom], radius=15, fill=(0, 0, 0, 120))
        elif subtitle_style == "netflix":
            draw.rounded_rectangle([40, local_box_top, target_w - 40, local_box_bottom], radius=12, fill=(0, 0, 0, 70))
            
        shadow_offset = 2
        word_counter = 0
        
        for i, line in enumerate(lines):
            y = (start_y + (i * line_height)) - y_offset
            
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            current_x = (target_w - line_width) // 2
            
            line_words = line.split()
            for lw in line_words:
                is_highlight = (word_counter == highlight_idx)
                
                # Pop-in animasyonu için konum ve font ayarla
                active_font = pop_font if is_highlight else font
                pop_offset_x = -2 if is_highlight else 0
                pop_offset_y = -4 if is_highlight else 0
                
                # Gölge
                for dx, dy in [(-shadow_offset, -shadow_offset), (shadow_offset, -shadow_offset), 
                               (-shadow_offset, shadow_offset), (shadow_offset, shadow_offset)]:
                    draw.text((current_x + dx + pop_offset_x, y + dy + pop_offset_y), lw, font=active_font, fill=(0, 0, 0, 255))
                    
                # Text
                color = highlight_color if is_highlight else base_color
                draw.text((current_x + pop_offset_x, y + pop_offset_y), lw, font=active_font, fill=color)
                
                # Space width
                lw_bbox = draw.textbbox((0, 0), lw + " ", font=font)
                current_x += (lw_bbox[2] - lw_bbox[0])
                word_counter += 1
                
        # Disk I/O yerine doğrudan bellekten numpy array kullan (performans: ~%30-40 hızlanma)
        overlay_array = np.array(overlay)
        
        c = ImageClip(overlay_array)
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


# ─────────────────────────────────────────────────────────────
# KALİTE BAZLI RENDER AYARLARI
# ─────────────────────────────────────────────────────────────

RENDER_QUALITY_PROFILES = {
    "low": {
        "fps": 24,
        "preset": "fast",
        "crf": "26",
    },
    "medium": {
        "fps": 30,
        "preset": "medium",
        "crf": "20",
    },
    "high": {
        "fps": 30,
        "preset": "slow",
        "crf": "18",  # 16→18: platformlar zaten re-encode ediyor, dosya boyutunu optimize eder
    },
}

def get_render_settings(video_mode, total_duration, quality_level="medium"):
    """Kalite düzeyine, süreye ve moda göre render ayarlarını belirler."""
    cpu_threads = max(2, min(8, (os.cpu_count() or 4)))
    profile = RENDER_QUALITY_PROFILES.get(quality_level, RENDER_QUALITY_PROFILES["medium"])

    settings = {
        "fps": profile["fps"],
        "preset": profile["preset"],
        "threads": cpu_threads,
        "ffmpeg_params": [
            "-movflags", "+faststart",
            "-crf", profile["crf"],
            "-pix_fmt", "yuv420p",
            "-profile:v", "high",
            "-level", "4.2",
            "-b:a", "192k",  # İlk render'da da ses kalitesini garanti altına al
        ],
    }

    # Uzun videolarda (3dk+) encode süresini kontrol altına al
    if total_duration >= 180 and quality_level != "high":
        settings["preset"] = "fast"

    # AI video modunda encode daha ağır olur
    if video_mode == "ai_video" and quality_level == "low":
        settings["preset"] = "fast"

    return settings


# ─────────────────────────────────────────────────────────────
# RENK DÜZELTME / COLOR GRADING
# ─────────────────────────────────────────────────────────────

def color_grade_image(image_path, output_path=None, style="auto_enhance"):
    """
    Görsele renk düzeltme/grading uygular.
    style: auto_enhance, cinematic_warm, cinematic_cool, vintage, none
    """
    if style == "none":
        return image_path
    
    try:
        from PIL import ImageEnhance, ImageFilter
        img = Image.open(image_path).convert("RGB")
        
        if style == "auto_enhance":
            # Profesyonel otomatik iyileştirme
            img = ImageEnhance.Contrast(img).enhance(1.12)      # +12% kontrast
            img = ImageEnhance.Brightness(img).enhance(1.04)    # +4% parlaklık
            img = ImageEnhance.Color(img).enhance(1.18)         # +18% doygunluk
            img = ImageEnhance.Sharpness(img).enhance(1.15)     # +15% keskinlik
        
        elif style == "cinematic_warm":
            img = ImageEnhance.Contrast(img).enhance(1.20)
            img = ImageEnhance.Color(img).enhance(1.10)
            # Sıcak ton: hafif turuncu/amber overlay
            warm_overlay = Image.new("RGB", img.size, (255, 200, 150))
            img = Image.blend(img, warm_overlay, 0.06)
            img = ImageEnhance.Brightness(img).enhance(1.02)
        
        elif style == "cinematic_cool":
            img = ImageEnhance.Contrast(img).enhance(1.22)
            img = ImageEnhance.Color(img).enhance(0.90)
            # Soğuk ton: hafif mavi overlay
            cool_overlay = Image.new("RGB", img.size, (150, 180, 255))
            img = Image.blend(img, cool_overlay, 0.06)
        
        elif style == "vintage":
            img = ImageEnhance.Color(img).enhance(0.75)
            img = ImageEnhance.Contrast(img).enhance(1.15)
            sepia_overlay = Image.new("RGB", img.size, (255, 230, 200))
            img = Image.blend(img, sepia_overlay, 0.10)
            img = ImageEnhance.Brightness(img).enhance(0.97)
        
        save_path = output_path or image_path
        img.save(save_path, quality=92, optimize=True)
        return save_path
    
    except Exception as e:
        print(f"[-] Color grading hatası: {e}")
        return image_path


def _apply_color_grade_to_clip(clip, style="auto_enhance"):
    """
    MoviePy VideoClip'e numpy tabanlı hafif color grading uygular.
    video_clip sahneleri için color_grade_image'ın video versiyonu.
    Ağır olmayan, frame-level basit renk tonu düzeltmesi yapar.
    """
    if style == "none":
        return clip

    try:
        GRADE_PARAMS = {
            "auto_enhance":    {"contrast": 1.10, "brightness": 1.03, "saturation": 1.12, "overlay": None},
            "cinematic_warm":  {"contrast": 1.15, "brightness": 1.01, "saturation": 1.05, "overlay": (255, 200, 150, 0.05)},
            "cinematic_cool":  {"contrast": 1.18, "brightness": 1.00, "saturation": 0.92, "overlay": (150, 180, 255, 0.05)},
            "vintage":         {"contrast": 1.10, "brightness": 0.97, "saturation": 0.80, "overlay": (255, 230, 200, 0.08)},
        }
        params = GRADE_PARAMS.get(style, GRADE_PARAMS["auto_enhance"])

        contrast    = params["contrast"]
        brightness  = params["brightness"]
        saturation  = params["saturation"]
        overlay     = params["overlay"]  # (R, G, B, alpha) or None

        def grade_frame(get_frame, t):
            frame = get_frame(t).astype(np.float32)
            # Contrast: ortalama etrafında ölçekle
            mean = 127.5
            frame = np.clip((frame - mean) * contrast + mean * brightness, 0, 255)
            # Saturation: grayscale ile blend
            if saturation != 1.0:
                gray = 0.299 * frame[:, :, 0] + 0.587 * frame[:, :, 1] + 0.114 * frame[:, :, 2]
                gray = gray[:, :, np.newaxis]
                frame = np.clip(gray + (frame - gray) * saturation, 0, 255)
            # Color overlay
            if overlay:
                r, g, b, alpha = overlay
                ov = np.array([r, g, b], dtype=np.float32)
                frame = np.clip(frame * (1 - alpha) + ov * alpha, 0, 255)
            return frame.astype(np.uint8)

        return apply_clip_transform(clip, grade_frame)
    except Exception as e:
        print(f"[!] Video color grade hatası (atlanıyor): {e}")
        return clip


# Sahne mood'una göre otomatik color grade eşleştirmesi
MOOD_TO_COLOR_GRADE = {
    "tense":     "cinematic_cool",    # Gerilimli → soğuk mavi tonlar
    "inspiring": "cinematic_warm",    # İlham verici → sıcak amber tonlar
    "shocking":  "auto_enhance",      # Şok edici → yüksek kontrast, canlı
    "calm":      "cinematic_warm",    # Sakin → sıcak yumuşak tonlar
    "funny":     "auto_enhance",      # Komik → canlı doğal renkler
}

def get_scene_color_grade(scene_index, scene_pacings, default_style="auto_enhance"):
    """Sahne mood'una göre uygun color grade stilini döndürür."""
    if scene_pacings and scene_index < len(scene_pacings):
        scene_data = scene_pacings[scene_index]
        mood = None
        if isinstance(scene_data, dict):
            mood = scene_data.get("mood", None)
        if mood and mood in MOOD_TO_COLOR_GRADE:
            return MOOD_TO_COLOR_GRADE[mood]
    return default_style


def smart_resize_image(image_path, target_w, target_h, output_path=None):
    """
    Görseli akıllıca hedef boyuta getirir:
    - LANCZOS (en kaliteli) resize
    - Crop + letterbox yerine center crop (dikey videolar için)
    - Küçük görselleri tespit eder
    """
    try:
        img = Image.open(image_path).convert("RGB")
        orig_w, orig_h = img.size
        
        # Hedef aspect ratio
        target_ratio = target_w / target_h
        orig_ratio = orig_w / orig_h
        
        if abs(orig_ratio - target_ratio) < 0.1:
            # Yakın oran → doğrudan resize
            img = img.resize((target_w, target_h), Image.LANCZOS)
        else:
            # Farklı oran → center crop + resize
            if orig_ratio > target_ratio:
                # Daha geniş → yandan kes
                new_w = int(orig_h * target_ratio)
                offset = (orig_w - new_w) // 2
                img = img.crop((offset, 0, offset + new_w, orig_h))
            else:
                # Daha uzun → üstten-alttan kes
                new_h = int(orig_w / target_ratio)
                offset = (orig_h - new_h) // 2
                img = img.crop((0, offset, orig_w, offset + new_h))
            
            img = img.resize((target_w, target_h), Image.LANCZOS)
        
        save_path = output_path or image_path
        img.save(save_path, quality=92, optimize=True)
        return save_path
    
    except Exception as e:
        print(f"[-] Smart resize hatası: {e}")
        return image_path

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


def burn_subtitle_on_image(image_path, text, output_path, subtitle_style="tiktok", aspect_ratio="9:16"):
    """Görselin üzerine kalın, renkli, gölgeli altyazı yakar. 5 stil destekler."""
    target_w, target_h = get_resolution(aspect_ratio)
    img = Image.open(image_path).convert("RGBA")
    img = img.resize((target_w, target_h), Image.LANCZOS)
    
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    font_path = ensure_font(subtitle_style)
    
    # Stil bazlı parametreler
    STYLE_CONFIG = {
        "tiktok": {
            "font_size": 58, "wrap_width": 18, "shadow_offset": 3,
            "text_color": (255, 255, 80, 255), "shadow_color": (0, 0, 0, 255),
            "bg_fill": (0, 0, 0, 120), "bg_radius": 15, "y_offset": 200,
        },
        "netflix": {
            "font_size": 50, "wrap_width": 24, "shadow_offset": 2,
            "text_color": (255, 255, 255, 255), "shadow_color": (0, 0, 0, 255),
            "bg_fill": (0, 0, 0, 70), "bg_radius": 12, "y_offset": 260,
        },
        "hormozi": {
            "font_size": 64, "wrap_width": 14, "shadow_offset": 4,
            "text_color": (255, 255, 255, 255), "shadow_color": (0, 0, 0, 255),
            "highlight_color": (255, 220, 50, 255),
            "bg_fill": None, "bg_radius": 0, "y_offset": 180,
        },
        "mrbeast": {
            "font_size": 62, "wrap_width": 15, "shadow_offset": 4,
            "text_color": (255, 80, 80, 255), "shadow_color": (0, 0, 0, 255),
            "bg_fill": (0, 0, 0, 160), "bg_radius": 20, "y_offset": 200,
        },
        "minimal": {
            "font_size": 40, "wrap_width": 30, "shadow_offset": 2,
            "text_color": (255, 255, 255, 230), "shadow_color": (0, 0, 0, 180),
            "bg_fill": None, "bg_radius": 0, "y_offset": 300,
        },
    }
    
    config = STYLE_CONFIG.get(subtitle_style, STYLE_CONFIG["tiktok"])
    font_size = config["font_size"]
    shadow_offset = config["shadow_offset"]
    text_color = config["text_color"]
    
    font = None
    if os.path.exists(font_path):
        font = ImageFont.truetype(font_path, font_size)
    if font is None:
        font = ImageFont.load_default()
    
    wrapped = textwrap.fill(text, width=config["wrap_width"])
    lines = wrapped.split("\n")
    
    line_height = font_size + 12
    total_text_height = len(lines) * line_height
    start_y = target_h - total_text_height - config["y_offset"]
    
    # Arka plan kutusu (bazı stillerde yok)
    if config["bg_fill"]:
        box_padding = 25
        box_top = start_y - box_padding
        box_bottom = start_y + total_text_height + box_padding
        draw.rounded_rectangle(
            [40, box_top, target_w - 40, box_bottom],
            radius=config["bg_radius"],
            fill=config["bg_fill"]
        )
    
    # Metin render
    for i, line in enumerate(lines):
        y = start_y + (i * line_height)
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (target_w - text_width) // 2
        
        # 8 yönlü gölge (daha kaliteli)
        for dx, dy in [(-shadow_offset, 0), (shadow_offset, 0), (0, -shadow_offset), (0, shadow_offset),
                       (-shadow_offset, -shadow_offset), (shadow_offset, -shadow_offset), 
                       (-shadow_offset, shadow_offset), (shadow_offset, shadow_offset)]:
            draw.text((x + dx, y + dy), line, font=font, fill=config["shadow_color"])
        
        # Hormozi stili: en uzun kelimeyi sarı yap
        if subtitle_style == "hormozi" and "highlight_color" in config:
            words = line.split()
            if words:
                longest_word = max(words, key=len)
                current_x = x
                for word in words:
                    word_bbox = draw.textbbox((0, 0), word + " ", font=font)
                    word_w = word_bbox[2] - word_bbox[0]
                    if word == longest_word:
                        draw.text((current_x, y), word, font=font, fill=config["highlight_color"])
                    else:
                        draw.text((current_x, y), word, font=font, fill=text_color)
                    current_x += word_w
            else:
                draw.text((x, y), line, font=font, fill=text_color)
        else:
            draw.text((x, y), line, font=font, fill=text_color)
    
    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")
    result.save(output_path, quality=92, optimize=True)

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
                 subtitle_style="tiktok", subtitle_delay=0.0, video_mode="slideshow",
                 watermark_enabled=False, transition_style="none",
                 bgm_enabled=False, bgm_tone="auto", aspect_ratio="9:16",
                 quality_level="medium", color_grade_style="auto_enhance",
                 scene_pacings=None, letterbox_enabled=False):
    target_w, target_h = get_resolution(aspect_ratio)
    print(f"[+] Video kurgulanıyor (Mod: {video_mode}, Boyut: {target_w}x{target_h}, Kalite: {quality_level}): {output_filename}...")
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
        
        # Akıllı Tempolama: pacing değerlerine göre süreleri ayarla
        PACING_MULTIPLIERS = {"fast": 0.80, "normal": 1.0, "slow": 1.15}
        if scene_pacings and len(scene_pacings) == len(slide_durations):
            raw_durations = []
            for i, pacing_data in enumerate(scene_pacings):
                # Dict formatı (yeni) veya string formatı (eski) desteği
                if isinstance(pacing_data, dict):
                    pacing = pacing_data.get("pacing", "normal")
                else:
                    pacing = pacing_data
                mult = PACING_MULTIPLIERS.get(pacing, 1.0)
                raw_durations.append(slide_durations[i] * mult)
            
            # Toplam süreyi korumak için normalize et
            raw_total = sum(raw_durations)
            if raw_total > 0:
                scale = total_duration / raw_total
                slide_durations = [d * scale for d in raw_durations]
            
            # Minimum süre garantisi: hiçbir sahne 2 saniyeden kısa olmasın
            slide_durations = [max(2.0, d) for d in slide_durations]
            
            # Hook (ilk sahne) en fazla 4 saniye
            if slide_durations[0] > 4.0:
                excess = slide_durations[0] - 4.0
                slide_durations[0] = 4.0
                # Fazlayı diğer sahnelere dağıt
                others = len(slide_durations) - 1
                if others > 0:
                    for j in range(1, len(slide_durations)):
                        slide_durations[j] += excess / others
            
            # Son sahne (CTA) en az 3 saniye
            if len(slide_durations) > 1 and slide_durations[-1] < 3.0:
                deficit = 3.0 - slide_durations[-1]
                slide_durations[-1] = 3.0
                others = len(slide_durations) - 1
                if others > 0:
                    per_scene = deficit / others
                    for j in range(len(slide_durations) - 1):
                        slide_durations[j] = max(2.0, slide_durations[j] - per_scene)
        
        for i, img in enumerate(image_paths):
            slide_duration = slide_durations[i]
            processed_img = img

            # Watermark uygula
            if watermark_enabled:
                wm_img = f"assets/wm_{os.path.basename(processed_img)}"
                apply_watermark(processed_img, wm_img)
                temp_files.append(wm_img)
                processed_img = wm_img
            
            # Statik görsellere renk düzeltme ve akıllı resize uygula
            if not (img.endswith(".mp4") or img.endswith(".webm")):
                # Renk düzeltme
                if color_grade_style != "none":
                    # Sahne mood'una göre renk grading (mood varsa sahne bazlı, yoksa global)
                    scene_grade = get_scene_color_grade(i, scene_pacings, color_grade_style)
                    graded_img = f"assets/graded_{os.path.basename(processed_img)}"
                    color_grade_image(processed_img, graded_img, scene_grade)
                    temp_files.append(graded_img)
                    processed_img = graded_img
                
                # Akıllı resize (LANCZOS + center crop)
                resized_img = f"assets/resized_{os.path.basename(processed_img)}"
                smart_resize_image(processed_img, target_w, target_h, resized_img)
                temp_files.append(resized_img)
                processed_img = resized_img
            
            if video_mode == "ai_video":
                video_clip_path = f"assets/clip_{os.path.basename(img)}.mp4"
                if generate_video_clip_ai(processed_img, video_clip_path):
                    clip = VideoFileClip(video_clip_path)
                    clip = apply_clip_resize(clip, width=target_w, height=target_h)
                    clip = apply_clip_duration(clip, slide_duration)
                    temp_files.append(video_clip_path)
                else:
                    clip = ImageClip(processed_img)
                    clip = apply_clip_duration(clip, slide_duration)
            elif img.endswith(".mp4") or img.endswith(".webm"):
                # Video klip veya animasyon dosyası
                try:
                    clip = VideoFileClip(img)
                    # Sesi kaldır (narration ile çakışmaması için)
                    clip = apply_clip_audio(clip, None)
                    clip = apply_clip_resize(clip, width=target_w, height=target_h)
                    # Klip süresini sahne süresine ayarla
                    if clip.duration < slide_duration:
                        # Kısa klipleri döngüye al
                        from math import ceil
                        loop_count = ceil(slide_duration / clip.duration)
                        clips_loop = [clip] * loop_count
                        clip = concatenate_videoclips(clips_loop, method="compose")
                    clip = apply_clip_duration(clip, slide_duration)

                    # Video kliplere de color grade uygula (görsel tutarlılık için)
                    if color_grade_style != "none":
                        scene_grade = get_scene_color_grade(i, scene_pacings, color_grade_style)
                        clip = _apply_color_grade_to_clip(clip, scene_grade)
                        print(f"[+] Sahne {i} (video klip) renk düzeltmesi: {scene_grade}")
                except Exception as vid_err:
                    print(f"[-] Video klip yüklenemedi ({img}): {vid_err}, statik görsel kullanılıyor.")
                    clip = ImageClip(processed_img)
                    clip = apply_clip_duration(clip, slide_duration)
            else:
                clip = ImageClip(processed_img)
                clip = apply_clip_duration(clip, slide_duration)
                if not is_target_resolution_image(processed_img, aspect_ratio=aspect_ratio):
                    clip = apply_clip_resize(clip, width=target_w, height=target_h)
                
                # Sadece ilk sahnede (Hook) Camera Shake uygula
                if i == 0:
                    clip = video_effects.apply_camera_shake(clip, duration=0.8, intensity=15)
                
                # Statikliği kırmak için her zaman hafif hareket ekle (slideshow olsa bile)
                if video_mode == "cinematic":
                    clip = video_effects.smart_effect_for_scene(clip, i, len(image_paths))
                else:
                    # Sadece çok hafif bir zoom in (fake motion blur etkisi verir)
                    clip = video_effects.zoom_in_effect(clip, zoom_ratio=0.02)

            # Dinamik Karaoke Altyazı Ekleme
            if narrations and i < len(narrations) and subtitle_style != "none":
                enhanced_narration = subtitle_enhancer.enhance_text_for_speech(narrations[i])
                try:
                    from moviepy import CompositeVideoClip
                    dynamic_sub_clip = generate_karaoke_subtitle_clips(enhanced_narration, slide_duration, temp_files, subtitle_style, subtitle_delay, aspect_ratio)
                    if dynamic_sub_clip:
                        clip = CompositeVideoClip([clip, dynamic_sub_clip])
                    else:
                        # Fallback to static if dynamic fails
                        subtitle_img = f"assets/sub_{os.path.basename(img)}"
                        burn_subtitle_on_image(processed_img, enhanced_narration, subtitle_img, subtitle_style, aspect_ratio)
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

        # --- Sinematik Post-Efektler (Vignette + Film Grain + Letterbox) ---
        if quality_level in ("medium", "high"):
            final_video = video_effects.apply_cinematic_post_effects(
                final_video,
                vignette=True,
                grain=True,  # Film grain her zaman uygulansın (AI hissini gizler)
                letterbox=letterbox_enabled,
            )

        # --- Ses Katmanları (BGM ve SFX) ---
        audio_layers = [audio_clip]
        
        # 1. Arka Plan Müziği (BGM)
        if bgm_enabled:
            bgm_path = get_bgm_path(bgm_tone)
            if bgm_path and os.path.exists(bgm_path):
                try:
                    print(f"[BGM] Müzik ekleniyor: {bgm_path} (ton: {bgm_tone})")
                    bgm_clip = AudioFileClip(bgm_path)

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

                    # Auto-Ducking Uygulaması
                    ducking_func = make_ducking_volume_func(audio_clip, base_vol=0.15, duck_vol=0.035, threshold=0.015)
                    
                    def apply_ducking(get_frame, t):
                        import numpy as np
                        frame = get_frame(t)
                        if isinstance(t, np.ndarray):
                            vols = np.array([ducking_func(ti) for ti in t]).reshape(-1, 1)
                            return frame * vols
                        else:
                            return frame * ducking_func(t)
                            
                    if hasattr(bgm_looped, 'transform'):
                        bgm_looped = bgm_looped.transform(apply_ducking)
                    else:
                        bgm_looped = bgm_looped.fl(apply_ducking)

                    audio_layers.append(bgm_looped)
                    print("[BGM] Auto-Ducking ile arka plan müzik başarıyla eklendi!")
                except Exception as bgm_err:
                    print(f"[BGM] Müzik eklenirken hata (devam ediliyor): {bgm_err}")
            else:
                print("[BGM] Müzik dosyası bulunamadı, sözsüz devam ediliyor.")

        # 2. Ses Efektleri (SFX)
        try:
            from sfx_manager import sfx_manager
            current_sfx_time = 0.0
            
            # İlk saniye Hook efekti (Boom/Impact)
            hook_sfx = sfx_manager.get_clip("hook", 0.0, volume=0.8)
            if hook_sfx:
                audio_layers.append(hook_sfx)
                print("[SFX] Başlangıç 'Hook' ses efekti eklendi.")
                
            # Sahneler arası geçiş (Whoosh) efektleri
            if transition_style != "none":
                for i, slide_dur in enumerate(slide_durations):
                    current_sfx_time += slide_dur
                    if i < len(slide_durations) - 1:
                        # Geçişin başlangıcına denk gelmesi için hafif offset
                        trans_time = max(0, current_sfx_time - 0.2)
                        trans_sfx = sfx_manager.get_clip("transition", trans_time, volume=0.5)
                        if trans_sfx:
                            audio_layers.append(trans_sfx)
                print("[SFX] Sahne geçişi ses efektleri eklendi.")
        except Exception as sfx_err:
            print(f"[-] SFX eklenirken hata: {sfx_err}")

        # Tüm sesleri birleştirip videoya uygula
        mixed_audio = CompositeAudioClip(audio_layers)
        final_video = apply_clip_audio(final_video, mixed_audio)

        # --- Intro / Outro Ekleme (Son Aşama) ---
        try:
            intro_path = "assets/intro.mp4"
            outro_path = "assets/outro.mp4"
            sequence = []
            
            if os.path.exists(intro_path):
                print(f"[+] Intro videosu algılandı: {intro_path}")
                intro_clip = VideoFileClip(intro_path)
                intro_clip = apply_clip_resize(intro_clip, width=target_w, height=target_h)
                sequence.append(intro_clip)
                clips.append(intro_clip) # Cleanup için listeye ekle
                
            sequence.append(final_video)
            
            if os.path.exists(outro_path):
                print(f"[+] Outro videosu algılandı: {outro_path}")
                outro_clip = VideoFileClip(outro_path)
                outro_clip = apply_clip_resize(outro_clip, width=target_w, height=target_h)
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
            
        render_settings = get_render_settings(video_mode, total_duration, quality_level)
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
        
        # --- POST-PROCESSING ---
        if quality_level in ("medium", "high") and os.path.exists(output_filename):
            try:
                import subprocess
                temp_pp = output_filename.replace(".mp4", "_pp.mp4")
                
                # Ses normalizasyonu (LUFS -14, TikTok/YouTube standardı) + hafif sharpening
                pp_filters = []
                if quality_level == "high":
                    pp_filters.append("unsharp=3:3:0.3:3:3:0.1")  # Hafif keskinlik
                
                vf_arg = ",".join(pp_filters) if pp_filters else None
                
                # High kalitede 2-Pass encoding (daha iyi bit dağılımı)
                if quality_level == "high" and vf_arg:
                    passlog = output_filename.replace(".mp4", "_passlog")
                    
                    # Pass 1: Analiz (video analiz edilir, çıktı /dev/null'a gider)
                    pass1_cmd = [
                        "ffmpeg", "-y", "-i", output_filename,
                        "-vf", vf_arg,
                        "-c:v", "libx264", "-preset", "slow", "-b:v", "6M",
                        "-pass", "1", "-passlogfile", passlog,
                        "-an",  # Ses işleme yok (sadece video analiz)
                        "-f", "null", "/dev/null"
                    ]
                    
                    # Pass 2: Asıl encode (analiz sonucuna göre bit dağılımı)
                    pass2_cmd = [
                        "ffmpeg", "-y", "-i", output_filename,
                        "-vf", vf_arg,
                        "-c:v", "libx264", "-preset", "slow", "-b:v", "6M",
                        "-pass", "2", "-passlogfile", passlog,
                        "-af", "loudnorm=I=-14:TP=-1:LRA=11",
                        "-c:a", "aac", "-b:a", "192k",
                        temp_pp
                    ]
                    
                    print("[POST] 2-Pass encoding başlıyor (Pass 1: analiz)...")
                    result1 = subprocess.run(pass1_cmd, capture_output=True, timeout=180)
                    
                    if result1.returncode == 0:
                        print("[POST] Pass 1 tamamlandı. Pass 2: encode...")
                        result2 = subprocess.run(pass2_cmd, capture_output=True, timeout=180)
                        
                        if result2.returncode == 0 and os.path.exists(temp_pp):
                            os.replace(temp_pp, output_filename)
                            print("[POST] 2-Pass encoding + LUFS normalizasyon + keskinleştirme başarılı!")
                        else:
                            if os.path.exists(temp_pp):
                                os.remove(temp_pp)
                            print("[POST] Pass 2 başarısız, orijinal video korunuyor.")
                    else:
                        print("[POST] Pass 1 başarısız, tek-pass post-processing'e düşülüyor...")
                        # Fallback: tek-pass post-processing
                        fallback_cmd = [
                            "ffmpeg", "-y", "-i", output_filename,
                            "-af", "loudnorm=I=-14:TP=-1:LRA=11",
                            "-vf", vf_arg,
                            "-c:v", "libx264",
                            "-c:a", "aac", "-b:a", "192k",
                            temp_pp
                        ]
                        result_fb = subprocess.run(fallback_cmd, capture_output=True, timeout=120)
                        if result_fb.returncode == 0 and os.path.exists(temp_pp):
                            os.replace(temp_pp, output_filename)
                            print("[POST] Tek-pass fallback post-processing başarılı!")
                        elif os.path.exists(temp_pp):
                            os.remove(temp_pp)
                    
                    # Passlog dosyalarını temizle
                    for ext in ["-0.log", "-0.log.mbtree"]:
                        logfile = passlog + ext
                        if os.path.exists(logfile):
                            os.remove(logfile)
                else:
                    # Medium kalite: sadece LUFS normalizasyonu (tek-pass)
                    pp_cmd = [
                        "ffmpeg", "-y", "-i", output_filename,
                        "-af", "loudnorm=I=-14:TP=-1:LRA=11",
                    ]
                    if vf_arg:
                        pp_cmd.extend(["-vf", vf_arg])
                    pp_cmd.extend([
                        "-c:v", "copy" if not vf_arg else "libx264",
                        "-c:a", "aac", "-b:a", "192k",
                        temp_pp
                    ])
                    
                    result = subprocess.run(pp_cmd, capture_output=True, timeout=120)
                    if result.returncode == 0 and os.path.exists(temp_pp):
                        os.replace(temp_pp, output_filename)
                        print("[POST] Ses normalizasyonu (LUFS -14) başarıyla uygulandı!")
                        if vf_arg:
                            print("[POST] Video keskinleştirme uygulandı!")
                    else:
                        # Başarısızsa orijinali kullan
                        if os.path.exists(temp_pp):
                            os.remove(temp_pp)
                        print("[POST] Post-processing atlandı (FFmpeg hatası)")
            except FileNotFoundError:
                print("[POST] FFmpeg bulunamadı, post-processing atlanıyor.")
            except Exception as pp_err:
                print(f"[POST] Post-processing hatası: {pp_err}")
        
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
