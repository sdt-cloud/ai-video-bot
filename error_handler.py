"""
Gelişmiş Hata Yönetimi ve Logging Sistemi
"""

import logging
import traceback
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
import asyncio

class VideoProductionLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.setup_logging()
        
    def setup_logging(self):
        """Log sistemini kurar"""
        # Log dizinini oluştur
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Log formatı
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(
            f"{self.log_dir}/video_production.log",
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        
        # Error file handler
        error_handler = logging.FileHandler(
            f"{self.log_dir}/errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Root logger'ı yapılandır
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(error_handler)
        root_logger.addHandler(console_handler)
        
        # Video production logger
        self.logger = logging.getLogger('video_production')
        
    def log_video_production_step(self, step: str, task_id: str, details: Dict = None):
        """Video üretim adımlarını loglar"""
        log_data = {
            'step': step,
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        
        self.logger.info(f"VIDEO_STEP: {json.dumps(log_data, ensure_ascii=False)}")
        
    def log_error(self, error: Exception, context: Dict = None):
        """Hataları detaylı loglar"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Boş veya geçersiz hata mesajlarını önle
        if not error_data['error_message'] or error_data['error_message'] == '{}' or error_data['error_message'] == 'None':
            error_data['error_message'] = 'Bilinmeyen hata'
        
        # JSON serialization hatasını önle
        try:
            json_str = json.dumps(error_data, ensure_ascii=False)
            if json_str == '{}' or json_str == 'null':
                self.logger.error(f"ERROR: {error_data['error_type']} - Boş hata objesi")
            else:
                self.logger.error(f"ERROR: {json_str}")
        except Exception as log_error:
            # JSON hata verirse basit log kullan
            self.logger.error(f"ERROR: {error_data['error_type']} - {error_data['error_message']}")
        
        # Hata raporu dosyasına yaz (sadece anlamlı hatalar için)
        if error_data['error_message'] != 'Bilinmeyen hata':
            error_report_file = f"{self.log_dir}/error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            try:
                os.makedirs(self.log_dir, exist_ok=True)
                with open(error_report_file, 'w', encoding='utf-8') as f:
                    json.dump(error_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.logger.error(f"Hata raporu yazılamadı: {e}")
    
    def log_performance_metrics(self, metrics: Dict):
        """Performans metriklerini loglar"""
        self.logger.info(f"PERFORMANCE: {json.dumps(metrics, ensure_ascii=False)}")
        
    def log_api_usage(self, api_name: str, endpoint: str, response_time: float, status: str):
        """API kullanımını loglar"""
        api_data = {
            'api_name': api_name,
            'endpoint': endpoint,
            'response_time': response_time,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"API_USAGE: {json.dumps(api_data, ensure_ascii=False)}")

# Global logger instance
video_logger = VideoProductionLogger()

def handle_video_errors(func):
    """Video üretim fonksiyonları için hata yönetimi decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                'function': func.__name__,
                'args': str(args)[:200],  # İlk 200 karakter
                'kwargs': str(kwargs)[:200]
            }
            video_logger.log_error(e, context)
            return None
    return wrapper

def async_handle_video_errors(func):
    """Async video üretim fonksiyonları için hata yönetimi decorator"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            context = {
                'function': func.__name__,
                'args': str(args)[:200],
                'kwargs': str(kwargs)[:200]
            }
            video_logger.log_error(e, context)
            return None
    return wrapper

class ErrorRecoverySystem:
    def __init__(self):
        self.retry_attempts = 3
        self.retry_delays = [1, 3, 5]  # saniye
        
    async def retry_with_backoff(self, func, *args, **kwargs):
        """Exponential backoff ile yeniden deneme"""
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_error = e
                video_logger.logger.warning(f"Deneme {attempt + 1} başarısız: {e}")
                
                if attempt < self.retry_attempts - 1:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    await asyncio.sleep(delay)
        
        video_logger.log_error(last_error, {'retry_attempts': self.retry_attempts})
        return None
    
    def fallback_script_generation(self, topic: str) -> Optional[Dict]:
        """Senaryo üretimi için fallback"""
        try:
            # Basit fallback senaryo
            return {
                "scenes": [
                    {
                        "narration": f"{topic} hakkında ilginç bilgiler",
                        "image_prompt": f"Educational illustration about {topic}, simple and clear"
                    },
                    {
                        "narration": f"{topic} neden önemlidir?",
                        "image_prompt": f"Importance of {topic} in daily life, educational style"
                    }
                ]
            }
        except Exception as e:
            video_logger.log_error(e, {'fallback_type': 'script'})
            return None
    
    def fallback_voice_generation(self, text: str, output_path: str) -> bool:
        """Ses üretimi için fallback"""
        try:
            # Edge-TTS en güvenilir seçenek
            from voice_generator import generate_voice
            return generate_voice(text, output_path)
        except Exception as e:
            video_logger.log_error(e, {'fallback_type': 'voice'})
            return False
    
    def fallback_image_generation(self, prompt: str, output_path: str) -> bool:
        """Görsel üretimi için fallback"""
        try:
            # En basit görsel üretim yöntemi
            from image_generator import generate_image
            simplified_prompt = f"Simple illustration: {prompt.split(',')[0]}"
            return generate_image(simplified_prompt, output_path)
        except Exception as e:
            video_logger.log_error(e, {'fallback_type': 'image'})
            return False

# Global error recovery instance
error_recovery = ErrorRecoverySystem()

def log_step(step_name: str):
    """Adım loglama decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            task_id = kwargs.get('task_id', 'unknown')
            
            video_logger.log_video_production_step(
                step_name, 
                task_id, 
                {'start_time': start_time.isoformat()}
            )
            
            try:
                result = func(*args, **kwargs)
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                video_logger.log_video_production_step(
                    f"{step_name}_completed",
                    task_id,
                    {'duration': duration, 'success': True}
                )
                
                return result
                
            except Exception as e:
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                video_logger.log_error(e, {
                    'step': step_name,
                    'task_id': task_id,
                    'duration': duration
                })
                
                raise
                
        return wrapper
    return decorator

# Kullanım örnekleri
if __name__ == "__main__":
    # Test logging
    video_logger.log_video_production_step("test", "123", {"test": True})
    
    # Test error logging
    try:
        raise ValueError("Test hatası")
    except Exception as e:
        video_logger.log_error(e, {"test_context": "logging_test"})
