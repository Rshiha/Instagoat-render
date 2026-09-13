import re, os, uuid
import yt_dlp

URL_REGEX = r"(https?://[^\s]+)"

def is_supported(url):
    url = url.lower()
    return any(x in url for x in [
        "instagram.com", "facebook.com", "fb.watch",
        "tiktok.com", "youtube.com", "youtu.be",
        "twitter.com", "x.com"
    ])

def download_video(url):
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
    url = m.group(1)
    return url if is_supported(url) else None

def dl_command(args, ctx):
    if not args:
        return "❌ Usage:.dl <link>\nEx:.dl https://www.instagram.com/reel/..."

    text = " ".join(args) if isinstance(args, list) else str(args)
    m = re.search(URL_REGEX, text)
    if not m:
        return "❌ Valid link de!"

    url = m.group(1)
    if not is_supported(url):
        return "❌ Supported: Insta / FB / TikTok / YT / Twitter"

    cl = ctx.get("client")
    thread_id = ctx.get("thread_id")

    try:
        cl.direct_send(f"⏳ Downloading...\n🔗 {url}", thread_ids=[thread_id])
        path = download_video(url)

        if path and os.path.exists(path):
            if os.path.getsize(path) > 90*1024*1024:
                cl.direct_send("❌ 90MB+ besi, Insta te pathano jabena!", thread_ids=[thread_id])
            else:
                cl.direct_send_file(path, thread_ids=[thread_id])
            try: os.remove(path)
            except: pass
            return None
        else:
            return "❌ Download failed! Private link hote pare!"
    except Exception as e:
        return f"❌ Error: {e}"

DOWNLOADER_COMMANDS = {
    "dl": dl_command,
    "download": dl_command
}
