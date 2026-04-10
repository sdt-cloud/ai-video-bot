import asyncio
import os
import tempfile
from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from typing import List, Optional
import database
import time
import traceback

# Connection error filter'ı import et
from connection_filter import setup_connection_filter

# Connection filter'ı kur
setup_connection_filter()

# Bot modüllerini içe aktar
from script_generator import generate_script
from voice_generator import generate_voice_async
from image_generator import generate_image
from video_maker import create_video
from nedir_integration import NedirIntegration
from queue_manager import start_queue_manager, get_queue_status
from performance_optimizer import parallel_process_images, get_optimized_settings
from error_handler import error_recovery, video_logger
from custom_social_api import custom_social_router

app = FastAPI()

# Sosyal medya yönetimi route'larını ekle
app.include_router(custom_social_router)

class VideoRequest(BaseModel):
    topic: str
    category: Optional[str] = "Genel"
    tone: Optional[str] = "Enerjik"
    duration: int = Field(default=30, ge=15, le=300)
    language: Optional[str] = "tr"
    script_ai: Optional[str] = "Gemini"
    voice_ai: Optional[str] = "Edge-TTS"
    voice_type: Optional[str] = "erkek"  # Ses tipi seçeneği
    image_ai: Optional[str] = "Pollinations"
    subtitle_style: Optional[str] = "tiktok"
    video_mode: Optional[str] = "slideshow"

class BulkVideoRequest(BaseModel):
    topics: List[str]
    duration: int = Field(default=30, ge=15, le=300)
    language: Optional[str] = "tr"
    script_ai: Optional[str] = "Gemini"
    voice_ai: Optional[str] = "Edge-TTS"
    image_ai: Optional[str] = "Pollinations"
    subtitle_style: Optional[str] = "tiktok"
    video_mode: Optional[str] = "slideshow"

async def process_video(task):
    task_id = task["id"]
    topic = task["topic"]
    temp_files = []  # Temizlik için temp dosyaları takip et
    
    print(f"[{task_id}] İŞLEM BAŞLIYOR: {topic}")
    video_logger.log_video_production_step("started", str(task_id), {"topic": topic})
    
    try:
        # 1. Senaryo Aşaması
        database.update_status(task_id, "scripting", 10)
        script_data = await error_recovery.retry_with_backoff(
            generate_script,
            topic, 
            task.get("script_ai", "Gemini"), 
            task.get("duration", 30)
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
        target_duration_seconds = int(task.get("duration", 30) or 30)
        voice_success = await generate_voice_async(
            full_narration,
            voice_file,
            voice_ai_provider,
            voice_type,
            target_duration_seconds=target_duration_seconds,
        )
        
        if not voice_success:
            database.update_status(task_id, "failed", 30, "Ses sentezlenemedi.")
            return
            
        # 3. Medya Aşaması (Görseller) - PARALEL İŞLEME
        database.update_status(task_id, "media", 50)
        
        # Paralel görsel üretimi için hazırlık
        prompts = []
        output_paths = []
        for i, scene in enumerate(scenes):
            prompt = scene.get("image_prompt", "")
            img_name = f"assets/scene_{task_id}_{i}.jpg"
            prompts.append(prompt)
            output_paths.append(img_name)
            temp_files.append(img_name)
        
        # Paralel görsel üretimi
        image_ai_provider = task.get("image_ai", "Pollinations")
        loop = asyncio.get_running_loop()
        image_results = await loop.run_in_executor(
            None,
            parallel_process_images,
            prompts,
            output_paths,
            image_ai_provider
        )
        
        # Başarılı görselleri filtrele
        image_paths = [output_paths[i] for i, success in enumerate(image_results) if success]
        
        success_rate = len(image_paths) / len(scenes) * 100 if scenes else 0
        database.update_status(task_id, "media", 50 + int(success_rate * 0.3))
            
        if not image_paths:
            database.update_status(task_id, "failed", 80, "Hiç görsel indirilemedi.")
            return
            
        # 4. Video Kurgu (Render)
        database.update_status(task_id, "rendering", 85)
        safe_topic = "".join([c if c.isalnum() else "_" for c in topic])[:20]
        output_filename = f"vid_{task_id}_{safe_topic}.mp4"
        output_video_path = f"frontend/videos/{output_filename}"
        
        # Sahne metinlerini topla (altyazı için)
        narrations = [scene.get("narration", "") for scene in scenes]
        subtitle_style = task.get("subtitle_style", "tiktok")
        video_mode = task.get("video_mode", "slideshow")
        
        video_success = await error_recovery.retry_with_backoff(
            create_video,
            image_paths, 
            voice_file, 
            output_video_path, 
            narrations=narrations, 
            subtitle_style=subtitle_style, 
            video_mode=video_mode
        )
        
        if video_success:
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
        req.script_ai, req.voice_ai, req.image_ai, req.subtitle_style, req.video_mode, req.voice_type
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
                req.script_ai, req.voice_ai, req.image_ai, req.subtitle_style, req.video_mode
            )
            task_ids.append(task_id)
    
    video_logger.log_video_production_step("bulk_queued", "bulk", {"count": len(task_ids)})
    return {"status": "success", "count": len(req.topics), "task_ids": task_ids}

