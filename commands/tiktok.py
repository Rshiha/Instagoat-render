import requests, os, uuid, random

def tik_command(args, ctx):
    if not args:
        return "❌ Usage:.tik funny"
    query = " ".join(args).replace("-", "").strip() or "funny"
    cl = ctx.get("client")
    thread_id = ctx.get("thread_id")
    try:
        cl.direct_send(f"🎵 TikTok search: {query}...", thread_ids=[thread_id])
        r = requests.post("https://www.tikwm.com/api/feed/search", data={"keywords": query, "count": "20", "cursor": "0"}, headers={"User-Agent": "Mozilla/5.0"}, timeout=20).json()
        videos = r.get("data", {}).get("videos", [])
        if not videos:
            return f"❌ '{query}' video pailam na!"
        video = random.choice(videos)
        video_url = video.get("play")
        if not video_url: return "❌ Link pawa jay nai!"
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
        return "❌ TikTok failed!"

TIKTOK_COMMANDS = {"tik": tik_command, "tiktok": tik_command}