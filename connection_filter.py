"""
Connection Error Filter - asyncio ve diğer hataları filtreler
"""

import logging
import sys

class ConnectionErrorFilter(logging.Filter):
    """ConnectionResetError ve boş JSON hatalarını filtreler"""
    
    def filter(self, record):
        message = record.getMessage()
        
        # Filtrelenecek hata mesajları
        filtered_errors = [
            'ConnectionResetError',
            'An existing connection was forcibly closed',
            '_ProactorBasePipeTransport._call_connection_lost',
            'WinError 10054'
        ]
        
        # Boş JSON hatalarını filtrele
        if message == '{}' or message == 'ERROR: {}':
            return False
        
        # Connection hatalarını filtrele
        if any(error in message for error in filtered_errors):
            return False
        
        return True

def setup_connection_filter():
    """Connection error filter'ını kurar"""
    # Tüm root logger'ları al
    root_logger = logging.getLogger()
    
    # Ana logger'a filter ekle
    connection_filter = ConnectionErrorFilter()
    root_logger.addFilter(connection_filter)
    
    # Console handler'ını da filtrele
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.addFilter(connection_filter)
    
    print("🔧 Hata filtresi aktif - Connection ve boş JSON hataları filtreleniyor")
