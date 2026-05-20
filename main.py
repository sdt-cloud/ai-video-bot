import os
import sys
import argparse
import asyncio
import concurrent.futures
from typing import List, Dict, Optional

# Import bot modules
from script_generator import generate_script, generate_script_from_custom_text
from voice_generator import generate_voice_async
from image_generator import generate_image
from video_maker import create_video
from clip_fetcher import fetch_clip_auto
from image_animator import animate_image
from thumbnail_generator import create_thumbnail, select_best_thumbnail_scene
from performance_optimizer import parallel_process_images

# Console color helpers
class Color:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="🎬 AI Video Bot — Enterprise-Grade Automated Video Production CLI Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Topic and custom scripts
    parser.add_argument("-t", "--topic", type=str, help="Video topic (e.g., 'Secret Inventions of Nikola Tesla')")
    parser.add_argument("-cs", "--custom-script", type=str, help="Custom script text or path to a text file containing the script")
    
    # Video details
    parser.add_argument("-d", "--duration", type=int, default=30, help="Target video duration in seconds (15 to 300)")
    parser.add_argument("-l", "--language", type=str, default="tr", choices=["tr", "en", "es"], help="Script and voice language")
    parser.add_argument("-q", "--quality", type=str, default="medium", choices=["low", "medium", "high"], help="Video production quality level")
    parser.add_argument("-ar", "--aspect-ratio", type=str, default="9:16", choices=["9:16", "16:9", "1:1"], help="Video aspect ratio")
    
    # AI Engine settings
    parser.add_argument("-sa", "--script-ai", type=str, default="Gemini", choices=["Gemini", "OpenAI"], help="AI engine for script writing")
    parser.add_argument("-va", "--voice-ai", type=str, default="Edge-TTS", choices=["Edge-TTS", "ElevenLabs"], help="AI engine for voice synthesis")
    parser.add_argument("-vt", "--voice-type", type=str, default="erkek", choices=["erkek", "kadin"], help="Voice gender type")
    parser.add_argument("-ia", "--image-ai", type=str, default="Pollinations", choices=["Stock-Auto", "Pollinations", "OpenAI", "Flux", "SDXL", "Pexels", "Pixabay", "Unsplash"], help="AI engine / Stock provider for visuals")
    parser.add_argument("-ap", "--animation-provider", type=str, default="none", choices=["none", "auto", "stability_ai", "runway", "replicate", "luma"], help="Image-to-video animation provider")

    # Post effects & customization
    parser.add_argument("-ss", "--subtitle-style", type=str, default="tiktok", choices=["tiktok", "classic", "minimal"], help="Subtitle design style")
    parser.add_argument("-sd", "--subtitle-delay", type=float, default=1.0, help="Subtitle delay in seconds")
    parser.add_argument("-vm", "--video-mode", type=str, default="slideshow", choices=["slideshow", "zoom_motion"], help="Video movement and animation mode")
    parser.add_argument("-tr", "--transition", type=str, default="none", choices=["none", "fade", "crossfade", "zoom", "spin", "glitch", "auto"], help="Scene transition effect")
    parser.add_argument("--bgm", action="store_true", help="Enable automatic cinematic background music matching the tone")
    parser.add_argument("--bgm-tone", type=str, default="auto", help="Background music tone (e.g. dramatic, epic, happy, energetic, auto)")
    parser.add_argument("-sp", "--sentence-pause", type=float, default=0.0, help="Brief silence duration between narrator sentences")
    parser.add_argument("--watermark", action="store_true", help="Add default AI Video Bot watermark layer")
    parser.add_argument("-cg", "--color-grade", type=str, default="auto_enhance", choices=["none", "auto_enhance", "warm", "cool", "vintage", "cinematic"], help="Color grading filter style")
    parser.add_argument("--letterbox", action="store_true", help="Enable aesthetic black letterbox borders")
    parser.add_argument("--light-leak", action="store_true", help="Add organic light leak transition overlays")
    parser.add_argument("--no-thumbnail", action="store_true", help="Disable generating an automatic clickbait cover thumbnail")
    parser.add_argument("-o", "--output", type=str, help="Custom output video path (e.g. exports/my_video.mp4)")

    return parser.parse_args()

