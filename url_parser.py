import requests
import re
from html.parser import HTMLParser

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_blocks = []
        # Asla kendi kendini kapatan etiketleri buraya eklemeyin (meta, link, img vb.)
        self.ignore_tags = {
            'script', 'style', 'nav', 'footer', 'header', 'aside', 
            'iframe', 'noscript', 'button', 'form', 'select', 'option'
        }
        self.in_ignored_tag = 0

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self.ignore_tags:
            self.in_ignored_tag += 1

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in self.ignore_tags:
            self.in_ignored_tag = max(0, self.in_ignored_tag - 1)

    def handle_data(self, data):
        if self.in_ignored_tag > 0:
            return
        
        text = data.strip()
        if text:
            # Fazla boşlukları temizle
            text = re.sub(r'\s+', ' ', text)
            # Çok kısa veya tamamen sembolden oluşanları atla
            if len(text) > 1 or text.isalnum():
                self.text_blocks.append(text)

def extract_article_text(url: str) -> str:
    """
    Verilen URL'den HTML içeriğini çeker ve temiz metin çıkarır.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr,en-US;q=0.7,en;q=0.3"
    }
    
    print(f"[url_parser] URL çekiliyor: {url}")
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    
    resp.encoding = resp.apparent_encoding
    
    extractor = TextExtractor()
    extractor.feed(resp.text)
    
    raw_text = " ".join(extractor.text_blocks)
    
    # Ekstra temizlik
    cleaned_text = re.sub(r'\s+', ' ', raw_text).strip()
    
    # 8000 kelime sınırı
    words = cleaned_text.split()
    if len(words) > 8000:
        cleaned_text = " ".join(words[:8000])
        print(f"[url_parser] Metin çok uzun olduğu için 8000 kelimeyle sınırlandırıldı.")
        
    print(f"[url_parser] Başarıyla temizlendi. Toplam karakter: {len(cleaned_text)}")
    return cleaned_text

if __name__ == "__main__":
    try:
        url = "https://tr.wikipedia.org/wiki/Schr%C3%B6dinger%27in_kedisi"
        text = extract_article_text(url)
        print(text[:800] + "...")
    except Exception as e:
        print(f"Hata: {e}")
