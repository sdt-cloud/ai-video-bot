"""
Video Üretim Performans Optimizasyon Modülü
"""

import asyncio
import concurrent.futures
import time
from typing import List, Dict, Callable
import threading
import queue
import logging
from typing import List, Dict, Callable, Union

class PerformanceOptimizer:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.task_queue = queue.Queue()
        self.results = {}
        self.logger = logging.getLogger(__name__)
        
    def parallel_image_generation(self, prompts: List[str], output_paths: List[str], provider: Union[str, List[str]] = "Pollinations") -> List[bool]:
        """Görselleri paralel olarak indirir"""
        from image_generator import generate_image
        
        # Provider listesini hazırla
        if isinstance(provider, str):
            providers = [provider] * len(prompts)
        else:
            providers = provider
            
        def generate_single_image(args):
            prompt, output_path, current_provider = args
            from image_validator import evaluate_image_relevance
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    success = generate_image(prompt, output_path, current_provider)
                    if not success:
                        self.logger.warning(f"Görsel üretimi başarısız (Deneme: {attempt+1}/{max_retries})")
                        continue
                        
                    # Görseli Denetle
                    score, reason = evaluate_image_relevance(prompt, output_path)
                    if score >= 7:
                        if attempt > 0:
                            self.logger.info(f"Görsel kabul edildi (Puan: {score}/10). {attempt+1}. denemede başarılı.")
                        return True
                    else:
                        self.logger.warning(f"Görsel reddedildi (Puan: {score}/10). Neden: {reason} (Deneme: {attempt+1}/{max_retries})")
                        
                except Exception as e:
                    self.logger.error(f"Görsel üretim hatası: {e}")
            
            # 3 deneme de başarısızsa (veya görsel kalitesizse) AI ile zorla (Fallback)
            self.logger.warning(f"[*] 3 deneme başarısız. AI ile zorla üretiliyor: {output_path}")
            try:
                # "DALL-E" veya "OpenAI" diyerek garanti bir model çağırıyoruz
                return generate_image(prompt, output_path, "OpenAI")
            except Exception as e:
                self.logger.error(f"Zorunlu AI fallback hatası: {e}")
                return False
        
        # Paralel işlem için argümanları hazırla
        tasks = list(zip(prompts, output_paths, providers))
        
        if not tasks:
            return []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(tasks))) as executor:
            results = list(executor.map(generate_single_image, tasks))
            
        return results
    
    async def async_voice_generation(self, text: str, output_path: str, provider: str = "Edge-TTS") -> bool:
        """Ses üretimini optimize eder"""
        try:
            from voice_generator import generate_voice_async
            return await generate_voice_async(text, output_path, provider)
        except Exception as e:
            self.logger.error(f"Ses üretim hatası: {e}")
            return False
    
    def optimize_script_generation(self, topic: str, ai_provider: str = "Gemini", duration: int = 30) -> Dict:
        """Senaryo üretimini optimize eder"""
        from script_generator import generate_script
        
        start_time = time.time()
        
        try:
            script_data = generate_script(topic, ai_provider, duration)
            
            generation_time = time.time() - start_time
            self.logger.info(f"Senaryo üretim süresi: {generation_time:.2f}s")
            
            return script_data
            
        except Exception as e:
            self.logger.error(f"Senaryo üretim hatası: {e}")
            return None
    
    def batch_video_processing(self, tasks: List[Dict]) -> List[Dict]:
        """Toplu video işlemini optimize eder"""
        results = []
        
        # Görselleri grup halinde paralel işle
        for task in tasks:
            if 'scenes' in task and len(task['scenes']) > 0:
                scenes = task['scenes']
                prompts = [scene.get('image_prompt', '') for scene in scenes]
                task_id = task.get('id', 'unknown')
                
                output_paths = [f"assets/scene_{task_id}_{i}.jpg" for i in range(len(scenes))]
                
                # Paralel görsel üretimi
                image_results = self.parallel_image_generation(prompts, output_paths, task.get('image_ai', 'Pollinations'))
                
                # Başarılı görselleri filtrele
                successful_images = []
                for i, success in enumerate(image_results):
                    if success and i < len(output_paths):
                        successful_images.append(output_paths[i])
                
                task['generated_images'] = successful_images
                task['image_generation_success_rate'] = len(successful_images) / len(scenes) * 100
            
            results.append(task)
        
        return results
    
    def cache_management(self, cache_dir: str = "cache", max_size_mb: int = 500):
        """Önbellek yönetimi"""
        import os
        import shutil
        
        if not os.path.exists(cache_dir):
            return
        
        total_size = 0
        files = []
        
        for root, dirs, filenames in os.walk(cache_dir):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                size = os.path.getsize(file_path)
                files.append((file_path, size, os.path.getmtime(file_path)))
                total_size += size
        
        # Boyut sınırını aşarsa eski dosyaları temizle
        if total_size > max_size_mb * 1024 * 1024:
            files.sort(key=lambda x: x[2])  # Modifikasyon tarihine göre sırala
            
            current_size = total_size
            for file_path, size, _ in files:
                if current_size <= max_size_mb * 1024 * 1024 * 0.8:  # 80'e düşür
                    break
                
                try:
                    os.remove(file_path)
                    current_size -= size
                    self.logger.info(f"Önbellek temizlendi: {file_path}")
                except Exception as e:
                    self.logger.error(f"Önbellek temizleme hatası: {e}")
    
    def resource_monitor(self) -> Dict:
        """Sistem kaynaklarını izler"""
        import psutil
        
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('.').percent,
            'active_threads': threading.active_count()
        }
    
    def adaptive_quality_settings(self) -> Dict:
        """Sistem kaynaklarına göre kalite ayarlarını adapte eder"""
        resources = self.resource_monitor()
        
        settings = {
            'image_resolution': '512x512',
            'voice_quality': 'medium',
            'max_concurrent_tasks': 2,
            'video_quality': 'medium'
        }
        
        # Yüksek CPU kullanımı
        if resources['cpu_percent'] > 80:
            settings['max_concurrent_tasks'] = 1
            settings['image_resolution'] = '256x256'
        
        # Yüksek RAM kullanımı
        if resources['memory_percent'] > 85:
            settings['max_concurrent_tasks'] = 1
            settings['video_quality'] = 'low'
        
        # Düşük disk alanı
        if resources['disk_usage'] > 90:
            settings['video_quality'] = 'low'
            self.cache_management(max_size_mb=100)  # Önbelleği temizle
        
        return settings

# Global optimizer instance
optimizer = PerformanceOptimizer()

def get_optimized_settings():
    """Optimize edilmiş ayarları döndürür"""
    return optimizer.adaptive_quality_settings()

def parallel_process_images(prompts: List[str], output_paths: List[str], provider: Union[str, List[str]] = "Pollinations") -> List[bool]:
    """Görselleri paralel işler"""
    return optimizer.parallel_image_generation(prompts, output_paths, provider)
