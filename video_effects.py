import numpy as np
import cv2

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
        h, w = frame.shape[:2]
        scale = 1 + (zoom_ratio * t)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        x = (new_w - w) // 2
        y = (new_h - h) // 2
        return resized[y:y+h, x:x+w]
    return apply_clip_transform(clip, filter)

def zoom_out_effect(clip, zoom_ratio=0.04):
    def filter(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        total_duration = clip.duration or 5
        max_zoom = 1 + (zoom_ratio * total_duration)
        current_zoom = max_zoom - (zoom_ratio * t)
        new_w, new_h = int(w * current_zoom), int(h * current_zoom)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        x = (new_w - w) // 2
        y = (new_h - h) // 2
        return resized[y:y+h, x:x+w]
    return apply_clip_transform(clip, filter)

def pan_left_to_right_effect(clip, pan_ratio=0.1):
    def filter(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        scale = 1.1
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        total_duration = clip.duration or 5
        max_x = new_w - w
        current_x = int((t / total_duration) * max_x)
        y = (new_h - h) // 2
        return resized[y:y+h, current_x:current_x+w]
    return apply_clip_transform(clip, filter)

def pan_top_to_bottom_effect(clip, pan_ratio=0.1):
    """Dikey videolar için yukarıdan aşağıya pan efekti."""
    def filter(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        scale = 1.1
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        total_duration = clip.duration or 5
        max_y = new_h - h
        current_y = int((t / total_duration) * max_y)
        x = (new_w - w) // 2
        return resized[current_y:current_y+h, x:x+w]
    return apply_clip_transform(clip, filter)

def pan_bottom_to_top_effect(clip, pan_ratio=0.1):
    """Dikey videolar için aşağıdan yukarıya pan efekti."""
    def filter(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        scale = 1.1
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        total_duration = clip.duration or 5
        max_y = new_h - h
        current_y = max_y - int((t / total_duration) * max_y)
        x = (new_w - w) // 2
        return resized[current_y:current_y+h, x:x+w]
    return apply_clip_transform(clip, filter)

def ken_burns_effect(clip, zoom_ratio=0.06):
    """Ken Burns — eşzamanlı zoom + pan (sinematik klasik)."""
    def filter(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        total_duration = clip.duration or 5
        progress = t / total_duration
        current_zoom = 1 + (zoom_ratio * progress * total_duration)
        new_w, new_h = int(w * current_zoom), int(h * current_zoom)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        # Soldan sağa + hafif yukarıdan aşağıya pan
        max_x = new_w - w
        max_y = new_h - h
        x = int(progress * max_x * 0.6)
        y = int(progress * max_y * 0.3)
        x = max(0, min(x, max_x))
        y = max(0, min(y, max_y))
        return resized[y:y+h, x:x+w]
    return apply_clip_transform(clip, filter)

def parallax_effect(clip, intensity=0.03):
    """Sahte parallax — kenarları daha hızlı hareket ettirerek derinlik hissi."""
    import math
    def filter(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        total_duration = clip.duration or 5
        progress = t / total_duration
        # Hafif zoom + offset
        zoom = 1.08
        new_w, new_h = int(w * zoom), int(h * zoom)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        # Sinüs hareketi (ileri-geri sallanma)
        dx = int(math.sin(progress * math.pi * 2) * intensity * w)
        dy = int(math.cos(progress * math.pi) * intensity * h * 0.5)
        cx = (new_w - w) // 2 + dx
        cy = (new_h - h) // 2 + dy
        cx = max(0, min(cx, new_w - w))
        cy = max(0, min(cy, new_h - h))
        return resized[cy:cy+h, cx:cx+w]
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
    import random as _random
    def filter(get_frame, t):
        frame = get_frame(t)
        if t > duration:
            return frame
        
        # Sarsıntı zamanla azalır
        decay = max(0, 1.0 - (t / duration))
        current_intensity = intensity * decay
        
        dx = int(_random.uniform(-current_intensity, current_intensity))
        dy = int(_random.uniform(-current_intensity, current_intensity))
        
        h, w = frame.shape[:2]
        
        # Siyah kenar oluşmaması için hafif zoom (%5) yapıp içinden kesiyoruz
        zoom = 1.05
        new_w, new_h = int(w * zoom), int(h * zoom)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        cx = (new_w - w) // 2 + dx
        cy = (new_h - h) // 2 + dy
        
        # Sınırların dışına çıkmamak için
        cx = max(0, min(cx, new_w - w))
        cy = max(0, min(cy, new_h - h))
        
        return resized[cy:cy+h, cx:cx+w]
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


def apply_procedural_light_leak(clip, intensity=0.18):
    """
    Klip üzerine matematiksel (prosedürel) olarak sinematik, yumuşak akan bir 
    ışık sızıntısı (light leak) katmanı ekler. Her karede farklı konumda parlar.
    """
    import numpy as np
    import math

    _grid_cache = {}

    def filter(get_frame, t):
        frame = get_frame(t).astype(np.float32)
        h, w = frame.shape[:2]
        
        # Grid cache'leme
        if (h, w) not in _grid_cache:
            Y, X = np.ogrid[:h, :w]
            _grid_cache[(h, w)] = (X, Y)
        else:
            X, Y = _grid_cache[(h, w)]

        # Zaman bazlı yumuşak ve doğal hareket
        cx1 = w * (0.5 + 0.45 * math.sin(t * 0.95 + 1.2))
        cy1 = h * (0.2 + 0.3 * math.cos(t * 0.7 + 0.5))
        r1 = max(w * 0.25, w * (0.4 + 0.15 * math.sin(t * 1.3)))
        alpha1 = intensity * (0.6 + 0.4 * math.sin(t * 1.8))

        cx2 = w * (0.3 + 0.45 * math.cos(t * 1.1 + 2.5))
        cy2 = h * (0.7 + 0.25 * math.sin(t * 0.85 + 3.1))
        r2 = max(w * 0.2, w * (0.3 + 0.12 * math.cos(t * 1.5)))
        alpha2 = intensity * 0.6 * (0.5 + 0.5 * math.cos(t * 1.4 + 1.0))

        dist_sq1 = (X - cx1) ** 2 + (Y - cy1) ** 2
        g1 = np.exp(-dist_sq1 / (2 * (r1 ** 2))) * alpha1

        dist_sq2 = (X - cx2) ** 2 + (Y - cy2) ** 2
        g2 = np.exp(-dist_sq2 / (2 * (r2 ** 2))) * alpha2

        color1 = np.array([255.0, 135.0, 30.0], dtype=np.float32) # Altın / Amber
        color2 = np.array([245.0, 45.0, 95.0], dtype=np.float32)  # Sinematik Pembe / Kırmızı

        leak = g1[:, :, np.newaxis] * color1 + g2[:, :, np.newaxis] * color2
        blended = frame + leak
        return np.clip(blended, 0, 255).astype(np.uint8)

    return apply_clip_transform(clip, filter)


def apply_zoom_transition_in(clip, duration=0.45):
    """Giriş sahnesi için hızlı büyüyerek gelme efekti."""
    import cv2
    def filter(get_frame, t):
        frame = get_frame(t)
        if t > duration:
            return frame
        h, w = frame.shape[:2]
        progress = t / duration
        scale = 0.45 + 0.55 * progress
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        x = (new_w - w) // 2
        y = (new_h - h) // 2
        if x >= 0 and y >= 0:
            return resized[y:y+h, x:x+w]
        else:
            pad_y = max(0, -y)
            pad_x = max(0, -x)
            padded = cv2.copyMakeBorder(resized, pad_y, pad_y, pad_x, pad_x, cv2.BORDER_CONSTANT, value=[0,0,0])
            return padded[pad_y:pad_y+h, pad_x:pad_x+w]
    return apply_clip_transform(clip, filter)


def apply_zoom_transition_out(clip, duration=0.45):
    """Çıkış sahnesi için hızlı büyüyerek yok olma efekti."""
    import cv2
    def filter(get_frame, t):
        frame = get_frame(t)
        total_dur = clip.duration or 5.0
        if t < total_dur - duration:
            return frame
        h, w = frame.shape[:2]
        progress = (t - (total_dur - duration)) / duration
        scale = 1.0 + 0.55 * progress
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        x = (new_w - w) // 2
        y = (new_h - h) // 2
        return resized[y:y+h, x:x+w]
    return apply_clip_transform(clip, filter)


def apply_spin_transition_in(clip, duration=0.45):
    """Giriş sahnesi için dönerek gelme efekti."""
    import cv2
    def filter(get_frame, t):
        frame = get_frame(t)
        if t > duration:
            return frame
        h, w = frame.shape[:2]
        progress = t / duration
        angle = -180 * (1 - progress)
        scale = 0.5 + 0.5 * progress
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, scale)
        rotated = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=[0,0,0])
        return rotated
    return apply_clip_transform(clip, filter)


def apply_spin_transition_out(clip, duration=0.45):
    """Çıkış sahnesi için dönerek gitme efekti."""
    import cv2
    def filter(get_frame, t):
        frame = get_frame(t)
        total_dur = clip.duration or 5.0
        if t < total_dur - duration:
            return frame
        h, w = frame.shape[:2]
        progress = (t - (total_dur - duration)) / duration
        angle = 180 * progress
        scale = 1.0 - 0.5 * progress
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, scale)
        rotated = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=[0,0,0])
        return rotated
    return apply_clip_transform(clip, filter)


def apply_glitch_transition(clip, duration=0.35, is_outgoing=True):
    """Chromatic aberration ve rastgele blok satır kayması ile glitch geçişi."""
    import random
    import numpy as np
    def filter(get_frame, t):
        frame = get_frame(t)
        total_dur = clip.duration or 5.0
        if is_outgoing:
            if t < total_dur - duration:
                return frame
            progress = (t - (total_dur - duration)) / duration
        else:
            if t > duration:
                return frame
            progress = 1.0 - (t / duration)
        if progress <= 0:
            return frame
        h, w = frame.shape[:2]
        glitched = frame.copy()
        shift = int(w * 0.05 * progress)
        if shift > 0:
            r = frame[:, :, 0]
            g = frame[:, :, 1]
            b = frame[:, :, 2]
            glitched[:, :, 0] = np.roll(r, shift, axis=1)
            glitched[:, :, 1] = g
            glitched[:, :, 2] = np.roll(b, -shift, axis=1)
        num_slices = int(5 + 12 * progress)
        for _ in range(num_slices):
            slice_y = random.randint(0, h - 30)
            slice_h = random.randint(10, 35)
            slice_shift = random.randint(-int(w * 0.09 * progress), int(w * 0.09 * progress))
            if slice_shift != 0:
                slice_img = glitched[slice_y:slice_y+slice_h, :]
                glitched[slice_y:slice_y+slice_h, :] = np.roll(slice_img, slice_shift, axis=1)
        return glitched
    return apply_clip_transform(clip, filter)


def make_slide_in_position(w, h, direction="left", duration=0.45):
    """Kompozit katmanlar için slayt geçiş pozisyon fonksiyonu."""
    def pos(t):
        if t > duration:
            return (0, 0)
        progress = t / duration
        if direction == "left":
            return (int(w * (1 - progress)), 0)
        elif direction == "right":
            return (int(-w * (1 - progress)), 0)
        elif direction == "up":
            return (0, int(h * (1 - progress)))
        elif direction == "down":
            return (0, int(-h * (1 - progress)))
        return (0, 0)
    return pos


def apply_cinematic_post_effects(clip, vignette=True, grain=True, letterbox=False, light_leak=False):
    """
    Tüm sinematik post-efektleri tek çağrıyla uygular.
    Bu fonksiyon video_maker.py'den çağrılacak.
    """
    try:
        if light_leak:
            clip = apply_procedural_light_leak(clip, intensity=0.16)
        if vignette:
            clip = apply_vignette(clip, strength=0.35)
        if grain:
            clip = apply_film_grain(clip, intensity=0.020)
        if letterbox:
            clip = apply_letterbox(clip, bar_ratio=0.04)
        print("[FX] Sinematik post-efektler uygulandı (vignette, film grain, light leak)")
    except Exception as e:
        print(f"[!] Sinematik post-efekt hatası (devam ediliyor): {e}")
    return clip


def align_durations_to_beats(slide_durations, audio_path):
    """
    Slayt sürelerini (slide_durations) arka plan müziğinin vuruş anlarına (beats) kilitler.
    Her geçişin tam bir davul vuruşunda/tempo anında gerçekleşmesini sağlar.
    """
    try:
        import librosa
        import numpy as np
        import os
        
        if not audio_path or not os.path.exists(audio_path):
            return slide_durations

        print(f"[Beat-Sync] Müzik analiz ediliyor: {audio_path}...")
        # Düşük örnekleme hızı (sr=22050) ve mono yükleme ile süper hızlı analiz
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        
        # Tempo ve vuruş zaman kodları bulma
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        
        if len(beat_times) < 2:
            print("[Beat-Sync] Yetersiz ritim vuruşu tespit edildi, varsayılan süreler kullanılıyor.")
            return slide_durations
            
        print(f"[Beat-Sync] Ritim tespiti başarılı: {tempo:.1f} BPM. Vuruş sayısı: {len(beat_times)}")
        
        # Bitiş süreleri kümülatif toplam hesabı
        cum_durations = np.cumsum(slide_durations)
        new_cum_durations = []
        
        for t in cum_durations:
            # En yakın vuruş zamanını bul
            idx = (np.abs(np.array(beat_times) - t)).argmin()
            closest_beat = beat_times[idx]
            
            # Aşırı konuşma senkron kaymasını engellemek için %35'lik koruma bariyeri
            if abs(closest_beat - t) < t * 0.35:
                new_cum_durations.append(closest_beat)
            else:
                new_cum_durations.append(t)
                
        # Tekrar tekil süreleri elde et
        new_durations = []
        last = 0.0
        for t in new_cum_durations:
            dur = t - last
            new_durations.append(max(2.0, dur))
            last = t
            
        print("[Beat-Sync] Sahne geçiş süreleri müzik ritmine kilitlendi! 🎵")
        return new_durations
        
    except ImportError:
        print("[Beat-Sync] 'librosa' kütüphanesi kurulu değil. Ritmik kurgu devre dışı bırakıldı.")
        return slide_durations
    except Exception as e:
        print(f"[Beat-Sync] Ritim eşleme sırasında hata oluştu: {e}")
        return slide_durations
