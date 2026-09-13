import os
import re
import yt_dlp


def clean_filename(name):
    name = re.sub(r'[\\/:*?"<>|]+', '', str(name))
    return name.strip()[:150] or "audio"


def get_saavn_audio(song_name):
    os.makedirs("downloads", exist_ok=True)

    output_base = os.path.join("downloads", "%(title)s.%(ext)s")

    options = {
        "format": "bestaudio/best",
        "outtmpl": output_base,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch1",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)

            if not info:
                return None, None

            if "entries" in info:
                entries = info.get("entries") or []
                if not entries:
                    return None, None
                info = entries[0]

            title = info.get("title") or song_name
            original_ext = info.get("ext", "webm")
            source_path = ydl.prepare_filename(info)
            mp3_path = os.path.splitext(source_path)[0] + ".mp3"

            if not os.path.exists(mp3_path):
                safe_title = clean_filename(title)
                mp3_path = os.path.join("downloads", safe_title + ".mp3")

            if os.path.exists(mp3_path):
                return mp3_path, title

            return None, None

    except Exception as e:
        print(f"AUDIO DOWNLOAD ERROR: {e}", flush=True)
        return None, None


def play(a, c):
    if not a:
        return "🎵 Usage: .play song name"

    song_name = " ".join(a).strip()

    try:
        file_path, title = get_saavn_audio(song_name)

        if not file_path:
            return "❌ গানটি ডাউনলোড করা যায়নি। অন্য নাম দিয়ে চেষ্টা করুন।"

    except Exception as e:
        print(f"AUDIO DOWNLOAD ERROR: {e}", flush=True)
        return "❌ গান ডাউনলোড করতে সমস্যা হয়েছে।"

    return {
        "type": "audio",
        "path": file_path,
        "title": title,
        "cleanup": lambda: (
            os.remove(file_path)
            if os.path.exists(file_path)
            else None
        ),
    }


MEDIA_COMMANDS = {
    "play": play,
    "song": play,
    "music": play,
}
