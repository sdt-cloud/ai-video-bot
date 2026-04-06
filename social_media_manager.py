"""
Sosyal Medya Otomatik Paylaşım Sistemi
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import tweepy
import googleapiclient.discovery
import googleapiclient.errors
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

@dataclass
class SocialPost:
    """Sosyal medya gönderisi için veri yapısı"""
    video_path: str
    title: str
    description: str
    tags: List[str]
    platform: str
    scheduled_time: Optional[datetime] = None
    thumbnail_path: Optional[str] = None

class SocialMediaManager:
    def __init__(self):
        self.config = self.load_config()
        self.setup_apis()
    
    def load_config(self) -> Dict:
        """Sosyal medya API konfigürasyonunu yükler"""
        config_path = "config/social_media_config.json"
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Varsayılan konfigürasyon
        default_config = {
            "youtube": {
                "enabled": False,
                "api_key": os.environ.get("YOUTUBE_API_KEY"),
                "client_secrets_file": "config/youtube_client_secrets.json",
                "token_file": "config/youtube_token.json",
                "category_id": "22",  # People & Blogs
                "privacy_status": "public"
            },
            "twitter": {
                "enabled": False,
                "api_key": os.environ.get("TWITTER_API_KEY"),
                "api_secret": os.environ.get("TWITTER_API_SECRET"),
                "access_token": os.environ.get("TWITTER_ACCESS_TOKEN"),
                "access_token_secret": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET"),
                "bearer_token": os.environ.get("TWITTER_BEARER_TOKEN")
            },
            "tiktok": {
                "enabled": False,
                "session_id": os.environ.get("TIKTOK_SESSION_ID"),
                "username": os.environ.get("TIKTOK_USERNAME")
            },
            "facebook": {
                "enabled": False,
                "page_id": os.environ.get("FACEBOOK_PAGE_ID"),
                "access_token": os.environ.get("FACEBOOK_ACCESS_TOKEN")
            }
        }
        
        # Konfigürasyon dosyasını oluştur
        os.makedirs("config", exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return default_config
    
    def setup_apis(self):
        """API bağlantılarını kurar"""
        self.youtube_api = None
        self.twitter_api = None
        
        # YouTube API
        if self.config["youtube"]["enabled"] and self.config["youtube"]["api_key"]:
            try:
                self.youtube_api = googleapiclient.discovery.build(
                    'youtube', 'v3', 
                    developerKey=self.config["youtube"]["api_key"]
                )
                print("✅ YouTube API bağlantısı kuruldu")
            except Exception as e:
                print(f"❌ YouTube API hatası: {e}")
        
        # Twitter API
        if self.config["twitter"]["enabled"] and all([
            self.config["twitter"]["api_key"],
            self.config["twitter"]["api_secret"],
            self.config["twitter"]["access_token"],
            self.config["twitter"]["access_token_secret"]
        ]):
            try:
                auth = tweepy.OAuthHandler(
                    self.config["twitter"]["api_key"],
                    self.config["twitter"]["api_secret"]
                )
                auth.set_access_token(
                    self.config["twitter"]["access_token"],
                    self.config["twitter"]["access_token_secret"]
                )
                self.twitter_api = tweepy.API(auth)
                print("✅ Twitter API bağlantısı kuruldu")
            except Exception as e:
                print(f"❌ Twitter API hatası: {e}")
    
    def generate_content_for_platform(self, post: SocialPost) -> Dict[str, str]:
        """Platforma özel içerik üretir"""
        base_title = post.title
        base_desc = post.description
        
        content = {
            "youtube": {
                "title": base_title,
                "description": f"{base_desc}\n\n🎬 AI Video Bot ile otomatik üretildi\n\n{', '.join(post.tags)}",
                "tags": post.tags + ["AI", "Otomatik Video", "Teknoloji"]
            },
            "twitter": {
                "text": f"{base_title}\n\n{base_desc[:200]}...\n\n🎬 #AI #Video #Teknoloji {', '.join(['#' + tag for tag in post.tags[:3]])}",
                "media": post.video_path
            },
            "tiktok": {
                "caption": f"{base_title}\n\n{base_desc}\n\n{', '.join(['#' + tag for tag in post.tags[:5]])}",
                "hashtags": post.tags + ["aivideo", "teknoloji", "otomatik"]
            },
            "facebook": {
                "message": f"{base_title}\n\n{base_desc}\n\n🎬 AI Video Bot ile otomatik üretildi\n\n{', '.join(['#' + tag for tag in post.tags])}",
                "link": f"https://youtube.com/watch?v={post.video_path}" if post.video_path else None
            }
        }
        
        return content[post.platform]
    
    def post_to_youtube(self, post: SocialPost) -> Dict:
        """Videoyu YouTube'a yükler"""
        if not self.youtube_api:
            return {"success": False, "error": "YouTube API bağlantısı yok"}
        
        try:
            # YouTube OAuth2 flow (ilk kullanım için)
            if not os.path.exists(self.config["youtube"]["token_file"]):
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config["youtube"]["client_secrets_file"],
                    scopes=['https://www.googleapis.com/auth/youtube.upload']
                )
                credentials = flow.run_local_server(port=0)
                
                with open(self.config["youtube"]["token_file"], 'w') as token:
                    token.write(credentials.to_json())
            
            credentials = Credentials.from_authorized_user_file(
                self.config["youtube"]["token_file"],
                ['https://www.googleapis.com/auth/youtube.upload']
            )
            
            youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)
            
            # Video yükleme
            request_body = {
                'snippet': {
                    'title': post.title,
                    'description': post.description,
                    'categoryId': self.config["youtube"]["category_id"],
                    'tags': post.tags
                },
                'status': {
                    'privacyStatus': self.config["youtube"]["privacy_status"]
                }
            }
            
            media = googleapiclient.http.MediaFileUpload(
                post.video_path,
                chunksize=-1,
                resumable=True
            )
            
            response = youtube.videos().insert(
                part='snippet,status',
                body=request_body,
                media_body=media
            ).execute()
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            return {
                "success": True,
                "video_id": video_id,
                "video_url": video_url,
                "platform": "youtube"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def post_to_twitter(self, post: SocialPost) -> Dict:
        """Gönderiyi Twitter'a yükler"""
        if not self.twitter_api:
            return {"success": False, "error": "Twitter API bağlantısı yok"}
        
        try:
            content = self.generate_content_for_platform(post)
            
            # Video yükleme (Twitter API v2)
            if post.video_path:
                media = self.twitter_api.media_upload(post.video_path)
                tweet = self.twitter_api.update_status(
                    status=content["text"],
                    media_ids=[media.media_id]
                )
            else:
                tweet = self.twitter_api.update_status(status=content["text"])
            
            return {
                "success": True,
                "tweet_id": tweet.id_str,
                "tweet_url": f"https://twitter.com/user/status/{tweet.id_str}",
                "platform": "twitter"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def post_to_tiktok(self, post: SocialPost) -> Dict:
        """Videoyu TikTok'a yükler (simülasyon)"""
        # Not: TikTok API'si resmi olarak açık değil
        # Bu fonksiyon simülasyon veya üçüncü parti API için
        
        try:
            content = self.generate_content_for_platform(post)
            
            # Simülasyon - gerçek TikTok API'si gerektirir
            print(f"🎬 TikTok simülasyon: {content['caption']}")
            
            return {
                "success": True,
                "message": "TikTok API'si simülasyon modunda",
                "platform": "tiktok",
                "caption": content["caption"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def post_to_facebook(self, post: SocialPost) -> Dict:
        """Gönderiyi Facebook'a yükler"""
        if not self.config["facebook"]["enabled"]:
            return {"success": False, "error": "Facebook API bağlantısı yok"}
        
        try:
            content = self.generate_content_for_platform(post)
            
            # Facebook Graph API
            url = f"https://graph.facebook.com/v18.0/{self.config['facebook']['page_id']}/videos"
            
            params = {
                'access_token': self.config["facebook"]["access_token"],
                'description': content["message"]
            }
            
            files = {}
            if post.video_path:
                files['source'] = open(post.video_path, 'rb')
            
            response = requests.post(url, params=params, files=files)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "post_id": result.get("id"),
                    "platform": "facebook"
                }
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def post_to_all_platforms(self, post: SocialPost) -> List[Dict]:
        """Tüm platformlara gönderir"""
        results = []
        
        platforms = {
            "youtube": self.post_to_youtube,
            "twitter": self.post_to_twitter,
            "tiktok": self.post_to_tiktok,
            "facebook": self.post_to_facebook
        }
        
        for platform, post_func in platforms.items():
            if self.config[platform]["enabled"]:
                print(f"🚀 {platform.upper()} platformuna gönderiliyor...")
                result = post_func(post)
                results.append(result)
                
                if result["success"]:
                    print(f"✅ {platform.upper()} başarılı: {result.get('video_url', result.get('tweet_url', 'Başarılı'))}")
                else:
                    print(f"❌ {platform.upper()} hata: {result.get('error')}")
            else:
                print(f"⏭️ {platform.upper()} atlandı (devre dışı)")
        
        return results

# Global instance
social_manager = SocialMediaManager()
