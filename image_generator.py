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

def generate_image_openai(prompt, output_filename, quality="standard", aspect_ratio="9:16"):
    import base64
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # gpt-image-1 / dall-e-3 size maps
    size_map = {
        "9:16": "1024x1792",
        "16:9": "1792x1024",
        "1:1": "1024x1024"
    }
    image_size = size_map.get(aspect_ratio, "1024x1792")
    
    # DALL-E 3 → gpt-image-1 migrasyonu
    quality_map = {"hd": "high", "standard": "medium"}
    mapped_quality = quality_map.get(quality, "medium")
    quality_label = mapped_quality.upper()
    print(f"[+] '{output_filename}' için görsel üretiliyor... (AI: GPT Image 1, Boyut: {image_size}, Kalite: {quality_label})")
    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size=image_size,
            quality=mapped_quality,
            n=1,
        )
        
        # GPT Image modelleri base64 döner (URL değil!)
        img_data = response.data[0]
        if hasattr(img_data, 'b64_json') and img_data.b64_json:
            img_bytes = base64.b64decode(img_data.b64_json)
            with open(output_filename, 'wb') as f:
                f.write(img_bytes)
            print(f"[+] Görsel kaydedildi: {output_filename} ({len(img_bytes)} bytes)")
            return True
        elif hasattr(img_data, 'url') and img_data.url:
            # Eski API uyumluluğu: URL döndürülürse indir
            session = get_session()
            img_response = session.get(img_data.url, stream=True, timeout=30)
            if img_response.status_code == 200:
                with open(output_filename, 'wb') as f:
                    for chunk in img_response.iter_content(1024):
                        f.write(chunk)
                print(f"[+] Görsel kaydedildi: {output_filename}")
                return True
            else:
                print(f"[-] Görsel indirilemedi, HTTP {img_response.status_code}")
                return False
        else:
            print("[-] GPT Image beklenmeyen yanıt formatı")
            return False
            
    except Exception as e:
        print(f"[-] GPT Image görseli üretilirken hata oluştu: {e}")
        # Fallback: Pollinations → HuggingFace zinciri
        print("[+] Fallback: Pollinations ile deneniyor...")
        if generate_image_pollinations(prompt, output_filename):
            return True
        print("[+] Fallback: Hugging Face ile deneniyor...")
        return generate_image_huggingface(prompt, output_filename)


def generate_image_pollinations(prompt, output_filename, aspect_ratio="9:16"):
    print(f"[+] '{output_filename}' için görsel indiriliyor... (AI: Pollinations, Boyut: {aspect_ratio})")
    
    # URL Encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)

    width, height = 1080, 1920
    if aspect_ratio == "16:9":
        width, height = 1920, 1080
    elif aspect_ratio == "1:1":
        width, height = 1080, 1080

    # Timeout durumlarında farklı URL varyantlarıyla yeniden dene.
    seed = int(time.time() * 1000) % 1000000
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed={seed + 1}",
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


