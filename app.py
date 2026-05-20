import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from typing import List, Optional
import database

# Connection error filter'ı import et
from connection_filter import setup_connection_filter

# Connection filter'ı kur
setup_connection_filter()

# Bot modüllerini içe aktar
from script_generator import generate_script, generate_script_from_custom_text
from voice_generator import generate_voice_async
from video_maker import create_video
from clip_fetcher import fetch_clip_auto
from image_animator import animate_image

from queue_manager import start_queue_manager, get_queue_status
from performance_optimizer import parallel_process_images
from error_handler import error_recovery, video_logger

app = FastAPI()

class VideoRequest(BaseModel):
    topic: str
    custom_script: Optional[str] = None
    category: Optional[str] = "Genel"
    tone: Optional[str] = "Enerjik"
    duration: int = Field(default=30, ge=15, le=300)
    language: Optional[str] = "tr"
    script_ai: Optional[str] = "Gemini"
    voice_ai: Optional[str] = "Edge-TTS"
    voice_type: Optional[str] = "erkek"
    image_ai: Optional[str] = "Pollinations"
    subtitle_style: Optional[str] = "tiktok"
    subtitle_delay: Optional[float] = 1.0
    video_mode: Optional[str] = "slideshow"
    sentence_pause: Optional[float] = 0.0
    watermark_enabled: Optional[bool] = False
    transition_style: Optional[str] = "none"
    bgm_enabled: Optional[bool] = False
    bgm_tone: Optional[str] = "auto"
    quality_level: Optional[str] = "medium"
    aspect_ratio: Optional[str] = "9:16"
    animation_provider: Optional[str] = "none"
    color_grade_style: Optional[str] = "auto_enhance"
    light_leak_enabled: Optional[bool] = False

class BulkVideoRequest(BaseModel):
    topics: List[str]
    duration: int = Field(default=30, ge=15, le=300)
    language: Optional[str] = "tr"
    script_ai: Optional[str] = "Gemini"
    voice_ai: Optional[str] = "Edge-TTS"
    voice_type: Optional[str] = "erkek"
    image_ai: Optional[str] = "Pollinations"
    subtitle_style: Optional[str] = "tiktok"
    subtitle_delay: Optional[float] = 1.0
    video_mode: Optional[str] = "slideshow"
    sentence_pause: Optional[float] = 0.0
    watermark_enabled: Optional[bool] = False
    transition_style: Optional[str] = "none"
    bgm_enabled: Optional[bool] = False
    bgm_tone: Optional[str] = "auto"
    quality_level: Optional[str] = "medium"
    aspect_ratio: Optional[str] = "9:16"
    animation_provider: Optional[str] = "none"
    light_leak_enabled: Optional[bool] = False

