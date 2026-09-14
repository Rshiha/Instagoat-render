import os
import time
import json
import threading
import urllib.parse
import subprocess

from flask import Flask, send_from_directory, abort
from instagrapi import Client

from commands import COMMANDS, BOT_NAME
from commands.downloader import auto_detect, download_video

try:
    from commands.media import select_song, download_selected_song, DOWNLOAD_DIR
except Exception as e:
    print(f"MEDIA LOAD ERR: {e}", flush=True)
    select_song = None
    download_selected_song = None
    DOWNLOAD_DIR = "/tmp/downloads"


app = Flask(__name__)

PREFIX = os.getenv("BOT_PREFIX", ".")
START_TIME = time.time()
BOT_RUNNING = False
BOT_USERNAME = "Unknown"
TEACH_FILE = "bby_teachings.json"
SETTINGS_FILE = "ig_settings.json"

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))


# =========================
# YOUTUBE COOKIES
# =========================

def load_cookies():
    paths = [
        "/etc/secrets/cookies.txt",
        os.path.join(os.path.dirname(__file__), "cookies.txt"),
        "cookies.txt"
    ]

    for path in paths:
        try:
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                os.environ["YTDLP_COOKIES"] = path
                print("🍪 YouTube Cookies: LOADED", flush=True)
                return path
        except Exception:
            pass

    print("⚠️ YouTube Cookies: MISSING", flush=True)
    return None


COOKIE_FILE = load_cookies()


# =========================
# TEACHING
# =========================

def load_teachings():
    try:
        if not os.path.exists(TEACH_FILE):
            return {}

        with open(TEACH_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

        result = {}

        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue

                q = item.get("question")
                a = item.get("answer")

                if q and a:
                    result[str(q)] = str(a)

        return result

    except Exception as e:
        print(f"TEACH LOAD ERR: {e}", flush=True)
        return {}


TEACHINGS = load_teachings()


def save_teachings():
    try:
        with open(TEACH_FILE, "w", encoding="utf-8") as f:
            json.dump(TEACHINGS, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"TEACH SAVE ERR: {e}", flush=True)
        return False


def normalize(text):
    if not text:
        return ""

    text = " ".join(str(text).strip().lower().split())

    for char in "!?।,.;:'\"“”‘’`~":
        text = text.replace(char, "")

    return text.strip()


def teach(text):
    count = 0

    for line in text.splitlines():
        if not line.lower().startswith(".bby teach "):
            continue

        data = line[11:].strip()

        if " - " not in data:
            continue

        question, answer = data.split(" - ", 1)
        question = normalize(question)
        answer = answer.strip()

        if question and answer:
            TEACHINGS[question] = answer
            count += 1

    if count == 0:
        return (
            "🥹 ঠিকভাবে teach করা হয়নি!\n\n"
            "Example:\n"
            ".bby teach hi - hello"
        )

    if not save_teachings():
        return "❌ Teach save করা যায়নি!"

    return f"🥹 {count}টা কথা শিখে নিলাম! ❤️"


def taught_reply(text):
    question = normalize(text)

    if not question:
        return None

    if question in TEACHINGS:
        return TEACHINGS[question]

    for key, answer in TEACHINGS.items():
        key = normalize(key)

        if len(key) >= 3 and key in question:
            return answer

    return None


# =========================
# FLASK
# =========================

@app.route("/")
def home():
    return f"🐐 {BOT_NAME} LIVE! @{BOT_USERNAME}"


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    # Serves temporarily-downloaded songs so they can be sent as a link,
    # since Instagram DMs only accept JPG/JPEG/PNG/WEBP as raw file uploads.
    safe_name = os.path.basename(filename)

    if not os.path.isfile(os.path.join(DOWNLOAD_DIR, safe_name)):
        abort(404)

    return send_from_directory(DOWNLOAD_DIR, safe_name, as_attachment=True)


@app.route("/health")
def health():
    return {
        "status": "online",
        "bot": BOT_NAME,
        "username": BOT_USERNAME,
        "running": BOT_RUNNING,
        "ai": "OFF",
        "taught": len(TEACHINGS),
        "youtube_cookies": bool(COOKIE_FILE),
        "music": bool(select_song),
        "poll_interval": POLL_INTERVAL
    }


# =========================
# CONTEXT
# =========================

def make_context(client, message, thread):
    try:
        user = client.user_info(int(message.user_id))
    except Exception:
        user = None

    return {
        "client": client,
        "user": user,
        "user_id": str(message.user_id),
        "username": getattr(user, "username", "Unknown") if user else "Unknown",
        "full_name": getattr(user, "full_name", "Unknown") if user else "Unknown",
        "profile_pic_url": str(getattr(user, "profile_pic_url", "")) if user else "",
        "followers": getattr(user, "follower_count", 0) if user else 0,
        "following": getattr(user, "following_count", 0) if user else 0,
        "posts": getattr(user, "media_count", 0) if user else 0,
        "bio": getattr(user, "biography", "") if user else "",
        "start_time": START_TIME,
        "thread_id": thread.id,
        "thread": thread,
        "message": message
    }


# =========================
# SEND MESSAGE
# =========================

def send_message(client, thread_id, text):
    if text is None:
        return

    if isinstance(text, dict) and text.get("photo"):
        try:
            client.direct_send_photo(text["photo"], thread_ids=[thread_id])

            if text.get("caption"):
                client.direct_send(text["caption"], thread_ids=[thread_id])

            return
        except Exception:
            text = text.get("caption", "❌ Photo failed")

    text = str(text)

    for i in range(0, len(text), 1800):
        try:
            client.direct_send(text[i:i + 1800], thread_ids=[thread_id])
            time.sleep(0.5)
        except Exception as e:
            print(f"SEND ERR: {e}", flush=True)


def send_video(client, thread_id, path):
    if not path or not os.path.exists(path):
        send_message(client, thread_id, "❌ Video download failed!")
        return

    try:
        if os.path.getsize(path) > 90 * 1024 * 1024:
            send_message(client, thread_id, "❌ Video 90MB-এর বেশি!")
            return

        client.direct_send_video(path, thread_ids=[thread_id])
    except Exception as e:
        print(f"VIDEO SEND ERR: {e}", flush=True)
        send_message(client, thread_id, "❌ Video send failed!")
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def make_playable_video(audio_path):
    """
    Instagram DMs can't play a raw audio file inline (direct_send_file only
    accepts JPG/JPEG/PNG/WEBP). But a short video WITH an audio track plays
    natively/inline in Direct. So we mux the song onto a static cover frame
    and send that as a video — the recipient just taps play, no download.
    """
    video_path = os.path.splitext(audio_path)[0] + ".mp4"

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x1DB954:s=720x720:r=1",
        "-i", audio_path,
        "-shortest",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        video_path,
    ]

    result = subprocess.run(cmd, capture_output=True, timeout=100)

    if result.returncode != 0 or not os.path.isfile(video_path):
        print(f"FFMPEG ERR: {result.stderr[-500:]}", flush=True)
        return None

    return video_path


