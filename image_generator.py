import requests
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv()

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
        
        # Resmi URL'den indirip kaydetme
        img_response = requests.get(image_url, stream=True)
        if img_response.status_code == 200:
            with open(output_filename, 'wb') as f:
                for chunk in img_response.iter_content(1024):
                    f.write(chunk)
            print(f"[+] Görsel kaydedildi: {output_filename}")
            return True
        else:
            print(f"[-] DALL-E Görseli indirilemedi, HTTP Status: {img_response.status_code}")
            return False
            
    except Exception as e:
        print(f"[-] DALL-E Görseli üretilirken hata oluştu: {e}")
        return False

def generate_image_pollinations(prompt, output_filename):
    print(f"[+] '{output_filename}' için görsel indiriliyor... (AI: Pollinations)")
    
    # URL Encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    
    # Pollinations AI URL (width=1080, height=1920 for Shorts/Reels, nologo=true to remove watermark)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true"
    
    try:
        response = requests.get(url, stream=True)
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

def generate_image(prompt, output_filename, ai_provider="Pollinations"):
    if "dall-e" in ai_provider.lower() or "openai" in ai_provider.lower():
        return generate_image_openai(prompt, output_filename)
    else:
        return generate_image_pollinations(prompt, output_filename)

if __name__ == "__main__":
    # Test
    test_prompt = "A cinematic hyperrealistic image of an astronaut standing alone on a snowy mountain peak during a dark night with glowing stars, 8k resolution"
    generate_image(test_prompt, "test_image.jpg")