def generate_image_huggingface(prompt, output_filename, model="black-forest-labs/FLUX.1-schnell", aspect_ratio="9:16"):
    """
    Hugging Face Inference API ile görsel üretir.
    Yeni router endpoint (2025+): router.huggingface.co/hf-inference/
    API key .env'de HUGGINGFACE_API_KEY olmalı.
    Token: https://huggingface.co/settings/tokens → Fine-grained → Inference Providers izni
    """
    api_key = os.environ.get("HUGGINGFACE_API_KEY", "").strip()
    if not api_key:
        print("[!] HUGGINGFACE_API_KEY bulunamadı, Hugging Face atlanıyor.")
        return False

    print(f"[+] '{output_filename}' için görsel üretiliyor... (AI: HuggingFace, Model: {model}, Boyut: {aspect_ratio})")
    
    width, height = 768, 1360
    if aspect_ratio == "16:9":
        width, height = 1360, 768
    elif aspect_ratio == "1:1":
        width, height = 1024, 1024

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Yeni: router.huggingface.co (OpenAI uyumlu, JSON yanıt → base64 URL)
    # Eski: api-inference.huggingface.co (binary yanıt)
    endpoint_strategies = [
        {
            "name": "router-openai",
            "url": f"https://router.huggingface.co/hf-inference/models/{model}/v1/images/generations",
            "payload": {"prompt": prompt, "n": 1},
            "response_type": "openai_json",  # {"data": [{"b64_json": "..."}]} veya {"data": [{"url": "..."}]}
        },
        {
            "name": "router-binary",
            "url": f"https://router.huggingface.co/hf-inference/models/{model}",
            "payload": {"inputs": prompt, "parameters": {"num_inference_steps": 4, "width": width, "height": height}},
            "response_type": "binary",
        },
        {
            "name": "legacy-binary",
            "url": f"https://api-inference.huggingface.co/models/{model}",
            "payload": {
                "inputs": prompt,
                "parameters": {
                    "width": width,
                    "height": height,
                    "num_inference_steps": 4,
                    "guidance_scale": 0.0,
                }
            },
            "response_type": "binary",
        },
    ]

    session = get_session()

    for strategy in endpoint_strategies:
        url = strategy["url"]
        payload = strategy["payload"]
        resp_type = strategy["response_type"]
        name = strategy["name"]

        for attempt in range(1, 4):
            try:
                resp = session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=(15, 120),
                )

                if resp.status_code == 200:
                    if resp_type == "openai_json":
                        # OpenAI uyumlu JSON yanıt: data[0].b64_json veya data[0].url
                        try:
                            data = resp.json()
                            img_data = data.get("data", [{}])[0]
                            if "b64_json" in img_data:
                                import base64
                                img_bytes = base64.b64decode(img_data["b64_json"])
                                with open(output_filename, "wb") as f:
                                    f.write(img_bytes)
                                print(f"[+] HuggingFace (router) görseli kaydedildi: {output_filename}")
                                return True
                            elif "url" in img_data:
                                img_resp = session.get(img_data["url"], timeout=30)
                                if img_resp.status_code == 200:
                                    with open(output_filename, "wb") as f:
                                        f.write(img_resp.content)
                                    print(f"[+] HuggingFace (router-url) görseli kaydedildi: {output_filename}")
                                    return True
                        except Exception as parse_err:
                            print(f"[!] HuggingFace JSON parse hatası ({name}): {parse_err}")
                            # İçerik binary image olabilir
                            if len(resp.content) > 1000:
                                with open(output_filename, "wb") as f:
                                    f.write(resp.content)
                                print(f"[+] HuggingFace (binary fallback) görseli kaydedildi: {output_filename}")
                                return True
                    else:
                        # Binary image yanıt
                        content_type = resp.headers.get("content-type", "")
                        if "image" in content_type or len(resp.content) > 1000:
                            with open(output_filename, "wb") as f:
                                f.write(resp.content)
                            print(f"[+] HuggingFace ({name}) görseli kaydedildi: {output_filename}")
                            return True
                        else:
                            print(f"[-] HuggingFace ({name}) yanıt görsel değil: {content_type} ({len(resp.content)} byte)")

                elif resp.status_code == 503:
                    try:
                        wait_time = min(float(resp.json().get("estimated_time", 20)), 45)
                    except Exception:
                        wait_time = 20
                    print(f"[!] HuggingFace model yükleniyor ({name}), {wait_time:.0f}s bekleniyor... (deneme {attempt}/3)")
                    time.sleep(wait_time)
                    continue

                elif resp.status_code == 429:
                    print(f"[-] HuggingFace rate limit ({name}). {10*attempt}s bekleniyor...")
                    time.sleep(10 * attempt)
                    continue

                elif resp.status_code == 404:
                    # Bu endpoint yok, bir sonraki stratejiye geç
                    print(f"[!] HuggingFace endpoint bulunamadı ({name}), bir sonraki deneniyor...")
                    break

                elif resp.status_code == 401:
                    print("[-] HuggingFace yetki hatası (401). Token'ın 'Make calls to Inference Providers' iznine sahip olması gerekiyor.")
                    print("    Token oluşturma: https://huggingface.co/settings/tokens → Fine-grained → Inference → Inference Providers")
                    return False

                else:
                    try:
                        err_msg = resp.json().get("error", resp.text[:200])
                    except Exception:
                        err_msg = resp.text[:200]
                    print(f"[-] HuggingFace ({name}) hata: HTTP {resp.status_code} - {err_msg}")
                    break

            except requests.exceptions.Timeout:
                print(f"[!] HuggingFace timeout ({name}, deneme {attempt}/3)")
            except Exception as e:
                print(f"[-] HuggingFace hata ({name}): {e}")
                break

    print("[-] HuggingFace: Tüm endpoint stratejileri başarısız.")
    return False