async def process_video(task):
    task_id = task["id"]
    topic = task["topic"]
    temp_files = []  # Temizlik için temp dosyaları takip et
    
    print(f"[{task_id}] İŞLEM BAŞLIYOR: {topic}")
    video_logger.log_video_production_step("started", str(task_id), {"topic": topic})
    
    try:
        # 1. Senaryo Aşaması
        database.update_status(task_id, "scripting", 10)
        custom_script = (task.get("custom_script") or "").strip()
        quality_level = task.get("quality_level", "medium")
        if custom_script:
            database.update_status(task_id, "scripting", 12, "Özel script kullanılıyor: sahneler hazırlanıyor.")
            script_data = await error_recovery.retry_with_backoff(
                generate_script_from_custom_text,
                topic,
                custom_script,
                task.get("script_ai", "Gemini"),
                task.get("duration", 30),
                quality_level,
            )
        else:
            script_data = await error_recovery.retry_with_backoff(
                generate_script,
                topic, 
                task.get("script_ai", "Gemini"), 
                task.get("duration", 30),
                task.get("language", "tr"),
                quality_level,
            )
        
        if not script_data or "scenes" not in script_data:
            database.update_status(task_id, "failed", 10, "Senaryo üretilemedi API hatası.")
            return

        fallback_provider = script_data.get("_meta", {}).get("fallback_provider")
        if fallback_provider:
            database.update_status(
                task_id,
                "scripting",
                15,
                f"Bilgi: OpenAI kotası nedeniyle otomatik {fallback_provider} fallback kullanıldı."
            )
            
        scenes = script_data.get("scenes", [])
        
        # 2. Medya Aşaması (Ses)
        database.update_status(task_id, "media", 30)
        full_narration = " ".join([scene.get("narration", "") for scene in scenes])
        
        os.makedirs("frontend/videos", exist_ok=True)
        os.makedirs("assets", exist_ok=True)
        
        voice_file = f"assets/narration_{task_id}.mp3"
        temp_files.append(voice_file)
        
        voice_ai_provider = task.get("voice_ai", "Edge-TTS")
        voice_type = task.get("voice_type", "erkek")
        sentence_pause = task.get("sentence_pause", 0.0)
        target_duration_seconds = int(task.get("duration", 30) or 30)
        voice_success = await generate_voice_async(
            full_narration,
            voice_file,
            voice_ai_provider,
            voice_type,
            target_duration_seconds=target_duration_seconds,
            sentence_pause=sentence_pause,
            language=task.get("language", "tr")
        )
        
        if not voice_success:
            database.update_status(task_id, "failed", 30, "Ses sentezlenemedi.")
            return
            
        # 3. Medya Aşaması (Görseller ve Video Klipleri) - PARALEL İŞLEME
        database.update_status(task_id, "media", 50)
        
        # Paralel görsel üretimi için hazırlık
        prompts = []
        output_paths = []
        providers = []
        media_types = []  # Her sahnenin medya tipi: "image" veya "video_clip"
        clip_queries = []  # Video clip sahneleri için arama sorgusu
        image_ai_provider = task.get("image_ai", "Pollinations")
        aspect_ratio = task.get("aspect_ratio", "9:16")
        animation_provider = task.get("animation_provider", "none")
        premium_models = ["OpenAI", "Flux", "Flux-Pro", "SDXL"]
        
        for i, scene in enumerate(scenes):
            prompt = scene.get("image_prompt", "")
            media_type = scene.get("media_type", "image")
            clip_query = scene.get("clip_search_query", "")
            
            media_types.append(media_type)
            clip_queries.append(clip_query)
            
            if media_type == "video_clip":
                # Video klip sahneleri için MP4 uzantısı
                clip_name = f"assets/clip_{task_id}_{i}.mp4"
                output_paths.append(clip_name)
                temp_files.append(clip_name)
                prompts.append(prompt)  # Fallback görsel için
                providers.append(image_ai_provider)
            else:
                img_name = f"assets/scene_{task_id}_{i}.jpg"
                prompts.append(prompt)
                output_paths.append(img_name)
                temp_files.append(img_name)
                
                # İlk sahne (Hook) ve son sahne için Premium AI (HD kalite)
                if (i == 0 or i == len(scenes) - 1) and image_ai_provider not in premium_models:
                    providers.append("OpenAI-HD")
                    log_info = "İlk sahne GPT Image 1 HD ile yükseltildi." if i == 0 else "Son sahne GPT Image 1 HD ile yükseltildi."
                    step_name = "premium_hook" if i == 0 else "premium_outro"
                    video_logger.log_video_production_step(step_name, str(task_id), {"info": log_info})
                else:
                    providers.append(image_ai_provider)
        
        # Önce video kliplerini paralel olarak indir (G/Ç Paralelleştirmesi)
        clip_indices = [i for i, mt in enumerate(media_types) if mt == "video_clip" and clip_queries[i]]
        
        if clip_indices:
            print(f"[{task_id}] Toplam {len(clip_indices)} video klip paralel olarak indiriliyor...")
            
            def download_single_clip(i):
                print(f"[{task_id}] Sahne {i}: Video klip indiriliyor... ('{clip_queries[i]}' konu: '{topic}')")
                clip_success = fetch_clip_auto(clip_queries[i], output_paths[i], topic=topic)
                if clip_success:
                    video_logger.log_video_production_step("clip_fetched", str(task_id), {
                        "scene": i, "query": clip_queries[i]
                    })
                    return i, True
                else:
                    return i, False
            
            import concurrent.futures
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(5, len(clip_indices))) as executor:
                clip_results = await loop.run_in_executor(
                    None,
                    lambda: list(executor.map(download_single_clip, clip_indices))
                )
            
            # Başarısız klipleri statik görsele dönüştür
            for idx, success in clip_results:
                if not success:
                    print(f"[{task_id}] Sahne {idx}: Klip bulunamadı, statik görsel kullanılacak.")
                    media_types[idx] = "image"
                    output_paths[idx] = f"assets/scene_{task_id}_{idx}.jpg"
                    temp_files.append(output_paths[idx])
        
        # Statik görselleri paralel olarak üret (sadece image tipindekiler)
        image_indices = [i for i, mt in enumerate(media_types) if mt == "image"]
        image_prompts = [prompts[i] for i in image_indices]
        image_outputs = [output_paths[i] for i in image_indices]
        image_providers = [providers[i] for i in image_indices]
        
        if image_prompts:
            loop = asyncio.get_running_loop()
            image_results = await loop.run_in_executor(
                None,
                parallel_process_images,
                image_prompts,
                image_outputs,
                image_providers,
                topic,
            )
            
            # Başarısız görselleri işaretle
            for idx, success in enumerate(image_results):
                if not success:
                    real_idx = image_indices[idx]
                    output_paths[real_idx] = None  # Başarısız
        
        # Animasyon provider aktifse, görselleri paralel olarak videoya dönüştür
        if animation_provider and animation_provider != "none":
            anim_indices = [i for i, mt in enumerate(media_types) if mt == "image" and output_paths[i] and os.path.exists(output_paths[i])]
            
            if anim_indices:
                print(f"[{task_id}] Toplam {len(anim_indices)} görsel paralel olarak anime ediliyor ({animation_provider})...")
                
                def animate_single_image(i):
                    anim_output = f"assets/anim_{task_id}_{i}.mp4"
                    print(f"[{task_id}] Sahne {i}: Animasyon uygulanıyor ({animation_provider})...")
                    anim_success = animate_image(output_paths[i], anim_output, animation_provider)
                    if anim_success:
                        return i, anim_output
                    return i, None
                
                import concurrent.futures
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
                        video_logger.log_video_production_step("animated", str(task_id), {
                            "scene": idx, "provider": animation_provider
                        })
        
        # Başarılı medya dosyalarını filtrele
        valid_media_paths = [p for p in output_paths if p and os.path.exists(p)]
        
        success_rate = len(valid_media_paths) / len(scenes) * 100 if scenes else 0
        database.update_status(task_id, "media", 50 + int(success_rate * 0.3))
            
        if not valid_media_paths:
            database.update_status(task_id, "failed", 80, "Hiç medya indirilemedi.")
            return
            
        # 4. Video Kurgu (Render)
        database.update_status(task_id, "rendering", 85)
        safe_topic = "".join([c if c.isalnum() else "_" for c in topic])[:20]
        output_filename = f"vid_{task_id}_{safe_topic}.mp4"
        output_video_path = f"frontend/videos/{output_filename}"
        
        # Sahne metinlerini topla (altyazı için)
        narrations = [scene.get("narration", "") for scene in scenes]
        scene_pacings = [
            {"pacing": scene.get("pacing", "normal"), "mood": scene.get("mood", "")}
            for scene in scenes
        ]
        subtitle_style = task.get("subtitle_style", "tiktok")
        video_mode = task.get("video_mode", "slideshow")
        watermark_enabled = bool(task.get("watermark_enabled", False))
        transition_style = task.get("transition_style", "none")
        bgm_enabled = bool(task.get("bgm_enabled", False))
        bgm_tone = task.get("bgm_tone", "auto") or "auto"
        light_leak_enabled = bool(task.get("light_leak_enabled", False))
        
        video_success = await error_recovery.retry_with_backoff(
            create_video,
            valid_media_paths, 
            voice_file, 
            output_video_path, 
            narrations=narrations, 
            subtitle_style=subtitle_style, 
            subtitle_delay=task.get("subtitle_delay", 1.0),
            video_mode=video_mode,
            watermark_enabled=watermark_enabled,
            transition_style=transition_style,
            bgm_enabled=bgm_enabled,
            bgm_tone=bgm_tone,
            aspect_ratio=aspect_ratio,
            quality_level=quality_level,
            color_grade_style=task.get("color_grade_style", "auto_enhance"),
            scene_pacings=scene_pacings,
            letterbox_enabled=bool(task.get("letterbox_enabled", False)),
            light_leak_enabled=light_leak_enabled,
        )
        
        if video_success:
            # 5. Thumbnail (Kapak) Üretimi
            if valid_media_paths:
                try:
                    from thumbnail_generator import create_thumbnail
                    thumb_filename = f"thumb_{task_id}_{safe_topic}.jpg"
                    thumb_path = f"frontend/videos/{thumb_filename}"
                    create_thumbnail(valid_media_paths[0], topic, thumb_path)
                    video_logger.log_video_production_step("thumbnail", str(task_id), {"output": thumb_filename})
                except Exception as thumb_err:
                    print(f"[-] Thumbnail oluşturma hatası (İşlem devam ediyor): {thumb_err}")

            database.update_status(task_id, "completed", 100, None, output_filename)
            video_logger.log_video_production_step("completed", str(task_id), {"output": output_filename})
            print(f"[{task_id}] İŞLEM BİTTİ: {output_filename}")
        else:
            database.update_status(task_id, "failed", 85, "Video birleştirilemedi.")
            
    except Exception as e:
        video_logger.log_error(e, {"task_id": task_id, "topic": topic})
        database.update_status(task_id, "failed", 0, f"İşlem hatası: {str(e)}")
        
    finally:
        # Temp dosyaları temizle (başarılı olsa da olmasa da)
        cleanup_temp_files(temp_files, task_id)


