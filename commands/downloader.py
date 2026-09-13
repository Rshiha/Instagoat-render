import re, os, uuid, requests
import yt_dlp

URL_REGEX = r"(https?://[^\s]+)"

def is_supported(url):
    url = url.lower()
    return any(x in url for x in ["instagram.com","facebook.com","fb.watch","tiktok.com","youtube.com","youtu.be","twitter.com","x.com"])

def download_video(url, client=None):
    url = url.split('?')[0].strip()

    # 1. Instagram er jonno logged-in client use koro (429 fix)
    if "instagram.com" in url and client:
        try:
            print(f"Trying Insta via logged-in client: {url}", flush=True)
            pk = client.media_pk_from_url(url)
            info = client.media_info(pk)
            # video url ber koro
            dl_url = None
            if info.video_url:
                dl_url = info.video_url
            elif info.thumbnail_url:
                dl_url = info.thumbnail_url

            if dl_url:
                tmp_id = str(uuid.uuid4())[:8]
                ext = "mp4" if info.video_url else "jpg"
                path = f"/tmp/{tmp_id}.{ext}"
                r = requests.get(dl_url, stream=True, timeout=30)
                r.raise_for_status()
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                return path
        except Exception as e:
            print(f"Insta client DL failed: {e}", flush=True)
            # fallback to yt-dlp te jabe

    # 2. Baki sob + fallback er jonno yt-dlp
    tmp_id = str(uuid.uuid4())[:8]
    out_tmpl = f"/tmp/{tmp_id}.%(ext)s"
    ydl_opts = {
        'outtmpl': out_tmpl,
        'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'max_filesize': 100 * 1024 * 1024,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for f in os.listdir("/tmp"):
            if f.startswith(tmp_id):
                return os.path.join("/tmp", f)
        return None
    except Exception as e:
        print(f"DL Error: {e}", flush=True)
        return None

def auto_detect(text):
    if not text: return None
    m = re.search(URL_REGEX, text)
    if not m: return None
    url = m.group(1).split('?')[0]
    return url if is_supported(url) else None

def dl_command(args, ctx):
    if not args:
        return "❌ Usage:.dl <link>"
    text = " ".join(args) if isinstance(args, list) else str(args)
    m = re.search(URL_REGEX, text)
    if not m:
        return "❌ Valid link de!"
    url = m.group(1).split('?')[0]
    if not is_supported(url):
        return "❌ Supported: Insta / FB / TikTok / YT / Twitter"

    cl = ctx.get("client")
    thread_id = ctx.get("thread_id")
    try:
        cl.direct_send(f"⏳ Downloading...\n🔗 {url}", thread_ids=[thread_id])
        path = download_video(url, client=cl)
        if path and os.path.exists(path):
            if os.path.getsize(path) > 90*1024*1024:
                cl.direct_send("❌ 90MB+ besi!", thread_ids=[thread_id])
            else:
                cl.direct_send_file(path, thread_ids=[thread_id])
            try: os.remove(path)
            except: pass
            return None
        else:
            return "❌ Download failed! 429 / Private hote pare, arekbar try kor!"
    except Exception as e:
        return f"❌ Error: {e}"

DOWNLOADER_COMMANDS = {"dl": dl_command, "download": dl_command}