@app.get("/api/nedir/fetch")
async def fetch_nedir_contents(post_type: str = "posts", limit: int = 20):
    import requests
    import re
    import html
    import random
    
    wp_api_base = os.environ.get("NEDIR_WP_API_URL", "http://localhost/wp-json/wp/v2")
    
    # Daha önce kuyruğa alınmış / tamamlanmış başlıkları al
    existing_topics = database.get_existing_topics()
    
    try:
        # Önce toplam post sayısını öğren (per_page=1 ile sadece header bilgisi için)
        head_url = f"{wp_api_base}/{post_type.strip()}?per_page=1"
        head_resp = requests.get(head_url, timeout=10)
        if head_resp.status_code != 200:
            return {"status": "error", "message": f"WordPress API Hatası: {head_resp.status_code}"}
        
        total_posts = int(head_resp.headers.get("X-WP-Total", 0))
        
        if total_posts == 0:
            return {"status": "error", "message": f"'{post_type}' tipinde içerik bulunamadı. show_in_rest ayarını kontrol edin."}
        
        # Sayfa sayısını ASIL limit değerine göre hesapla
        import math
        total_pages = math.ceil(total_posts / limit)
        
        # Rastgele bir sayfa seç
        random_page = random.randint(1, max(1, total_pages))
        
        fetch_url = f"{wp_api_base}/{post_type.strip()}?per_page={limit}" + f"&page={random_page}"
        response = requests.get(fetch_url, timeout=10)
        
        # Sayfa aşımı olursa son sayfayı dene
        if response.status_code == 400:
            random_page = 1
            fetch_url = f"{wp_api_base}/{post_type.strip()}?per_page={limit}" + "&page=1"
            response = requests.get(fetch_url, timeout=10)
        
        if response.status_code != 200:
            return {"status": "error", "message": f"WordPress API Hatası: {response.status_code}"}
            
        posts = response.json()
        results = []
        skipped = 0
        for post in posts:
            title = post.get("title", {}).get("rendered", "Başlıksız")
            excerpt = post.get("excerpt", {}).get("rendered", "")
            
            clean_excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()
            clean_excerpt = html.unescape(clean_excerpt)
            title = html.unescape(title)
            
            # Daha önce yapılmışsa atla
            if title.lower() in existing_topics:
                skipped += 1
                continue
            
            if not clean_excerpt:
                content = post.get("content", {}).get("rendered", "")
                clean_excerpt = html.unescape(re.sub(r'<[^>]+>', '', content).strip())[:250] + "..."
                
            results.append({
                "id": post.get("id"),
                "title": title,
                "excerpt": clean_excerpt
            })
            
        return {
            "status": "success",
            "data": results,
            "meta": {
                "total_posts": total_posts,
                "page": random_page,
                "total_pages": total_pages,
                "skipped_already_done": skipped
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"Veri çekilirken bağlantı hatası: {str(e)}"}

@app.get("/api/nedir/concepts")
async def get_nedir_concepts(category: Optional[str] = None, limit: int = 20):
    """Nedir.me'den kavramları çeker"""
    try:
        integration = NedirIntegration()
        concepts = integration.get_concepts(category=category, limit=limit)
        return {
            "status": "success",
            "data": concepts,
            "count": len(concepts)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/nedir/bulk-videos")
async def create_bulk_videos_from_nedir(category: Optional[str] = None, max_concepts: int = 10):
    """Nedir.me kavramlarından otomatik video konuları oluşturur"""
    try:
        integration = NedirIntegration()
        video_topics = integration.batch_process_for_videos(max_concepts=max_concepts)
        
        if not video_topics:
            return {"status": "error", "message": "Video konuları oluşturulamadı"}
        
        # Veritabanına ekle
        task_ids = []
        for topic in video_topics:
            task_id = database.add_video_task(topic, category, "Otomatik", 60, "Türkçe", "Gemini", "Edge-TTS", "Pollinations", "tiktok", "slideshow", "erkek")
            task_ids.append(task_id)
        
        # NOT: Artık kuyruk yöneticisi otomatik işleyecek
        # asyncio.create_task(process_video(task)) kaldırıldı
        
        return {
            "status": "success", 
            "message": f"{len(task_ids)} video kuyruğa eklendi",
            "task_ids": task_ids
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/stats")
async def get_stats():
    return database.get_stats()

@app.get("/api/videos/completed")
async def get_completed_videos():
    """Get completed videos for social media posting"""
    return database.get_tasks_by_status("completed")

@app.get("/social")
async def social_dashboard():
    """Serve the new social media dashboard HTML"""
    return FileResponse("custom_social_dashboard.html")

@app.get("/custom-social")
async def custom_social_dashboard():
    """Alias for the new social media dashboard HTML"""
    return FileResponse("custom_social_dashboard.html")

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

# Frontend Statik Dosyalarını Sun
app.mount("/static", StaticFiles(directory="frontend"), name="static")

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
async def test_voice_api(request):
    """Ses test API endpoint'i"""
    try:
        data = await request.json()
        text = data.get("text", "Test metni")
        voice_type = data.get("voice_type", "erkek")
        
        # Geçici ses dosyası oluştur
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_filename = tmp_file.name
            
            # Ses üret
            success = await generate_voice_async(text, tmp_filename, "ElevenLabs", voice_type)
            
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