def cleanup_temp_files(temp_files: List[str], task_id: int):
    """Temp dosyaları temizler, video dosyalarını korur"""
    for file_path in temp_files:
        try:
            if os.path.exists(file_path) and not file_path.startswith("frontend/videos/"):
                os.remove(file_path)
                print(f"[{task_id}] Temizlendi: {file_path}")
        except Exception as e:
            print(f"[{task_id}] Temizlik hatası: {file_path} - {e}")


@app.post("/api/videos/single")
async def add_single_video(req: VideoRequest):
    task_id = database.add_video_task(
        req.topic, req.category, req.tone, req.duration, req.language,
        req.script_ai, req.voice_ai, req.image_ai, req.subtitle_style, req.video_mode,
        req.voice_type, req.custom_script, req.sentence_pause,
        req.watermark_enabled, req.transition_style,
        req.bgm_enabled, req.bgm_tone,
        req.subtitle_delay,
        req.quality_level, req.aspect_ratio, req.animation_provider,
        req.color_grade_style, req.light_leak_enabled
    )
    video_logger.log_video_production_step("queued", str(task_id), {"topic": req.topic})
    return {"status": "success", "task_id": task_id}

@app.post("/api/videos/bulk")
async def add_bulk_videos(req: BulkVideoRequest):
    task_ids = []
    for topic in req.topics:
        topic = topic.strip()
        if topic:
            task_id = database.add_video_task(
                topic, "Genel", "Enerjik", req.duration, req.language,
                req.script_ai, req.voice_ai, req.image_ai, req.subtitle_style, req.video_mode,
                req.voice_type, None, req.sentence_pause,
                req.watermark_enabled, req.transition_style,
                req.bgm_enabled, req.bgm_tone,
                req.subtitle_delay,
                req.quality_level, req.aspect_ratio, req.animation_provider,
                "auto_enhance", req.light_leak_enabled
            )
            task_ids.append(task_id)
    
    video_logger.log_video_production_step("bulk_queued", "bulk", {"count": len(task_ids)})
    return {"status": "success", "count": len(req.topics), "task_ids": task_ids}


