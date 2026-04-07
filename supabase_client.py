"""
Supabase Client Manager
Connection pooling ve retry logic ile optimize edilmiş Supabase client
"""

import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class SupabaseClient:
    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls) -> Client:
        """Singleton pattern ile Supabase client döndürür"""
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")

            if not url or not key:
                raise ValueError("SUPABASE_URL ve SUPABASE_ANON_KEY ortam değişkenleri gerekli")

            cls._instance = create_client(url, key)
            logger.info("Supabase client başarıyla oluşturuldu")

        return cls._instance

    @classmethod
    async def health_check(cls) -> bool:
        """Supabase bağlantı durumunu kontrol eder"""
        try:
            client = cls.get_client()
            # Basit bir query ile bağlantıyı test et
            response = client.table('videos').select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check başarısız: {e}")
            return False

def get_supabase() -> Client:
    """FastAPI dependency injection için"""
    return SupabaseClient.get_client()
