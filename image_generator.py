import requests
import urllib.parse
import os

def generate_image(prompt, output_filename):
    print(f"[+] '{output_filename}' için görsel indiriliyor...")
    
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

if __name__ == "__main__":
    # Test
    test_prompt = "A cinematic hyperrealistic image of an astronaut standing alone on a snowy mountain peak during a dark night with glowing stars, 8k resolution"
    generate_image(test_prompt, "test_image.jpg")
