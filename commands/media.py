import os, glob, uuid, shutil, yt_dlp
DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
PENDING_SEARCH = {}

def find_cookie_file():
    for path in [os.getenv("YTDLP_COOKIES"), "/etc/secrets/cookies.txt", "cookies.txt", os.path.join(os.getcwd(), "cookies.txt")]:
        if path and os.path.isfile(path):
            try:
                if path.startswith("/etc/secrets"):
                    tmp_path = "/tmp/cookies.txt"
                    shutil.copyfile(path, tmp_path)
                    return tmp_path
                return path
            except: return path
    return None

def get_youtube_search_results(song_name, limit=5):
    ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    cookie_file = find_cookie_file()
    if cookie_file: ydl_opts["cookiefile"] = cookie_file
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{song_name}", download=False)
            return [{"id": e.get("id"), "title": e.get("title")} for e in info.get("entries", [])]
    except Exception as e:
        print(f"SEARCH ERROR: {e}", flush=True)
        return []

def get_youtube_audio_by_url(video_id, video_title):
    job_id = uuid.uuid4().hex
    output_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": False,
        "retries": 10,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }
    cookie_file = find_cookie_file()
    if cookie_file: ydl_opts["cookiefile"] = cookie_file
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)
            files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*"))
            return (files[0], video_title) if files else (None, None)
    except Exception as e:
        print(f"AUDIO DOWNLOAD ERROR: {e}", flush=True)
        return None, None

def play(a, c):
    # user_id সঠিক ভাবে নাও
    if isinstance(c, dict):
        user_id = str(c.get("user_id", "default"))
    else:
        user_id = str(c) if c else "default"

    if not a:
        return "🎵 Usage:.play song name"

    text = " ".join(a).strip()
    #.play এর ভিতরে Number check করবো না, main.py করবে
    if text.isdigit():
        return None

    results = get_youtube_search_results(text, limit=5)
    if not results:
        return "❌ কোনো গান পাওয়া যায়নি!"

    PENDING_SEARCH[user_id] = results
    # main.py এর last_key trick এর জন্য
    if len(PENDING_SEARCH) > 10:
        PENDING_SEARCH.clear()
        PENDING_SEARCH[user_id] = results

    msg = f"🔍 **{text}** এর জন্য:\n\n"
    for i, r in enumerate(results, 1):
        t = r['title'][:55]
        msg += f"{i}. {t}\n"
    msg += "\n👉 Play করতে 1, 2, 3 লিখো!"
    return msg

MEDIA_COMMANDS = {"play": play, "song": play, "music": play}