def send_audio(client, thread_id, result):
    if not isinstance(result, dict):
        send_message(client, thread_id, result)
        return

    path = result.get("path")

    if not path or not os.path.exists(path):
        send_message(client, thread_id, "❌ Audio file পাওয়া যায়নি!")
        return

    video_path = None

    def do_cleanup():
        try:
            cleanup = result.get("cleanup")

            if cleanup:
                cleanup()
            elif os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
        except Exception:
            pass

    title = result.get("title", "Song")

    try:
        if os.path.getsize(path) > 90 * 1024 * 1024:
            send_message(client, thread_id, "❌ Audio 90MB-এর বেশি!")
            do_cleanup()
            return

        print(f"🎵 Converting to playable video: {title}", flush=True)
        video_path = make_playable_video(path)

        if not video_path or os.path.getsize(video_path) > 90 * 1024 * 1024:
            raise Exception("video conversion failed or too large")

        print(f"🎵 Sending (direct play): {title}", flush=True)
        client.direct_send_video(video_path, thread_ids=[thread_id])

        print("✅ AUDIO SENT AS PLAYABLE VIDEO", flush=True)
        do_cleanup()
        return
    except Exception as e:
        print(f"AUDIO SEND ERR: {e}", flush=True)

        # Fallback: if conversion/send fails for any reason, at least
        # give a link instead of nothing.
        try:
            base_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("BASE_URL")

            if not base_url:
                raise Exception("no base url for fallback link")

            filename = os.path.basename(path)
            link = f"{base_url.rstrip('/')}/audio/{urllib.parse.quote(filename)}"

            send_message(
                client,
                thread_id,
                f"🎵 {title}\n\n⚠️ Direct play fail করেছে, তাই link দিলাম (10 মিনিট valid):\n{link}"
            )
            threading.Timer(600, do_cleanup).start()
        except Exception as e2:
            print(f"AUDIO FALLBACK ERR: {e2}", flush=True)
            send_message(client, thread_id, "❌ গান পাঠানো যায়নি!")
            do_cleanup()

        return


# =========================
# SONG SELECTION
# =========================

