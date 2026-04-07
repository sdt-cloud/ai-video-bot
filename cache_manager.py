"""
Multi-level Cache Manager
Görsel üretimi için 3-seviye önbellek sistemi
"""

import hashlib
import os
import json
from typing import Optional, Dict
from pathlib import Path
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)

class LRUCache:
    """Memory-based LRU cache"""
    def __init__(self, max_size: int = 50):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size

    def get(self, key: str) -> Optional[bytes]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: bytes):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value

        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

class ImageCacheManager:
    """3-seviyeli görsel önbellek sistemi"""

    def __init__(self, cache_dir: str = "image_cache", max_disk_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.metadata_file = self.cache_dir / "metadata.json"
        self.max_disk_bytes = max_disk_mb * 1024 * 1024

        # Level 1: Memory cache (LRU)
        self.memory_cache = LRUCache(max_size=50)

        # Metadata yükle
        self.metadata = self._load_metadata()

        logger.info(f"Cache manager başlatıldı: {cache_dir}")

    def _generate_key(self, prompt: str, provider: str, size: str = "1080x1920") -> str:
        """Önbellek anahtarı oluştur"""
        content = f"{prompt}_{provider}_{size}"
        return hashlib.md5(content.encode()).hexdigest()

    def _load_metadata(self) -> Dict:
        """Metadata dosyasını yükle"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_metadata(self):
        """Metadata dosyasını kaydet"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Metadata kaydedilemedi: {e}")

    def get_cached_image(self, prompt: str, provider: str) -> Optional[str]:
        """Önbellekten görsel al"""
        key = self._generate_key(prompt, provider)

        # Level 1: Memory cache
        image_data = self.memory_cache.get(key)
        if image_data:
            logger.info(f"Cache hit (memory): {key[:8]}")
            temp_path = self.cache_dir / f"temp_{key}.jpg"
            with open(temp_path, 'wb') as f:
                f.write(image_data)
            return str(temp_path)

        # Level 2: Disk cache
        cache_path = self.cache_dir / f"{key}.jpg"
        if cache_path.exists():
            logger.info(f"Cache hit (disk): {key[:8]}")

            # Memory cache'e ekle
            with open(cache_path, 'rb') as f:
                image_data = f.read()
                self.memory_cache.set(key, image_data)

            return str(cache_path)

        logger.debug(f"Cache miss: {key[:8]}")
        return None

    def cache_image(self, prompt: str, provider: str, image_path: str) -> bool:
        """Görseli önbelleğe ekle"""
        try:
            key = self._generate_key(prompt, provider)

            # Dosyayı oku
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # Level 1: Memory cache
            self.memory_cache.set(key, image_data)

            # Level 2: Disk cache
            cache_path = self.cache_dir / f"{key}.jpg"
            with open(cache_path, 'wb') as f:
                f.write(image_data)

            # Metadata güncelle
            self.metadata[key] = {
                'prompt': prompt[:100],
                'provider': provider,
                'size': len(image_data),
                'path': str(cache_path)
            }
            self._save_metadata()

            # Disk alanı kontrolü
            self._cleanup_if_needed()

            logger.info(f"Görsel önbelleğe eklendi: {key[:8]}")
            return True

        except Exception as e:
            logger.error(f"Önbelleğe eklenemedi: {e}")
            return False

    def _cleanup_if_needed(self):
        """Disk alanı doluysa eski dosyaları temizle"""
        total_size = sum(
            Path(meta['path']).stat().st_size
            for meta in self.metadata.values()
            if Path(meta['path']).exists()
        )

        if total_size > self.max_disk_bytes:
            logger.warning(f"Cache full ({total_size / 1024 / 1024:.1f}MB), cleaning up...")

            # En eski dosyaları sil (basit FIFO)
            keys_to_remove = list(self.metadata.keys())[:len(self.metadata) // 4]

            for key in keys_to_remove:
                try:
                    cache_path = Path(self.metadata[key]['path'])
                    if cache_path.exists():
                        cache_path.unlink()
                    del self.metadata[key]
                except Exception as e:
                    logger.error(f"Cleanup error: {e}")

            self._save_metadata()
            logger.info(f"Cleaned {len(keys_to_remove)} old cache files")

    def get_stats(self) -> Dict:
        """Önbellek istatistikleri"""
        total_files = len(self.metadata)
        total_size = sum(
            Path(meta['path']).stat().st_size
            for meta in self.metadata.values()
            if Path(meta['path']).exists()
        )

        return {
            'memory_cache_size': len(self.memory_cache.cache),
            'disk_cache_files': total_files,
            'disk_cache_size_mb': total_size / 1024 / 1024,
            'max_disk_size_mb': self.max_disk_bytes / 1024 / 1024
        }

# Global cache manager instance
cache_manager = ImageCacheManager()
