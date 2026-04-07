import requests
import urllib.parse
import os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

# Global session with connection pooling and retry strategy
_session = None

def get_session():
    """Connection pooling ile requests session oluştur"""
    global _session
    if _session is None:
        _session = requests.Session()
        
        # Retry stratejisi
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
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
    
    # Pollinations AI URL (width=1080, height=1920 for Shorts/Reels, nologo=true to remove watermark)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"
    
    try:
        session = get_session()
        response = session.get(url, stream=True, timeout=60)
        if response.status_code == 200:
            with open(output_filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"[+] Görsel kaydedildi: {output_filename}")
            return True
        else:
            print(f"[-] Görsel indirilemedi, HTTP Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[-] Görsel indirilirken hata oluştu: {e}")
        return False

def generate_image_replicate(prompt, output_filename, model_name="black-forest-labs/flux-schnell"):
    import replicate
    print(f"[+] '{output_filename}' için görsel üretiliyor... (AI: Replicate - {model_name})")
    
    try:
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
        return False

def generate_image(prompt, output_filename, ai_provider="Pollinations"):
    provider_lower = ai_provider.lower()
    if "dall-e" in provider_lower or "openai" in provider_lower:
        return generate_image_openai(prompt, output_filename)
    elif "flux" in provider_lower:
        # flux, flux-schnell, flux-pro gibi varyasyonları destekle
        model = "black-forest-labs/flux-schnell"
        if "pro" in provider_lower: model = "black-forest-labs/flux-pro"
        return generate_image_replicate(prompt, output_filename, model)
    elif "sdxl" in provider_lower:
        return generate_image_replicate(prompt, output_filename, "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7f23bb69422f281454559869502b4")
    elif "replicate" in provider_lower:
        return generate_image_replicate(prompt, output_filename)
    else:
        return generate_image_pollinations(prompt, output_filename)

if __name__ == "__main__":
    # Test
    test_prompt = "A cinematic hyperrealistic image of an astronaut standing alone on a snowy mountain peak during a dark night with glowing stars, 8k resolution"
    generate_image(test_prompt, "test_image.jpg")
