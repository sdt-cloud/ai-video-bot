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
