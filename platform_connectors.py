"""
Sosyal Medya Platform Bağlantıları
"""

import os
import json
import tweepy
import requests
from typing import Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

class YouTubeConnector:
    def __init__(self, config: Dict):
        self.config = config
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload']
        self.client_secrets_file = config.get('client_secrets_file', 'client_secrets.json')
        self.credentials_file = 'youtube_credentials.pickle'
        
    def is_connected(self) -> bool:
        """YouTube'a bağlanmış mı kontrol et"""
        return os.path.exists(self.credentials_file)
    
    def connect(self) -> bool:
        """YouTube'a bağlan"""
        try:
            credentials = None
            
            # Mevcut credentials'ı yükle
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'rb') as token:
                    credentials = pickle.load(token)
            
            # Credentials yoksa veya geçersizse yeni al
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    if os.path.exists(self.client_secrets_file):
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.client_secrets_file, self.scopes)
                        credentials = flow.run_local_server(port=0)
                    else:
                        return False
                
                # Credentials'ı kaydet
                with open(self.credentials_file, 'wb') as token:
                    pickle.dump(credentials, token)
            
            self.credentials = credentials
            return True
            
        except Exception as e:
            print(f"YouTube bağlantı hatası: {e}")
            return False
    
    def upload_video(self, video_path: str, title: str, description: str, tags: str) -> bool:
        """Videoyu YouTube'a yükle"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            youtube = build('youtube', 'v3', credentials=self.credentials)
            
            # Video meta verileri
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags.split(),
                    'categoryId': '22'  # Education
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Videoyu yükle
            media = MediaFileUpload(video_path, resumable=True)
            request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = request.execute()
            return True
            
        except Exception as e:
            print(f"YouTube yükleme hatası: {e}")
            return False

class TwitterConnector:
    def __init__(self, config: Dict):
        self.config = config
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.access_token = config.get('access_token', '')
        self.access_token_secret = config.get('access_token_secret', '')
        
    def is_connected(self) -> bool:
        """Twitter'a bağlanmış mı kontrol et"""
        return all([self.api_key, self.api_secret, self.access_token, self.access_token_secret])
    
    def connect(self) -> bool:
        """Twitter'a bağlan"""
        try:
            if not self.is_connected():
                return False
            
            client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret
            )
            
            self.client = client
            return True
            
        except Exception as e:
            print(f"Twitter bağlantı hatası: {e}")
            return False
    
    def post_tweet(self, text: str, media_path: Optional[str] = None) -> bool:
        """Tweet at"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            # Media varsa önce yükle
            media_ids = []
            if media_path and os.path.exists(media_path):
                media = self.client.media_upload(media_path)
                media_ids.append(media.media_id)
            
            # Tweet at
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids if media_ids else None
            )
            
            return True
            
        except Exception as e:
            print(f"Twitter gönderme hatası: {e}")
            return False

class FacebookConnector:
    def __init__(self, config: Dict):
        self.config = config
        self.page_id = config.get('page_id', '')
        self.access_token = config.get('access_token', '')
        
    def is_connected(self) -> bool:
        """Facebook'a bağlanmış mı kontrol et"""
        return all([self.page_id, self.access_token])
    
    def connect(self) -> bool:
        """Facebook'a bağlan"""
        try:
            if not self.is_connected():
                return False
            
            # Test isteği
            url = f"https://graph.facebook.com/{self.page_id}"
            params = {'access_token': self.access_token}
            response = requests.get(url, params=params)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Facebook bağlantı hatası: {e}")
            return False
    
    def post_to_page(self, message: str, media_path: Optional[str] = None) -> bool:
        """Sayfaya gönderi at"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            url = f"https://graph.facebook.com/{self.page_id}/feed"
            params = {'access_token': self.access_token}
            
            data = {'message': message}
            
            # Media varsa
            if media_path and os.path.exists(media_path):
                # Önce videoyu yükle
                upload_url = f"https://graph.facebook.com/{self.page_id}/videos"
                upload_params = {'access_token': self.access_token}
                
                with open(media_path, 'rb') as video_file:
                    files = {'source': video_file}
                    upload_response = requests.post(upload_url, params=upload_params, files=files)
                    
                    if upload_response.status_code == 200:
                        video_id = upload_response.json().get('id')
                        data['attached_media'] = [{'media_fbid': video_id}]
            
            response = requests.post(url, params=params, data=data)
            return response.status_code == 200
            
        except Exception as e:
            print(f"Facebook gönderme hatası: {e}")
            return False

class TikTokConnector:
    def __init__(self, config: Dict):
        self.config = config
        self.username = config.get('username', '')
        self.session_id = config.get('session_id', '')
        
    def is_connected(self) -> bool:
        """TikTok'a bağlanmış mı kontrol et"""
        return all([self.username, self.session_id])
    
    def connect(self) -> bool:
        """TikTok'a bağlan"""
        try:
            if not self.is_connected():
                return False
            
            # TODO: TikTok API implementasyonu
            # Şimdilik true döndür
            return True
            
        except Exception as e:
            print(f"TikTok bağlantı hatası: {e}")
            return False
    
    def upload_video(self, video_path: str, caption: str, hashtags: str) -> bool:
        """Videoyu TikTok'a yükle"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            # TODO: TikTok upload implementasyonu
            # Üçüncü parti kütüphane veya API kullanılacak
            print(f"TikTok'a yüklenecek: {video_path}")
            return True
            
        except Exception as e:
            print(f"TikTok yükleme hatası: {e}")
            return False

class PlatformManager:
    def __init__(self):
        self.youtube = None
        self.twitter = None
        self.facebook = None
        self.tiktok = None
        self.load_config()
    
    def load_config(self):
        """Konfigürasyonu yükle"""
        if os.path.exists('social_config.json'):
            with open('social_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                if config.get('youtube', {}).get('enabled'):
                    self.youtube = YouTubeConnector(config['youtube'])
                
                if config.get('twitter', {}).get('enabled'):
                    self.twitter = TwitterConnector(config['twitter'])
                
                if config.get('facebook', {}).get('enabled'):
                    self.facebook = FacebookConnector(config['facebook'])
                
                if config.get('tiktok', {}).get('enabled'):
                    self.tiktok = TikTokConnector(config['tiktok'])
    
    def update_config(self, platform: str, platform_config: Dict):
        """Platform konfigürasyonunu güncelle"""
        if os.path.exists('social_config.json'):
            with open('social_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        config[platform] = platform_config
        
        with open('social_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.load_config()
    
    def get_platform_status(self) -> Dict:
        """Platform durumlarını döndür"""
        return {
            'youtube': {
                'connected': self.youtube.is_connected() if self.youtube else False,
                'enabled': self.youtube is not None
            },
            'twitter': {
                'connected': self.twitter.is_connected() if self.twitter else False,
                'enabled': self.twitter is not None
            },
            'facebook': {
                'connected': self.facebook.is_connected() if self.facebook else False,
                'enabled': self.facebook is not None
            },
            'tiktok': {
                'connected': self.tiktok.is_connected() if self.tiktok else False,
                'enabled': self.tiktok is not None
            }
        }

# Global instance
platform_manager = PlatformManager()
