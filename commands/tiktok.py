import requests, os, uuid, random

def tik_command(args, ctx):
    if not args:
        return "❌ Usage: .tik funny"
    
    full_string = " ".join(args)
    # চ্যাটের অতিরিক্ত টেক্সট (যেমন: "- TikTok video") ছেঁটে ফেলা
    if " - " in full_string:
        query = full_string.split(" - ")[0].strip()
    else:
        query = full_string.replace("-", "").strip()
        
    if not query:
        query = "funny"
    
    cl = ctx.get("client")
    thread_id = ctx.get("thread_id")
    
    try:
        cl.direct_send(f"🎵 TikTok search: {query}...", thread_ids=[thread_id])
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        
        url = "https://tikwm.com"
        data = {"keywords": query, "count": "10", "cursor": "0"}
        
        response = requests.post(url, data=data, headers=headers, timeout=20)
        
        if response.status_code != 200:
            return f"❌ TikTok API Blocked (Status: {response.status_code})"
            
        r = response.json()
        videos = r.get("data", {}).get("videos", [])
        
        if not videos:
            return f"❌ '{query}' video pailam na!"
            
        video = random.choice(videos)
        video_url = video.get("play") or video.get("hdplay")
        
        if not video_url: 
            return "❌ Link pawa jay nai!"
            
        tmp = f"/tmp/{uuid.uuid4().hex[:8]}.mp4"
        with requests.get(video_url, stream=True, timeout=30) as resp:
            with open(tmp, "wb") as f:
                for c in resp.iter_content(1024*64):
                    if c: f.write(c)
                    
        cl.direct_send_video(tmp, thread_ids=[thread_id])
        
        try: os.remove(tmp)
        except: pass
        
        return f"✅ Done: {query}"
        
    except Exception as e:
        print(f"TIK ERROR {e}")
        return f"❌ TikTok failed!"

TIKTOK_COMMANDS = {"tik": tik_command, "tiktok": tik_command}
