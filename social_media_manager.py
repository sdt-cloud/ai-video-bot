import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db

class SocialMediaManager:
    def __init__(self):
        self.api_configs = self.load_api_configs()
        
    def load_api_configs(self):
        """API konfigürasyonlarını yükler"""
        config_file = "social_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "ayrshare": {"api_key": "", "enabled": False},
            "outstand": {"api_key": "", "enabled": False},
            "postforme": {"api_key": "", "enabled": False}
        }
    
    def save_api_configs(self):
        """API konfigürasyonlarını kaydeder"""
        with open("social_config.json", 'w', encoding='utf-8') as f:
            json.dump(self.api_configs, f, indent=2, ensure_ascii=False)
    
    def post_to_ayrshare(self, content: str, platforms: List[str], media_path: str = None, schedule_time: str = None) -> Dict:
        """Ayrshare API üzerinden gönderi yapar"""
        if not self.api_configs["ayrshare"]["enabled"] or not self.api_configs["ayrshare"]["api_key"]:
            return {"error": "Ayrshare API yapılandırılmamış"}
        
        url = "https://api.ayrshare.com/api/post"
        headers = {
            "Authorization": f"Bearer {self.api_configs['ayrshare']['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "post": content,
            "platforms": platforms
        }
        
        if media_path:
            # Önce medya yükle
            media_upload_url = "https://api.ayrshare.com/api/media/upload"
            with open(media_path, 'rb') as f:
                files = {'file': f}
                upload_response = requests.post(media_upload_url, headers=headers, files=files)
                if upload_response.status_code == 200:
                    media_url = upload_response.json().get('url')
                    payload["mediaUrls"] = [media_url]
        
        if schedule_time:
            payload["scheduleDate"] = schedule_time
        
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    
    def post_to_outstand(self, content: str, platforms: List[str], media_path: str = None, schedule_time: str = None) -> Dict:
        """Outstand API üzerinden gönderi yapar"""
        if not self.api_configs["outstand"]["enabled"] or not self.api_configs["outstand"]["api_key"]:
            return {"error": "Outstand API yapılandırılmamış"}
        
        url = "https://api.outstand.so/v1/posts"
        headers = {
            "Authorization": f"Bearer {self.api_configs['outstand']['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": content,
            "platforms": platforms
        }
        
        if media_path:
            # Medya yükleme işlemi
            media_upload_url = "https://api.outstand.so/v1/media"
            with open(media_path, 'rb') as f:
                files = {'file': f}
                upload_response = requests.post(media_upload_url, headers=headers, files=files)
                if upload_response.status_code == 200:
                    media_id = upload_response.json().get('id')
                    payload["media"] = [media_id]
        
        if schedule_time:
            payload["schedule_at"] = schedule_time
        
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    
    def post_to_postforme(self, content: str, platforms: List[str], media_path: str = None, schedule_time: str = None) -> Dict:
        """PostForMe API üzerinden gönderi yapar"""
        if not self.api_configs["postforme"]["enabled"] or not self.api_configs["postforme"]["api_key"]:
            return {"error": "PostForMe API yapılandırılmamış"}
        
        url = "https://api.postforme.dev/v1/posts"
        headers = {
            "Authorization": f"Bearer {self.api_configs['postforme']['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": content,
            "platforms": platforms
        }
        
        if media_path:
            # Medya yükleme işlemi
            media_upload_url = "https://api.postforme.dev/v1/media"
            with open(media_path, 'rb') as f:
                files = {'file': f}
                upload_response = requests.post(media_upload_url, headers=headers, files=files)
                if upload_response.status_code == 200:
                    media_url = upload_response.json().get('url')
                    payload["media"] = [media_url]
        
        if schedule_time:
            payload["schedule_at"] = schedule_time
        
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    
    def post_video_to_social_media(self, video_id: int, platforms: List[str], content: str = None, schedule_time: str = None, provider: str = "ayrshare") -> Dict:
        """Videoyu belirtilen sosyal medya platformlarına gönderir"""
        
        # Video bilgilerini veritabanından al
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
        
        # Platform adlarını dönüştür
        platform_mapping = {
            "youtube": "youtube",
            "twitter": "x", 
            "instagram": "instagram",
            "tiktok": "tiktok",
            "facebook": "facebook"
        }
        
        mapped_platforms = [platform_mapping.get(p.lower(), p.lower()) for p in platforms]
        
        # Seçilen provider üzerinden gönder
        if provider == "ayrshare":
            result = self.post_to_ayrshare(content, mapped_platforms, video_path, schedule_time)
        elif provider == "outstand":
            result = self.post_to_outstand(content, mapped_platforms, video_path, schedule_time)
        elif provider == "postforme":
            result = self.post_to_postforme(content, mapped_platforms, video_path, schedule_time)
        else:
            return {"error": "Geçersiz provider"}
        
        # Sonucu veritabanına kaydet
        if "error" not in result:
            self.save_post_result(video_id, platforms, content, result, provider)
        
        return result
    
    def save_post_result(self, video_id: int, platforms: List[str], content: str, result: Dict, provider: str):
        """Gönderi sonucunu veritabanına kaydeder"""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Sosyal medya gönderileri tablosu oluştur
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER,
                    platforms TEXT,
                    content TEXT,
                    provider TEXT,
                    result TEXT,
                    status TEXT DEFAULT 'posted',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (id)
                )
            """)
            
            cursor.execute("""
                INSERT INTO social_posts (video_id, platforms, content, provider, result)
                VALUES (?, ?, ?, ?, ?)
            """, (video_id, json.dumps(platforms), content, provider, json.dumps(result)))
    
    def get_post_history(self, limit: int = 50) -> List[Dict]:
        """Sosyal medya gönderi geçmişini alır"""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sp.*, v.topic, v.video_path 
                FROM social_posts sp
                JOIN videos v ON sp.video_id = v.id
                ORDER BY sp.created_at DESC
                LIMIT ?
            """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                result["platforms"] = json.loads(result["platforms"])
                result["result"] = json.loads(result["result"])
                results.append(result)
            
            return results
    
    def configure_api(self, provider: str, api_key: str, enabled: bool = True):
        """API yapılandırmasını günceller"""
        if provider in self.api_configs:
            self.api_configs[provider]["api_key"] = api_key
            self.api_configs[provider]["enabled"] = enabled
            self.save_api_configs()
            return True
        return False
    
    def get_platform_list(self) -> Dict[str, List[str]]:
        """Desteklenen platformları döndürür"""
        return {
            "ayrshare": ["facebook", "x", "instagram", "linkedin", "tiktok", "youtube", "threads", "pinterest"],
            "outstand": ["x", "linkedin", "instagram", "facebook", "threads", "tiktok", "youtube", "bluesky", "pinterest"],
            "postforme": ["tiktok", "instagram", "youtube", "facebook", "x"]
        }

# Örnek kullanım
if __name__ == "__main__":
    manager = SocialMediaManager()
    
    # API anahtarını yapılandır (örnek)
    # manager.configure_api("ayrshare", "your_api_key_here", True)
    
    # Videoyu sosyal medyada paylaş
    # result = manager.post_video_to_social_media(
    #     video_id=1,
    #     platforms=["instagram", "tiktok", "youtube"],
    #     content="Yeni AI videom yayında! 🚀",
    #     provider="ayrshare"
    # )
    # print(result)
