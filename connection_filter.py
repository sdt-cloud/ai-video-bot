"""
Connection Error Filter - asyncio hatalarını filtreler
"""

import logging
import sys

class ConnectionErrorFilter(logging.Filter):
    """ConnectionResetError gibi hataları filtreler"""
    
    def filter(self, record):
        # Filtrelenecek hata mesajları
        filtered_errors = [
            'ConnectionResetError',
            'An existing connection was forcibly closed',
            '_ProactorBasePipeTransport._call_connection_lost',
            'WinError 10054'
        ]
        
        # Hata mesajı bu kelimeleri içeriyorsa filtrele
        if any(error in record.getMessage() for error in filtered_errors):
            return False
        
        return True

def setup_connection_filter():
    """Connection error filter'ını kurar"""
    # asyncio logger'ını al
    asyncio_logger = logging.getLogger('asyncio')
    
    # Filter ekle
    connection_filter = ConnectionErrorFilter()
    asyncio_logger.addFilter(connection_filter)
    
    # Diğer yaygın logger'ları da filtrele
    other_loggers = ['uvicorn.error', 'uvicorn.access']
    for logger_name in other_loggers:
        logger = logging.getLogger(logger_name)
        logger.addFilter(connection_filter)
