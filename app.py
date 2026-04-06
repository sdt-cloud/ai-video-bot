import asyncio
import os
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import asyncio
import logging
import uvicorn
import database
import time
import traceback
import script_generator
import voice_generator
import image_generator
import video_maker
import queue_manager
import nedir_integration
from connection_filter import setup_connection_filter
from social_media_manager import social_manager

# Connection filter'ı kur
setup_connection_filter()

# Bot modüllerini içe aktar
from script_generator import generate_script
from voice_generator import generate_voice_async
from image_generator import generate_image
from video_maker import create_video
from nedir_integration import NedirIntegration
from queue_manager import start_queue_manager, get_queue_status

app = FastAPI()

class VideoRequest(BaseModel):
    topic: str
    category: Optional[str] = "Genel"
    tone: Optional[str] = "Enerjik"
    duration: Optional[int] = 30
    language: Optional[str] = "tr"
    script_ai: Optional[str] = "Gemini"
    voice_ai: Optional[str] = "Edge-TTS"
    voice_type: Optional[str] = "erkek"  # Ses tipi seçeneği
    image_ai: Optional[str] = "Pollinations"
    subtitle_style: Optional[str] = "tiktok"
    video_mode: Optional[str] = "slideshow"

class BulkVideoRequest(BaseModel):
    topics: List[str]
    duration: Optional[int] = 30
    language: Optional[str] = "tr"
    script_ai: Optional[str] = "Gemini"
    voice_ai: Optional[str] = "Edge-TTS"
    image_ai: Optional[str] = "Pollinations"
    subtitle_style: Optional[str] = "tiktok"
    video_mode: Optional[str] = "slideshow"

async def process_video(task):
    task_id = task["id"]
    topic = task["topic"]
    print(f"[{task_id}] İŞLEM BAŞLIYOR: {topic}")
    
    # 1. Senaryo Aşaması
    database.update_status(task_id, "scripting", 10)
    script_data = generate_script(topic, task.get("script_ai", "Gemini"), task.get("duration", 30))
    
    if not script_data or "scenes" not in script_data:
        database.update_status(task_id, "failed", 10, "Senaryo üretilemedi API hatası.")
        return
        
    scenes = script_data.get("scenes", [])
    
    # 2. Medya Aşaması (Ses)
    database.update_status(task_id, "media", 30)
    full_narration = " ".join([scene.get("narration", "") for scene in scenes])
    
    os.makedirs("frontend/videos", exist_ok=True)
    os.makedirs("assets", exist_ok=True)
    
    voice_file = f"assets/narration_{task_id}.mp3"
    voice_ai_provider = task.get("voice_ai", "Edge-TTS")
    voice_type = task.get("voice_type", "erkek")
    voice_success = await generate_voice_async(full_narration, voice_file, voice_ai_provider, voice_type)
    
    if not voice_success:
        database.update_status(task_id, "failed", 30, "Ses sentezlenemedi.")
        return
        
    # 3. Medya Aşaması (Görseller)
    database.update_status(task_id, "media", 50)
    image_paths = []
    total_imgs = len(scenes)
    for i, scene in enumerate(scenes):
        prompt = scene.get("image_prompt", "")
        img_name = f"assets/scene_{task_id}_{i}.jpg"
        image_ai_provider = task.get("image_ai", "Pollinations")
        img_success = generate_image(prompt, img_name, image_ai_provider)
        if img_success:
            image_paths.append(img_name)
        
        # Sadece ilerleme barı için % hesapla (50 ile 80 arası resimlere gitsin)
        current_progress = 50 + int((i / total_imgs) * 30)
        database.update_status(task_id, "media", current_progress)
            
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
    
    video_success = create_video(image_paths, voice_file, output_video_path, narrations=narrations, subtitle_style=subtitle_style, video_mode=video_mode)
    
    if video_success:
        database.update_status(task_id, "completed", 100, None, output_filename)
        print(f"[{task_id}] İŞLEM BİTTİ: {output_filename}")
    else:
        database.update_status(task_id, "failed", 85, "Video birleştirilemedi.")


