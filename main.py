import os
import sys

# Modüllerimizi içeri aktarıyoruz
from script_generator import generate_script
from voice_generator import generate_voice
from image_generator import generate_image
from video_maker import create_video

def main():
    print("=======================================")
    print("    YAPAY ZEKA VİDEO OTOMASYONU")
    print("=======================================")
    
    # Konuyu al
    topic = input("Lütfen video konusunu giriniz (Örn: Nicola Tesla'nın gizli icatları): ")
    if not topic.strip():
        print("Geçerli bir konu girmediniz. Çıkış yapılıyor.")
        return
        
    print("\nAdım 1: Senaryo ve Promptlar Hazırlanıyor...")
    script_data = generate_script(topic)
    
    if not script_data or "scenes" not in script_data:
        print("[-] Senaryo üretilemedi. API anahtarınızda bakiye olmayabilir veya ağ sorunu var.")
        return
        
    scenes = script_data.get("scenes", [])
    
    # Tüm metni birleştirip tek bir ses dosyası yapacağız
    full_narration = " ".join([scene.get("narration", "") for scene in scenes])
    
    print("\nAdım 2: Ses Sentezleniyor...")
    voice_file = "assets/narration.mp3"
    
    # Klasör kontrolü
    os.makedirs("assets", exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    
    voice_success = generate_voice(full_narration, voice_file)
    if not voice_success:
        print("Ses oluşturulamadı, işlem iptal edildi.")
        return
        
    print("\nAdım 3: Görseller İndiriliyor...")
    image_paths = []
    for i, scene in enumerate(scenes):
        prompt = scene.get("image_prompt", "")
        img_name = f"assets/scene_{i}.jpg"
        
        # Pollinations bazen aynı promptta aynı resmi verir, seed veya farklılaştırıcı eklemek iyidir ama şimdilik prompt yeterli.
        img_success = generate_image(prompt, img_name)
        if img_success:
            image_paths.append(img_name)
        else:
            print(f"[-] Uyarı: {i}. görsel indirilemedi, videodan çıkarılacak.")
            
    if not image_paths:
        print("Hiç görsel indirilemedi, işlem iptal edildi.")
        return
        
    print("\nAdım 4: Video Kurgulanıyor...")
    output_video = f"exports/{topic.replace(' ', '_')[:20]}_shorts.mp4"
    video_success = create_video(image_paths, voice_file, output_video)
    
    if video_success:
        print("\n=======================================")
        print(f"TEBRİKLER! Videonuz hazırlandı: {output_video}")
        print("Tiktok, Instagram Reels veya YouTube Shorts'ta paylaşabilirsiniz.")
        print("=======================================")

if __name__ == "__main__":
    main()
