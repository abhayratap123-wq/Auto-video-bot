import os
import time
import requests
import urllib.parse
import subprocess
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse

app = FastAPI(title="Auto Media API")

# --- FILE CLEANUP SYSTEM (स्टोरेज फुल होने से बचाने के लिए) ---
def cleanup_files(files):
    for file in files:
        if os.path.exists(file):
            try:
                os.remove(file)
            except:
                pass

# ==========================================
# 1. IMAGE API (Normal, Pro, VIP Modes)
# URL Format: /vimg?mode=vip&prompt=hacker cat
# ==========================================
@app.get("/vimg")
def generate_image(mode: str = "normal", prompt: str = ""):
    if not prompt:
        return {"error": "Prompt is required!"}
    
    # Modes (High Quality Filters)
    mode = mode.lower()
    if mode == "pro":
        final_prompt = prompt + ", highly detailed, cinematic lighting, 4k, professional photography"
    elif mode == "vip":
        final_prompt = prompt + ", masterpiece, unreal engine 5 render, award winning, hyperrealistic, 8k resolution"
    else:
        final_prompt = prompt # Normal Mode
        
    safe_prompt = urllib.parse.quote(final_prompt)
    img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1080&height=1920&nologo=true"
    
    # इमेज को डाउनलोड करने की जगह डायरेक्ट यूज़र को रीडायरेक्ट कर देंगे (सबसे फास्ट)
    return RedirectResponse(url=img_url)

# ==========================================
# 2. VIDEO API (Custom Seconds limit)
# URL Format: /video?scand=15&prompt=hello world
# ==========================================
@app.get("/video")
def generate_video(background_tasks: BackgroundTasks, scand: int = 10, prompt: str = ""):
    if not prompt:
        return {"error": "Prompt is required!"}
    
    # 150 सेकंड की लिमिट सेट करना
    if scand > 150:
        scand = 150
        
    # Unique ID ताकि एक साथ 10 लोग रिक्वेस्ट करें तो मिक्स न हो
    uid = str(int(time.time()))
    img_path = f"/tmp/img_{uid}.jpg"
    aud_path = f"/tmp/aud_{uid}.mp3"
    vid_path = f"/tmp/vid_{uid}.mp4"
    
    try:
        # A. Download High Quality Image (VIP style by default for videos)
        vip_prompt = prompt + ", cinematic, highly detailed, 8k"
        img_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(vip_prompt)}?width=1080&height=1920&nologo=true"
        img_data = requests.get(img_url).content
        with open(img_path, 'wb') as f:
            f.write(img_data)
            
        # B. Generate Voice (USA Accent)
        subprocess.run(["edge-tts", "--voice", "en-US-ChristopherNeural", "--text", prompt, "--write-media", aud_path])
        
        # C. Generate Video via FFmpeg (Super Fast)
        # -stream_loop -1 का मतलब है अगर ऑडियो छोटा है, तो वीडियो की लंबाई (scand) तक ऑडियो लूप होता रहेगा
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_path,         # Image input
            "-stream_loop", "-1", "-i", aud_path, # Audio input (looped if short)
            "-c:v", "libx264", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(scand),                     # Max time set by user
            "-pix_fmt", "yuv420p",
            "-shortest",                          # Safety
            vid_path
        ]
        
        subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # D. Delete raw files immediately, keep only video
        cleanup_files([img_path, aud_path])
        
        # E. Send Video to user, and tell server to DELETE video AFTER sending
        background_tasks.add_task(cleanup_files, [vid_path])
        
        return FileResponse(vid_path, media_type="video/mp4", filename="AutoVideo.mp4")
        
    except Exception as e:
        cleanup_files([img_path, aud_path, vid_path])
        return {"error": str(e)}

