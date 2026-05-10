from moviepy import vfx
import numpy as np
from PIL import Image

def apply_clip_transform(clip, filter_func):
    """
    MoviePy v1 ve v2 arasındaki API farklarını yönetir.
    v1: fl()
    v2: transform() veya image_transform()
    """
    for method in ['transform', 'fl', 'image_transform']:
        if hasattr(clip, method):
            return getattr(clip, method)(filter_func)
    return clip

def zoom_in_effect(clip, zoom_ratio=0.04):
    def filter(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        base_size = img.size
        new_size = [
            int(base_size[0] * (1 + (zoom_ratio * t))),
            int(base_size[1] * (1 + (zoom_ratio * t)))
        ]
        img = img.resize(new_size, Image.LANCZOS)
        x = (new_size[0] - base_size[0]) // 2
        y = (new_size[1] - base_size[1]) // 2
        img = img.crop((x, y, x + base_size[0], y + base_size[1]))
        return np.array(img)
    return apply_clip_transform(clip, filter)

def zoom_out_effect(clip, zoom_ratio=0.04):
    def filter(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        base_size = img.size
        total_duration = clip.duration or 5 # Fallback
        max_zoom = 1 + (zoom_ratio * total_duration)
        current_zoom = max_zoom - (zoom_ratio * t)
        new_size = [
            int(base_size[0] * current_zoom),
            int(base_size[1] * current_zoom)
        ]
        img = img.resize(new_size, Image.LANCZOS)
        x = (new_size[0] - base_size[0]) // 2
        y = (new_size[1] - base_size[1]) // 2
        img = img.crop((x, y, x + base_size[0], y + base_size[1]))
        return np.array(img)
    return apply_clip_transform(clip, filter)

def pan_left_to_right_effect(clip, pan_ratio=0.1):
    def filter(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        base_size = img.size
        scale = 1.1 
        new_size = [int(base_size[0] * scale), int(base_size[1] * scale)]
        img = img.resize(new_size, Image.LANCZOS)
        total_duration = clip.duration or 5
        max_x = new_size[0] - base_size[0]
        current_x = int((t / total_duration) * max_x)
        y = (new_size[1] - base_size[1]) // 2
        img = img.crop((current_x, y, current_x + base_size[0], y + base_size[1]))
        return np.array(img)
    return apply_clip_transform(clip, filter)

def pan_top_to_bottom_effect(clip, pan_ratio=0.1):
    """Dikey videolar için yukarıdan aşağıya pan efekti."""
    def filter(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        base_size = img.size
        scale = 1.1
        new_size = [int(base_size[0] * scale), int(base_size[1] * scale)]
        img = img.resize(new_size, Image.LANCZOS)
        total_duration = clip.duration or 5
        max_y = new_size[1] - base_size[1]
        current_y = int((t / total_duration) * max_y)
        x = (new_size[0] - base_size[0]) // 2
        img = img.crop((x, current_y, x + base_size[0], current_y + base_size[1]))
        return np.array(img)
    return apply_clip_transform(clip, filter)

def pan_bottom_to_top_effect(clip, pan_ratio=0.1):
    """Dikey videolar için aşağıdan yukarıya pan efekti."""
    def filter(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        base_size = img.size
        scale = 1.1
        new_size = [int(base_size[0] * scale), int(base_size[1] * scale)]
        img = img.resize(new_size, Image.LANCZOS)
        total_duration = clip.duration or 5
        max_y = new_size[1] - base_size[1]
        current_y = max_y - int((t / total_duration) * max_y)
        x = (new_size[0] - base_size[0]) // 2
        img = img.crop((x, current_y, x + base_size[0], current_y + base_size[1]))
        return np.array(img)
    return apply_clip_transform(clip, filter)

def ken_burns_effect(clip, zoom_ratio=0.06):
    """Ken Burns — eşzamanlı zoom + pan (sinematik klasik)."""
    def filter(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        base_size = img.size
        total_duration = clip.duration or 5
        progress = t / total_duration
        current_zoom = 1 + (zoom_ratio * progress * total_duration)
        new_size = [int(base_size[0] * current_zoom), int(base_size[1] * current_zoom)]
        img = img.resize(new_size, Image.LANCZOS)
        # Soldan sağa + hafif yukarıdan aşağıya pan
        max_x = new_size[0] - base_size[0]
        max_y = new_size[1] - base_size[1]
        x = int(progress * max_x * 0.6)
        y = int(progress * max_y * 0.3)
        x = max(0, min(x, max_x))
        y = max(0, min(y, max_y))
        img = img.crop((x, y, x + base_size[0], y + base_size[1]))
        return np.array(img)
    return apply_clip_transform(clip, filter)

def parallax_effect(clip, intensity=0.03):
    """Sahte parallax — kenarları daha hızlı hareket ettirerek derinlik hissi."""
    def filter(get_frame, t):
        frame = get_frame(t)
        img = Image.fromarray(frame)
        base_size = img.size
        total_duration = clip.duration or 5
        progress = t / total_duration
        # Hafif zoom + offset
        zoom = 1.08
        new_size = [int(base_size[0] * zoom), int(base_size[1] * zoom)]
        img = img.resize(new_size, Image.LANCZOS)
        # Sinüs hareketi (ileri-geri sallanma)
        import math
        dx = int(math.sin(progress * math.pi * 2) * intensity * base_size[0])
        dy = int(math.cos(progress * math.pi) * intensity * base_size[1] * 0.5)
        cx = (new_size[0] - base_size[0]) // 2 + dx
        cy = (new_size[1] - base_size[1]) // 2 + dy
        cx = max(0, min(cx, new_size[0] - base_size[0]))
        cy = max(0, min(cy, new_size[1] - base_size[1]))
        img = img.crop((cx, cy, cx + base_size[0], cy + base_size[1]))
        return np.array(img)
    return apply_clip_transform(clip, filter)


# Tüm efektler listesi
ALL_EFFECTS = [
    zoom_in_effect,
    zoom_out_effect,
    pan_left_to_right_effect,
    pan_top_to_bottom_effect,
    pan_bottom_to_top_effect,
    ken_burns_effect,
    parallax_effect,
]

def apply_random_effect(clip):
    import random
    effect_fn = random.choice(ALL_EFFECTS)
    return effect_fn(clip)

def smart_effect_for_scene(clip, scene_index, total_scenes):
    """
    Sahne pozisyonuna göre akıllı efekt ataması:
    - İlk sahne (hook): zoom_in (dikkat çekme)
    - Son sahne (outro): zoom_out (kapanış)
    - 2. sahne: ken_burns (sinematik giriş)
    - Ortalar: diğer efektlerden rastgele
    """
    if scene_index == 0:
        return zoom_in_effect(clip, zoom_ratio=0.05)
    elif scene_index == total_scenes - 1:
        return zoom_out_effect(clip, zoom_ratio=0.04)
    elif scene_index == 1:
        return ken_burns_effect(clip, zoom_ratio=0.04)
    else:
        import random
        mid_effects = [
            pan_left_to_right_effect,
            pan_top_to_bottom_effect,
            pan_bottom_to_top_effect,
            ken_burns_effect,
            parallax_effect,
        ]
        effect_fn = random.choice(mid_effects)
        return effect_fn(clip)

def apply_camera_shake(clip, duration=0.6, intensity=15):
    """Videonun ilk saniyelerinde şiddeti azalan bir sarsıntı (Hook) efekti uygular."""
    def filter(get_frame, t):
        frame = get_frame(t)
        if t > duration:
            return frame
        
        # Sarsıntı zamanla azalır
        decay = max(0, 1.0 - (t / duration))
        current_intensity = intensity * decay
        
        import random
        dx = int(random.uniform(-current_intensity, current_intensity))
        dy = int(random.uniform(-current_intensity, current_intensity))
        
        img = Image.fromarray(frame)
        base_size = img.size
        
        # Siyah kenar oluşmaması için hafif zoom (%5) yapıp içinden kesiyoruz
        zoom = 1.05
        new_size = [int(base_size[0] * zoom), int(base_size[1] * zoom)]
        img = img.resize(new_size, Image.LANCZOS)
        
        cx = (new_size[0] - base_size[0]) // 2 + dx
        cy = (new_size[1] - base_size[1]) // 2 + dy
        
        # Sınırların dışına çıkmamak için
        cx = max(0, min(cx, new_size[0] - base_size[0]))
        cy = max(0, min(cy, new_size[1] - base_size[1]))
        
        img = img.crop((cx, cy, cx + base_size[0], cy + base_size[1]))
        return np.array(img)
    return apply_clip_transform(clip, filter)


def apply_fade_in(clip, duration=0.4):
    """MoviePy v1/v2 uyumlu fade-in efekti."""
    try:
        # MoviePy v2
        if hasattr(clip, 'with_effects'):
            from moviepy.video.fx import FadeIn
            return clip.with_effects([FadeIn(duration)])
        # MoviePy v1
        if hasattr(clip, 'fadein'):
            return clip.fadein(duration)
    except Exception as e:
        print(f"[!] fade_in efekti uygulanamadı: {e}")
    return clip


def apply_fade_out(clip, duration=0.4):
    """MoviePy v1/v2 uyumlu fade-out efekti."""
    try:
        # MoviePy v2
        if hasattr(clip, 'with_effects'):
            from moviepy.video.fx import FadeOut
            return clip.with_effects([FadeOut(duration)])
        # MoviePy v1
        if hasattr(clip, 'fadeout'):
            return clip.fadeout(duration)
    except Exception as e:
        print(f"[!] fade_out efekti uygulanamadı: {e}")
    return clip


# ─────────────────────────────────────────────────────────────
# SİNEMATİK POST-EFEKTLER (Vignette, Film Grain, Letterbox)
# ─────────────────────────────────────────────────────────────

def apply_vignette(clip, strength=0.35):
    """Sinematik köşe karartma efekti — derinlik ve odak hissi katar."""
    # Vignette mask'ı bir kez hesapla ve önbelleğe al
    _vignette_cache = {}
    
    def filter(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        cache_key = (h, w)
        
        if cache_key not in _vignette_cache:
            # Gaussian vignette mask oluştur
            Y = np.arange(h).reshape(-1, 1)
            X = np.arange(w).reshape(1, -1)
            cx, cy = w / 2, h / 2
            # Eliptik mesafe (dikey videolarda daha iyi görünür)
            dist = np.sqrt(((X - cx) / (w / 2)) ** 2 + ((Y - cy) / (h / 2)) ** 2)
            mask = 1.0 - np.clip(dist * strength, 0, 1)
            # Pürüzsüzleştirme: mask'ı yumuşat
            mask = np.power(mask, 1.5)
            _vignette_cache[cache_key] = mask[:, :, np.newaxis].astype(np.float32)
        
        mask = _vignette_cache[cache_key]
        return np.clip(frame * mask, 0, 255).astype(np.uint8)
    
    return apply_clip_transform(clip, filter)


def apply_film_grain(clip, intensity=0.025):
    """Hafif film tanesi efekti — organik ve sinematik his verir."""
    def filter(get_frame, t):
        frame = get_frame(t)
        # Her karede farklı noise (t'ye bağlı seed ile tekrarlanabilir)
        rng = np.random.RandomState(int(t * 1000) % 2**31)
        noise = rng.normal(0, intensity * 255, frame.shape).astype(np.int16)
        noisy = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return noisy
    
    return apply_clip_transform(clip, filter)


def apply_letterbox(clip, bar_ratio=0.04):
    """Üst ve alta ince sinema bantları ekler — profesyonel görünüm."""
    def filter(get_frame, t):
        frame = get_frame(t).copy()
        h = frame.shape[0]
        bar_h = int(h * bar_ratio)
        if bar_h > 0:
            frame[:bar_h] = 0      # Üst bant
            frame[-bar_h:] = 0     # Alt bant
        return frame
    
    return apply_clip_transform(clip, filter)


def apply_cinematic_post_effects(clip, vignette=True, grain=True, letterbox=False):
    """
    Tüm sinematik post-efektleri tek çağrıyla uygular.
    Bu fonksiyon video_maker.py'den çağrılacak.
    """
    try:
        if vignette:
            clip = apply_vignette(clip, strength=0.35)
        if grain:
            clip = apply_film_grain(clip, intensity=0.020)
        if letterbox:
            clip = apply_letterbox(clip, bar_ratio=0.04)
        print("[FX] Sinematik post-efektler uygulandı (vignette, film grain)")
    except Exception as e:
        print(f"[!] Sinematik post-efekt hatası (devam ediliyor): {e}")
    return clip
