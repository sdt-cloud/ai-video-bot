"""
Sosyal Medya Otomatik Paylaşım Sistemi
"""

import os
import json
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

@dataclass
class SocialPost:
    """Sosyal medya gönderisi verisi"""
    video_path: str
    title: str
    description: str
    tags: List[str]
    platform: str
    scheduled_time: Optional[datetime] = None
    status: str = "pending"  # pending, posted, failed

class SocialMediaManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self.load_config()
        self.posts = []
        
    def load_config(self):
        """Sosyal medya API konfigürasyonlarını yükler"""
        config_file = "social_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # Varsayılan konfigürasyon
        default_config = {
            "youtube": {
                "enabled": False,
                "api_key": "",
                "channel_id": "",
                "client_secrets_file": ""
            },
            "twitter": {
                "enabled": False,
                "api_key": "",
                "api_secret": "",
                "access_token": "",
                "access_token_secret": ""
            },
            "tiktok": {
                "enabled": False,
                "username": "",
                "session_id": ""
            },
            "facebook": {
                "enabled": False,
                "page_id": "",
                "access_token": ""
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        return default_config
    
    def generate_content(self, topic: str, video_description: str) -> Dict[str, str]:
        """Platformlara özel içerik üretir"""
        
        # Etiketler
        tags = self.generate_tags(topic)
        
        # YouTube için
        youtube_title = f"🎬 {topic} - Nedir? Nasıl Çalışır? | [2026]"
        youtube_description = f"""
{video_description}

📚 Konu hakkında daha fazla bilgi için nedir.me adresini ziyaret edin!

🔔 Abone olmayı unutmayın!
👍 Beğen ve paylaş!

{tags}
"""
        
        # Twitter için
        twitter_text = f"""
🎬 {topic} hakkında yeni video!

📹 Detaylı anlatım ve görsellerle hazırladığımız videomuzda {topic} konusunu tüm yönleriyle ele aldık.

{video_description[:200]}...

#nedir #nasılçalışır #{tags.replace('#', ' #')}
"""
        
        # TikTok için
        tiktok_text = f"""
{topic} nedir? 🤔

Kısa ve öz anlatım! 📹

{video_description[:150]}

{tags}
"""
        
        # Facebook için
        facebook_text = f"""
🎬 Yeni Video: {topic}

{video_description}

📚 Konu hakkında daha fazla bilgi için nedir.me adresini ziyaret edin!

{tags}
"""
        
        return {
            "youtube": {
                "title": youtube_title,
                "description": youtube_description,
                "tags": tags
            },
            "twitter": {
                "text": twitter_text
            },
            "tiktok": {
                "text": tiktok_text
            },
            "facebook": {
                "text": facebook_text
            }
        }
    
    def generate_tags(self, topic: str) -> str:
        """Konuya göre etiketler üretir"""
        base_tags = ["nedir", "nasılçalışır", "bilgi", "eğitim", "2026"]
        
        # Konu spesifik etiketler
        topic_lower = topic.lower()
        if "yazılım" in topic_lower or "program" in topic_lower:
            base_tags.extend(["yazılım", "programlama", "teknoloji"])
        elif "bilgisayar" in topic_lower:
            base_tags.extend(["bilgisayar", "teknoloji", "donanım"])
        elif "internet" in topic_lower:
            base_tags.extend(["internet", "ağ", "web"])
        elif "tarih" in topic_lower:
            base_tags.extend(["tarih", "geçmiş", "kultur"])
        
        # Konu kelimesini de ekle
        topic_words = topic.split()
        base_tags.extend([word for word in topic_words if len(word) > 3])
        
        # Hashtag formatına çevir
        hashtags = ["#" + tag.replace(" ", "").replace("ç", "c").replace("ğ", "g").replace("ı", "i").replace("ö", "o").replace("ş", "s").replace("ü", "u") for tag in base_tags]
        
        return " ".join(hashtags[:15])  # Maksimum 15 etiket
    
    async def post_to_youtube(self, post: SocialPost) -> bool:
        """YouTube'a video yükler"""
        try:
            # YouTube API entegrasyonu
            # Google API Client Library kullanılacak
            self.logger.info(f"YouTube'a yükleniyor: {post.title}")
            
            # TODO: YouTube API implementasyonu
            # from googleapiclient.discovery import build
            # from googleapiclient.http import MediaFileUpload
            
            return True
            
        except Exception as e:
            self.logger.error(f"YouTube yükleme hatası: {e}")
            return False
    
    async def post_to_twitter(self, post: SocialPost) -> bool:
        """Twitter'a gönderi atar"""
        try:
            # Twitter API entegrasyonu
            # tweepy kütüphanesi kullanılacak
            self.logger.info(f"Twitter'a gönderiliyor: {post.title[:50]}...")
            
            # TODO: Twitter API implementasyonu
            # import tweepy
            
            return True
            
        except Exception as e:
            self.logger.error(f"Twitter gönderme hatası: {e}")
            return False
    
    async def post_to_tiktok(self, post: SocialPost) -> bool:
        """TikTok'a video yükler"""
        try:
            # TikTok API entegrasyonu
            # Resmi olmayan API veya otomasyon araçları
            self.logger.info(f"TikTok'a yükleniyor: {post.title[:50]}...")
            
            # TODO: TikTok implementasyonu
            # TikTokUploader gibi kütüphaneler
            
            return True
            
        except Exception as e:
            self.logger.error(f"TikTok yükleme hatası: {e}")
            return False
    
    async def post_to_facebook(self, post: SocialPost) -> bool:
        """Facebook'a gönderi atar"""
        try:
            # Facebook Graph API entegrasyonu
            self.logger.info(f"Facebook'a gönderiliyor: {post.title[:50]}...")
            
            # TODO: Facebook API implementasyonu
            # facebook-sdk kullanılacak
            
            return True
            
        except Exception as e:
            self.logger.error(f"Facebook gönderme hatası: {e}")
            return False
    
    async def post_to_platforms(self, post: SocialPost, platforms: List[str]) -> Dict[str, bool]:
        """Seçili platformlara gönderi atar"""
        results = {}
        
        if "youtube" in platforms and self.config["youtube"]["enabled"]:
            results["youtube"] = await self.post_to_youtube(post)
        
        if "twitter" in platforms and self.config["twitter"]["enabled"]:
            results["twitter"] = await self.post_to_twitter(post)
        
        if "tiktok" in platforms and self.config["tiktok"]["enabled"]:
            results["tiktok"] = await self.post_to_tiktok(post)
        
        if "facebook" in platforms and self.config["facebook"]["enabled"]:
            results["facebook"] = await self.post_to_facebook(post)
        
        return results
    
    def schedule_post(self, video_path: str, topic: str, description: str, 
                    platforms: List[str], scheduled_time: datetime = None):
        """Gönderi zamanlar"""
        
        # Platformlara özel içerik üret
        content = self.generate_content(topic, description)
        
        # Gönderi nesneleri oluştur
        posts = []
        for platform in platforms:
            if platform == "youtube":
                post = SocialPost(
                    video_path=video_path,
                    title=content["youtube"]["title"],
                    description=content["youtube"]["description"],
                    tags=content["youtube"]["tags"],
                    platform=platform,
                    scheduled_time=scheduled_time
                )
            else:
                post = SocialPost(
                    video_path=video_path,
                    title=topic,
                    description=content[platform]["text"],
                    tags=[],
                    platform=platform,
                    scheduled_time=scheduled_time
                )
            posts.append(post)
        
        self.posts.extend(posts)
        
        # Zamanlanmış görev oluştur
        if scheduled_time:
            asyncio.create_task(self.scheduled_poster(posts))
        else:
            asyncio.create_task(self.post_to_platforms(posts[0], platforms))
    
    async def scheduled_poster(self, posts: List[SocialPost]):
        """Zamanlanmış gönderileri yayınlar"""
        now = datetime.now()
        
        for post in posts:
            if post.scheduled_time and post.scheduled_time > now:
                wait_time = (post.scheduled_time - now).total_seconds()
                await asyncio.sleep(wait_time)
            
            platforms = [post.platform]
            await self.post_to_platforms(post, platforms)
    
    def get_post_status(self) -> List[Dict]:
        """Gönderi durumlarını döndürür"""
        return [
            {
                "title": post.title,
                "platform": post.platform,
                "status": post.status,
                "scheduled_time": post.scheduled_time.isoformat() if post.scheduled_time else None
            }
            for post in self.posts
        ]

# Global instance
social_manager = SocialMediaManager()