def handle_song_number(client, thread, message):
    if not select_song or not download_selected_song:
        return False

    text = (getattr(message, "text", "") or "").strip()

    if not text.isdigit():
        return False

    number = int(text)

    if number < 1 or number > 5:
        return False

    try:
        result = select_song(number, make_context(client, message, thread))
    except Exception as e:
        print(f"SONG SELECT ERR: {e}", flush=True)
        return False

    if result is None:
        return False

    thread_id = thread.id

    if isinstance(result, str):
        send_message(client, thread_id, result)
        return True

    if not isinstance(result, dict):
        send_message(client, thread_id, "❌ Song selection failed!")
        return True

    send_message(client, thread_id, "⏳ গান download হচ্ছে... 🎵")

    try:
        result = download_selected_song(result)
    except Exception as e:
        print(f"SONG DOWNLOAD ERR: {e}", flush=True)
        send_message(client, thread_id, "❌ গান download করা যায়নি!")
        return True

    if isinstance(result, dict) and result.get("type") == "audio":
        send_audio(client, thread_id, result)
    else:
        send_message(client, thread_id, result or "❌ গান download করা যায়নি!")

    return True


# =========================
# PROCESS MESSAGE
# =========================

def process_message(client, thread, message):
    text = (getattr(message, "text", "") or "").strip()

    if not text:
        return

    thread_id = thread.id
    lower = text.lower()

    if text.isdigit():
        if handle_song_number(client, thread, message):
            return

    if lower.startswith(".bby teach "):
        send_message(client, thread_id, teach(text))
        return

    reply = taught_reply(text)

    if reply is not None:
        print(f"🧠 TAUGHT: {text}", flush=True)
        send_message(client, thread_id, reply)
        return

    if not text.startswith(PREFIX):
        try:
            url = auto_detect(text)
        except Exception:
            url = None

        if url:
            try:
                send_message(client, thread_id, f"⏳ Downloading...\n🔗 {url}")
                path = download_video(url, client=client)
                send_video(client, thread_id, path)
            except Exception as e:
                print(f"AUTO DL ERR: {e}", flush=True)
                send_message(client, thread_id, "❌ Download failed!")

            return

    if lower in ("hi", "hello", "hey"):
        command = COMMANDS.get("hi")

        if command:
            try:
                result = command([], make_context(client, message, thread))
            except Exception:
                result = "❌ Command error."
        else:
            result = "Hello! ❤️"

    elif lower in ("menu", "help"):
        command = COMMANDS.get("menu")

        if command:
            try:
                result = command([], make_context(client, message, thread))
            except Exception:
                result = "❌ Command error."
        else:
            result = "❌ Menu পাওয়া যায়নি!"

    elif text.startswith(PREFIX):
        body = text[len(PREFIX):].strip()

        if not body:
            command = COMMANDS.get("menu")

            if command:
                try:
                    result = command([], make_context(client, message, thread))
                except Exception:
                    result = "❌ Command error."
            else:
                result = "❌ Menu পাওয়া যায়নি!"
        else:
            parts = body.split()
            name = parts[0].lower()
            args = parts[1:]

            command = COMMANDS.get(name)

            if not command:
                send_message(client, thread_id, f"❌ Unknown command: {name}")
                return

            try:
                result = command(args, make_context(client, message, thread))
            except Exception as e:
                print(f"COMMAND ERR: {e}", flush=True)
                result = "❌ Command error."

    else:
        print(f"ℹ️ No taught reply for: {text}", flush=True)
        return

    if isinstance(result, dict) and result.get("type") == "audio":
        send_audio(client, thread_id, result)
    elif isinstance(result, dict) and result.get("type") == "video":
        send_video(client, thread_id, result.get("path"))
    else:
        send_message(client, thread_id, result)

# =========================
# INSTAGRAM BOT
# =========================

def is_instagram_403(error):
    """Instagram 403 / 1404006 type error detect"""
    text = str(error).lower()

    return (
        "1404006" in text
        or "item_ack" in text
        or "clientforbiddenerror" in text
        or "status_code\":\"403" in text
        or "403" in text
    )


