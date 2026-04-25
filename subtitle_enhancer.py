"""
Gelişmiş Altyazı Sistemi
"""

import re
from typing import List, Dict

class SubtitleEnhancer:
    def __init__(self):
        self.turkish_vowels = "aeıioöü"
    
    def enhance_text_for_speech(self, text: str) -> str:
        """Metni seslendirmeye uygun hale getirir"""
        # Noktalama düzeltmeleri
        text = self.fix_punctuation(text)
        
        # Sayıları yazıya çevir
        text = self.convert_numbers_to_text(text)
        
        # Kısaltmalar ve ünlü harfler
        text = self.expand_abbreviations(text)
        
        return text
    
    def fix_punctuation(self, text: str) -> str:
        """Noktalama işaretlerini düzeltir"""
        # Cümle sonundaki boşlukları temizle
        text = re.sub(r'\s+([.!?])', r'\1', text)
        
        # Virgülden sonra boşluk ekle
        text = re.sub(r',(?!\s)', ', ', text)
        
        # Parantez içi düzeltmeleri
        text = re.sub(r'\s*\(\s*([^)]+)\s*\)\s*', r' (\1)', text)
        
        return text.strip()
    
    def convert_numbers_to_text(self, text: str) -> str:
        """Sayıları yazıya çevirir"""
        number_words = {
            '0': 'sıfır',
            '1': 'bir', '2': 'iki', '3': 'üç', '4': 'dört',
            '5': 'beş', '6': 'altı', '7': 'yedi', '8': 'sekiz',
            '9': 'dokuz', '10': 'on', '20': 'yirmi', '30': 'otuz',
            '40': 'kırk', '50': 'elli', '60': 'altmış', '70': 'yetmiş',
            '80': 'seksen', '90': 'doksan', '100': 'yüz'
        }
        
        def replace_number(match):
            num = match.group()
            return number_words.get(num, num)
        
        # Basit sayıları değiştir
        for num, word in number_words.items():
            text = text.replace(num, word)
        
        return text
    
    def expand_abbreviations(self, text: str) -> str:
        """Kısaltmaları açar"""
        abbreviations = {
            'AI': 'Yapay Zeka',
            'API': 'A. P. I.',
            'vs': 'karşı',
            'dr': 'doktor',
            'prof': 'profesör',
            'sn': 'saniye',
            'dk': 'dakika',
            'sa': 'saat',
            'kg': 'kilogram',
            'km': 'kilometre',
            'TL': 'Türk Lirası'
        }
        
        for abbr, full in abbreviations.items():
            text = re.sub(r'\b' + re.escape(abbr) + r'\b', full, text, flags=re.IGNORECASE)
        
        return text
    
    def enhance_for_video(self, scenes: List[Dict]) -> List[Dict]:
        """Sahneler için metinleri iyileştirir"""
        enhanced_scenes = []
        
        for scene in scenes:
            narration = scene.get('narration', '')
            if narration:
                enhanced_narration = self.enhance_text_for_speech(narration)
                scene['enhanced_narration'] = enhanced_narration
                scene['speech_ready'] = True
            
            enhanced_scenes.append(scene)
        
        return enhanced_scenes
    
    def generate_subtitle_timing(self, text: str, duration: int = 30) -> List[Dict]:
        """Altyazı zamanlaması oluşturur"""
        words = text.split()
        total_words = len(words)
        
        if total_words == 0:
            return []
        
        total_chars = sum(len(word) for word in words)
        if total_chars == 0:
            return []
            
        # Konuşma sonlarındaki sessizlik ve esleri telafi etmek için
        # altyazı akışını %15 oranında hızlandırıyoruz (geriden gelmeyi önler).
        active_duration = duration * 0.85
        time_per_char = active_duration / total_chars
        
        subtitles = []
        current_time = 0.0
        
        for i, word in enumerate(words):
            word_duration = len(word) * time_per_char
            
            subtitles.append({
                'index': i + 1,
                'text': word,
                'start_time': current_time,
                'end_time': current_time + word_duration,
                'duration': word_duration
            })
            
            current_time += word_duration
            
        # Sahnenin geri kalan kısmında sessizlik olacağı için 
        # hiçbir kelimenin sarı yanmadığı (highlight_idx = -1) bir bitiş frame'i ekle.
        remaining_time = duration - active_duration
        if remaining_time > 0:
            subtitles.append({
                'index': -1,
                'text': '',
                'start_time': current_time,
                'end_time': duration,
                'duration': remaining_time
            })
        
        return subtitles

# Global enhancer instance
subtitle_enhancer = SubtitleEnhancer()
