import os
import re
import uuid
import requests
import yt_dlp


URL_REGEX = r"(https?://[^\s]+)"


# =========================================================
# SUPPORTED PLATFORMS
# =========================================================

def is_supported(url):
    url = url.lower()

    return any(
        platform in url
        for platform in [
            "instagram.com",
            "facebook.com",
            "fb.watch",
            "tiktok.com",
            "youtube.com",
            "youtu.be",
            "twitter.com",
            "x.com"
        ]
    )


# =========================================================
# COOKIE FILE
# =========================================================

def find_cookie_file():
    paths = []

    env_cookie = os.getenv(
        "YTDLP_COOKIES",
        ""
    ).strip()

    if env_cookie:
        paths.append(env_cookie)

    # Render Secret File
    paths.append(
        "/etc/secrets/cookies.txt"
    )

    # Project folder
    project_root = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )

    paths.append(
        os.path.join(
            project_root,
            "cookies.txt"
        )
    )

    # Current directory
    paths.append("cookies.txt")

    checked = set()

    for path in paths:

        if not path:
            continue

        path = os.path.abspath(path)

        if path in checked:
            continue

        checked.add(path)

        try:
            if (
                os.path.isfile(path)
                and os.path.getsize(path) > 0
            ):
                return path

        except Exception:
            pass

    return None


# =========================================================
# REMOTE FILE
# =========================================================

def save_remote_file(url, ext="mp4"):

    tmp_id = uuid.uuid4().hex[:10]

    path = (
        f"/tmp/{tmp_id}.{ext}"
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/139.0.0.0 "
            "Safari/537.36"
        ),
        "Referer": "https://www.instagram.com/"
    }

    response = requests.get(
        url,
        headers=headers,
        stream=True,
        timeout=45
    )

    response.raise_for_status()

    with open(path, "wb") as f:

        for chunk in response.iter_content(
            chunk_size=1024 * 64
        ):

            if chunk:
                f.write(chunk)

    return path


# =========================================================
# INSTAGRAM
# =========================================================

def download_instagram(url, client):

    try:

        print(
            f"📸 Instagram download: {url}",
            flush=True
        )

        match = re.search(
            r"instagram\.com/"
            r"(?:reel|reels|p|tv)/"
            r"([A-Za-z0-9_-]+)",
            url,
            re.I
        )

        if not match:
            print(
                "❌ Instagram shortcode not found",
                flush=True
            )
            return None

        code = match.group(1)

        try:
            pk = client.media_pk_from_code(
                code
            )

        except Exception:
            pk = client.media_pk_from_url(
                url
            )

        media = client.media_info(pk)

        video_url = getattr(
            media,
            "video_url",
            None
        )

        if not video_url:
            print(
                "❌ Instagram video URL পাওয়া যায়নি",
                flush=True
            )
            return None

        path = save_remote_file(
            video_url,
            "mp4"
        )

        print(
            f"✅ Instagram saved: {path}",
            flush=True
        )

        return path

    except Exception as e:

        print(
            f"❌ Instagram DL ERROR: {e}",
            flush=True
        )

        return None


# =========================================================
# YT-DLP
# =========================================================

def download_with_ytdlp(url):

    tmp_id = uuid.uuid4().hex[:10]

    output = (
        f"/tmp/{tmp_id}.%(ext)s"
    )

    ydl_opts = {
        "outtmpl": output,

        "format": (
            "best[height<=720][ext=mp4]"
            "/best[ext=mp4]"
            "/best"
        ),

        "quiet": True,
        "no_warnings": True,

        "noplaylist": True,

        "merge_output_format": "mp4",

        "max_filesize": (
            100 * 1024 * 1024
        ),

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
                    "web"
                ]
            }
        }
    }

    # -----------------------------------------------------
    # COOKIES
    # -----------------------------------------------------

    cookie_file = find_cookie_file()

    if cookie_file:

        ydl_opts["cookiefile"] = (
            cookie_file
        )

        print(
            f"🍪 yt-dlp cookies: {cookie_file}",
            flush=True
        )

    else:

        print(
            "⚠️ yt-dlp cookies file not found",
            flush=True
        )

    # -----------------------------------------------------
    # DOWNLOAD
    # -----------------------------------------------------

    try:

        fallback_clients = [
            ["android"],
            ["android", "web"],
            ["ios"],
        ]

        try:
            with yt_dlp.YoutubeDL(
                ydl_opts
            ) as ydl:

                ydl.download([url])

        except Exception as first_err:

            if "not available" not in str(first_err) and \
               "reloaded" not in str(first_err):
                raise

            last_err = first_err

            for clients in fallback_clients:

                print(
                    f"⚠️ Format fallback: trying {clients}",
                    flush=True
                )

                retry_opts = dict(ydl_opts)
                retry_opts["format"] = "best"
                retry_opts["extractor_args"] = {
                    "youtube": {
                        "player_client": clients
                    }
                }

                try:
                    with yt_dlp.YoutubeDL(
                        retry_opts
                    ) as ydl:

                        ydl.download([url])

                    last_err = None
                    break

                except Exception as retry_err:
                    last_err = retry_err
                    continue

            if last_err:
                raise last_err

        # Find downloaded file
        for filename in os.listdir(
            "/tmp"
        ):

            if filename.startswith(
                tmp_id + "."
            ):

                path = os.path.join(
                    "/tmp",
                    filename
                )

                if os.path.isfile(path):

                    print(
                        f"✅ Downloaded: {path}",
                        flush=True
                    )

                    return path

        print(
            "❌ Downloaded file পাওয়া যায়নি",
            flush=True
        )

        return None

    except Exception as e:

        print(
            f"❌ yt-dlp ERROR: {e}",
            flush=True
        )

        return None


