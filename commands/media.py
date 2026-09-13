import os
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlparse

import requests


# =========================================================
# CONFIG
# =========================================================

DOWNLOAD_DIR = os.path.join(
    tempfile.gettempdir(),
    "instagoat_audio"
)

os.makedirs(
    DOWNLOAD_DIR,
    exist_ok=True
)


# =========================================================
# CLEAN FILENAME
# =========================================================

def clean_filename(name):

    name = re.sub(
        r'[\\/:*?"<>|]+',
        "_",
        name
    )

    name = name.strip()

    if not name:
        name = "audio"

    return name[:100]


# =========================================================
# DOWNLOAD AUDIO
# =========================================================

def download_audio(query):

    """
    Downloads audio using yt-dlp.

    Works with a search query such as:
        .play Tere Liye Atif Aslam

    or a supported URL.

    Use only content you are allowed to download.
    """

    output_template = os.path.join(
        DOWNLOAD_DIR,
        "%(title)s.%(ext)s"
    )

    # -----------------------------------------------------
    # Search or URL
    # -----------------------------------------------------

    if (
        query.startswith("http://")
        or query.startswith("https://")
    ):

        source = query

    else:

        source = (
            "ytsearch1:"
            + query
        )


    # -----------------------------------------------------
    # yt-dlp
    # -----------------------------------------------------

    command = [
        "yt-dlp",

        "--no-playlist",

        "--no-warnings",

        "--quiet",

        "--restrict-filenames",

        "-x",

        "--audio-format",
        "mp3",

        "--audio-quality",
        "128K",

        "-o",
        output_template,

        source
    ]


    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120
        )


    except FileNotFoundError:

        raise RuntimeError(
            "yt-dlp is not installed."
        )


    except subprocess.TimeoutExpired:

        raise RuntimeError(
            "Download timeout."
        )


    # -----------------------------------------------------
    # Error
    # -----------------------------------------------------

    if result.returncode != 0:

        error = (
            result.stderr
            or result.stdout
            or "Unknown yt-dlp error"
        )

        print(
            f"❌ YT-DLP ERROR: {error}",
            flush=True
        )

        raise RuntimeError(
            "Song download failed."
        )


    # -----------------------------------------------------
    # Find MP3
    # -----------------------------------------------------

    files = []

    try:

        for filename in os.listdir(
            DOWNLOAD_DIR
        ):

            path = os.path.join(
                DOWNLOAD_DIR,
                filename
            )

            if (
                os.path.isfile(path)
                and filename.lower().endswith(
                    ".mp3"
                )
            ):

                files.append(path)

    except Exception:

        pass


    if not files:

        raise RuntimeError(
            "MP3 file was not created."
        )


    # Newest file
    files.sort(
        key=os.path.getmtime,
        reverse=True
    )

    return files[0]


# =========================================================
# GET TITLE
# =========================================================

def get_title(path):

    try:

        name = os.path.basename(
            path
        )

        if name.lower().endswith(
            ".mp3"
        ):

            name = name[:-4]

        return name.replace(
            "_",
            " "
        )

    except Exception:

        return "Audio"


# =========================================================
# CLEANUP
# =========================================================

def cleanup_file(path):

    try:

        if path and os.path.exists(
            path
        ):

            os.remove(
                path
            )

    except Exception as e:

        print(
            f"⚠️ FILE CLEANUP ERROR: {e}",
            flush=True
        )


# =========================================================
# PLAY
# =========================================================

def play(args, ctx):

    if not args:

        return (
            "🎵 MUSIC PLAYER\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Usage:\n"
            ".play song name\n\n"
            "Example:\n"
            ".play Tere Liye Atif Aslam"
        )


    query = " ".join(args).strip()


    if not query:

        return (
            "❌ Please enter a song name."
        )


    print(
        f"🎵 Downloading: {query}",
        flush=True
    )


    try:

        path = download_audio(
            query
        )

        title = get_title(
            path
        )


        print(
            f"✅ Audio downloaded: "
            f"{path}",
            flush=True
        )


        # -------------------------------------------------
        # Main.py will handle the actual send
        # -------------------------------------------------

        return {

            "type": "audio",

            "path": path,

            "title": title,

            "cleanup": lambda:
                cleanup_file(path)
        }


    except Exception as e:

        print(
            f"❌ PLAY ERROR: {e}",
            flush=True
        )


        return (
            "❌ গানটি download করা যায়নি.\n\n"
            f"🎵 Requested: {query}\n"
            "⚠️ অন্য গান বা supported URL দিয়ে চেষ্টা করো."
        )


# =========================================================
# SONG
# =========================================================

def song(args, ctx):

    return play(
        args,
        ctx
    )


# =========================================================
# MUSIC
# =========================================================

def music(args, ctx):

    return play(
        args,
        ctx
    )


# =========================================================
# COMMANDS
# =========================================================

MEDIA_COMMANDS = {

    "play": play,

    "song": song,

    "music": music
    }
