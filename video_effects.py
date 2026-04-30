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

def apply_random_effect(clip):
    import random
    effects = [zoom_in_effect, zoom_out_effect, pan_left_to_right_effect]
    effect_fn = random.choice(effects)
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