def generate_image_replicate(prompt, output_filename, model_name="black-forest-labs/flux-schnell", aspect_ratio="9:16"):
    if not is_replicate_available():
        print(f"[+] Fallback: '{output_filename}' için Pollinations deneniyor...")
        return generate_image_pollinations(prompt, output_filename, aspect_ratio=aspect_ratio)

    print(f"[+] '{output_filename}' için görsel üretiliyor... (AI: Replicate - {model_name}, Boyut: {aspect_ratio})")
    
    try:
        import replicate

        # Replicate modelleri için en boy oranı ayarları
        input_data = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
        }
        
        # Farklı modeller için farklı girdi parametreleri gerekebilir
        if "flux" in model_name:
            input_data["output_format"] = "webp"
            input_data["num_outputs"] = 1
        elif "sdxl" in model_name:
            width, height = 768, 1344
            if aspect_ratio == "16:9":
                width, height = 1344, 768
            elif aspect_ratio == "1:1":
                width, height = 1024, 1024

            input_data = {
                "prompt": prompt,
                "width": width,
                "height": height,
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
        print("[+] Fallback: Pollinations ile yeniden deneniyor...")
        return generate_image_pollinations(prompt, output_filename)

# ─────────────────────────────────────────────────────────────
# STOK GÖRSEL SAĞLAYICILARI (ücretsiz, çok hızlı)
# ─────────────────────────────────────────────────────────────

# AI görsel prompt'larında sık geçen ama stok arama için anlamsız olan terimler
_STOCK_NOISE_WORDS = frozenset({
    "a", "an", "the", "of", "in", "on", "at", "to", "for", "with", "and", "or",
    "cinematic", "hyperrealistic", "realistic", "photorealistic", "ultra",
    "lighting", "professional", "photography", "photo", "photograph",
    "8k", "4k", "hd", "resolution", "sharp", "focus", "focused",
    "detailed", "high", "quality", "highly", "extreme", "extremely",
    "dramatic", "scene", "image", "shot", "view", "style", "artistic",
    "beautiful", "stunning", "gorgeous", "amazing", "incredible",
    "background", "foreground", "composition", "frame", "portrait",
    "wide", "angle", "close-up", "closeup", "close", "up",
    "bird's", "eye", "low", "macro",
    "render", "rendering", "generated", "digital", "illustration",
    "no", "without", "blurry", "watermark", "text", "overlay",
    "ugly", "deformed", "concept", "art",
    # Style anchor / color grading terimleri
    "moody", "teal", "orange", "grading", "shadows", "color", "grain",
    "film", "35mm", "motion", "blur", "touch", "human", "realistic",
    "stock", "subtle", "dark", "bright", "vivid", "warm", "cool",
})


def _topic_to_english_keywords(topic: str) -> list[str]:
    """
    Türkçe/diğer dil konuları için basit İngilizce eşleme tablosu.
    Konuyu önce temizler, sonra anahtar kelimelere çevirir.
    Tam çeviri yapmaz; sadece stok aramalarda kullanılacak kısa İngilizce terimler üretir.
    """
    topic_lower = topic.lower().strip()
    # Sık kullanılan Türkçe → İngilizce eşleştirmeler
    mappings = {
        "uzay": "space", "güneş": "sun", "ay": "moon", "yıldız": "stars",
        "okyanus": "ocean", "deniz": "sea", "orman": "forest", "dağ": "mountain",
        "şehir": "city", "insan": "person", "çocuk": "child", "bilim": "science",
        "teknoloji": "technology", "yapay zeka": "artificial intelligence",
        "robot": "robot", "tarih": "history", "savaş": "war", "doğa": "nature",
        "hayvan": "animal", "kuş": "bird", "köpek": "dog", "kedi": "cat",
        "yemek": "food", "para": "money", "ekonomi": "economy",
        "spor": "sport", "futbol": "football", "müzik": "music",
        "film": "movie", "kitap": "book", "sağlık": "health",
        "hastalık": "disease", "ilaç": "medicine", "beyin": "brain",
        "evren": "universe", "gezegen": "planet", "iklim": "climate",
        "deprem": "earthquake", "volkan": "volcano", "fırtına": "storm",
        "piramit": "pyramid", "antik": "ancient", "mısır": "egypt",
        "roket": "rocket", "astronot": "astronaut", "mars": "mars",
    }
    keywords = []
    for tr_word, en_word in mappings.items():
        if tr_word in topic_lower:
            keywords.append(en_word)
    # Eşleşme bulunamazsa orijinal konuyu kelimelerine böl (max 3)
    if not keywords:
        words = topic_lower.split()[:3]
        keywords = [w for w in words if len(w) > 2]
    return keywords[:3]


def _stock_search_keyword(prompt: str, topic: str = "") -> str:
    """
    Uzun AI prompt'undan noise word'leri filtreleyerek anlamlı arama terimi çıkarır.
    topic parametresi verilirse konu kelimeleri sonuçta öncelikli olarak yer alır.
    """
    words = [w.lower().strip(",.;:!?\"'()[]") for w in prompt.strip().split()]
    meaningful = [w for w in words if w and len(w) > 2 and w not in _STOCK_NOISE_WORDS]

    # Konu anahtar kelimelerini öne al
    topic_keywords = []
    if topic:
        topic_keywords = _topic_to_english_keywords(topic)
        # Prompt'ta olmayan konu kelimelerini başa ekle
        topic_keywords = [k for k in topic_keywords if k not in " ".join(meaningful)]

    combined = topic_keywords + meaningful
    if combined:
        return " ".join(combined[:5])
    # Fallback: hiç anlamlı kelime bulunamazsa ilk 4 kelimeyi kullan
    return " ".join(words[:4]) if len(words) >= 4 else prompt[:60]

def fetch_stock_image_pexels(prompt: str, output_filename: str, topic: str = "", aspect_ratio: str = "9:16") -> bool:
    """Pexels API ile ücretsiz stok görsel indir. API key .env'de PEXELS_API_KEY olmalı."""
    api_key = os.environ.get("PEXELS_API_KEY", "").strip()
    if not api_key:
        print("[!] PEXELS_API_KEY bulunamadı, Pexels atlanıyor.")
        return False

    keyword = _stock_search_keyword(prompt, topic)
    print(f"[+] '{output_filename}' için görsel aranıyor... (Pexels: '{keyword}')")

    session = get_session()
    headers = {"Authorization": api_key}

    try:
        # Aspect Ratio bazlı dikey/yatay/kare oryantasyon seçimi
        orientation = "portrait"
        if aspect_ratio == "16:9":
            orientation = "landscape"
        elif aspect_ratio == "1:1":
            orientation = "square"

        params = {
            "query": keyword,
            "orientation": orientation,
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
def fetch_stock_image_pixabay(prompt: str, output_filename: str, topic: str = "", aspect_ratio: str = "9:16") -> bool:
    """Pixabay API ile ücretsiz stok görsel indir. API key .env'de PIXABAY_API_KEY olmalı."""
    api_key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not api_key:
        print("[!] PIXABAY_API_KEY bulunamadı, Pixabay atlanıyor.")
        return False

    keyword = _stock_search_keyword(prompt, topic)
    print(f"[+] '{output_filename}' için görsel aranıyor... (Pixabay: '{keyword}')")

    session = get_session()
    try:
        # Aspect Ratio bazlı dikey/yatay/kare oryantasyon seçimi (Pixabay 'all' veya 'horizontal'/'vertical' destekler)
        orientation = "vertical"
        if aspect_ratio == "16:9":
            orientation = "horizontal"
        elif aspect_ratio == "1:1":
            orientation = "all"

        params = {
            "key": api_key,
            "q": urllib.parse.quote(keyword),
            "image_type": "photo",
            "orientation": orientation,
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
def fetch_stock_image_unsplash(prompt: str, output_filename: str, topic: str = "", aspect_ratio: str = "9:16") -> bool:
    """Unsplash API ile ücretsiz stok görsel indir. API key .env'de UNSPLASH_ACCESS_KEY olmalı."""
    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()
    if not access_key:
        print("[!] UNSPLASH_ACCESS_KEY bulunamadı, Unsplash atlanıyor.")
        return False

    keyword = _stock_search_keyword(prompt, topic)
    print(f"[+] '{output_filename}' için görsel aranıyor... (Unsplash: '{keyword}')")

    session = get_session()
    headers = {"Authorization": f"Client-ID {access_key}"}
    try:
        # Aspect Ratio bazlı dikey/yatay/kare oryantasyon seçimi
        orientation = "portrait"
        if aspect_ratio == "16:9":
            orientation = "landscape"
        elif aspect_ratio == "1:1":
            orientation = "squarish"

        params = {
            "query": keyword,
            "orientation": orientation,
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
def fetch_stock_image_auto(prompt: str, output_filename: str, topic: str = "", aspect_ratio: str = "9:16") -> bool:
    """Otomatik stok görsel: Pexels → Pixabay → Unsplash → GPT Image → Pollinations → HuggingFace"""
    print(f"[+] Stock-Auto modu başlatıldı: '{output_filename}' (Aspect Ratio: {aspect_ratio})")

    # 1. Pexels
    if fetch_stock_image_pexels(prompt, output_filename, topic, aspect_ratio=aspect_ratio):
        return True

    # 2. Pixabay
    if fetch_stock_image_pixabay(prompt, output_filename, topic, aspect_ratio=aspect_ratio):
        return True

    # 3. Unsplash
    if fetch_stock_image_unsplash(prompt, output_filename, topic, aspect_ratio=aspect_ratio):
        return True

    # 4. GPT Image 1 (eski DALL-E 3'ün yerini aldı)
    print("[!] Tüm stok kaynaklar başarısız. GPT Image 1 deneniyor...")
    if generate_image_openai(prompt, output_filename, aspect_ratio=aspect_ratio):
        return True

    # 5. Pollinations
    print("[!] GPT Image başarısız. Pollinations deneniyor...")
    if generate_image_pollinations(prompt, output_filename, aspect_ratio=aspect_ratio):
        return True

    # 6. Hugging Face (son çare - ücretsiz AI)
    print("[!] Pollinations başarısız. Son çare: Hugging Face deneniyor...")
    return generate_image_huggingface(prompt, output_filename, aspect_ratio=aspect_ratio)
# ─────────────────────────────────────────────────────────────
# ANA YÖNLENDIRICI
# ─────────────────────────────────────────────────────────────
def generate_image(prompt, output_filename, ai_provider="Stock-Auto", topic: str = "", aspect_ratio: str = "9:16"):
    """
    Görsel üretici / indiricisi.
    topic: Video konusu (Türkçe/İngilizce). Stok aramalarda konuya göre
           daha alakalı sonuçlar elde etmek için kullanılır.
    """
    provider_lower = ai_provider.lower()

    # Stok görsel sağlayıcıları
    if provider_lower == "pexels":
        return fetch_stock_image_pexels(prompt, output_filename, topic, aspect_ratio=aspect_ratio) or generate_image_openai(prompt, output_filename, aspect_ratio=aspect_ratio)
    elif provider_lower == "pixabay":
        return fetch_stock_image_pixabay(prompt, output_filename, topic, aspect_ratio=aspect_ratio) or generate_image_openai(prompt, output_filename, aspect_ratio=aspect_ratio)
    elif provider_lower == "unsplash":
        return fetch_stock_image_unsplash(prompt, output_filename, topic, aspect_ratio=aspect_ratio) or generate_image_openai(prompt, output_filename, aspect_ratio=aspect_ratio)
    elif provider_lower == "stock-auto":
        return fetch_stock_image_auto(prompt, output_filename, topic, aspect_ratio=aspect_ratio)

    # AI görsel sağlayıcıları
    elif provider_lower == "openai-hd" or provider_lower == "dall-e-hd" or provider_lower == "gpt-image-hd":
        # Hook ve CTA sahneleri için HD kalite (gpt-image-1 quality="high")
        return generate_image_openai(prompt, output_filename, quality="hd", aspect_ratio=aspect_ratio)
    elif "dall-e" in provider_lower or "openai" in provider_lower or "gpt-image" in provider_lower:
        return generate_image_openai(prompt, output_filename, aspect_ratio=aspect_ratio)
    elif "flux" in provider_lower:
        model = "black-forest-labs/flux-schnell"
        if "pro" in provider_lower:
            model = "black-forest-labs/flux-pro"
        return generate_image_replicate(prompt, output_filename, model, aspect_ratio=aspect_ratio)
    elif "sdxl" in provider_lower:
        return generate_image_replicate(prompt, output_filename, "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7f23bb69422f281454559869502b4", aspect_ratio=aspect_ratio)
    elif "replicate" in provider_lower:
        return generate_image_replicate(prompt, output_filename, aspect_ratio=aspect_ratio)
    elif "pollinations" in provider_lower:
        return generate_image_pollinations(prompt, output_filename, aspect_ratio=aspect_ratio)
    elif "huggingface" in provider_lower or "hugging" in provider_lower or "hf" == provider_lower:
        # Model seçimi: huggingface-flux, huggingface-dev, huggingface-sdxl
        if "dev" in provider_lower:
            hf_model = "black-forest-labs/FLUX.1-dev"
        elif "sdxl" in provider_lower:
            hf_model = "stabilityai/stable-diffusion-xl-base-1.0"
        else:
            hf_model = "black-forest-labs/FLUX.1-schnell"  # Varsayılan: hızlı ve ücretsiz
        return generate_image_huggingface(prompt, output_filename, hf_model, aspect_ratio=aspect_ratio)
    else:
        # Bilinmeyen sağlayıcı → Stock-Auto
        print(f"[!] Bilinmeyen sağlayıcı '{ai_provider}', Stock-Auto kullanılıyor.")
        return fetch_stock_image_auto(prompt, output_filename, topic, aspect_ratio=aspect_ratio)
if __name__ == "__main__":
    # Test
    test_prompt = "A cinematic hyperrealistic image of an astronaut standing alone on a snowy mountain peak during a dark night with glowing stars, 8k resolution"
    generate_image(test_prompt, "test_image.jpg")
