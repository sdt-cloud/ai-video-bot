"""
Sosyal Medya API Kurulum Rehberi
Bu script her platform için gerekli adımları ve API anahtarlarını nasıl alacağınızı gösterir
"""

import webbrowser
import json

def print_setup_guide():
    print("""
🚀 SOSYAL MEDYA API KURULUM REHBERİ
=====================================

Bu rehber ile kendi sosyal medya yönetim sisteminizi ücretsiz kurabilirsiniz!

💰 MALİYET KARŞILAŞTIRMASI:
---------------------------
Ücretli Servisler: $10-49/ay
Kendi Sisteminiz: $0/ay (sadece API limitleri var)

📋 PLATFORM LİMİTLERİ:
----------------------
• Facebook: 200 request/saat (Ücretsiz)
• Twitter: 500,000 tweet/ay (Ücretsiz) 
• Instagram: 200 request/saat (Ücretsiz)
• YouTube: 10,000 units/gün (Ücretsiz)
• TikTok: Business onayı gerektirir

🔧 ADIM ADIM KURULUM:
====================

1️⃣ FACEBOOK GRAPH API
----------------------
Gerekli: App ID, App Secret, Access Token, Page ID

Adımlar:
1. https://developers.facebook.com/ adresine gidin
2. "Create App" → "Business" seçin
3. App oluşturduktan sonra "Add Product" → "Facebook Login" ekleyin
4. "Settings" → "Basic" bölümünden App ID ve App Secret'ı kopyalayın
5. "Tools" → "Graph API Explorer" gidin
6. "Get User Access Token" → İzinleri seçin:
   • pages_read_engagement
   • pages_manage_posts
   • publish_to_groups
7. Token'ı kopyalayın
8. Page ID bulmak için: https://graph.facebook.com/me/accounts

2️⃣ TWITTER/X API V2
-------------------
Gerekli: API Key, API Secret, Access Token, Access Token Secret, Bearer Token

Adımlar:
1. https://developer.twitter.com/ adresine gidin
2. "Sign up for Free Account" seçin
3. "Create Project" oluşturun
4. "Create App" oluşturun
5. App oluşturduktan sonra "Keys and tokens" bölümünde:
   • API Key ve API Secret'ı kopyalayın
   • "Generate" ile Access Token ve Secret'ı oluşturun
   • Bearer Token'ı da kopyalayın
6. App permissions'ı "Read and Write" yapın

3️⃣ INSTAGRAM BASIC DISPLAY API
--------------------------------
Gerekli: App ID, App Secret, Access Token, Instagram Business Account ID

Adımlar:
1. Facebook Developer hesabınızı kullanın (aynı hesap)
2. https://developers.facebook.com/docs/instagram-basic-display-api gidin
3. "Get Started" butonuna tıklayın
4. "Create App" → "Business" seçin
5. "Instagram Basic Display" ürününü ekleyin
6. "Add Platform" → "Website" seçip sitenizi girin
7. Test kullanıcıları ekleyin
8. Access Token alın
9. Instagram Business Account ID bulmak için Graph API kullanın

4️⃣ YOUTUBE DATA API V3
-----------------------
Gerekli: API Key, Client ID, Client Secret, Refresh Token

Adımlar:
1. https://console.cloud.google.com/ adresine gidin
2. Yeni proje oluşturun
3. "APIs & Services" → "Library" gidin
4. "YouTube Data API v3" aratıp etkinleştirin
5. "APIs & Services" → "Credentials" gidin
6. "Create Credentials" → "OAuth 2.0 Client ID" oluşturun
7. "Application type": Web application
8. "Authorized redirect URIs": http://localhost:8080/callback
9. Client ID ve Client Secret'ı kopyalayın
10. OAuth2 playground'da refresh token alın:
    • https://developers.google.com/oauthplayground
    • YouTube Data API v3 seçin
    • Authorize APIs butonuna tıklayın
    • Access token al

5️⃣ TIKTOK API (İsteğe Bağlı)
-----------------------------
Gerekli: Client Key, Client Secret, Access Token

Not: TikTok API'si business onayı gerektirir. Manuel upload daha pratik olabilir.

🎯 HIZLI KURULUM SCRIPTİ:
========================

Aşağıdaki kod ile platformları kolayca yapılandırabilirsiniz:

```python
from custom_social_manager import CustomSocialMediaManager

manager = CustomSocialMediaManager()

# Facebook yapılandırması
manager.configure_platform("facebook", {
    "app_id": "FACEBOOK_APP_ID",
    "app_secret": "FACEBOOK_APP_SECRET", 
    "access_token": "FACEBOOK_ACCESS_TOKEN",
    "page_id": "FACEBOOK_PAGE_ID",
    "enabled": True
})

# Twitter yapılandırması
manager.configure_platform("twitter", {
    "api_key": "TWITTER_API_KEY",
    "api_secret": "TWITTER_API_SECRET",
    "access_token": "TWITTER_ACCESS_TOKEN",
    "access_token_secret": "TWITTER_ACCESS_TOKEN_SECRET",
    "bearer_token": "TWITTER_BEARER_TOKEN",
    "enabled": True
})

# Diğer platformlar...
```

🔗 FAYDALI LİNKLER:
-------------------
• Facebook Developer: https://developers.facebook.com/
• Twitter Developer: https://developer.twitter.com/
• Instagram API: https://developers.facebook.com/docs/instagram-basic-display-api
• Google Cloud Console: https://console.cloud.google.com/
• YouTube API: https://developers.google.com/youtube/v3

⚠️ ÖNEMLİ NOTLAR:
-----------------
• Tüm API'ler ücretsizdir ama request limitleri vardır
• Günde 50-100 gönderiden fazlası için limitlere dikkat edin
• Instagram için Business Account gereklidir
• TikTok business onayı gerektirir (manuel upload önerilir)
• YouTube video upload longer timeout gerektirir

🚀 TEST ETME:
-------------
Kurulumdan sonra test etmek için:

```python
import asyncio
from custom_social_manager import CustomSocialMediaManager

async def test_post():
    manager = CustomSocialMediaManager()
    
    # Facebook test
    result = await manager.post_to_facebook(
        content="Test gönderi 🚀",
        image_path="test.jpg"
    )
    print("Facebook:", result)
    
    # Twitter test
    result = await manager.post_to_twitter(
        content="Test tweet 🐦",
        media_path="test.jpg"
    )
    print("Twitter:", result)

asyncio.run(test_post())
```

💡 İPUÇLARI:
-----------
• Başlangıçta tek platform ile test edin
• Rate limiting hatalarına karşı retry logic ekleyin
• Büyük videolar için chunked upload kullanın
• Error handling ve logging ekleyin
• Scheduled posting için cron job kullanın

🎉 SONUÇ:
---------
Bu sistem ile aylık $0 maliyetle tüm sosyal medya platformlarınızı yönetebilirsiniz!
""")

