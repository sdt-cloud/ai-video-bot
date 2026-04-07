from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
from custom_social_manager import CustomSocialMediaManager
import openai
import os

# FastAPI router for custom social media endpoints
custom_social_router = APIRouter(prefix="/social/api", tags=["social media"])
manager = CustomSocialMediaManager()

class PlatformConfig(BaseModel):
    platform: str
    enabled: bool
    config_data: Optional[dict] = None

class CustomPostRequest(BaseModel):
    video_id: int
    platforms: List[str]
    content: Optional[str] = None
    youtube_title: Optional[str] = None

class GenerateContentRequest(BaseModel):
    video_id: int

@custom_social_router.post("/generate-content")
async def generate_ai_content(request: GenerateContentRequest):
    """Generate AI title and description for video"""
    try:
        # Video bilgilerini al
        from database import get_db
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos WHERE id = ?", (request.video_id,))
            video = cursor.fetchone()
            
            if not video:
                raise HTTPException(status_code=404, detail="Video not found")
            
            video_data = dict(video)
        
        # AI ile başlık ve açıklama üret
        topic = video_data.get('topic', '')
        category = video_data.get('category', '')
        
        prompt = f"""
        Aşağıdaki video konusu için çekici bir başlık ve kısa açıklama oluştur.
        
        Video Konusu: {topic}
        Kategori: {category}
        
        Başlık: (Maksimum 60 karakter, çekici ve SEO dostu)
        Açıklama: (Maksimum 150 karakter, ilgi çekici ve paylaşılabilir)
        
        Sosyal medya için optimize edilmiş, Türkçe içerik üret.
        """
        
        # OpenAI API çağrısı
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sen sosyal medya uzmanısın. Videolar için çekici başlıklar ve açıklamalar üretiyorsun."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Yanıtı parse et
        lines = ai_response.split('\n')
        title = ""
        description = ""
        
        for line in lines:
            if line.startswith('Başlık:'):
                title = line.replace('Başlık:', '').strip()
            elif line.startswith('Açıklama:'):
                description = line.replace('Açıklama:', '').strip()
        
        # Eğer parse edilemediyse varsayılan değerler kullan
        if not title:
            title = f"🎬 {topic}"
        if not description:
            description = f"Muhteşem bir video: {topic}. İzlemeyi unutmayın! 👍"
        
        # Başlık ve açıklamayı kısalt
        title = title[:60] if len(title) > 60 else title
        description = description[:150] if len(description) > 150 else description
        
        return {
            "title": title,
            "description": description,
            "video_topic": topic,
            "category": category
        }
        
    except Exception as e:
        # Hata durumunda basit varsayılan değerler döndür
        return {
            "title": f"🎬 {topic if 'topic' in locals() else 'Harika Video'}",
            "description": f"Muhteşem bir video içeriği! İzlemeyi unutmayın. 👍",
            "error": str(e)
        }

@custom_social_router.get("/status")
async def get_platform_status():
    """Get current platform status"""
    return manager.get_platform_status()

@custom_social_router.get("/config")
async def get_platform_config():
    """Get current platform API configuration"""
    return manager.api_configs

@custom_social_router.post("/config")
async def update_platform_config(config: PlatformConfig):
    """Update platform configuration"""
    if config.config_data:
        # Save config data and set enabled if requested
        updated_config = dict(config.config_data)
        if config.enabled:
            updated_config["enabled"] = True
        current_config = manager.api_configs.get(config.platform, {})
        current_config.update(updated_config)
        success = manager.configure_platform(config.platform, current_config)
    else:
        # Only update enabled state
        current_config = manager.api_configs.get(config.platform, {})
        current_config["enabled"] = config.enabled
        success = manager.configure_platform(config.platform, current_config)
    
    if success:
        return {"success": True}
    else:
        raise HTTPException(status_code=400, detail="Invalid platform")

@custom_social_router.post("/post")
async def create_custom_post(request: CustomPostRequest, background_tasks: BackgroundTasks):
    """Post video to custom social media platforms"""
    if not request.video_id or not request.platforms:
        raise HTTPException(status_code=400, detail="Video ID and platforms are required")
    
    # Background task olarak çalıştır
    background_tasks.add_task(
        manager.post_video_to_platforms,
        request.video_id,
        request.platforms,
        request.content
    )
    
    return {"success": True, "message": "Gönderi işlemi başlatıldı"}

