"""
Otomatik Video Kuyruk Yöneticisi
"""

import asyncio
import time
import logging
from typing import List, Dict
import database

# Circular import'i önlemek için app modülünü dinamik import et
def get_process_video_function():
    from app import process_video
    return process_video

class QueueManager:
    def __init__(self, max_concurrent_tasks: int = 2, check_interval: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.check_interval = check_interval
        self.is_running = False
        self.current_tasks = set()
        self.logger = logging.getLogger(__name__)
        
    async def start_queue_processor(self):
        """Kuyruk işlemcisini başlatır"""
        if self.is_running:
            return
            
        self.is_running = True
        self.logger.info("Kuyruk işlemcisi başlatıldı")
        
        while self.is_running:
            try:
                await self.process_queue()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Kuyruk işleme hatası: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def process_queue(self):
        """Bekleyen görevleri işler"""
        # Aktif görev sayısını kontrol et
        if len(self.current_tasks) >= self.max_concurrent_tasks:
            return
            
        # Bekleyen görevleri al
        pending_tasks = database.get_pending_tasks(limit=self.max_concurrent_tasks - len(self.current_tasks))
        
        for task in pending_tasks:
            if task['id'] not in self.current_tasks:
                await self.start_task(task)
    
    async def start_task(self, task: Dict):
        """Tek bir görevi başlatır"""
        task_id = task['id']
        self.current_tasks.add(task_id)
        
        self.logger.info(f"Task {task_id} başlatılıyor: {task['topic']}")
        
        try:
            # Görevi arka planda çalıştır
            asyncio.create_task(self.run_task_with_cleanup(task))
        except Exception as e:
            self.logger.error(f"Task {task_id} başlatılamadı: {e}")
            self.current_tasks.discard(task_id)
            database.update_status(task_id, "failed", 0, str(e))
    
    async def run_task_with_cleanup(self, task: Dict):
        """Görevi çalıştırır ve temizlik yapar"""
        task_id = task['id']
        
        try:
            process_video = get_process_video_function()
            await process_video(task)
            self.logger.info(f"Task {task_id} tamamlandı")
        except Exception as e:
            self.logger.error(f"Task {task_id} başarısız: {e}")
            database.update_status(task_id, "failed", 0, str(e))
        finally:
            # Görevi aktif listeden çıkar
            self.current_tasks.discard(task_id)
            
            # 1 saniye bekle ve yeni görev kontrol et
            await asyncio.sleep(1)
            await self.process_queue()
    
    def stop_queue_processor(self):
        """Kuyruk işlemcisini durdurur"""
        self.is_running = False
        self.logger.info("Kuyruk işlemcisi durduruldu")
    
    def get_queue_status(self) -> Dict:
        """Kuyruk durumunu döndürür"""
        pending_count = database.get_pending_tasks_count()
        processing_count = len(self.current_tasks)
        
        return {
            "pending_tasks": pending_count,
            "processing_tasks": processing_count,
            "max_concurrent": self.max_concurrent_tasks,
            "is_running": self.is_running
        }

# Global queue manager instance
queue_manager = QueueManager()

async def start_queue_manager():
    """Global kuyruk yöneticisini başlatır"""
    await queue_manager.start_queue_processor()

def get_queue_status():
    """Kuyruk durumunu döndürür"""
    return queue_manager.get_queue_status()

def stop_queue_manager():
    """Kuyruk yöneticisini durdurur"""
    queue_manager.stop_queue_processor()
