"""
Nedir.me API Entegrasyon Modülü
WordPress'ten kavramları alıp otomatik video üretimi
"""

import requests
import json
import time
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class NedirIntegration:
    def __init__(self):
        self.wp_base_url = os.getenv("WP_BASE_URL", "http://localhost:8881")
        self.wp_username = os.getenv("WP_USERNAME", "")
        self.wp_password = os.getenv("WP_PASSWORD", "")
        self.batch_size = 10
        self.delay_between_requests = 2
        
    def get_concepts(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """WordPress'ten kavramları çeker"""
        try:
            url = f"{self.wp_base_url}/wp-json/wp/v2/kavram"
            params = {
                'per_page': min(limit, 100),
                'status': 'publish',
                '_fields': 'id,title,excerpt,meta,ana-kategori'
            }
            
            if category:
                params['ana-kategori'] = category
                
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                concepts = response.json()
                return self._process_concepts(concepts)
            else:
                print(f"❌ API Hatası: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Kavramlar alınırken hata: {e}")
            return []
    
    def _process_concepts(self, concepts: List[Dict]) -> List[Dict]:
        """Kavramları işleyip video için uygun formata getirir"""
        processed = []
        
        for concept in concepts:
            title = concept.get('title', {}).get('rendered', '').strip()
            excerpt = concept.get('excerpt', {}).get('rendered', '').strip()
            
            if title and len(title) > 3:
                processed.append({
                    'id': concept.get('id'),
                    'title': title,
                    'description': excerpt,
                    'category': concept.get('ana-kategori', ['genel'])[0] if concept.get('ana-kategori') else 'genel',
                    'meta': concept.get('meta', {})
                })
        
        return processed
    
    def get_concept_details(self, concept_id: int) -> Optional[Dict]:
        """Tek bir kavramın detaylarını çeker"""
        try:
            url = f"{self.wp_base_url}/wp-json/wp/v2/kavram/{concept_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"❌ Kavram detayı alınırken hata: {e}")
            return None
    
    def create_video_topics_from_concepts(self, concepts: List[Dict]) -> List[str]:
        """Kavramlardan video konuları oluşturur"""
        topics = []
        
        for concept in concepts:
            title = concept['title']
            description = concept.get('description', '')
            category = concept.get('category', 'genel')
            
            # Farklı formatlarda video konuları oluştur
            topics.append(f"{title} nedir? {category} kategorisinde açıklama")
            
            if description and len(description) > 50:
                topics.append(f"{title}: {description[:100]}...")
                
            # Pratik örnek formatı
            topics.append(f"{title} günlük hayatta nerelerde kullanılır?")
        
        return topics
    
    def batch_process_for_videos(self, max_concepts: int = 20) -> List[str]:
        """Kavramları toplu işleyip video konuları listesi döndürür"""
        print("🔄 Nedir.me'den kavramlar alınıyor...")
        
        concepts = self.get_concepts(limit=max_concepts)
        
        if not concepts:
            print("❌ Kavram bulunamadı")
            return []
        
        print(f"✅ {len(concepts)} kavram bulundu")
        
        # Video konuları oluştur
        video_topics = self.create_video_topics_from_concepts(concepts)
        
        print(f"🎬 {len(video_topics)} video konusu oluşturuldu")
        
        return video_topics[:max_concepts * 2]  # Her kavram için max 2 video
    
    def update_video_status(self, concept_id: int, video_path: str):
        """WordPress'te kavramın video durumunu günceller"""
        try:
            if not self.wp_username or not self.wp_password:
                print("⚠️ WordPress kimlik bilgileri eksik")
                return False
            
            url = f"{self.wp_base_url}/wp-json/wp/v2/kavram/{concept_id}"
            headers = {'Content-Type': 'application/json'}
            
            # Video meta bilgisini güncelle
            meta_data = {
                'video_url': video_path,
                'video_generated': True,
                'video_date': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            data = {
                'meta': meta_data
            }
            
            response = requests.post(url, json=data, headers=headers, 
                                  auth=(self.wp_username, self.wp_password), timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Kavram {concept_id} video durumu güncellendi")
                return True
            else:
                print(f"❌ Güncelleme hatası: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Video durumu güncellenirken hata: {e}")
            return False

# Test ve kullanım örneği
if __name__ == "__main__":
    integration = NedirIntegration()
    
    # Test: kavramları al
    concepts = integration.get_concepts(limit=5)
    print(f"📋 Bulunan kavramlar: {[c['title'] for c in concepts]}")
    
    # Test: video konuları oluştur
    topics = integration.create_video_topics_from_concepts(concepts)
    print(f"🎬 Video konuları: {topics}")
