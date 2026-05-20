import os
import shutil

src_dir = "/home/sedat/.gemini/antigravity/brain/b0c92e68-2cf1-4c7a-9e68-4a3ea08aaf8a"
dest_dir = "/home/sedat/Masaüstü/Projeler/scratch/sedatorman.me/assets"

os.makedirs(dest_dir, exist_ok=True)

try:
    shutil.copy(os.path.join(src_dir, "scorpion_online_cover_1779234448587.png"), os.path.join(dest_dir, "scorpion_online.png"))
    shutil.copy(os.path.join(src_dir, "ai_video_bot_cover_1779234467511.png"), os.path.join(dest_dir, "ai_video_bot.png"))
    shutil.copy(os.path.join(src_dir, "nedir_me_cover_1779234487379.png"), os.path.join(dest_dir, "nedir_me.png"))
    print("Assets copied successfully!")
except Exception as e:
    print(f"Error copying assets: {e}")
