"""
WordPress kategori kontrol script'i
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_wp_categories():
    """WordPress'ten kategorileri çeker"""
    try:
        wp_base_url = os.getenv("WP_BASE_URL", "http://localhost:8881")
        url = f"{wp_base_url}/wp-json/wp/v2/categories"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            categories = response.json()
            print("WordPress Kategorileri:")
            print("=" * 50)
            
            for cat in categories:
                cat_id = cat.get('id', 'N/A')
                cat_name = cat.get('name', 'N/A')
                cat_slug = cat.get('slug', 'N/A')
                cat_count = cat.get('count', 0)
                
                print(f"ID: {cat_id}")
                print(f"Name: {cat_name}")
                print(f"Slug: {cat_slug}")
                print(f"Count: {cat_count}")
                print("-" * 30)
            
            # Frontend için uygun format
            print("\nFrontend için kategori seçenekleri:")
            print("=" * 50)
            for cat in categories:
                slug = cat.get('slug', '')
                name = cat.get('name', '')
                if slug:
                    print(f'<option value="{slug}">{name}</option>')
            
        else:
            print(f"API Hatası: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    get_wp_categories()
