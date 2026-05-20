# 🎬 AI Video Bot — Enterprise CLI Automation Manual

Welcome to the **AI Video Bot CLI Manual**. This comprehensive guide details how to leverage the CLI interface (`main.py`) to completely automate video production queues, schedule automated creation pipelines, run batch generation scripts, and integration scenarios.

---

## 🚀 1. CLI Usage & Core Syntax

To run the bot in CLI mode, launch `main.py` using Python from the root directory:
```bash
python main.py [arguments]
```
> [!TIP]
> If you execute `python main.py` **without any arguments**, the CLI gracefully falls back to a user-friendly interactive terminal mode!

---

## 📊 2. Argument Specifications & Parameters

| Flag | Long Flag | Type | Allowed Values | Default | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `-t` | `--topic` | `string` | Any topic description | `None` | Topic for script generation. |
| `-cs` | `--custom-script` | `string` | Text string or file path | `None` | Pre-written script or file path. |
| `-d` | `--duration` | `int` | `15` to `300` | `30` | Target video duration in seconds. |
| `-l` | `--language` | `string` | `tr`, `en`, `es` | `tr` | Language for narration & voice. |
| `-q` | `--quality` | `string` | `low`, `medium`, `high` | `medium` | Overall video quality rendering level. |
| `-ar` | `--aspect-ratio` | `string` | `9:16`, `16:9`, `1:1` | `9:16` | Resolution ratio. |
| `-sa` | `--script-ai` | `string` | `Gemini`, `OpenAI` | `Gemini` | Script generator engine. |
| `-va` | `--voice-ai` | `string` | `Edge-TTS`, `ElevenLabs` | `Edge-TTS` | Voice synthesis engine. |
| `-vt` | `--voice-type` | `string` | `erkek`, `kadin` | `erkek` | Voice gender model. |
| `-ia` | `--image-ai` | `string` | `Stock-Auto`, `Pollinations`, `OpenAI`, `Flux`, `SDXL`, `Pexels`, `Pixabay`, `Unsplash` | `Pollinations` | Visual asset model. |
| `-ap` | `--animation-provider` | `string` | `none`, `stability_ai`, `runway`, `replicate`, `luma` | `none` | Image-to-video animation model. |
| `-ss` | `--subtitle-style` | `string` | `tiktok`, `classic`, `minimal` | `tiktok` | Subtitle design preset. |
| `-sd` | `--subtitle-delay` | `float` | `0.1` to `3.0` | `0.75` | Subtitle pacing delay multiplier. |
| `-vm` | `--video-mode` | `string` | `slideshow`, `zoom_motion` | `slideshow` | Movement and zoom transition. |
| `-tr` | `--transition` | `string` | `none`, `fade`, `crossfade`, `zoom`, `spin`, `glitch`, `auto` | `none` | Scene transitions. |
| `--bgm` | *Flag* | *None* | Switch | `False` | Enable background music matching tone. |
| `--bgm-tone` | `string` | `dramatic`, `epic`, `happy`, `energetic`, `auto` | `auto` | BGM emotional tone select. |
| `-sp` | `--sentence-pause` | `float` | `0.0` to `2.5` | `0.0` | Brief silence delay between sentences. |
| `--watermark` | *Flag* | *None* | Switch | `False` | Apply default watermark overlay. |
| `-cg` | `--color-grade` | `string` | `none`, `auto_enhance`, `warm`, `cool`, `vintage`, `cinematic` | `auto_enhance` | Color filter adjustment. |
| `--letterbox` | *Flag* | *None* | Switch | `False` | Cinematic black borders. |
| `--light-leak` | *Flag* | *None* | Switch | `False` | Organic light leak film overlays. |
| `--no-thumbnail` | *Flag* | *None* | Switch | `False` | Disable automatic thumbnail output. |
| `-o` | `--output` | `string` | Custom path (e.g. `exports/v.mp4`) | `None` | Output file destination path. |

---

## 💡 3. Quick-Start Production Examples

### 📱 TikTok / YouTube Shorts (Default Portrait)
Produce a quick 30-second Energetic TikTok video on Roman Gladiator Facts:
```bash
python main.py -t "Unbelievable Roman Gladiator Facts" -d 30 -l en -q high --bgm --bgm-tone energetic --watermark
```

### 🎬 YouTube Long-Form (Landscape Cinematic)
Produce a 2-minute landscape history documentary on the Renaissance, using zoom motion and custom black letterbox bars:
```bash
python main.py -t "The Hidden Genius of Renaissance Art" -d 120 -ar 16:9 -vm zoom_motion -tr crossfade --letterbox --light-leak -o exports/renaissance_doc.mp4
```

### 🧠 Pre-written Custom Script Video
If you want to feed your own exact script (avoiding LLM generation for the text) and generate professional visuals, voices and subtitles:
```bash
python main.py -cs "scripts/my_amazing_text.txt" -d 45 -l tr --bgm -o exports/my_custom_narration.mp4
```

---

## ⚙️ 4. Advanced Automation & Developer Shell Recipes

Since the CLI operates entirely inside a single Python thread with parallel queues, it is extremely easy to wrap inside automation shell scripts, cron scheduling engines, and automated microservices.

### Recipe A: Batch Production from Text File
If you have a file containing a list of topics (`topics.txt`), create a bash script (`batch_generator.sh`) to process each line sequentially:

```bash
#!/bin/bash
# batch_generator.sh

TOPIC_FILE="topics.txt"

if [ ! -f "$TOPIC_FILE" ]; then
    echo "[-] Error: $TOPIC_FILE not found!"
    exit 1
fi

echo "[+] Starting Batch AI Video Production queue..."
while IFS= read -r topic || [ -n "$topic" ]; do
    # Skip empty lines and comment lines
    [[ -z "$topic" || "$topic" =~ ^# ]] && continue
    
    echo "=========================================================="
    echo "🚀 Processing Topic: $topic"
    echo "=========================================================="
    
    python main.py -t "$topic" -d 30 -l en --bgm --watermark
    
    echo "[+] Done processing: $topic"
    sleep 5 # Cool-down period to avoid API rate-limiting
done < "$TOPIC_FILE"

echo "[🎉] Batch video generation completed successfully!"
```

### Recipe B: Scheduling with Cron Jobs
You can program your Linux server or developer machine to automatically create a daily viral Shorts video at 9:00 AM every day.

Open the cron manager:
```bash
crontab -e
```

Add the following cron expression (loads variables, executes `main.py` with a random or selected topic, and saves logs):
```cron
0 9 * * * cd /home/sedat/Masaüstü/Projeler/scratch/ai-video-bot && ./venv/bin/python main.py -t "Mind-bending Science Fact of the Day" -d 35 -l en --bgm > logs/cron_daily.log 2>&1
```

---

## 🏆 5. Features Built-in CLI Parallelism
Your CLI is fully integrated with our premium performance optimizers:
*   **Parallel Stock Videos:** Sourcing stock media from Pexels & Pixabay simultaneously under ThreadPools.
*   **Parallel Visual Generation:** Fetching multiple AI visuals simultaneously rather than serial processing.
*   **Automatic Clickbait Cover Thumbnail:** Generates a stunning `.jpg` cover alongside your video using a system-level font and dynamic golden highlights.
