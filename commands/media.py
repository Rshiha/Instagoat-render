import os
import glob
import uuid
import shutil
import yt_dlp

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# User এর Search List মনে রাখার জন্য
PENDING_SEARCH = {}

def find_cookie_file():
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
                    return tmp_path
                return path
            except:
                return path
    return None

def get_youtube_search_results(song_name, limit=5):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    cookie_file = find_cookie_file()
    if cookie_file and os.path.exists(cookie_file):
        ydl_opts["cookiefile"] = cookie_file

    search_query = f"ytsearch{limit}:{song_name}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            results = []
            for entry in info.get("entries", []):
                results.append({
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "url": f"https://www.youtube.com/watch?v={entry.get('id')}"
                })
            return results
    except Exception as e:
        print(f"SEARCH ERROR: {e}", flush=True)
        return []

def get_youtube_audio_by_url(video_id, video_title):
    job_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "retries": 10,
        "extractor_args": {"youtube": {"player_client": ["android", "ios", "web"]}},
    }
    cookie_file = find_cookie_file()
    if cookie_file and os.path.exists(cookie_file):
        ydl_opts["cookiefile"] = cookie_file

    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*"))
            if not files:
                return None, None
            return files[0], video_title
    except Exception as e:
        print(f"AUDIO DOWNLOAD ERROR: {e}", flush=True)
        return None, None

def play(a, c):
    # c হলো user id বা chat id - তোমার bot এর main.py থেকে c আসে
    user_id = c if isinstance(c, str) else str(c) if c else "default"

    if not a:
        return "🎵 Usage:.play song name\nExample:.play Alvu"

    text = " ".join(a).strip()

    # যদি User 1,2,3 লিখে
    if text.isdigit():
        idx = int(text) - 1
        if user_id in PENDING_SEARCH:
            results = PENDING_SEARCH[user_id]
            if 0 <= idx < len(results):
                selected = results[idx]
                # List clear করে দাও
                del PENDING_SEARCH[user_id]
                file_path, title = get_youtube_audio_by_url(selected['id'], selected['title'])
                if not file_path:
                    return "❌ গানটি ডাউনলোড করা যায়নি।"
                def cleanup():
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                    except: pass
                return {"type": "audio", "path": file_path, "title": title, "cleanup": cleanup}
            else:
                return f"❌ 1 থেকে {len(results)} এর মধ্যে লিখো!"
        else:
            return "❌ আগে.play দিয়ে গান Search করো!"

    # নতুন Search
    results = get_youtube_search_results(text, limit=5)
    if not results:
        return "❌ কোনো গান পাওয়া যায়নি!"

    PENDING_SEARCH[user_id] = results

    msg = f"🔍 **{text}** এর জন্য পাওয়া গেছে:\n\n"
    for i, r in enumerate(results, 1):
        title = r['title'][:50] + "..." if len(r['title']) > 50 else r['title']
        msg += f"**{i}.** {title}\n"
    msg += "\n👉 গানটি Play করতে **1, 2, 3** লিখো!"
    return msg

MEDIA_COMMANDS = {
    "play": play,
    "song": play,
    "music": play,
        }
