"""
GIF / Meme / Kısa Video Klip Fetcher
=====================================
Giphy, Tenor, Pexels Video, Pixabay Video API'lerinden
kısa klip/GIF indirip MP4 formatında döner.
"""

import os
import random
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

# Global session with connection pooling
_session = None


def _get_session():
    global _session
    if _session is None:
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        _session = requests.Session()
        retry = Retry(total=2, connect=2, read=2, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=5, pool_maxsize=10)
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    return _session


def _download_file(url: str, output_path: str, timeout: int = 30) -> bool:
    """URL'den dosya indir."""
    try:
        session = _get_session()
        resp = session.get(url, stream=True, timeout=timeout)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(1024):
                    if chunk:
                        f.write(chunk)
            return True
        print(f"[-] İndirme başarısız: HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"[-] İndirme hatası: {e}")
        return False


def convert_gif_to_mp4(gif_path: str, mp4_path: str) -> bool:
    """GIF'i MoviePy ile MP4'e dönüştürür (ses yok)."""
    try:
        from moviepy import VideoFileClip
        clip = VideoFileClip(gif_path)
        clip.write_videofile(
            mp4_path,
            codec="libx264",
            audio=False,
            fps=15,
            preset="ultrafast",
            logger=None,
        )
        clip.close()
        # GIF'i sil
        if os.path.exists(gif_path):
            os.remove(gif_path)
        return True
    except Exception as e:
        print(f"[-] GIF→MP4 dönüşüm hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# GIPHY API
# ─────────────────────────────────────────────────────────────

def fetch_gif_giphy(query: str, output_path: str) -> bool:
    """Giphy API ile GIF arayıp MP4 olarak indirir."""
    api_key = os.environ.get("GIPHY_API_KEY", "").strip()
    if not api_key:
        print("[!] GIPHY_API_KEY bulunamadı, Giphy atlanıyor.")
        return False

    print(f"[+] GIF aranıyor... (Giphy: '{query}')")
    session = _get_session()

    try:
        params = {
            "api_key": api_key,
            "q": query,
            "limit": 15,
            "offset": random.randint(0, 50),
            "rating": "g",
            "lang": "en",
        }
        resp = session.get("https://api.giphy.com/v1/gifs/search", params=params, timeout=10)
        if resp.status_code != 200:
            print(f"[-] Giphy API hatası: HTTP {resp.status_code}")
            return False

        data = resp.json().get("data", [])
        if not data:
            print(f"[-] Giphy: '{query}' için sonuç bulunamadı.")
            return False

        gif = random.choice(data)
        # MP4 formatını tercih et (daha küçük, daha hızlı)
        mp4_url = gif.get("images", {}).get("original_mp4", {}).get("mp4")
        if mp4_url:
            if _download_file(mp4_url, output_path):
                print(f"[+] Giphy MP4 kaydedildi: {output_path}")
                return True

        # Fallback: GIF indir ve MP4'e dönüştür
        gif_url = gif.get("images", {}).get("original", {}).get("url")
        if gif_url:
            gif_temp = output_path.replace(".mp4", ".gif")
            if _download_file(gif_url, gif_temp):
                if convert_gif_to_mp4(gif_temp, output_path):
                    print(f"[+] Giphy GIF→MP4 kaydedildi: {output_path}")
                    return True

        return False
    except Exception as e:
        print(f"[-] Giphy hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# TENOR API
# ─────────────────────────────────────────────────────────────

def fetch_gif_tenor(query: str, output_path: str) -> bool:
    """Tenor API ile GIF arayıp MP4 olarak indirir."""
    api_key = os.environ.get("TENOR_API_KEY", "").strip()
    if not api_key:
        print("[!] TENOR_API_KEY bulunamadı, Tenor atlanıyor.")
        return False

    print(f"[+] GIF aranıyor... (Tenor: '{query}')")
    session = _get_session()

    try:
        params = {
            "key": api_key,
            "q": query,
            "limit": 15,
            "media_filter": "mp4,gif",
            "contentfilter": "medium",
        }
        resp = session.get("https://tenor.googleapis.com/v2/search", params=params, timeout=10)
        if resp.status_code != 200:
            print(f"[-] Tenor API hatası: HTTP {resp.status_code}")
            return False

        results = resp.json().get("results", [])
        if not results:
            print(f"[-] Tenor: '{query}' için sonuç bulunamadı.")
            return False

        item = random.choice(results)
        media = item.get("media_formats", {})

        # MP4 tercih et
        mp4_data = media.get("mp4", {})
        if mp4_data.get("url"):
            if _download_file(mp4_data["url"], output_path):
                print(f"[+] Tenor MP4 kaydedildi: {output_path}")
                return True

        # Fallback: GIF
        gif_data = media.get("gif", {})
        if gif_data.get("url"):
            gif_temp = output_path.replace(".mp4", ".gif")
            if _download_file(gif_data["url"], gif_temp):
                if convert_gif_to_mp4(gif_temp, output_path):
                    print(f"[+] Tenor GIF→MP4 kaydedildi: {output_path}")
                    return True

        return False
    except Exception as e:
        print(f"[-] Tenor hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# PEXELS VIDEO API
# ─────────────────────────────────────────────────────────────

def fetch_video_pexels(query: str, output_path: str) -> bool:
    """Pexels Video API ile kısa stok video indirir."""
    api_key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not api_key:
        print("[!] PEXELS_API_KEY bulunamadı, Pexels Video atlanıyor.")
        return False

    print(f"[+] Video klip aranıyor... (Pexels Video: '{query}')")
    session = _get_session()
    headers = {"Authorization": api_key}

    try:
        params = {
            "query": query,
            "orientation": "portrait",
            "per_page": 10,
            "page": random.randint(1, 3),
            "size": "small",  # Kısa klipler için küçük boyut
        }
        resp = session.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[-] Pexels Video API hatası: HTTP {resp.status_code}")
            return False

        videos = resp.json().get("videos", [])
        if not videos:
            print(f"[-] Pexels Video: '{query}' için sonuç bulunamadı.")
            return False

        video = random.choice(videos)
        # En uygun kalitedeki dosyayı seç (HD, portrait tercihi)
        video_files = video.get("video_files", [])
        best_file = None
        for vf in video_files:
            # Portrait ve orta çözünürlük tercih et
            if vf.get("height", 0) >= 720 and vf.get("width", 0) <= vf.get("height", 0):
                best_file = vf
                break
        if not best_file and video_files:
            best_file = video_files[0]

        if best_file and best_file.get("link"):
            if _download_file(best_file["link"], output_path):
                print(f"[+] Pexels Video kaydedildi: {output_path}")
                return True

        return False
    except Exception as e:
        print(f"[-] Pexels Video hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# PIXABAY VIDEO API
# ─────────────────────────────────────────────────────────────

def fetch_video_pixabay(query: str, output_path: str) -> bool:
    """Pixabay Video API ile kısa stok video indirir."""
    api_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not api_key:
        print("[!] PIXABAY_API_KEY bulunamadı, Pixabay Video atlanıyor.")
        return False

    print(f"[+] Video klip aranıyor... (Pixabay Video: '{query}')")
    session = _get_session()

    try:
        params = {
            "key": api_key,
            "q": urllib.parse.quote(query),
            "video_type": "film",
            "per_page": 10,
            "page": random.randint(1, 3),
            "safesearch": "true",
        }
        resp = session.get("https://pixabay.com/api/videos/", params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[-] Pixabay Video API hatası: HTTP {resp.status_code}")
            return False

        hits = resp.json().get("hits", [])
        if not hits:
            print(f"[-] Pixabay Video: '{query}' için sonuç bulunamadı.")
            return False

        hit = random.choice(hits)
        videos = hit.get("videos", {})
        # Medium kalite tercih et (dengeli boyut/kalite)
        medium = videos.get("medium", {})
        video_url = medium.get("url") or videos.get("small", {}).get("url")

        if video_url:
            if _download_file(video_url, output_path):
                print(f"[+] Pixabay Video kaydedildi: {output_path}")
                return True

        return False
    except Exception as e:
        print(f"[-] Pixabay Video hatası: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# OTOMATİK FALLBACK ZİNCİRİ
# ─────────────────────────────────────────────────────────────

def fetch_clip_auto(query: str, output_path: str) -> bool:
    """
    Otomatik klip arama: Pexels Video → Pixabay Video → Giphy → Tenor
    Stok videoları önce dener (daha kaliteli), sonra GIF kaynaklarına düşer.
    """
    print(f"[+] Clip-Auto modu başlatıldı: '{query}'")

    # 1. Pexels Video (en yüksek kalite, portrait desteği)
    if fetch_video_pexels(query, output_path):
        return True

    # 2. Pixabay Video
    if fetch_video_pixabay(query, output_path):
        return True

    # 3. Giphy (GIF → MP4)
    if fetch_gif_giphy(query, output_path):
        return True

    # 4. Tenor (GIF → MP4)
    if fetch_gif_tenor(query, output_path):
        return True

    print(f"[-] Tüm klip kaynakları başarısız: '{query}'")
    return False


if __name__ == "__main__":
    # Test
    test_query = "space explosion"
    os.makedirs("assets", exist_ok=True)
    fetch_clip_auto(test_query, "assets/test_clip.mp4")
