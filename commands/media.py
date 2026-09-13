import os
import glob
import uuid
import shutil
import tempfile
import yt_dlp

# Render এর জন্য /tmp use করো
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def find_cookie_file():
    """Render Secret Files are available under /etc/secrets/<filename>. কিন্তু ওটা Read-only, তাই /tmp এ copy করতে হবে"""
    candidates = []
    env_cookie = os.getenv("YTDLP_COOKIES")
    if env_cookie:
        candidates.append(env_cookie)
    candidates.extend([
        "/etc/secrets/cookies.txt",
        os.path.join(os.getcwd(), "cookies.txt"),
    ])
    for path in candidates:
        if path and os.path.isfile(path):
            try:
                if path.startswith("/etc/secrets"):
                    tmp_path = "/tmp/cookies.txt"
                    shutil.copyfile(path, tmp_path)
                    print(f"🍪 yt-dlp cookies: enabled (copied)", flush=True)
                    return tmp_path
                print(f"🍪 yt-dlp cookies: enabled ({path})", flush=True)
                return path
            except Exception as e:
                print(f"Cookie copy failed: {e}", flush=True)
                return path
    print("🍪 yt-dlp cookies: not found; trying without cookies", flush=True)
    return None

def get_youtube_audio(song_name):
    if not song_name:
        return None, None

    job_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")

    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        },
    }

    cookie_file = find_cookie_file()
    if cookie_file and os.path.exists(cookie_file):
        ydl_opts["cookiefile"] = cookie_file

    search_query = f"ytsearch1:{song_name}"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if not info:
                return None, None
            if "entries" in info:
                entries = info.get("entries") or []
                if not entries:
                    return None, None
                info = entries[0]
            title = info.get("title") or song_name
            files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*"))
            if not files:
                return None, None
            return files[0], title
    except Exception as e:
        for path in glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*")):
            try:
                os.remove(path)
            except OSError:
                pass
        print(f"AUDIO DOWNLOAD ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None, None

def play(a, c):
    if not a:
        return "🎵 Usage:.play song name"
    song_name = " ".join(a).strip()
    file_path, title = get_youtube_audio(song_name)
    if not file_path:
        return "❌ গানটি ডাউনলোড করা যায়নি। কিছুক্ষণ পরে আবার চেষ্টা করুন।"
    def cleanup():
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError:
            pass
    return {
        "type": "audio",
        "path": file_path,
        "title": title,
        "cleanup": cleanup,
    }

MEDIA_COMMANDS = {
    "play": play,
    "song": play,
    "music": play,
        }
