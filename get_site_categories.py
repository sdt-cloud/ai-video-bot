"""
WordPress sitesindeki mevcut kategorileri çeker
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_site_categories():
    """WordPress sitesindeki mevcut kategorileri çeker"""
    try:
        wp_base_url = os.getenv("WP_BASE_URL", "http://localhost:8881")
        url = f"{wp_base_url}/wp-json/wp/v2/categories"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            categories = response.json()
            print("WordPress Sitenizdeki Mevcut Kategoriler:")
            print("=" * 50)
            
            # HTML option formatında çıktı
            html_options = ['<option value="">Tüm Kategoriler</option>']
            
            for cat in categories:
                slug = cat.get('slug', '')
                name = cat.get('name', '')
                count = cat.get('count', 0)
                
                if slug and name:
                    html_options.append(f'<option value="{slug}">{name} ({count} kavram)</option>')
                    print(f"✅ {name} -> {slug} ({count} kavram)")
            
            print("\nFrontend için HTML kodu:")
            print("=" * 50)
            for option in html_options:
                print(option)
            
            # JS için format
            print("\nJavaScript için kategori array:")
            print("=" * 50)
            js_categories = []
            for cat in categories:
                slug = cat.get('slug', '')
                name = cat.get('name', '')
                if slug and name:
                    js_categories.append(f'"{slug}": "{name}"')
            
            print("const categories = {")
            print(",\n".join(js_categories))
            print("};")
            
            return categories
        else:
            print(f"❌ API Hatası: {response.status_code}")
            print(f"Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        return []

if __name__ == "__main__":
    get_site_categories()