def run_bot():
    global BOT_RUNNING
    global BOT_USERNAME

    session_id = os.getenv("IG_SESSIONID")

    if not session_id:
        print("❌ IG_SESSIONID missing", flush=True)
        return

    # URL encoded session হলে automatically decode করবে
    session_id = urllib.parse.unquote(
        session_id.strip().strip('"').strip("'")
    )

    client = None

    # =========================
    # LOGIN
    # =========================

    try:
        client = Client()

        # Request-এর মধ্যে একটু delay রাখবে
        client.delay_range = [3, 7]

        # Saved device settings
        if os.path.exists(SETTINGS_FILE):
            try:
                client.load_settings(SETTINGS_FILE)
                print("⚙️ Loaded saved device settings", flush=True)
            except Exception as e:
                print(f"⚠️ SETTINGS LOAD SKIPPED: {e}", flush=True)

        print("🔐 Instagram session login হচ্ছে...", flush=True)

        client.login_by_sessionid(session_id)

        # Login successful হলে settings save
        try:
            client.dump_settings(SETTINGS_FILE)
        except Exception as e:
            print(f"⚠️ SETTINGS SAVE ERR: {e}", flush=True)

        BOT_USERNAME = getattr(client, "username", "Unknown")
        BOT_RUNNING = True

        print(f"🎉 LOGIN SUCCESS: @{BOT_USERNAME}", flush=True)
        print("🤖 Gemini: DISABLED", flush=True)
        print(
            "🍪 YouTube Cookies:",
            "LOADED" if COOKIE_FILE else "MISSING",
            flush=True
        )
        print(f"🧠 TAUGHT: {len(TEACHINGS)}", flush=True)
        print(
            "🎵 Music selection:",
            "ENABLED" if select_song else "DISABLED",
            flush=True
        )
        print(f"⏱️ Poll interval: {POLL_INTERVAL}s", flush=True)

    except Exception as e:
        BOT_RUNNING = False
        print(f"❌ LOGIN FAIL: {repr(e)}", flush=True)

        if is_instagram_403(e):
            print(
                "⚠️ Instagram session/request rejected (403/1404006).",
                flush=True
            )
            print(
                "⚠️ Retry করার আগে session/account restriction check করো.",
                flush=True
            )

        return

    # =========================
    # INITIAL DM LOAD
    # =========================

    last_messages = {}

    try:
        print("📨 Loading initial DM threads...", flush=True)

        threads = client.direct_threads(
            amount=20,
            thread_message_limit=25
        )

        for thread in threads:
            try:
                if thread.messages:
                    last_messages[thread.id] = str(
                        thread.messages[0].id
                    )
            except Exception:
                continue

        print(
            f"✅ Initial DM loaded: {len(last_messages)} threads",
            flush=True
        )

    except Exception as e:
        # Initial DM fail হলে bot crash করবে না
        print(f"⚠️ INITIAL DM LOAD FAILED: {repr(e)}", flush=True)

        if is_instagram_403(e):
            print(
                "⚠️ Instagram 403/1404006 detected.",
                flush=True
            )
            print(
                "⏳ DM polling temporarily paused for 60 seconds.",
                flush=True
            )

            # একই error বারবার instant print করবে না
            time.sleep(60)

        else:
            time.sleep(15)

    # =========================
    # DM POLLING
    # =========================

    errors = 0
    last_403_log = 0

    while True:

        try:
            threads = client.direct_threads(
                amount=20,
                thread_message_limit=25
            )

            errors = 0

            for thread in threads:

                try:
                    if not thread.messages:
                        continue

                    message = thread.messages[0]

                    message_id = str(
                        getattr(message, "id", "")
                    )

                    user_id = str(
                        getattr(message, "user_id", "")
                    )

                    if not message_id:
                        continue

                    # নিজের message ignore
                    if user_id == str(client.user_id):
                        continue

                    # পুরোনো message ignore
                    if last_messages.get(thread.id) == message_id:
                        continue

                    last_messages[thread.id] = message_id

                    text = (
                        getattr(message, "text", "") or ""
                    ).strip()

                    if not text:
                        continue

                    print(
                        f"📩 {text}",
                        flush=True
                    )

                    process_message(
                        client,
                        thread,
                        message
                    )

                except Exception as message_error:
                    print(
                        f"⚠️ MESSAGE PROCESS ERR: "
                        f"{repr(message_error)}",
                        flush=True
                    )

        except Exception as e:

            errors += 1
            error_text = str(e)

            # =========================
            # 403 / 1404006
            # =========================

            if is_instagram_403(e):

                now = time.time()

                # প্রতি error-এ FULL ERROR spam করবে না
                if now - last_403_log >= 60:
                    print(
                        f"⚠️ Instagram 403/1404006: {repr(e)}",
                        flush=True
                    )

                    print(
                        "⚠️ DM request Instagram reject করছে.",
                        flush=True
                    )

                    last_403_log = now

                # Exponential-ish backoff
                wait = min(
                    600,
                    60 * max(1, min(errors, 10))
                )

                print(
                    f"⏳ DM retry হবে {wait}s পরে "
                    f"(attempt {errors})",
                    flush=True
                )

                time.sleep(wait)

                continue

            # =========================
            # OTHER ERRORS
            # =========================

            print(
                f"🔍 FULL ERROR: {repr(e)}",
                flush=True
            )

            wait = min(
                120,
                10 + (errors * 10)
            )

            print(
                f"⚠️ DM loop error — retry {wait}s পরে",
                flush=True
            )

            time.sleep(wait)

        # Normal polling interval
        time.sleep(POLL_INTERVAL)


# =========================
# START
# =========================

threading.Thread(
    target=run_bot,
    daemon=True
).start()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "10000"))
    )
threading.Thread(
    target=run_bot,
    daemon=True
).start()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "10000"))
        )
# =========================
# INSTAGRAM BOT
# =========================

