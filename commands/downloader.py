import re
import os
import uuid
import requests
import yt_dlp


URL_REGEX = r"(https?://[^\s]+)"


def is_supported(url):
    url = url.lower()

    return any(
        x in url
        for x in [
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


def save_remote_file(url, ext):
    tmp_id = uuid.uuid4().hex[:8]
    path = f"/tmp/{tmp_id}.{ext}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/139.0.0.0 Safari/537.36"
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


def download_instagram(url, client):
    try:
        print(
            f"📸 Instagram client download: {url}",
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

        media = client.media_info(
            pk
        )

        video_url = getattr(
            media,
            "video_url",
            None
        )

        # NEVER use thumbnail as video.
        if not video_url:
            print(
                "❌ No Instagram video_url",
                flush=True
            )
            return None

        path = save_remote_file(
            video_url,
            "mp4"
        )

        print(
            f"✅ Instagram video saved: {path}",
            flush=True
        )

        return path

    except Exception as e:
        print(
            f"❌ Instagram client DL failed: {e}",
            flush=True
        )
        return None


def download_with_ytdlp(url):
    tmp_id = uuid.uuid4().hex[:8]

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
                "Chrome/139.0.0.0 Safari/537.36"
            )
        }
    }

    # Use cookies.txt when available.
    cookie_file = os.environ.get(
        "YTDLP_COOKIES",
        "cookies.txt"
    )

    if os.path.isfile(cookie_file):
        ydl_opts["cookiefile"] = cookie_file

        print(
            f"🍪 Using cookies: {cookie_file}",
            flush=True
        )

    try:
        with yt_dlp.YoutubeDL(
            ydl_opts
        ) as ydl:
            ydl.download([url])

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
                    return path

        return None

    except Exception as e:
        print(
            f"DL Error: {e}",
            flush=True
        )
        return None


def download_video(url, client=None):
    url = url.split("?")[0].strip()

    # Instagram:
    # First try logged-in instagrapi.
    if (
        "instagram.com" in url.lower()
        and client
    ):
        path = download_instagram(
            url,
            client
        )

        if path:
            return path

        print(
            "⚠️ Instagram client failed.",
            flush=True
        )

        # Do not immediately hammer Instagram
        # with repeated yt-dlp requests.
        return None

    # Other supported platforms.
    return download_with_ytdlp(
        url
    )


def auto_detect(text):
    if not text:
        return None

    match = re.search(
        URL_REGEX,
        text
    )

    if not match:
        return None

    url = match.group(1).split("?")[0]

    if is_supported(url):
        return url

    return None


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
                "❌ 90MB+ besi, "
                "pathano jabena!"
            )

        cl.direct_send_video(
            path,
            thread_ids=[thread_id]
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
        except:
            pass


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

    url = match.group(1).split("?")[0]

    if not is_supported(url):
        return (
            "❌ Supported: "
            "Insta / FB / TikTok / YT / Twitter"
        )

    cl = ctx.get("client")
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
            thread_ids=[thread_id]
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
            f"❌ Error: {e}"
        )


DOWNLOADER_COMMANDS = {
    "dl": dl_command,
    "download": dl_command
}