def open_developer_portals():
    """Geliştirici portallarını aç"""
    portals = {
        "Facebook Developer": "https://developers.facebook.com/",
        "Twitter Developer": "https://developer.twitter.com/",
        "Google Cloud Console": "https://console.cloud.google.com/",
        "Instagram API Docs": "https://developers.facebook.com/docs/instagram-basic-display-api",
        "YouTube API Docs": "https://developers.google.com/youtube/v3"
    }
    
    print("\n🌐 Geliştirici Portalları Açılıyor...")
    for name, url in portals.items():
        print(f"• {name}: {url}")
        try:
            webbrowser.open(url)
        except:
            print(f"  Tarayıcı açılamadı. Manuel olarak gidin: {url}")

def create_config_template():
    """Yapılandırma şablonu oluştur"""
    template = {
        "facebook": {
            "app_id": "BURAYA_FACEBOOK_APP_ID",
            "app_secret": "BURAYA_FACEBOOK_APP_SECRET",
            "access_token": "BURAYA_FACEBOOK_ACCESS_TOKEN",
            "page_id": "BURAYA_FACEBOOK_PAGE_ID",
            "enabled": False
        },
        "twitter": {
            "api_key": "BURAYA_TWITTER_API_KEY",
            "api_secret": "BURAYA_TWITTER_API_SECRET",
            "access_token": "BURAYA_TWITTER_ACCESS_TOKEN",
            "access_token_secret": "BURAYA_TWITTER_ACCESS_TOKEN_SECRET",
            "bearer_token": "BURAYA_TWITTER_BEARER_TOKEN",
            "enabled": False
        },
        "instagram": {
            "app_id": "BURAYA_INSTAGRAM_APP_ID",
            "app_secret": "BURAYA_INSTAGRAM_APP_SECRET",
            "access_token": "BURAYA_INSTAGRAM_ACCESS_TOKEN",
            "instagram_business_account_id": "BURAYA_IG_BUSINESS_ID",
            "enabled": False
        },
        "tiktok": {
            "client_key": "BURAYA_TIKTOK_CLIENT_KEY",
            "client_secret": "BURAYA_TIKTOK_CLIENT_SECRET",
            "access_token": "BURAYA_TIKTOK_ACCESS_TOKEN",
            "enabled": False
        },
        "youtube": {
            "api_key": "BURAYA_YOUTUBE_API_KEY",
            "client_id": "BURAYA_YOUTUBE_CLIENT_ID",
            "client_secret": "BURAYA_YOUTUBE_CLIENT_SECRET",
            "refresh_token": "BURAYA_YOUTUBE_REFRESH_TOKEN",
            "channel_id": "BURAYA_YOUTUBE_CHANNEL_ID",
            "enabled": False
        }
    }
    
    with open("custom_social_config_template.json", "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print("✅ Yapılandırma şablonu oluşturuldu: custom_social_config_template.json")

if __name__ == "__main__":
    print_setup_guide()
    
    choice = input("\nSeçiminiz (1: Rehberi göster, 2: Portalları aç, 3: Şablon oluştur): ")
    
    if choice == "1":
        print_setup_guide()
    elif choice == "2":
        open_developer_portals()
    elif choice == "3":
        create_config_template()
    else:
        print("Geçersiz seçim.")