@custom_social_router.get("/history")
async def get_custom_history(limit: int = 50):
    """Get custom social media post history"""
    from database import get_db
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_social_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id INTEGER,
                platforms TEXT,
                content TEXT,
                results TEXT,
                status TEXT DEFAULT 'posted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos (id)
            )
        """)
        cursor.execute("""
            SELECT csp.*, v.topic 
            FROM custom_social_posts csp
            JOIN videos v ON csp.video_id = v.id
            ORDER BY csp.created_at DESC
            LIMIT ?
        """, (limit,))
        
        posts = []
        for row in cursor.fetchall():
            post = dict(row)
            post["platforms"] = json.loads(post["platforms"])
            post["results"] = json.loads(post["results"])
            posts.append(post)
        
        return posts

@custom_social_router.get("/post/{post_id}")
async def get_custom_post(post_id: int):
    """Get specific custom post details"""
    from database import get_db
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT csp.*, v.topic 
            FROM custom_social_posts csp
            JOIN videos v ON csp.video_id = v.id
            WHERE csp.id = ?
        """, (post_id,))
        
        post = cursor.fetchone()
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        result = dict(post)
        result["platforms"] = json.loads(result["platforms"])
        result["results"] = json.loads(result["results"])
        
        return result

@custom_social_router.get("/test/{platform}")
async def test_platform(platform: str):
    """Test a specific platform connection"""
    try:
        if platform == "facebook":
            result = await manager.post_to_facebook("Test gönderi 🚀")
        elif platform == "twitter":
            result = await manager.post_to_twitter("Test tweet 🐦")
        elif platform == "instagram":
            return {"error": "Instagram testi için medya dosyası gerekli"}
        elif platform == "youtube":
            return {"error": "YouTube testi için video dosyası gerekli"}
        elif platform == "tiktok":
            result = await manager.post_to_tiktok("Test", None)
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")
        
        return result
    except Exception as e:
        return {"error": str(e)}

@custom_social_router.get("/setup-guide/{platform}")
async def get_setup_guide(platform: str):
    """Get setup guide for specific platform"""
    guides = {
        "facebook": {
            "title": "Facebook Graph API Kurulumu",
            "steps": [
                "https://developers.facebook.com/ adresine gidin",
                "Create App → Business seçin",
                "Facebook Login ürününü ekleyin",
                "App ID ve App Secret'ı alın",
                "Graph API Explorer'dan Access Token alın",
                "Page ID'yi bulun"
            ],
            "required_fields": ["app_id", "app_secret", "access_token", "page_id"],
            "cost": "Free (200 requests/hour)"
        },
        "twitter": {
            "title": "Twitter/X API Kurulumu",
            "steps": [
                "https://developer.twitter.com/ adresine gidin",
                "Free Account ile kayıt olun",
                "Create Project oluşturun",
                "Create App oluşturun",
                "API Key, Access Token ve Bearer Token'ı alın",
                "App permissions'ı Read and Write yapın"
            ],
            "required_fields": ["api_key", "api_secret", "access_token", "access_token_secret", "bearer_token"],
            "cost": "Free (500,000 tweets/month)"
        },
        "instagram": {
            "title": "Instagram API Kurulumu",
            "steps": [
                "Facebook Developer hesabını kullanın",
                "Instagram Basic Display ürününü ekleyin",
                "Test kullanıcıları ekleyin",
                "Access Token alın",
                "Instagram Business Account ID bulun"
            ],
            "required_fields": ["app_id", "app_secret", "access_token", "instagram_business_account_id"],
            "cost": "Free (200 requests/hour)"
        },
        "youtube": {
            "title": "YouTube API Kurulumu",
            "steps": [
                "https://console.cloud.google.com/ gidin",
                "Yeni proje oluşturun",
                "YouTube Data API v3'ü etkinleştirin",
                "OAuth 2.0 Client ID oluşturun",
                "API Key ve Client bilgilerini alın",
                "OAuth2 playground'da refresh token alın"
            ],
            "required_fields": ["api_key", "client_id", "client_secret", "refresh_token", "channel_id"],
            "cost": "Free (10,000 units/day)"
        },
        "tiktok": {
            "title": "TikTok API Kurulumu",
            "steps": [
                "TikTok Developer hesabı oluşturun",
                "Business account başvurusu yapın",
                "Client Key ve Secret alın",
                "Access token alın",
                "Not: Onay süreci gerektirir"
            ],
            "required_fields": ["client_key", "client_secret", "access_token"],
            "cost": "Requires business approval"
        }
    }
    
    guide = guides.get(platform)
    if not guide:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    return guide
