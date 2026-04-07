import requests
import json
import os
import base64
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db

class CustomSocialMediaManager:
    def __init__(self):
        self.api_configs = self.load_api_configs()
        
    def load_api_configs(self):
        """API konfigürasyonlarını yükler"""
        config_file = "custom_social_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        default_config = {
            "facebook": {
                "app_id": "",
                "app_secret": "",
                "access_token": "",
                "page_id": "",
                "enabled": False
            },
            "twitter": {
                "api_key": "",
                "api_secret": "",
                "access_token": "",
                "access_token_secret": "",
                "bearer_token": "",
                "enabled": False
            },
            "instagram": {
                "app_id": "",
                "app_secret": "",
                "access_token": "",
                "instagram_business_account_id": "",
                "enabled": False
            },
            "tiktok": {
                "client_key": "",
                "client_secret": "",
                "access_token": "",
                "enabled": False
            },
            "youtube": {
                "api_key": "",
                "client_id": "",
                "client_secret": "",
                "refresh_token": "",
                "channel_id": "",
                "enabled": False
            }
        }
        
        # Varsayılan konfigürasyonu kaydet
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return default_config
    
    def save_api_configs(self):
        """API konfigürasyonlarını kaydeder"""
        with open("custom_social_config.json", 'w', encoding='utf-8') as f:
            json.dump(self.api_configs, f, indent=2, ensure_ascii=False)
    
    # FACEBOOK INTEGRATION
    async def post_to_facebook(self, content: str, video_path: str = None, image_path: str = None) -> Dict:
        """Facebook'a gönderi yapar (Free Tier - 200 requests/hour)"""
        if not self.api_configs["facebook"]["enabled"]:
            return {"error": "Facebook API yapılandırılmamış"}
        
        try:
            access_token = self.api_configs["facebook"]["access_token"]
            page_id = self.api_configs["facebook"]["page_id"]
            
            # Base post data
            post_data = {
                "message": content,
                "access_token": access_token
            }
            
            # Video upload
            if video_path and os.path.exists(video_path):
                url = f"https://graph.facebook.com/v18.0/{page_id}/videos"
                
                with open(video_path, 'rb') as video_file:
                    files = {
                        'source': video_file,
                        'description': (None, content),
                        'access_token': (None, access_token)
                    }
                    response = requests.post(url, files=files, timeout=60)
                    
            # Image upload  
            elif image_path and os.path.exists(image_path):
                url = f"https://graph.facebook.com/v18.0/{page_id}/photos"
                
                with open(image_path, 'rb') as image_file:
                    files = {
                        'source': image_file,
                        'caption': (None, content),
                        'access_token': (None, access_token)
                    }
                    response = requests.post(url, files=files, timeout=30)
                    
            # Text only post
            else:
                url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
                response = requests.post(url, data=post_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "post_id": result.get("id"),
                    "platform": "facebook",
                    "url": f"https://facebook.com/{result.get('id')}"
                }
            else:
                return {"error": f"Facebook API Error: {response.text}"}
                
        except Exception as e:
            return {"error": f"Facebook posting error: {str(e)}"}
    
    # TWITTER/X INTEGRATION
    async def post_to_twitter(self, content: str, media_path: str = None) -> Dict:
        """Twitter/X'e gönderi yapar (Free Tier - 500,000 tweets/month)"""
        if not self.api_configs["twitter"]["enabled"]:
            return {"error": "Twitter API yapılandırılmamış"}
        
        try:
            bearer_token = self.api_configs["twitter"]["bearer_token"]
            
            # Media upload first if needed
            media_id = None
            if media_path and os.path.exists(media_path):
                # Initialize upload
                init_url = "https://upload.twitter.com/1.1/media/upload.json"
                init_data = {
                    "command": "INIT",
                    "media_type": "video/mp4" if media_path.endswith('.mp4') else "image/jpeg",
                    "total_bytes": os.path.getsize(media_path)
                }
                
                auth = self._get_twitter_auth()
                init_response = requests.post(init_url, data=init_data, auth=auth, timeout=30)
                
                if init_response.status_code == 200:
                    media_id = init_response.json().get("media_id_string")
                    
                    # Append media
                    append_url = "https://upload.twitter.com/1.1/media/upload.json"
                    with open(media_path, 'rb') as media_file:
                        append_data = {
                            "command": "APPEND",
                            "media_id": media_id,
                            "segment_index": 0
                        }
                        files = {"media": media_file}
                        append_response = requests.post(append_url, data=append_data, files=files, auth=auth, timeout=60)
                    
                    # Finalize upload
                    finalize_url = "https://upload.twitter.com/1.1/media/upload.json"
                    finalize_data = {
                        "command": "FINALIZE",
                        "media_id": media_id
                    }
                    requests.post(finalize_url, data=finalize_data, auth=auth, timeout=30)
            
            # Create tweet
            tweet_url = "https://api.twitter.com/2/tweets"
            headers = {
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json"
            }
            
            tweet_data = {"text": content}
            if media_id:
                tweet_data["media"] = {"media_ids": [media_id]}
            
            response = requests.post(tweet_url, headers=headers, json=tweet_data, timeout=30)
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "post_id": result["data"]["id"],
                    "platform": "twitter",
                    "url": f"https://twitter.com/user/status/{result['data']['id']}"
                }
            else:
                return {"error": f"Twitter API Error: {response.text}"}
                
        except Exception as e:
            return {"error": f"Twitter posting error: {str(e)}"}
    
    def _get_twitter_auth(self):
        """Twitter OAuth 1.0 authentication için"""
        import oauthlib.oauth1
        from requests_oauthlib import OAuth1
        
        return OAuth1(
            self.api_configs["twitter"]["api_key"],
            client_secret=self.api_configs["twitter"]["api_secret"],
            resource_owner_key=self.api_configs["twitter"]["access_token"],
            resource_owner_secret=self.api_configs["twitter"]["access_token_secret"]
        )
    
    # INSTAGRAM INTEGRATION
    async def post_to_instagram(self, content: str, media_path: str) -> Dict:
        """Instagram'a gönderi yapar (Free Tier - 200 requests/hour)"""
        if not self.api_configs["instagram"]["enabled"]:
            return {"error": "Instagram API yapılandırılmamış"}
        
        if not media_path or not os.path.exists(media_path):
            return {"error": "Instagram için medya dosyası gereklidir"}
        
        try:
            access_token = self.api_configs["instagram"]["access_token"]
            ig_account_id = self.api_configs["instagram"]["instagram_business_account_id"]
            
            # Step 1: Create media object
            create_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media"
            
            media_type = "VIDEO" if media_path.endswith('.mp4') else "IMAGE"
            
            if media_type == "VIDEO":
                # Upload video first
                upload_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media"
                with open(media_path, 'rb') as video_file:
                    files = {
                        'source': video_file,
                        'media_type': (None, 'VIDEO'),
                        'caption': (None, content),
                        'access_token': (None, access_token)
                    }
                    upload_response = requests.post(upload_url, files=files, timeout=120)
                    
                if upload_response.status_code == 200:
                    media_id = upload_response.json().get("id")
                else:
                    return {"error": f"Instagram upload error: {upload_response.text}"}
            else:
                # Image post
                with open(media_path, 'rb') as image_file:
                    files = {
                        'source': image_file,
                        'caption': (None, content),
                        'access_token': (None, access_token)
                    }
                    create_response = requests.post(create_url, files=files, timeout=60)
                    
                if create_response.status_code == 200:
                    media_id = create_response.json().get("id")
                else:
                    return {"error": f"Instagram media creation error: {create_response.text}"}
            
            # Step 2: Publish media
            publish_url = f"https://graph.facebook.com/v18.0/{ig_account_id}/media_publish"
            publish_data = {
                "creation_id": media_id,
                "access_token": access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_data, timeout=30)
            
            if publish_response.status_code == 200:
                result = publish_response.json()
                return {
                    "success": True,
                    "post_id": result.get("id"),
                    "platform": "instagram",
                    "url": f"https://instagram.com/p/{result.get('id')}"
                }
            else:
                return {"error": f"Instagram publish error: {publish_response.text}"}
                
        except Exception as e:
            return {"error": f"Instagram posting error: {str(e)}"}
    
    # YOUTUBE INTEGRATION
    async def post_to_youtube(self, title: str, description: str, video_path: str, tags: List[str] = None) -> Dict:
        """YouTube'a video yükler (Free Tier - 10,000 units/day)"""
        if not self.api_configs["youtube"]["enabled"]:
            return {"error": "YouTube API yapılandırılmamış"}
        
        if not video_path or not os.path.exists(video_path):
            return {"error": "Video dosyası bulunamadı"}
        
        try:
            # OAuth2 access token al
            access_token = self._get_youtube_access_token()
            if not access_token:
                return {"error": "YouTube access token alınamadı"}
            
            # Video metadata
            metadata = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": "22"  # People & Blogs
                },
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": False
                }
            }
            
            # Upload video
            upload_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Initiate resumable upload
            init_response = requests.post(upload_url, headers=headers, json=metadata, timeout=30)
            
            if init_response.status_code == 200:
                upload_url = init_response.headers.get("Location")
                
                # Upload actual video file
                with open(video_path, 'rb') as video_file:
                    upload_response = requests.post(upload_url, data=video_file, timeout=600)
                
                if upload_response.status_code == 200:
                    result = upload_response.json()
                    return {
                        "success": True,
                        "video_id": result["id"],
                        "platform": "youtube",
                        "url": f"https://youtube.com/watch?v={result['id']}"
                    }
                else:
                    return {"error": f"YouTube upload error: {upload_response.text}"}
            else:
                return {"error": f"YouTube init error: {init_response.text}"}
                
        except Exception as e:
            return {"error": f"YouTube posting error: {str(e)}"}
    
    def _get_youtube_access_token(self):
        """YouTube OAuth2 access token al"""
        try:
            refresh_token = self.api_configs["youtube"]["refresh_token"]
            client_id = self.api_configs["youtube"]["client_id"]
            client_secret = self.api_configs["youtube"]["client_secret"]
            
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret
            }
            
            response = requests.post(token_url, data=data, timeout=30)
            
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                return None
                
        except Exception:
            return None
    
    # TIKTOK INTEGRATION (Basic)
    async def post_to_tiktok(self, content: str, video_path: str) -> Dict:
        """TikTok'a video yükler (Limited access - approval required)"""
        if not self.api_configs["tiktok"]["enabled"]:
            return {"error": "TikTok API yapılandırılmamış"}
        
        # Not: TikTok API'si kısıtlı erişime sahip, onay gerektirir
        return {
            "error": "TikTok API currently requires business approval. Please use TikTok's Creative Center API or manual upload.",
            "info": "TikTok integration requires business account approval. Consider manual upload or alternative solutions."
        }
    
    # UNIFIED POSTING FUNCTION
    async def post_video_to_platforms(self, video_id: int, platforms: List[str], content: str = None, schedule_time: str = None) -> Dict:
        """Videoyu belirtilen platformlara gönderir"""
        
        # Video bilgilerini al
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
            video = cursor.fetchone()
            
        if not video:
            return {"error": "Video bulunamadı"}
        
        video = dict(video)
        video_path = video.get("video_path")
        
        if not video_path or not os.path.exists(video_path):
            return {"error": "Video dosyası bulunamadı"}
        
        # İçerik oluştur
        if not content:
            content = f"🎬 {video['topic']}\n\n#AI #Video #{video.get('category', 'technology').replace(' ', '')}"
        
        results = {}
        
        # Platformlara göre gönder
        for platform in platforms:
            try:
                if platform.lower() == "facebook":
                    result = await self.post_to_facebook(content, video_path)
                elif platform.lower() == "twitter":
                    result = await self.post_to_twitter(content, video_path)
                elif platform.lower() == "instagram":
                    result = await self.post_to_instagram(content, video_path)
                elif platform.lower() == "youtube":
                    result = await self.post_to_youtube(
                        title=video['topic'],
                        description=content,
                        video_path=video_path
                    )
                elif platform.lower() == "tiktok":
                    result = await self.post_to_tiktok(content, video_path)
                else:
                    result = {"error": f"Desteklenmeyen platform: {platform}"}
                
                results[platform] = result
                
            except Exception as e:
                results[platform] = {"error": f"{platform} hatası: {str(e)}"}
        
        # Sonuçları kaydet
        self.save_post_results(video_id, platforms, content, results)
        
        return {"results": results}
    
    def save_post_results(self, video_id: int, platforms: List[str], content: str, results: Dict):
        """Gönderi sonuçlarını veritabanına kaydeder"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Tablo oluştur
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
                INSERT INTO custom_social_posts (video_id, platforms, content, results)
                VALUES (?, ?, ?, ?)
            """, (video_id, json.dumps(platforms), content, json.dumps(results)))
    
    def get_platform_status(self) -> Dict:
        """Platformların yapılandırma durumunu döndürür"""
        return {
            "facebook": {
                "enabled": self.api_configs["facebook"]["enabled"],
                "cost": "Free (200 requests/hour)",
                "requirements": ["App ID", "App Secret", "Access Token", "Page ID"]
            },
            "twitter": {
                "enabled": self.api_configs["twitter"]["enabled"],
                "cost": "Free (500,000 tweets/month)",
                "requirements": ["API Key", "API Secret", "Access Token", "Access Token Secret", "Bearer Token"]
            },
            "instagram": {
                "enabled": self.api_configs["instagram"]["enabled"],
                "cost": "Free (200 requests/hour)",
                "requirements": ["App ID", "App Secret", "Access Token", "Instagram Business Account ID"]
            },
            "youtube": {
                "enabled": self.api_configs["youtube"]["enabled"],
                "cost": "Free (10,000 units/day)",
                "requirements": ["API Key", "Client ID", "Client Secret", "Refresh Token", "Channel ID"]
            },
            "tiktok": {
                "enabled": self.api_configs["tiktok"]["enabled"],
                "cost": "Requires business approval",
                "requirements": ["Client Key", "Client Secret", "Access Token (Business)"]
            }
        }
    
    def configure_platform(self, platform: str, config: Dict) -> bool:
        """Platform yapılandırmasını günceller"""
        if platform in self.api_configs:
            self.api_configs[platform].update(config)
            self.save_api_configs()
            return True
        return False

# Örnek kullanım
if __name__ == "__main__":
    manager = CustomSocialMediaManager()
    
    # Platform durumunu kontrol et
    status = manager.get_platform_status()
    print("Platform Durumları:")
    for platform, info in status.items():
        print(f"- {platform}: {'✅ Aktif' if info['enabled'] else '❌ Pasif'} ({info['cost']})")
