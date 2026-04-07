from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from social_media_manager import SocialMediaManager

# FastAPI router for social media endpoints
social_router = APIRouter(prefix="/social", tags=["social media"])
manager = SocialMediaManager()

class SocialConfig(BaseModel):
    provider: str
    api_key: str
    enabled: bool = True

class SocialPostRequest(BaseModel):
    video_id: int
    platforms: List[str]
    content: Optional[str] = None
    schedule_time: Optional[str] = None
    provider: str = "ayrshare"

@social_router.get("/config")
async def get_config():
    """Get current API configuration"""
    return manager.api_configs

@social_router.post("/config")
async def update_config(config: SocialConfig):
    """Update API configuration"""
    if manager.configure_api(config.provider, config.api_key, config.enabled):
        return {"success": True}
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")

@social_router.post("/post")
async def create_post(request: SocialPostRequest):
    """Post video to social media platforms"""
    if not request.video_id or not request.platforms:
        raise HTTPException(status_code=400, detail="Video ID and platforms are required")
    
    result = manager.post_video_to_social_media(
        video_id=request.video_id,
        platforms=request.platforms,
        content=request.content,
        schedule_time=request.schedule_time,
        provider=request.provider
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@social_router.get("/history")
async def get_history(limit: int = 50):
    """Get post history"""
    posts = manager.get_post_history(limit)
    return posts

@social_router.get("/post/{post_id}")
async def get_post(post_id: int):
    """Get specific post details"""
    from database import get_db
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sp.*, v.topic, v.video_path 
            FROM social_posts sp
            JOIN videos v ON sp.video_id = v.id
            WHERE sp.id = ?
        """, (post_id,))
        
        post = cursor.fetchone()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        result = dict(post)
        result["platforms"] = json.loads(result["platforms"])
        result["result"] = json.loads(result["result"])
        
        return result

@social_router.get("/platforms")
async def get_platforms():
    """Get supported platforms"""
    return manager.get_platform_list()