class MultiLangVideoRequest(BaseModel):
    topic: str
    languages: List[str] = ["tr", "en", "es"]
    duration: int = Field(default=30, ge=15, le=300)
    script_ai: Optional[str] = "Gemini"
    voice_ai: Optional[str] = "Edge-TTS"
    voice_type: Optional[str] = "erkek"
    image_ai: Optional[str] = "Pollinations"
    subtitle_style: Optional[str] = "tiktok"
    subtitle_delay: Optional[float] = 1.0
    video_mode: Optional[str] = "slideshow"
    sentence_pause: Optional[float] = 0.0
    watermark_enabled: Optional[bool] = False
    transition_style: Optional[str] = "none"
    bgm_enabled: Optional[bool] = False
    bgm_tone: Optional[str] = "auto"
    quality_level: Optional[str] = "medium"
    aspect_ratio: Optional[str] = "9:16"
    animation_provider: Optional[str] = "none"
    light_leak_enabled: Optional[bool] = False


@app.post("/api/videos/multi-lang")
async def add_multi_lang_video(req: MultiLangVideoRequest):
    """Aynı konuyu birden fazla dilde kuyruğa ekler (TR/EN/ES)."""
    task_ids = []
    lang_names = {"tr": "Türkçe", "en": "English", "es": "Espayıol"}
    for lang in req.languages:
        lang = lang.strip().lower()
        if lang not in ["tr", "en", "es"]:
            continue
        lang_label = lang_names.get(lang, lang)
        topic_with_lang = f"[{lang_label}] {req.topic}"
        task_id = database.add_video_task(
            topic_with_lang, "Genel", "Enerjik", req.duration, lang,
            req.script_ai, req.voice_ai, req.image_ai, req.subtitle_style, req.video_mode,
            req.voice_type, None, req.sentence_pause,
            req.watermark_enabled, req.transition_style,
            req.bgm_enabled, req.bgm_tone,
            req.subtitle_delay,
            req.quality_level, req.aspect_ratio, req.animation_provider,
            "auto_enhance", req.light_leak_enabled
        )
        task_ids.append({"language": lang, "task_id": task_id})
    
    video_logger.log_video_production_step("multi_lang_queued", "multi", {
        "topic": req.topic, "languages": req.languages, "count": len(task_ids)
    })
    return {"status": "success", "topic": req.topic, "tasks": task_ids}



