import asyncio
import os
from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import database
import time
import traceback

# Bot modüllerini içe aktar
from script_generator import generate_script
from voice_generator import generate_voice_async
from image_generator import generate_image
from video_maker import create_video

app = FastAPI()

class VideoRequest(BaseModel):
    topic: str
    category: Optional[str] = "Genel"
    tone: Optional[str] = "Enerjik"
    duration: Optional[int] = 30
    language: Optional[str] = "tr"
    script_ai: Optional[str] = "Gemini"
    voice_ai: Optional[str] = "Edge-TTS"
    image_ai: Optional[str] = "Pollinations"

class BulkVideoRequest(BaseModel):
    topics: List[str]
    duration: Optional[int] = 30
    language: Optional[str] = "tr"
    script_ai: Optional[str] = "Gemini"
    voice_ai: Optional[str] = "Edge-TTS"
    image_ai: Optional[str] = "Pollinations"

async def process_video(task):
    task_id = task["id"]
    topic = task["topic"]
    print(f"[{task_id}] İŞLEM BAŞLIYOR: {topic}")
    
    # 1. Senaryo Aşaması
    database.update_status(task_id, "scripting", 10)
    script_data = generate_script(topic, task.get("script_ai", "Gemini"))
    
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
    voice_success = await generate_voice_async(full_narration, voice_file)
    
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
        img_success = generate_image(prompt, img_name)
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
    
    video_success = create_video(image_paths, voice_file, output_video_path, narrations=narrations)
    
    if video_success:
        database.update_status(task_id, "completed", 100, None, output_filename)
        print(f"[{task_id}] İŞLEM BİTTİ: {output_filename}")
    else:
        database.update_status(task_id, "failed", 85, "Video birleştirilemedi.")


async def worker_loop():
    print("[+] Arka Plan İşçisi (Worker) Başladı. Görev bekleniyor...")
    while True:
        try:
            task = database.get_pending_task()
            if task:
                await process_video(task)
            else:
                await asyncio.sleep(3) # Görev yoksa 3 sn bekle
        except Exception as e:
            print(f"Worker Hatası: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(worker_loop())

@app.post("/api/videos/single")
async def add_single_video(req: VideoRequest):
    task_id = database.add_video_task(
        req.topic, req.category, req.tone, req.duration, req.language,
        req.script_ai, req.voice_ai, req.image_ai
    )
    return {"status": "success", "task_id": task_id}

@app.post("/api/videos/bulk")
async def add_bulk_videos(req: BulkVideoRequest):
    for topic in req.topics:
        topic = topic.strip()
        if topic:
            database.add_video_task(
                topic, "Genel", "Enerjik", req.duration, req.language,
                req.script_ai, req.voice_ai, req.image_ai
            )
    return {"status": "success", "count": len(req.topics)}

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
def serve_home():
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