# =========================================================
# MAIN DOWNLOAD
# =========================================================

def download_video(
    url,
    client=None
):

    url = (
        url
        .split("?")[0]
        .strip()
    )

    # Instagram
    if (
        "instagram.com"
        in url.lower()
        and client
    ):

        path = download_instagram(
            url,
            client
        )

        if path:
            return path

        print(
            "⚠️ Instagram client download failed",
            flush=True
        )

        return None

    # Other platforms
    return download_with_ytdlp(
        url
    )


# =========================================================
# AUTO DETECT
# =========================================================

def auto_detect(text):

    if not text:
        return None

    match = re.search(
        URL_REGEX,
        text
    )

    if not match:
        return None

    url = match.group(1)

    # Remove common trailing punctuation
    url = url.rstrip(
        ".,!?;:)]}"
    )

    if is_supported(url):
        return url

    return None


# =========================================================
# SEND DOWNLOAD
# =========================================================

def send_download(
    cl,
    thread_id,
    path
):

    if not path:

        return (
            "❌ Download failed! "
            "Private video hote pare!"
        )

    if not os.path.exists(path):

        return (
            "❌ Downloaded file পাওয়া যায়নি!"
        )

    try:

        size = os.path.getsize(
            path
        )

        if size > (
            90 * 1024 * 1024
        ):

            return (
                "❌ Video 90MB-এর বেশি, "
                "pathano jabena!"
            )

        cl.direct_send_video(
            path,
            thread_ids=[
                thread_id
            ]
        )

        print(
            f"✅ VIDEO SENT: {path}",
            flush=True
        )

        return None

    except Exception as e:

        print(
            f"❌ VIDEO SEND ERROR: {e}",
            flush=True
        )

        return (
            "❌ Video send failed!"
        )

    finally:

        try:
            os.remove(path)

        except Exception:
            pass


# =========================================================
# .DL COMMAND
# =========================================================

def dl_command(
    args,
    ctx
):

    if not args:

        return (
            "❌ Usage: .dl <link>"
        )

    text = (
        " ".join(args)
        if isinstance(args, list)
        else str(args)
    )

    match = re.search(
        URL_REGEX,
        text
    )

    if not match:

        return (
            "❌ Valid link de!"
        )

    url = match.group(1)

    url = url.rstrip(
        ".,!?;:)]}"
    )

    if not is_supported(url):

        return (
            "❌ Supported: "
            "Instagram / Facebook / TikTok / "
            "YouTube / Twitter"
        )

    cl = ctx.get(
        "client"
    )

    thread_id = ctx.get(
        "thread_id"
    )

    if not cl:

        return (
            "❌ Instagram client পাওয়া যায়নি!"
        )

    try:

        cl.direct_send(
            f"⏳ Downloading...\n🔗 {url}",
            thread_ids=[
                thread_id
            ]
        )

        path = download_video(
            url,
            client=cl
        )

        return send_download(
            cl,
            thread_id,
            path
        )

    except Exception as e:

        print(
            f"❌ DL COMMAND ERROR: {e}",
            flush=True
        )

        return (
            "❌ Download error!"
        )


# =========================================================
# COMMANDS
# =========================================================

DOWNLOADER_COMMANDS = {
    "dl": dl_command,
    "download": dl_command
        }
        
