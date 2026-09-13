import os
import glob
import uuid
import yt_dlp

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def find_cookie_file():
    """
    Render Secret Files are available under /etc/secrets/<filename>.
    Local fallback: ./cookies.txt
    Optional override: YTDLP_COOKIES=/path/to/cookies.txt
    """
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
            return path

    return None


def get_youtube_audio(song_name):
    if not song_name:
        return None, None

    job_id = uuid.uuid4().hex
    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{job_id}.%(ext)s"
    )

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "extractor_args": {
            "youtube": {
                "player_client": ["web"]
            }
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    cookie_file = find_cookie_file()
    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file
        print("🍪 yt-dlp cookies: enabled", flush=True)
    else:
        print("🍪 yt-dlp cookies: not found; trying without cookies", flush=True)

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

        # FFmpeg creates the final MP3 after yt-dlp finishes.
        mp3_files = glob.glob(
            os.path.join(DOWNLOAD_DIR, f"{job_id}.mp3")
        )

        if not mp3_files:
            # Fallback: find any file created for this job.
            files = glob.glob(
                os.path.join(DOWNLOAD_DIR, f"{job_id}.*")
            )
            if not files:
                return None, None
            return files[0], title

        return mp3_files[0], title

    except Exception as e:
        # Clean up partial files.
        for path in glob.glob(
            os.path.join(DOWNLOAD_DIR, f"{job_id}.*")
        ):
            try:
                os.remove(path)
            except OSError:
                pass

        print(f"AUDIO DOWNLOAD ERROR: {e}", flush=True)
        return None, None


def play(a, c):
    if not a:
        return "🎵 Usage: .play song name"

    song_name = " ".join(a).strip()

    try:
        file_path, title = get_youtube_audio(song_name)

        if not file_path:
            return (
                "❌ গানটি ডাউনলোড করা যায়নি। "
                "কিছুক্ষণ পরে আবার চেষ্টা করুন।"
            )

    except Exception as e:
        print(f"AUDIO DOWNLOAD ERROR: {e}", flush=True)
        return "❌ গান ডাউনলোড করতে সমস্যা হয়েছে।"

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
