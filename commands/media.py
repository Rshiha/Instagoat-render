import os
import glob
import uuid
import shutil
import yt_dlp

DOWNLOAD_DIR = "/tmp/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

PENDING_SEARCH = {}


# =========================================================
# COOKIES
# =========================================================

def find_cookie_file():
    paths = [
        os.getenv("YTDLP_COOKIES"),
        "/etc/secrets/cookies.txt",
        "cookies.txt",
        os.path.join(os.getcwd(), "cookies.txt"),
    ]

    for path in paths:
        if not path:
            continue

        try:
            if os.path.isfile(path):
                if os.path.getsize(path) <= 0:
                    continue

                if path.startswith("/etc/secrets"):
                    tmp_path = "/tmp/cookies.txt"

                    try:
                        shutil.copyfile(
                            path,
                            tmp_path
                        )
                        return tmp_path
                    except Exception:
                        return path

                return path

        except Exception:
            continue

    return None


# =========================================================
# YOUTUBE SEARCH
# =========================================================

def get_youtube_search_results(song_name, limit=5):

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "noplaylist": True,
    }

    cookie_file = find_cookie_file()

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

    try:
        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:

            info = ydl.extract_info(
                f"ytsearch{limit}:{song_name}",
                download=False
            )

            entries = info.get(
                "entries",
                []
            )

            results = []

            for entry in entries:
                if not entry:
                    continue

                video_id = entry.get("id")
                title = entry.get(
                    "title",
                    "Unknown"
                )

                if not video_id:
                    continue

                results.append({
                    "id": video_id,
                    "title": title
                })

            return results

    except Exception as e:

        print(
            f"SEARCH ERROR: {e}",
            flush=True
        )

        return []


# =========================================================
# DOWNLOAD AUDIO
# =========================================================

def get_youtube_audio_by_url(
    video_id,
    video_title
):

    job_id = uuid.uuid4().hex

    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{job_id}.%(ext)s"
    )

    ydl_opts = {
        "format": (
            "bestaudio[ext=m4a]"
            "/bestaudio"
            "/best"
        ),

        "outtmpl": output_template,

        "noplaylist": True,

        "quiet": True,
        "no_warnings": True,

        "retries": 5,

        "fragment_retries": 5,

        "socket_timeout": 30,

        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/139.0.0.0 "
                "Safari/537.36"
            )
        },

        "extractor_args": {
            "youtube": {
                "player_client": [
                    "android",
                    "ios",
                    "web",
                    "tv"
                ]
            }
        },

        "ignoreerrors": False
    }

    cookie_file = find_cookie_file()

    if cookie_file:
        ydl_opts["cookiefile"] = cookie_file

        print(
            f"🍪 Music cookies: {cookie_file}",
            flush=True
        )

    url = (
        "https://www.youtube.com/watch?v="
        + str(video_id)
    )

    try:

        print(
            f"🎵 Downloading: {video_title}",
            flush=True
        )

        try:
            with yt_dlp.YoutubeDL(
                ydl_opts
            ) as ydl:

                ydl.extract_info(
                    url,
                    download=True
                )

        except Exception as first_err:

            if "Requested format is not available" in str(first_err):

                print(
                    "⚠️ Format fallback: trying 'best'",
                    flush=True
                )

                retry_opts = dict(ydl_opts)
                retry_opts["format"] = "best"

                with yt_dlp.YoutubeDL(
                    retry_opts
                ) as ydl:

                    ydl.extract_info(
                        url,
                        download=True
                    )

            else:
                raise

        files = glob.glob(
            os.path.join(
                DOWNLOAD_DIR,
                f"{job_id}.*"
            )
        )

        files = [
            f for f in files
            if os.path.isfile(f)
        ]

        if not files:
            print(
                "❌ Audio file পাওয়া যায়নি",
                flush=True
            )

            return None, None

        path = files[0]

        print(
            f"✅ AUDIO READY: {path}",
            flush=True
        )

        return path, video_title

    except Exception as e:

        print(
            f"AUDIO DOWNLOAD ERROR: {e}",
            flush=True
        )

        return None, None


# =========================================================
# PLAY / SONG / MUSIC
# =========================================================

def play(a, c):

    if isinstance(c, dict):
        user_id = str(
            c.get(
                "user_id",
                "default"
            )
        )
    else:
        user_id = str(
            c or "default"
        )

    if not a:
        return (
            "🎵 Usage:\n"
            ".play song name"
        )

    text = (
        " ".join(a)
        .strip()
    )

    # Number selection is handled separately
    # by select_song()
    if text.isdigit():
        return None

    results = get_youtube_search_results(
        text,
        limit=5
    )

    if not results:
        return (
            "❌ কোনো গান পাওয়া যায়নি!"
        )

    PENDING_SEARCH[user_id] = results

    # Keep memory small
    if len(PENDING_SEARCH) > 50:

        first_key = next(
            iter(PENDING_SEARCH)
        )

        if first_key != user_id:
            PENDING_SEARCH.pop(
                first_key,
                None
            )

    msg = (
        f"🔍 {text} এর জন্য গান পাওয়া গেছে:\n\n"
    )

    for i, result in enumerate(
        results,
        1
    ):

        title = str(
            result.get(
                "title",
                "Unknown"
            )
        )

        title = title[:70]

        msg += (
            f"{i}. 🎵 {title}\n"
        )

    msg += (
        "\n👉 গান চালাতে "
        "1, 2, 3, 4 অথবা 5 লিখো।"
    )

    return msg


# =========================================================
# SELECT SONG
# =========================================================

def select_song(number, c):

    if isinstance(c, dict):
        user_id = str(
            c.get(
                "user_id",
                "default"
            )
        )
    else:
        user_id = str(
            c or "default"
        )

    try:
        number = int(number)
    except Exception:
        return None

    results = PENDING_SEARCH.get(
        user_id
    )

    if not results:
        return (
            "❌ কোনো pending song নেই!\n"
            "আগে `.song গানের নাম` লিখো।"
        )

    index = number - 1

    if index < 0 or index >= len(results):
        return (
            f"❌ শুধু 1-{len(results)} এর মধ্যে "
            "একটা number দাও।"
        )

    selected = results[index]

    video_id = selected.get("id")
    title = selected.get(
        "title",
        "Unknown"
    )

    if not video_id:
        return (
            "❌ এই গানটির YouTube ID পাওয়া যায়নি!"
        )

    # Remove pending result immediately
    # so repeated "1" does not download twice
    PENDING_SEARCH.pop(
        user_id,
        None
    )

    return {
        "type": "audio",
        "video_id": video_id,
        "title": title
    }


# =========================================================
# DOWNLOAD SELECTED SONG
# =========================================================

def download_selected_song(
    result
):

    if not isinstance(
        result,
        dict
    ):
        return None

    if result.get("type") != "audio":
        return result

    video_id = result.get(
        "video_id"
    )

    title = result.get(
        "title",
        "Unknown"
    )

    if not video_id:
        return (
            "❌ Song ID missing!"
        )

    path, real_title = (
        get_youtube_audio_by_url(
            video_id,
            title
        )
    )

    if not path:
        return (
            "❌ গান download করা যায়নি!"
        )

    return {
        "type": "audio",
        "path": path,
        "title": real_title or title,
        "cleanup": (
            lambda: safe_remove(path)
        )
    }


# =========================================================
# CLEANUP
# =========================================================

def safe_remove(path):

    if not path:
        return

    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# =========================================================
# COMMANDS
# =========================================================

MEDIA_COMMANDS = {
    "play": play,
    "song": play,
    "music": play,
        }
    