class SettingsRequest(BaseModel):
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    pexels_api_key: Optional[str] = None
    pixabay_api_key: Optional[str] = None
    unsplash_api_key: Optional[str] = None
    stability_api_key: Optional[str] = None
    replicate_api_token: Optional[str] = None
    luma_api_key: Optional[str] = None
    runway_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None

@app.get("/api/settings")
async def get_settings_api():
    return {
        "openai_api_key": os.environ.get("OPENAI_API_KEY", ""),
        "gemini_api_key": os.environ.get("GEMINI_API_KEY", ""),
        "elevenlabs_api_key": os.environ.get("ELEVENLABS_API_KEY", ""),
        "pexels_api_key": os.environ.get("PEXELS_API_KEY", ""),
        "pixabay_api_key": os.environ.get("PIXABAY_API_KEY", ""),
        "unsplash_api_key": os.environ.get("UNSPLASH_API_KEY", ""),
        "stability_api_key": os.environ.get("STABILITY_API_KEY", ""),
        "replicate_api_token": os.environ.get("REPLICATE_API_TOKEN", ""),
        "luma_api_key": os.environ.get("LUMA_API_KEY", ""),
        "runway_api_key": os.environ.get("RUNWAY_API_KEY", ""),
        "huggingface_api_key": os.environ.get("HUGGINGFACE_API_KEY", "")
    }

@app.post("/api/settings")
async def save_settings_api(req: SettingsRequest):
    keys = {
        "OPENAI_API_KEY": req.openai_api_key,
        "GEMINI_API_KEY": req.gemini_api_key,
        "ELEVENLABS_API_KEY": req.elevenlabs_api_key,
        "PEXELS_API_KEY": req.pexels_api_key,
        "PIXABAY_API_KEY": req.pixabay_api_key,
        "UNSPLASH_API_KEY": req.unsplash_api_key,
        "STABILITY_API_KEY": req.stability_api_key,
        "REPLICATE_API_TOKEN": req.replicate_api_token,
        "LUMA_API_KEY": req.luma_api_key,
        "RUNWAY_API_KEY": req.runway_api_key,
        "HUGGINGFACE_API_KEY": req.huggingface_api_key
    }
    
    for env_key, val in keys.items():
        if val is not None:
            os.environ[env_key] = val.strip()
            
    # .env dosyasını güncelle
    try:
        existing_keys = {}
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            k, v = parts
                            existing_keys[k.strip()] = v.strip()
        
        for env_key, val in keys.items():
            if val is not None:
                existing_keys[env_key] = val.strip()
        
        with open(".env", "w", encoding="utf-8") as f:
            for k, v in existing_keys.items():
                f.write(f"{k}={v}\n")
    except Exception as e:
        print(f"[-] .env güncelleme hatası: {e}")
        
    return {"status": "success"}

