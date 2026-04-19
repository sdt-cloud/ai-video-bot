import requests
import urllib.parse
import os
import time
import random
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

# Global session with connection pooling and retry strategy
_session = None
_replicate_checked = False
_replicate_available = False


def is_replicate_available():
    """Replicate paketinin kurulu olup olmadığını bir kez kontrol eder."""
    global _replicate_checked, _replicate_available
    if _replicate_checked:
        return _replicate_available

    try:
        import replicate  # noqa: F401
        _replicate_available = True
    except ImportError:
        _replicate_available = False
        print("[!] 'replicate' modülü kurulu değil. Replicate tabanlı görsellerde Pollinations fallback kullanılacak.")

    _replicate_checked = True
    return _replicate_available

def get_session():
    """Connection pooling ile requests session oluştur"""
    global _session
    if _session is None:
        _session = requests.Session()
        
        # Retry stratejisi
        retry_strategy = Retry(
            total=2,
            connect=2,
            read=2,
            backoff_factor=0.4,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        _session.mount("http://", adapter)
        _session.mount("https://", adapter)
    
    return _session

def generate_image_openai(prompt, output_filename):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    print(f"[+] '{output_filename}' için görsel indiriliyor... (AI: DALL-E 3)")
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792", # DALL-E 3 desteklenen en yakın portre çözünürlüğü
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        
        # Resmi URL'den indirip kaydetme - session kullan
        session = get_session()
        img_response = session.get(image_url, stream=True, timeout=30)
        if img_response.status_code == 200:
            with open(output_filename, 'wb') as f:
                for chunk in img_response.iter_content(1024):
                    f.write(chunk)
            print(f"[+] Görsel kaydedildi: {output_filename}")
            return True
        else:
            print(f"[-] Görsel indirilemedi, HTTP {img_response.status_code}")
            return False
            
    except Exception as e:
        print(f"[-] DALL-E Görseli üretilirken hata oluştu: {e}")
        # Fallback: Pollinations kullan
        print(f"[+] Fallback: Pollinations ile deneniyor...")
        return generate_image_pollinations(prompt, output_filename)

def generate_image_pollinations(prompt, output_filename):
    print(f"[+] '{output_filename}' için görsel indiriliyor... (AI: Pollinations)")
    
    # URL Encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)

    # Timeout durumlarında farklı URL varyantlarıyla yeniden dene.
    seed = int(time.time() * 1000) % 1000000
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&seed={seed + 1}",
    ]

    session = get_session()
    for attempt, url in enumerate(urls, start=1):
        try:
            response = session.get(url, stream=True, timeout=(10, 40))
            if response.status_code == 200:
                with open(output_filename, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        if chunk:
                            f.write(chunk)
                print(f"[+] Görsel kaydedildi: {output_filename}")
                return True

            print(f"[-] Pollinations denemesi {attempt} başarısız, HTTP Status: {response.status_code}")
        except requests.exceptions.ReadTimeout:
            print(f"[!] Pollinations denemesi {attempt} timeout oldu, yeniden deneniyor...")
        except Exception as e:
            print(f"[-] Pollinations denemesi {attempt} hata: {e}")

    return False

def generate_image_replicate(prompt, output_filename, model_name="black-forest-labs/flux-schnell"):
    if not is_replicate_available():
        print(f"[+] Fallback: '{output_filename}' için Pollinations deneniyor...")
        return generate_image_pollinations(prompt, output_filename)

    print(f"[+] '{output_filename}' için görsel üretiliyor... (AI: Replicate - {model_name})")
    
    try:
        import replicate

        # Replicate modelleri için en boy oranı ayarları (portre moduna zorla)
        input_data = {
            "prompt": prompt,
            "aspect_ratio": "9:16",
        }
        
        # Farklı modeller için farklı girdi parametreleri gerekebilir
        if "flux" in model_name:
            input_data["output_format"] = "webp"
            input_data["num_outputs"] = 1
        elif "sdxl" in model_name:
            input_data = {
                "prompt": prompt,
                "width": 768,
                "height": 1344, # SDXL portre
                "refine": "expert_ensemble_refiner",
                "apply_watermark": False,
                "num_inference_steps": 25
            }

        output = replicate.run(model_name, input=input_data)
        
        # Çıktı genelde bir liste olur (URL'ler)
        image_url = output[0] if isinstance(output, list) else output
        
        # Resmi indir - session kullan
        session = get_session()
        img_response = session.get(image_url, stream=True, timeout=30)
        if img_response.status_code == 200:
            with open(output_filename, 'wb') as f:
                for chunk in img_response.iter_content(1024):
                    f.write(chunk)
            print(f"[+] Görsel kaydedildi: {output_filename}")
            return True
        else:
            print(f"[-] Replicate Görseli indirilemedi, HTTP Status: {img_response.status_code}")
            return False
            
    except Exception as e:
        print(f"[-] Replicate hatası: {e}")
        print(f"[+] Fallback: Pollinations ile yeniden deneniyor...")
        return generate_image_pollinations(prompt, output_filename)

# ─────────────────────────────────────────────────────────────
# STOK GÖRSEL SAĞLAYICILARI (ücretsiz, çok hızlı)
# ─────────────────────────────────────────────────────────────

def _stock_search_keyword(prompt: str) -> str:
    """Uzun prompt'tan kısa arama anahtar kelimesi çıkar (ilk 4 kelime)."""
    words = prompt.strip().split()
    return " ".join(words[:4]) if len(words) >= 4 else prompt[:60]


def fetch_stock_image_pexels(prompt: str, output_filename: str) -> bool:
    """Pexels API ile ücretsiz stok görsel indir. API key .env'de PEXELS_API_KEY olmalı."""
    api_key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not api_key:
        print("[!] PEXELS_API_KEY bulunamadı, Pexels atlanıyor.")
        return False

    keyword = _stock_search_keyword(prompt)
    print(f"[+] '{output_filename}' için görsel aranıyor... (Pexels: '{keyword}')")

    session = get_session()
    headers = {"Authorization": api_key}

    try:
        # Portrait (dikey) 1080x1920 uyumlu görseller için
        params = {
            "query": keyword,
            "orientation": "portrait",
            "per_page": 10,
            "page": random.randint(1, 3),
        }
        resp = session.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[-] Pexels API hatası: HTTP {resp.status_code}")
            return False

        data = resp.json()
        photos = data.get("photos", [])
        if not photos:
            print(f"[-] Pexels: '{keyword}' için sonuç bulunamadı.")
            return False

        # En büyük dikey görseli seç
        photo = random.choice(photos)
        img_url = photo["src"].get("large2x") or photo["src"].get("large") or photo["src"]["original"]

        img_resp = session.get(img_url, stream=True, timeout=30)
        if img_resp.status_code == 200:
            with open(output_filename, "wb") as f:
                for chunk in img_resp.iter_content(1024):
                    if chunk:
                        f.write(chunk)
            print(f"[+] Pexels görseli kaydedildi: {output_filename}")
            return True
        else:
            print(f"[-] Pexels görsel indirilemedi: HTTP {img_resp.status_code}")
            return False

    except Exception as e:
        print(f"[-] Pexels hatası: {e}")
        return False


def fetch_stock_image_pixabay(prompt: str, output_filename: str) -> bool:
    """Pixabay API ile ücretsiz stok görsel indir. API key .env'de PIXABAY_API_KEY olmalı."""
    api_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not api_key:
        print("[!] PIXABAY_API_KEY bulunamadı, Pixabay atlanıyor.")
        return False

    keyword = _stock_search_keyword(prompt)
    print(f"[+] '{output_filename}' için görsel aranıyor... (Pixabay: '{keyword}')")

    session = get_session()
    try:
        params = {
            "key": api_key,
            "q": urllib.parse.quote(keyword),
            "image_type": "photo",
            "orientation": "vertical",
            "per_page": 10,
            "page": random.randint(1, 3),
            "safesearch": "true",
        }
        resp = session.get("https://pixabay.com/api/", params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[-] Pixabay API hatası: HTTP {resp.status_code}")
            return False

        data = resp.json()
        hits = data.get("hits", [])
        if not hits:
            print(f"[-] Pixabay: '{keyword}' için sonuç bulunamadı.")
            return False

        hit = random.choice(hits)
        img_url = hit.get("largeImageURL") or hit.get("webformatURL")

        img_resp = session.get(img_url, stream=True, timeout=30)
        if img_resp.status_code == 200:
            with open(output_filename, "wb") as f:
                for chunk in img_resp.iter_content(1024):
                    if chunk:
                        f.write(chunk)
            print(f"[+] Pixabay görseli kaydedildi: {output_filename}")
            return True
        else:
            print(f"[-] Pixabay görsel indirilemedi: HTTP {img_resp.status_code}")
            return False

    except Exception as e:
        print(f"[-] Pixabay hatası: {e}")
        return False


def fetch_stock_image_unsplash(prompt: str, output_filename: str) -> bool:
    """Unsplash API ile ücretsiz stok görsel indir. API key .env'de UNSPLASH_ACCESS_KEY olmalı."""
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
    if not access_key:
        print("[!] UNSPLASH_ACCESS_KEY bulunamadı, Unsplash atlanıyor.")
        return False

    keyword = _stock_search_keyword(prompt)
    print(f"[+] '{output_filename}' için görsel aranıyor... (Unsplash: '{keyword}')")

    session = get_session()
    headers = {"Authorization": f"Client-ID {access_key}"}
    try:
        params = {
            "query": keyword,
            "orientation": "portrait",
            "per_page": 10,
            "page": random.randint(1, 3),
        }
        resp = session.get("https://api.unsplash.com/search/photos", headers=headers, params=params, timeout=15)
        if resp.status_code != 200:
            print(f"[-] Unsplash API hatası: HTTP {resp.status_code}")
            return False

        data = resp.json()
        results = data.get("results", [])
        if not results:
            print(f"[-] Unsplash: '{keyword}' için sonuç bulunamadı.")
            return False

        photo = random.choice(results)
        img_url = photo["urls"].get("regular") or photo["urls"]["full"]

        img_resp = session.get(img_url, stream=True, timeout=30)
        if img_resp.status_code == 200:
            with open(output_filename, "wb") as f:
                for chunk in img_resp.iter_content(1024):
                    if chunk:
                        f.write(chunk)
            print(f"[+] Unsplash görseli kaydedildi: {output_filename}")
            return True
        else:
            print(f"[-] Unsplash görsel indirilemedi: HTTP {img_resp.status_code}")
            return False

    except Exception as e:
        print(f"[-] Unsplash hatası: {e}")
        return False


def fetch_stock_image_auto(prompt: str, output_filename: str) -> bool:
    """Otomatik stok görsel: Pexels → Pixabay → Unsplash → Pollinations → DALL-E"""
    print(f"[+] Stock-Auto modu başlatıldı: '{output_filename}'")

    # 1. Pexels
    if fetch_stock_image_pexels(prompt, output_filename):
        return True

    # 2. Pixabay
    if fetch_stock_image_pixabay(prompt, output_filename):
        return True

    # 3. Unsplash
    if fetch_stock_image_unsplash(prompt, output_filename):
        return True

    # 4. DALL-E 3
    print("[!] Tüm stok kaynaklar başarısız. DALL-E 3 deneniyor...")
    if generate_image_openai(prompt, output_filename):
        return True

    # 5. Pollinations (son çare - ücretsiz AI)
    print("[!] DALL-E da başarısız. Son çare: Pollinations deneniyor...")
    return generate_image_pollinations(prompt, output_filename)


# ─────────────────────────────────────────────────────────────
# ANA YÖNLENDIRICI
# ─────────────────────────────────────────────────────────────

def generate_image(prompt, output_filename, ai_provider="Stock-Auto"):
    provider_lower = ai_provider.lower()

    # Stok görsel sağlayıcıları
    if provider_lower == "pexels":
        return fetch_stock_image_pexels(prompt, output_filename) or generate_image_openai(prompt, output_filename)
    elif provider_lower == "pixabay":
        return fetch_stock_image_pixabay(prompt, output_filename) or generate_image_openai(prompt, output_filename)
    elif provider_lower == "unsplash":
        return fetch_stock_image_unsplash(prompt, output_filename) or generate_image_openai(prompt, output_filename)
    elif provider_lower == "stock-auto":
        return fetch_stock_image_auto(prompt, output_filename)

    # AI görsel sağlayıcıları
    elif "dall-e" in provider_lower or "openai" in provider_lower:
        return generate_image_openai(prompt, output_filename)
    elif "flux" in provider_lower:
        model = "black-forest-labs/flux-schnell"
        if "pro" in provider_lower:
            model = "black-forest-labs/flux-pro"
        return generate_image_replicate(prompt, output_filename, model)
    elif "sdxl" in provider_lower:
        return generate_image_replicate(prompt, output_filename, "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7f23bb69422f281454559869502b4")
    elif "replicate" in provider_lower:
        return generate_image_replicate(prompt, output_filename)
    elif "pollinations" in provider_lower:
        return generate_image_pollinations(prompt, output_filename)
    else:
        # Bilinmeyen sağlayıcı → Stock-Auto
        print(f"[!] Bilinmeyen sağlayıcı '{ai_provider}', Stock-Auto kullanılıyor.")
        return fetch_stock_image_auto(prompt, output_filename)

if __name__ == "__main__":
    # Test
    test_prompt = "A cinematic hyperrealistic image of an astronaut standing alone on a snowy mountain peak during a dark night with glowing stars, 8k resolution"
    generate_image(test_prompt, "test_image.jpg")
