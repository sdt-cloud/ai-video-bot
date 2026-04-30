"""
Gelişmiş Altyazı Sistemi
"""

import re
from typing import List, Dict

class SubtitleEnhancer:
    def __init__(self):
        self.turkish_vowels = "aeıioöü"
        self.emoji_dict = {
            "para": "💰", "kazanç": "💸", "zengin": "🤑", "milyoner": "🤑",
            "zaman": "⏳", "saat": "⏰", "dakika": "⏱️",
            "şok": "😱", "inanılmaz": "🤯", "sır": "🤫", "gizli": "🕵️",
            "dikkat": "⚠️", "önemli": "❗", "uyarı": "🛑",
            "dünya": "🌍", "uzay": "🚀", "bilim": "🔬", "gezegen": "🪐",
            "aşk": "❤️", "sevgi": "😍", "kalp": "💖",
            "ateş": "🔥", "sıcak": "🥵", "güneş": "☀️",
            "soğuk": "❄️", "buz": "🧊",
            "başarı": "🏆", "hedef": "🎯", "zafer": "🥇",
            "beyin": "🧠", "zeka": "💡", "fikir": "💡", "akıllı": "🧠",
            "göz": "👀", "bak": "👁️", "gör": "👁️",
            "mutlu": "😊", "komik": "😂", "üzgün": "😢",
            "korkunç": "👻", "karanlık": "🌑", "gece": "🌙",
            "yemek": "🍔", "su": "💧", "kahve": "☕",
            "ölüm": "💀", "tehlike": "☢️",
            "neden": "❓", "nasıl": "🤔"
        }
    
    def enhance_text_for_speech(self, text: str) -> str:
        """Metni seslendirmeye uygun hale getirir"""
        # Noktalama düzeltmeleri
        text = self.fix_punctuation(text)
        
        # Sayıları yazıya çevir (KAPALI - Modern TTS motorları sayıları kendi okur, ekranda rakam kalsın)
        # text = self.convert_numbers_to_text(text)
        
        # Kısaltmalar ve ünlü harfler
        text = self.expand_abbreviations(text)
        
        return text
    
    def add_emojis(self, text: str) -> str:
        """Kelimelere uygun emojileri ekler"""
        words = text.split()
        result = []
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word).lower()
            if clean_word in self.emoji_dict:
                # Emojiyi kelimeye bitiştir (beraber highlight olmaları için)
                word = f"{word} {self.emoji_dict[clean_word]}"
            result.append(word)
        return " ".join(result)
    
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
    
    def generate_subtitle_timing(self, text: str, duration: float = 30.0, speed_ratio: float = 0.80, delay: float = 0.5) -> List[Dict]:
        """Altyazı zamanlaması oluşturur. Hız ve gecikme ayarlıdır."""
        words = text.split()
        total_words = len(words)
        
        if total_words == 0:
            return []
        
        total_chars = sum(len(word) for word in words)
        if total_chars == 0:
            return []
            
        # Slayt süresine göre maksimum gecikmeyi sınırla (en fazla %30 gecikme)
        actual_delay = min(delay, duration * 0.3)
        
        # Konuşma sonlarındaki sessizlik ve esleri telafi etmek için
        # altyazı akışını belirtilen hız oranında hesapla (%80 hız gibi)
        available_duration = duration - actual_delay
        active_duration = available_duration * speed_ratio
        time_per_char = active_duration / total_chars
        
        subtitles = []
        current_time = 0.0
        
        # Başlangıç gecikmesi ekle (hiçbir kelimenin vurgulanmadığı boşluk)
        if actual_delay > 0:
            subtitles.append({
                'index': -1,
                'text': '',
                'start_time': 0.0,
                'end_time': actual_delay,
                'duration': actual_delay
            })
            current_time += actual_delay
        
        for i, word in enumerate(words):
            word_duration = len(word) * time_per_char
            
            subtitles.append({
                'index': i,
                'text': word,
                'start_time': current_time,
                'end_time': current_time + word_duration,
                'duration': word_duration
            })
            
            current_time += word_duration
            
        # Sahnenin geri kalan kısmında sessizlik olacağı için 
        # hiçbir kelimenin sarı yanmadığı (highlight_idx = -1) bir bitiş frame'i ekle.
        remaining_time = duration - current_time
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