@app.get("/api/stats")
async def get_stats():
    return database.get_stats()

@app.get("/api/videos/completed")
async def get_completed_videos():
    """Get completed videos for social media posting"""
    return database.get_tasks_by_status("completed")

@app.get("/favicon.ico")
async def favicon():
    """Return no content for missing favicon to prevent browser 404 logs."""
    return Response(status_code=204)

@app.get("/platform_setup_guides.html")
async def platform_setup_guides():
    """Serve platform setup guides HTML"""
    return FileResponse("platform_setup_guides.html")

@app.get("/api/videos")
async def get_videos():
    return database.get_all_tasks()

class DeleteRequest(BaseModel):
    task_ids: List[int]

@app.delete("/api/videos")
async def delete_videos(req: DeleteRequest):
    try:
        video_paths = database.delete_tasks(req.task_ids)
        # Attempt to delete physical files
        for vp in video_paths:
            path = f"frontend/videos/{vp}"
            if os.path.exists(path):
                os.remove(path)
        return {"status": "success", "deleted": len(req.task_ids)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Frontend Statik Dosyalarını Sun (Önbellekleme Aktif)
class CachedStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        # CSS, JS, resimler ve yazı tiplerini 7 gün boyunca önbelleğe al (Hız: 0ms)
        response.headers["Cache-Control"] = "public, max-age=604800, must-revalidate"
        return response

app.mount("/static", CachedStaticFiles(directory="frontend"), name="static")

@app.get("/")
async def serve_home():
    return FileResponse("frontend/index.html")

@app.on_event("startup")
async def startup_event():
    """Uygulama başladığında kuyruk yöneticisini başlatır"""
    # Veritabanını başlat
    database.init_db()
    
    # Kuyruk yöneticisini arka planda başlat
    asyncio.create_task(start_queue_manager())
    print("🚀 Otomatik kuyruk yöneticisi başlatıldı!")

@app.get("/api/queue-status")
async def get_queue_status_api():
    """Kuyruk durumunu döndürür"""
    return get_queue_status()

@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapanırken kuyruk yöneticisini durdurur"""
    from queue_manager import stop_queue_manager
    stop_queue_manager()
    print("🛑 Kuyruk yöneticisi durduruldu.")

@app.post("/api/test-voice")
async def test_voice_api(request: Request):
    """Ses test API endpoint'i"""
    try:
        data = await request.json()
        text = data.get("text", "Test metni")
        voice_type = data.get("voice_type", "erkek")
        voice_ai = data.get("voice_ai", "Edge-TTS")
        
        # Geçici ses dosyası oluştur
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_filename = tmp_file.name
            
            # Ses üret (Eğer ElevenLabs seçilirse ve hata verirse Edge-TTS'e fallback yap)
            print(f"[Ses Testi] Üretiliyor: {voice_ai} ({voice_type})")
            success = await generate_voice_async(text, tmp_filename, voice_ai, voice_type)
            
            if not success and voice_ai == "ElevenLabs":
                print("[⚠️ Ses Testi] ElevenLabs testi başarısız oldu (muhtemelen API anahtarı geçersiz veya limit doldu). Edge-TTS'e geçiliyor...")
                success = await generate_voice_async(text, tmp_filename, "Edge-TTS", voice_type)
            
            if success and os.path.exists(tmp_filename):
                # Dosyayı binary olarak geri döndür
                from fastapi.responses import FileResponse
                return FileResponse(tmp_filename, media_type="audio/mpeg", filename=f"test_voice_{voice_type}.mp3")
            else:
                return {"error": "Ses üretilemedi"}
                
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