@app.post("/api/videos/single")
async def add_single_video(req: VideoRequest):
    task_id = database.add_video_task(
        req.topic, req.category, req.tone, req.duration, req.language,
        req.script_ai, req.voice_ai, req.image_ai, req.subtitle_style, req.video_mode
    )
    return {"status": "success", "task_id": task_id}

@app.post("/api/videos/bulk")
async def add_bulk_videos(req: BulkVideoRequest):
    for topic in req.topics:
        topic = topic.strip()
        if topic:
            database.add_video_task(
                topic, "Genel", "Enerjik", req.duration, req.language,
                req.script_ai, req.voice_ai, req.image_ai, req.subtitle_style, req.video_mode
            )
    return {"status": "success", "count": len(req.topics)}

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
            task_id = database.add_task(topic, category, "Otomatik", 60, "Türkçe", "T5", "Edge-TTS", "Pollinations", "tiktok", "slideshow")
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

@app.get("/social", response_class=HTMLResponse)
async def social_dashboard():
    """Sosyal medya dashboard sayfası"""
    with open("frontend/social-dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/api/social/status")
async def get_social_status():
    """Sosyal medya platform durumlarını döndürür"""
    return {
        "youtube": social_manager.config["youtube"]["enabled"],
        "twitter": social_manager.config["twitter"]["enabled"],
        "tiktok": social_manager.config["tiktok"]["enabled"],
        "facebook": social_manager.config["facebook"]["enabled"]
    }

@app.post("/api/social/config")
async def update_social_config(request: Request):
    """Sosyal medya konfigürasyonunu günceller"""
    try:
        config = await request.json()
        
        # Konfigürasyonu güncelle
        social_manager.config.update(config)
        
        # Dosyaya kaydet
        import shutil
        shutil.copy("config/social_media_config.json", "config/social_media_config.json.backup")
        
        with open("config/social_media_config.json", 'w', encoding='utf-8') as f:
            json.dump(social_manager.config, f, indent=2, ensure_ascii=False)
        
        # API'leri yeniden kur
        social_manager.setup_apis()
        
        return {"success": True, "message": "Konfigürasyon güncellendi"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/social/share")
async def share_video(request: Request, background_tasks: BackgroundTasks):
    """Videoyu sosyal medyada paylaşır"""
    try:
        data = await request.json()
        
        # Video bilgilerini al
        video_id = data["video_id"]
        video = database.get_video_by_id(video_id)
        
        if not video:
            return {"success": False, "error": "Video bulunamadı"}
        
        # SocialPost objesi oluştur
        from social_media_manager import SocialPost
        post = SocialPost(
            video_path=f"frontend/videos/{video['filename']}",
            title=data["title"],
            description=data["description"],
            tags=data["tags"],
            platform=data["platforms"][0] if data["platforms"] else "youtube",
            scheduled_time=data.get("schedule_time")
        )
        
        # Arka planda paylaşımı başlat
        background_tasks.add_task(share_video_background, post, data["platforms"])
        
        return {"success": True, "message": "Video paylaşım için kuyruğa alındı"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def share_video_background(post: 'SocialPost', platforms: List[str]):
    """Arka planda video paylaşımı yapar"""
    try:
        # Her platform için paylaşım yap
        for platform in platforms:
            post.platform = platform
            result = social_manager.post_to_all_platforms([post])
            
            # Sonucu veritabanına kaydet
            database.add_share_history(
                video_id=post.video_path,
                platforms=platforms,
                success=result[0]["success"],
                post_url=result[0].get("video_url", result[0].get("tweet_url", "")),
                error=result[0].get("error", "")
            )
            
            print(f"✅ {platform} paylaşımı: {result[0]['success']}")
            
    except Exception as e:
        print(f"❌ Paylaşım hatası: {e}")

@app.get("/api/social/history")
async def get_share_history():
    """Paylaşım geçmişini döndürür"""
    try:
        history = database.get_share_history()
        return history
    except Exception as e:
        return []

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