async def main_async():
    args = parse_arguments()
    
    print(f"\n{Color.BLUE}{Color.BOLD}=======================================")
    print("    🎬 AI VIDEO BOT — AUTOMATED CLI")
    print(f"======================================={Color.END}")
    
    # Get topic or script
    topic = args.topic
    custom_script = args.custom_script
    
    # If custom script is a file path, load its contents
    if custom_script and os.path.exists(custom_script):
        try:
            with open(custom_script, "r", encoding="utf-8") as f:
                custom_script = f.read()
            print(f"{Color.GREEN}[+] Loaded custom script from file: {args.custom_script}{Color.END}")
        except Exception as file_err:
            print(f"{Color.RED}[-] Error reading custom script file: {file_err}{Color.END}")
            return

    # If no flags are provided, run interactively
    if not topic and not custom_script:
        topic = input(f"{Color.BOLD}Lütfen video konusunu giriniz (Örn: Nicola Tesla'nın gizli icatları): {Color.END}").strip()
        if not topic:
            print(f"{Color.RED}[- ] Geçerli bir konu girmediniz. Çıkış yapılıyor.{Color.END}")
            return

    # Set topic fallback for file names if using custom script only
    if not topic and custom_script:
        topic = "Custom_Script_Video"

    temp_files = []

    # -------------------------------------------------------------
    # Step 1: Scripting Phase
    # -------------------------------------------------------------
    print(f"\n{Color.YELLOW}[Adım 1/5] Senaryo ve Visual Promptlar Hazırlanıyor...{Color.END}")
    if custom_script:
        script_data = generate_script_from_custom_text(
            topic,
            custom_script,
            ai_provider=args.script_ai,
            duration=args.duration,
            quality_level=args.quality
        )
    else:
        script_data = generate_script(
            topic,
            ai_provider=args.script_ai,
            duration=args.duration,
            language=args.language,
            quality_level=args.quality
        )
        
    if not script_data or "scenes" not in script_data:
        print(f"{Color.RED} [-] Senaryo üretilemedi. API anahtarınızda bakiye olmayabilir veya ağ sorunu var.{Color.END}")
        return
        
    scenes = script_data.get("scenes", [])
    print(f"{Color.GREEN}[+] Toplam {len(scenes)} sahne hazırlandı.{Color.END}")
    
    # Combine narration for voice generation
    full_narration = " ".join([scene.get("narration", "") for scene in scenes])
    
    # -------------------------------------------------------------
    # Step 2: Voice Generation Phase
    # -------------------------------------------------------------
    print(f"\n{Color.YELLOW}[Adım 2/5] Ses Sentezleniyor...{Color.END}")
    os.makedirs("assets", exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    
    voice_file = f"assets/narration_cli_{os.getpid()}.mp3"
    temp_files.append(voice_file)
    
    voice_success = await generate_voice_async(
        full_narration,
        voice_file,
        ai_provider=args.voice_ai,
        voice_type=args.voice_type,
        target_duration_seconds=args.duration,
        sentence_pause=args.sentence_pause,
        language=args.language
    )
    
    if not voice_success or not os.path.exists(voice_file):
        print(f"{Color.RED}[- ] Ses oluşturulamadı, işlem iptal edildi.{Color.END}")
        return
    print(f"{Color.GREEN}[+] Ses sentezi tamamlandı: {voice_file}{Color.END}")

    # -------------------------------------------------------------
    # Step 3: Media Generation Phase (Images & Video clips in Parallel)
    # -------------------------------------------------------------
    print(f"\n{Color.YELLOW}[Adım 3/5] Medya Kaynakları Paralel Olarak İndiriliyor...{Color.END}")
    
    prompts = []
    output_paths = []
    providers = []
    media_types = []
    clip_queries = []
    premium_models = ["OpenAI", "Flux", "Flux-Pro", "SDXL"]
    
    for i, scene in enumerate(scenes):
        prompt = scene.get("image_prompt", "")
        media_type = scene.get("media_type", "image")
        clip_query = scene.get("clip_search_query", "")
        
        media_types.append(media_type)
        clip_queries.append(clip_query)
        
        if media_type == "video_clip":
            clip_name = f"assets/clip_cli_{os.getpid()}_{i}.mp4"
            output_paths.append(clip_name)
            temp_files.append(clip_name)
            prompts.append(prompt)
            providers.append(args.image_ai)
        else:
            img_name = f"assets/scene_cli_{os.getpid()}_{i}.jpg"
            prompts.append(prompt)
            output_paths.append(img_name)
            temp_files.append(img_name)
            
            # Premium Hook and Outro
            if (i == 0 or i == len(scenes) - 1) and args.image_ai not in premium_models:
                providers.append("OpenAI-HD")
            else:
                providers.append(args.image_ai)
                
    # Parallelize Stock Video Clips download
    clip_indices = [i for i, mt in enumerate(media_types) if mt == "video_clip" and clip_queries[i]]
    if clip_indices:
        print(f"[i] Toplam {len(clip_indices)} video klip paralel aranıyor ve indiriliyor...")
        
        def download_single_clip(i):
            print(f"  -> Sahne {i}: Klip indiriliyor (Sorgu: '{clip_queries[i]}')...")
            success = fetch_clip_auto(clip_queries[i], output_paths[i], topic=topic)
            return i, success
            
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(clip_indices))) as executor:
            clip_results = await loop.run_in_executor(
                None,
                lambda: list(executor.map(download_single_clip, clip_indices))
            )
            
        # Fallback missing clips to image types
        for idx, success in clip_results:
            if not success:
                print(f"{Color.YELLOW}  [!] Sahne {idx}: Klip indirilemedi. Görsel modeline dönüştürülüyor...{Color.END}")
                media_types[idx] = "image"
                output_paths[idx] = f"assets/scene_cli_{os.getpid()}_{idx}.jpg"
                temp_files.append(output_paths[idx])

    # Parallelize Image generation
    image_indices = [i for i, mt in enumerate(media_types) if mt == "image"]
    image_prompts = [prompts[i] for i in image_indices]
    image_outputs = [output_paths[i] for i in image_indices]
    image_providers = [providers[i] for i in image_indices]
    
    if image_prompts:
        print(f"[i] Toplam {len(image_prompts)} görsel paralel olarak üretiliyor...")
        loop = asyncio.get_running_loop()
        image_results = await loop.run_in_executor(
            None,
            parallel_process_images,
            image_prompts,
            image_outputs,
            image_providers,
            topic
        )
        
        for idx, success in enumerate(image_results):
            if not success:
                real_idx = image_indices[idx]
                output_paths[real_idx] = None
                
    # Parallelize Image Animations (Image-to-Video) if selected
    if args.animation_provider and args.animation_provider != "none":
        anim_indices = [i for i, mt in enumerate(media_types) if mt == "image" and output_paths[i] and os.path.exists(output_paths[i])]
        if anim_indices:
            print(f"[i] Toplam {len(anim_indices)} görsel paralel olarak anime ediliyor ({args.animation_provider})...")
            
            def animate_single_image(i):
                anim_output = f"assets/anim_cli_{os.getpid()}_{i}.mp4"
                print(f"  -> Sahne {i}: Anime ediliyor...")
                success = animate_image(output_paths[i], anim_output, args.animation_provider)
                return i, anim_output if success else None
                
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(3, len(anim_indices))) as executor:
                anim_results = await loop.run_in_executor(
                    None,
                    lambda: list(executor.map(animate_single_image, anim_indices))
                )
                
            for idx, anim_path in anim_results:
                if anim_path:
                    temp_files.append(anim_path)
                    output_paths[idx] = anim_path
                    media_types[idx] = "animated"

    valid_media_paths = [p for p in output_paths if p and os.path.exists(p)]
    if not valid_media_paths:
        print(f"{Color.RED}[-] Hiç görsel veya video klip üretilemedi, işlem iptal ediliyor.{Color.END}")
        # Clean up voice file
        if os.path.exists(voice_file):
            os.remove(voice_file)
        return
    print(f"{Color.GREEN}[+] Medya hazırlığı bitti. Toplam {len(valid_media_paths)}/{len(scenes)} medya hazır.{Color.END}")

    # -------------------------------------------------------------
    # Step 4: Video Compilation & Rendering Phase
    # -------------------------------------------------------------
    print(f"\n{Color.YELLOW}[Adım 4/5] Video Kurgulanıyor ve Render Alınıyor...{Color.END}")
    
    if args.output:
        output_video = args.output
    else:
        safe_topic = "".join([c if c.isalnum() else "_" for c in topic])[:20]
        output_video = f"exports/{safe_topic}_cli_video.mp4"
        
    narrations = [scene.get("narration", "") for scene in scenes]
    scene_pacings = [{"pacing": s.get("pacing", "normal"), "mood": s.get("mood", "")} for s in scenes]
    
    video_success = await create_video(
        valid_media_paths,
        voice_file,
        output_video,
        narrations=narrations,
        subtitle_style=args.subtitle_style,
        subtitle_delay=args.subtitle_delay,
        video_mode=args.video_mode,
        watermark_enabled=args.watermark,
        transition_style=args.transition,
        bgm_enabled=args.bgm,
        bgm_tone=args.bgm_tone,
        aspect_ratio=args.aspect_ratio,
        quality_level=args.quality,
        color_grade_style=args.color_grade,
        scene_pacings=scene_pacings,
        letterbox_enabled=args.letterbox,
        light_leak_enabled=args.light_leak
    )
    
    # -------------------------------------------------------------
    # Step 5: Clickbait Thumbnail Cover generation
    # -------------------------------------------------------------
    if video_success and not args.no_thumbnail:
        print(f"\n{Color.YELLOW}[Adım 5/5] Otomatik Kapak Fotoğrafı (Thumbnail) Üretiliyor...{Color.END}")
        try:
            thumb_path = output_video.replace(".mp4", "_thumbnail.jpg")
            best_media = select_best_thumbnail_scene(scenes, valid_media_paths)
            if best_media and best_media.endswith(".jpg"):
                create_thumbnail(best_media, topic, thumb_path, aspect_ratio=args.aspect_ratio)
            else:
                # Video karesinden yakalama yapamıyorsak ilk görseli kullan
                img_candidates = [p for p in valid_media_paths if p.endswith(".jpg")]
                if img_candidates:
                    create_thumbnail(img_candidates[0], topic, thumb_path, aspect_ratio=args.aspect_ratio)
        except Exception as thumb_err:
            print(f"{Color.YELLOW}[!] Thumbnail oluşturulamadı (İşlem engellenmedi): {thumb_err}{Color.END}")

    # Cleanup temporary assets
    print(f"\n{Color.YELLOW}[+] Geçici dosyalar temizleniyor...{Color.END}")
    for temp_f in temp_files:
        try:
            if os.path.exists(temp_f):
                os.remove(temp_f)
                print(f"  -> Silindi: {temp_f}")
        except Exception as cleanup_err:
            print(f"  -> [!] Temizleme hatası ({temp_f}): {cleanup_err}")
            
    if video_success and os.path.exists(output_video):
        print(f"\n{Color.GREEN}{Color.BOLD}=======================================")
        print(f"🎉 TEBRİKLER! Videonuz başarıyla hazırlandı:")
        print(f"🎥 Video: {output_video}")
        if not args.no_thumbnail and os.path.exists(output_video.replace(".mp4", "_thumbnail.jpg")):
            print(f"🖼️ Kapak Resmi: {output_video.replace('.mp4', '_thumbnail.jpg')}")
        print("Tiktok, Instagram Reels veya YouTube Shorts'ta paylaşabilirsiniz.")
        print(f"======================================={Color.END}\n")
    else:
        print(f"{Color.RED}[-] Video kurgulama hatası: Render işlemi başarısız.{Color.END}")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
