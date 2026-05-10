"""
Image Animator — Görselden Video Üretme
========================================
Stability AI (SVD), Runway ML, Replicate, Luma AI
API'leri ile statik görselleri hareketli videolara dönüştürür.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Global session
_session = None


def _get_session():
    global _session
    if _session is None:
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        _session = requests.Session()
        retry = Retry(total=2, connect=2, read=2, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=3, pool_maxsize=5)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    return _session


def _download_file(url: str, output_path: str, timeout: int = 60) -> bool:
    try:
        session = _get_session()
        resp = session.get(url, stream=True, timeout=timeout)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    if chunk:
                        f.write(chunk)
            return True
        print(f"[-] Animasyon indirme başarısız: HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"[-] Animasyon indirme hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# STABILITY AI (Stable Video Diffusion)
# ─────────────────────────────────────────────────────────────

def animate_stability_ai(image_path: str, output_path: str) -> bool:
    """
    Stability AI Stable Video Diffusion ile görselden video üretir.
    API key: STABILITY_API_KEY (.env)
    """
    api_key = os.environ.get("STABILITY_API_KEY", "").strip()
    if not api_key:
        print("[!] STABILITY_API_KEY bulunamadı, Stability AI atlanıyor.")
        return False

    print(f"[+] Görsel animasyonu başlatılıyor... (Stability AI SVD: '{image_path}')")

    try:
        url = "https://api.stability.ai/v2beta/image-to-video"
        headers = {"Authorization": f"Bearer {api_key}"}

        with open(image_path, "rb") as img_file:
            files = {"image": img_file}
            data = {
                "seed": 0,
                "cfg_scale": 1.8,
                "motion_bucket_id": 127,
            }
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)

        if resp.status_code != 200:
            print(f"[-] Stability AI başlatma hatası: HTTP {resp.status_code} — {resp.text[:200]}")
            return False

        generation_id = resp.json().get("id")
        if not generation_id:
            print("[-] Stability AI: generation_id alınamadı.")
            return False

        # Sonucu bekle (polling)
        result_url = f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}"
        max_wait = 120  # 2 dakika
        waited = 0

        while waited < max_wait:
            time.sleep(5)
            waited += 5
            result_resp = requests.get(result_url, headers={**headers, "Accept": "video/*"}, timeout=30)

            if result_resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(result_resp.content)
                print(f"[+] Stability AI animasyonu kaydedildi: {output_path}")
                return True
            elif result_resp.status_code == 202:
                # Henüz hazır değil
                continue
            else:
                print(f"[-] Stability AI sonuç hatası: HTTP {result_resp.status_code}")
                return False

        print("[-] Stability AI: Zaman aşımı (2 dakika)")
        return False

    except Exception as e:
        print(f"[-] Stability AI hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# RUNWAY ML (Gen-3 Alpha)
# ─────────────────────────────────────────────────────────────

def animate_runway(image_path: str, output_path: str) -> bool:
    """
    Runway ML Gen-3 ile görselden video üretir.
    API key: RUNWAY_API_KEY (.env)
    """
    api_key = os.environ.get("RUNWAY_API_KEY", "").strip()
    if not api_key:
        print("[!] RUNWAY_API_KEY bulunamadı, Runway ML atlanıyor.")
        return False

    print(f"[+] Görsel animasyonu başlatılıyor... (Runway ML: '{image_path}')")

    try:
        import base64
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Runway-Version": "2024-11-06",
        }

        payload = {
            "model": "gen3a_turbo",
            "promptImage": f"data:image/jpeg;base64,{image_b64}",
            "promptText": "Smooth cinematic motion, slow camera movement",
            "duration": 5,
            "ratio": "9:16",
        }

        resp = requests.post(
            "https://api.dev.runwayml.com/v1/image_to_video",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if resp.status_code not in (200, 201):
            print(f"[-] Runway ML başlatma hatası: HTTP {resp.status_code} — {resp.text[:200]}")
            return False

        task_id = resp.json().get("id")
        if not task_id:
            print("[-] Runway ML: task_id alınamadı.")
            return False

        # Sonucu bekle
        poll_url = f"https://api.dev.runwayml.com/v1/tasks/{task_id}"
        max_wait = 180  # 3 dakika
        waited = 0

        while waited < max_wait:
            time.sleep(10)
            waited += 10
            poll_resp = requests.get(poll_url, headers=headers, timeout=30)

            if poll_resp.status_code == 200:
                result = poll_resp.json()
                status = result.get("status", "")

                if status == "SUCCEEDED":
                    output_urls = result.get("output", [])
                    if output_urls:
                        if _download_file(output_urls[0], output_path):
                            print(f"[+] Runway ML animasyonu kaydedildi: {output_path}")
                            return True
                    return False
                elif status == "FAILED":
                    print(f"[-] Runway ML üretim başarısız: {result.get('failure', 'bilinmeyen hata')}")
                    return False
                # PENDING/RUNNING → devam et

        print("[-] Runway ML: Zaman aşımı (3 dakika)")
        return False

    except Exception as e:
        print(f"[-] Runway ML hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# REPLICATE (SVD / AnimateDiff)
# ─────────────────────────────────────────────────────────────

def animate_replicate(image_path: str, output_path: str, model: str = "stability-ai/svd") -> bool:
    """
    Replicate platformunda görselden video üretir.
    Modeller: stability-ai/svd, stability-ai/stable-video-diffusion
    """
    try:
        import replicate
    except ImportError:
        print("[!] 'replicate' modülü kurulu değil, Replicate atlanıyor.")
        return False

    api_token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not api_token:
        print("[!] REPLICATE_API_TOKEN bulunamadı, Replicate atlanıyor.")
        return False

    print(f"[+] Görsel animasyonu başlatılıyor... (Replicate: {model})")

    try:
        with open(image_path, "rb") as image_file:
            output = replicate.run(
                f"{model}:3f776d5209f25790c05739091851084741604a8839965d13735232759905470d",
                input={
                    "image": image_file,
                    "video_length": "14_frames_with_svd",
                    "fps": 6,
                    "motion_bucket_id": 127,
                },
            )

        video_url = output if isinstance(output, str) else (output[0] if isinstance(output, list) else str(output))

        if _download_file(video_url, output_path):
            print(f"[+] Replicate animasyonu kaydedildi: {output_path}")
            return True
        return False

    except Exception as e:
        print(f"[-] Replicate hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# LUMA AI (Dream Machine)
# ─────────────────────────────────────────────────────────────

def animate_luma(image_path: str, output_path: str) -> bool:
    """
    Luma AI Dream Machine ile görselden video üretir.
    API key: LUMA_API_KEY (.env)
    """
    api_key = os.environ.get("LUMA_API_KEY", "").strip()
    if not api_key:
        print("[!] LUMA_API_KEY bulunamadı, Luma AI atlanıyor.")
        return False

    print(f"[+] Görsel animasyonu başlatılıyor... (Luma AI: '{image_path}')")

    try:
        import base64
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "prompt": "Smooth cinematic motion, slow natural movement, professional quality",
            "keyframes": {
                "frame0": {
                    "type": "image",
                    "url": f"data:image/jpeg;base64,{image_b64}",
                }
            },
            "aspect_ratio": "9:16",
        }

        resp = requests.post(
            "https://api.lumalabs.ai/dream-machine/v1/generations",
            headers=headers,
            json=payload,
            timeout=30,
        )

        if resp.status_code not in (200, 201):
            print(f"[-] Luma AI başlatma hatası: HTTP {resp.status_code} — {resp.text[:200]}")
            return False

        generation_id = resp.json().get("id")
        if not generation_id:
            print("[-] Luma AI: generation_id alınamadı.")
            return False

        # Sonucu bekle
        poll_url = f"https://api.lumalabs.ai/dream-machine/v1/generations/{generation_id}"
        max_wait = 180
        waited = 0

        while waited < max_wait:
            time.sleep(10)
            waited += 10
            poll_resp = requests.get(poll_url, headers=headers, timeout=30)

            if poll_resp.status_code == 200:
                result = poll_resp.json()
                state = result.get("state", "")

                if state == "completed":
                    video_url = result.get("assets", {}).get("video")
                    if video_url:
                        if _download_file(video_url, output_path):
                            print(f"[+] Luma AI animasyonu kaydedildi: {output_path}")
                            return True
                    return False
                elif state == "failed":
                    print(f"[-] Luma AI üretim başarısız: {result.get('failure_reason', 'bilinmeyen')}")
                    return False
                # queued/dreaming → devam et

        print("[-] Luma AI: Zaman aşımı (3 dakika)")
        return False

    except Exception as e:
        print(f"[-] Luma AI hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# ANA YÖNLENDİRİCİ
# ─────────────────────────────────────────────────────────────

def animate_image(image_path: str, output_path: str, provider: str = "replicate") -> bool:
    """
    Görselden video üretme ana fonksiyonu.
    Provider'a göre uygun API'yi çağırır, başarısız olursa fallback kullanır.
    
    Providers: stability_ai, runway, replicate, luma, auto
    """
    provider_lower = provider.lower().replace("-", "_").replace(" ", "_")

    # Provider haritası
    provider_funcs = {
        "stability_ai": animate_stability_ai,
        "stability": animate_stability_ai,
        "runway": animate_runway,
        "runway_ml": animate_runway,
        "replicate": animate_replicate,
        "luma": animate_luma,
        "luma_ai": animate_luma,
    }

    # Auto mod: sırayla dene
    if provider_lower == "auto":
        for name, func in [
            ("Stability AI", animate_stability_ai),
            ("Replicate", animate_replicate),
            ("Luma AI", animate_luma),
            ("Runway ML", animate_runway),
        ]:
            print(f"[Auto-Animate] {name} deneniyor...")
            if func(image_path, output_path):
                return True
        print("[-] Auto-Animate: Tüm sağlayıcılar başarısız.")
        return False

    # Belirli provider
    func = provider_funcs.get(provider_lower)
    if func:
        success = func(image_path, output_path)
        if success:
            return True

        # Fallback: Replicate (en yaygın)
        if provider_lower != "replicate":
            print(f"[!] {provider} başarısız, Replicate fallback deneniyor...")
            return animate_replicate(image_path, output_path)
        return False

    print(f"[!] Bilinmeyen animasyon sağlayıcısı: '{provider}'")
    return False


if __name__ == "__main__":
    # Test
    test_img = "test_frame.jpg"
    if os.path.exists(test_img):
        animate_image(test_img, "test_animated.mp4", "replicate")
