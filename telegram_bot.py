import os
import time
import requests
import sqlite3
import threading
from dotenv import load_dotenv
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile

# .env dosyasını yükle
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    print("HATA: .env dosyasında TELEGRAM_BOT_TOKEN bulunamadı.")
    print("Bot başlatılamadı.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

API_URL = "http://127.0.0.1:8001/api/videos/single"
DB_PATH = "aivid_data.db"
VIDEO_DIR = "frontend/videos"

# Bellekteki kullanıcı durumları
user_states = {}

# Bot tarafından başlatılan görevlerin tutulduğu liste {task_id: chat_id}
active_bot_tasks = {}

def get_default_settings():
    return {
        "topic": "",
        "duration": 30,
        "language": "tr",
        "voice_type": "erkek",
        "voice_ai": "Edge-TTS",
        "subtitle_style": "tiktok",
        "bgm_enabled": False,
        "script_ai": "Gemini",
        "image_ai": "Stock-Auto"
    }

# Arka plan iş parçacığı: Tamamlanan videoları kontrol eder
def background_task_checker():
    while True:
        try:
            if active_bot_tasks:
                # Veritabanına bağlan
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Sadece bekleyen bot görevlerini kontrol et
                task_ids = list(active_bot_tasks.keys())
                for tid in task_ids:
                    cursor.execute("SELECT status, video_path, progress, error_message FROM videos WHERE id = ?", (tid,))
                    row = cursor.fetchone()
                    
                    if row:
                        status = row["status"]
                        chat_id = active_bot_tasks[tid]
                        
                        if status == "completed":
                            video_fname = row["video_path"]
                            v_path = os.path.join(VIDEO_DIR, video_fname)
                            
                            if os.path.exists(v_path):
                                bot.send_message(chat_id, f"✅ Videonuz başarıyla oluşturuldu! (Görev #{tid})")
                                with open(v_path, 'rb') as video_file:
                                    bot.send_video(chat_id, video_file, caption="İşte videonuz! 🎬")
                            else:
                                bot.send_message(chat_id, f"⚠️ Video tamamlandı ancak dosya bulunamadı! (Görev #{tid})")
                                
                            del active_bot_tasks[tid]
                            
                        elif status == "failed":
                            err = row["error_message"]
                            bot.send_message(chat_id, f"❌ Video oluşturulurken hata oluştu! (Görev #{tid})\nHata: {err}")
                            del active_bot_tasks[tid]
                            
                conn.close()
        except Exception as e:
            print(f"Checker Thread Error: {e}")
            
        time.sleep(10) # 10 saniyede bir kontrol et

# Arka plan kontrolünü başlat
checker_thread = threading.Thread(target=background_task_checker, daemon=True)
checker_thread.start()


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "🤖 *AI Video Üretici Botuna Hoş Geldiniz!*\n\n"
        "Bana bir konu yazın ve sizin için yapay zeka ile hemen kısa bir video oluşturayım.\n\n"
        "Örnek: `Uzaylıların dünyayı ziyareti`"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    topic = message.text
    
    # Kullanıcı için yeni bir hedef oluştur
    user_states[chat_id] = get_default_settings()
    user_states[chat_id]["topic"] = topic
    
    send_options(chat_id)

def get_markup(settings):
    markup = InlineKeyboardMarkup()
    
    # Süre
    duration = settings["duration"]
    markup.row(InlineKeyboardButton(f"⏳ Süre: {duration}s", callback_data="opt_duration"))
    
    # Dil
    lang = settings["language"].upper()
    markup.row(InlineKeyboardButton(f"🌐 Dil: {lang}", callback_data="opt_language"))
    
    # Metin Yapay Zekası
    script_ai = settings["script_ai"]
    markup.row(InlineKeyboardButton(f"🧠 Yapay Zeka: {script_ai}", callback_data="opt_script_ai"))
    
    # Ses Motoru (AI)
    voice_ai = settings.get("voice_ai", "Edge-TTS")
    markup.row(InlineKeyboardButton(f"🎙️ Ses Motoru: {voice_ai}", callback_data="opt_voice_ai"))

    # Görsel AI
    image_ai = settings.get("image_ai", "Stock-Auto")
    markup.row(InlineKeyboardButton(f"🖼️ Görsel Kaynağı: {image_ai}", callback_data="opt_image_ai"))

    # Ses Tipi
    voice = settings["voice_type"].capitalize()
    markup.row(InlineKeyboardButton(f"🗣️ Ses Tipi: {voice}", callback_data="opt_voice"))
    
    # Altyazı
    subtitle = settings["subtitle_style"].capitalize()
    markup.row(InlineKeyboardButton(f"📝 Altyazı: {subtitle}", callback_data="opt_subtitle"))
    
    # Müzik
    bgm = "Açık" if settings["bgm_enabled"] else "Kapalı"
    markup.row(InlineKeyboardButton(f"🎵 Müzik: {bgm}", callback_data="opt_bgm"))
    
    # Oluştur Butonu
    markup.row(InlineKeyboardButton("🚀 VİDEOYU OLUŞTUR", callback_data="do_generate"))
    
    return markup

def send_options(chat_id):
    settings = user_states[chat_id]
    markup = get_markup(settings)
    
    text = (
        f"🎯 **Konu:** _{settings['topic']}_\n\n"
        "Lütfen aşağıdaki seçenekleri isteğinize göre düzenleyin veya varsayılan ayarlarla oluşturmayı başlatın:"
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if chat_id not in user_states:
        bot.answer_callback_query(call.id, "Lütfen tekrar bir konu yazın.")
        return
        
    action = call.data
    settings = user_states[chat_id]
    
    if action == "opt_duration":
        durations = [15, 30, 60]
        idx = durations.index(settings["duration"])
        settings["duration"] = durations[(idx + 1) % len(durations)]
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_markup(settings))
        bot.answer_callback_query(call.id)
        
    elif action == "opt_language":
        langs = ["tr", "en", "es"]
        idx = langs.index(settings["language"])
        settings["language"] = langs[(idx + 1) % len(langs)]
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_markup(settings))
        bot.answer_callback_query(call.id)
        
    elif action == "opt_voice":
        voices = ["erkek", "kadin"]
        idx = voices.index(settings["voice_type"])
        settings["voice_type"] = voices[(idx + 1) % len(voices)]
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_markup(settings))
        bot.answer_callback_query(call.id)
        
    elif action == "opt_subtitle":
        styles = ["tiktok", "youtube", "none"]
        idx = styles.index(settings["subtitle_style"])
        settings["subtitle_style"] = styles[(idx + 1) % len(styles)]
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_markup(settings))
        bot.answer_callback_query(call.id)
        
    elif action == "opt_script_ai":
        ais = ["Gemini", "OpenAI"]
        idx = ais.index(settings["script_ai"]) if settings["script_ai"] in ais else 0
        settings["script_ai"] = ais[(idx + 1) % len(ais)]
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_markup(settings))
        bot.answer_callback_query(call.id)
        
    elif action == "opt_voice_ai":
        ais = ["Edge-TTS", "ElevenLabs"]
        current = settings.get("voice_ai", "Edge-TTS")
        idx = ais.index(current) if current in ais else 0
        settings["voice_ai"] = ais[(idx + 1) % len(ais)]
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_markup(settings))
        bot.answer_callback_query(call.id)

    elif action == "opt_image_ai":
        ais = ["Stock-Auto", "Pollinations", "OpenAI", "Flux"]
        current = settings.get("image_ai", "Stock-Auto")
        idx = ais.index(current) if current in ais else 0
        settings["image_ai"] = ais[(idx + 1) % len(ais)]
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_markup(settings))
        bot.answer_callback_query(call.id)
        
    elif action == "opt_bgm":
        settings["bgm_enabled"] = not settings["bgm_enabled"]
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=get_markup(settings))
        bot.answer_callback_query(call.id)
        
    elif action == "do_generate":
        bot.edit_message_text(
            f"🎯 **Konu:** _{settings['topic']}_\n⏳ *Kuyruğa gönderiliyor...*",
            chat_id, 
            call.message.message_id, 
            parse_mode="Markdown"
        )
        
        # API Payload
        payload = {
            "topic": settings["topic"],
            "duration": settings["duration"],
            "language": settings["language"],
            "voice_ai": settings.get("voice_ai", "Edge-TTS"),
            "voice_type": settings["voice_type"],
            "subtitle_style": settings["subtitle_style"],
            "bgm_enabled": settings["bgm_enabled"],
            "script_ai": settings["script_ai"],
            "image_ai": settings["image_ai"]
        }
        
        try:
            response = requests.post(API_URL, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id")
                if task_id:
                    active_bot_tasks[task_id] = chat_id
                    bot.edit_message_text(
                        f"✅ *Videonuz üretim kuyruğuna eklendi! (Görev #{task_id})*\n\n"
                        "Video hazır olduğunda size doğrudan buradan göndereceğim. Lütfen bekleyin...",
                        chat_id,
                        call.message.message_id,
                        parse_mode="Markdown"
                    )
                else:
                    bot.send_message(chat_id, "Beklenmeyen hata: API task_id döndürmedi.")
            else:
                bot.send_message(chat_id, f"API Hatası! Kod: {response.status_code}\nUygulamanın (app.py) çalıştığından emin olun.")
        except Exception as e:
            bot.send_message(chat_id, f"Sunucuya bağlanılamadı. Hata: {str(e)}\n\nLütfen AI Video Bot sunucusunun çalıştığından emin olun.")

if __name__ == "__main__":
    print(" Telegram botu başarıyla başlatıldı ve dinlemeye alındı...")
    bot.polling(none_stop=True)
