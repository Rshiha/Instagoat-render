import os
import time
import json
import random
import threading
import queue
import urllib.parse
import subprocess

from flask import Flask, send_from_directory, abort, request
from instagrapi import Client

from commands import COMMANDS, BOT_NAME
from commands.downloader import auto_detect, download_video

try:
    from commands.fun import FUN_COMMANDS
except Exception as e:
    print(f"FUN COMMANDS LOAD ERR: {e}", flush=True)
    FUN_COMMANDS = {}

try:
    from commands.media import select_song, download_selected_song, DOWNLOAD_DIR
except Exception as e:
    print(f"MEDIA LOAD ERR: {e}", flush=True)
    select_song = None
    download_selected_song = None
    DOWNLOAD_DIR = "/tmp/downloads"

try:
    from ai import get_ai_reply, generate_pic
except Exception as e:
    print(f"AI LOAD ERR: {e}", flush=True)
    get_ai_reply = None
    generate_pic = None


app = Flask(__name__)

PREFIX = os.getenv("BOT_PREFIX", ".")
START_TIME = time.time()
BOT_RUNNING = False
BOT_USERNAME = "Unknown"
TEACH_FILE = "bby_teachings.json"
SETTINGS_FILE = "ig_settings.json"

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "15"))

# একই instagrapi client দিয়ে একসাথে (parallel) একাধিক request পাঠালে
# Instagram সন্দেহজনক আচরণ মনে করে session/login invalidate করে দিতে পারে
# ("LoginRequired"). তাই client-এর প্রতিটা actual call এই lock দিয়ে
# serialize করা হয় — ভারী local কাজ (download/ffmpeg) parallel-ই থাকে,
# শুধু Instagram-এর সাথে কথা বলার সময়টুকু one-at-a-time রাখা হয়।
IG_LOCK = threading.Lock()

# আগে প্রতিটা মেসেজের জন্য আলাদা থ্রেড বানানো হতো (যেটা parallel client
# call-এর ঝুঁকি তৈরি করেছিল)। এখন একটাই worker thread + queue ব্যবহার
# হচ্ছে — মেসেজগুলো one-by-one process হয়, কিন্তু main polling loop
# instant queue.put() করেই আবার পরের poll-এ চলে যেতে পারে, আটকে থাকে না।
MESSAGE_QUEUE = queue.Queue()

# Bot নিজে যেসব message পাঠিয়েছে তাদের id — কেউ সেই message-এ reply
# করলে (উদাহরণ: AI-এর উত্তরে ফলো-আপ প্রশ্ন) সেটা ধরার জন্য ব্যবহার হয়।
bot_msg_ids = set()


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
            existing = TEACHINGS.get(question)

            if existing is None:
                TEACHINGS[question] = answer
            elif isinstance(existing, list):
                if answer not in existing:
                    existing.append(answer)
            elif existing != answer:
                # একই question-এর আগের answer + নতুনটা — দুটোই রাখা
                # হচ্ছে, রিপ্লাই দেওয়ার সময় randomly বেছে নেওয়া হবে
                TEACHINGS[question] = [existing, answer]

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


def pick_answer(answer):
    # TEACHINGS-এর value একটা string (single answer) অথবা list
    # (multiple answer) দুটোই হতে পারে — list হলে randomly একটা বেছে
    # নেওয়া হয়, যাতে একই question-এ বারবার একই রিপ্লাই না আসে।
    if isinstance(answer, list):
        return random.choice(answer) if answer else None

    return answer


def taught_reply(text):
    question = normalize(text)

    if not question:
        return None

    if question in TEACHINGS:
        return pick_answer(TEACHINGS[question])

    for key, answer in TEACHINGS.items():
        key = normalize(key)

        if len(key) >= 3 and key in question:
            return pick_answer(answer)

    return None


# =========================
# FLASK
# =========================

@app.route("/")
def home():
    return f"🐐 {BOT_NAME} LIVE! @{BOT_USERNAME}"


CRAWLER_UA_MARKERS = (
    "facebookexternalhit", "facebookcatalog", "facebookbot",
    "meta-externalagent", "instagram",
)


@app.route("/audio/<path:filename>")
def serve_audio(filename):
    # Serves temporarily-downloaded songs so they can be sent as a link,
    # since Instagram DMs only accept JPG/JPEG/PNG/WEBP as raw file uploads.
    #
    # Meta's own link-preview crawler re-fetches any raw link it sees in a
    # DM to build a preview (og:video/og:image), often several times. Block
    # it here so it can't repeatedly hammer this route or "use up" the
    # short-lived file before the actual recipient opens the link.
    ua = (request.headers.get("User-Agent") or "").lower()

    if any(marker in ua for marker in CRAWLER_UA_MARKERS):
        abort(403)

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
        with IG_LOCK:
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
        return None

    if isinstance(text, dict) and text.get("photo"):
        try:
            with IG_LOCK:
                client.direct_send_photo(text["photo"], thread_ids=[thread_id])

                msg_id = None
                if text.get("caption"):
                    sent = client.direct_send(text["caption"], thread_ids=[thread_id])
                    msg_id = getattr(sent, "id", None)

            return msg_id
        except Exception:
            text = text.get("caption", "❌ Photo failed")

    text = str(text)
    last_id = None

    for i in range(0, len(text), 1800):
        try:
            with IG_LOCK:
                sent = client.direct_send(text[i:i + 1800], thread_ids=[thread_id])
                last_id = getattr(sent, "id", None)
            time.sleep(0.5)
        except Exception as e:
            print(f"SEND ERR: {e}", flush=True)

    return last_id


def send_and_save(client, text, thread_id):
    # send_message ব্যবহার করে পাঠায় (chunking/photo handling সহ), তারপর
    # bot নিজের পাঠানো message-এর id মনে রাখে — যাতে কেউ সেই message-এ
    # reply করলে (যেমন AI উত্তরে ফলো-আপ) সেটা ধরা যায়।
    msg_id = send_message(client, thread_id, text)

    try:
        bot_msg_ids.add(msg_id)
    except Exception:
        pass

    return msg_id


def send_video(client, thread_id, path):
    if not path or not os.path.exists(path):
        send_message(client, thread_id, "❌ Video download failed!")
        return

    try:
        if os.path.getsize(path) > 90 * 1024 * 1024:
            send_message(client, thread_id, "❌ Video 90MB-এর বেশি!")
            return

        with IG_LOCK:
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


def build_link(base_url, filename):
    return f"{base_url.rstrip('/')}/audio/{urllib.parse.quote(filename)}"


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
    base_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("BASE_URL")

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
        with IG_LOCK:
            client.direct_send_video(video_path, thread_ids=[thread_id])

        print("✅ AUDIO SENT AS PLAYABLE VIDEO", flush=True)

        # Only send the AUDIO link — NOT the video link. Instagram/Meta's
        # own link-preview crawler (facebookexternalhit) auto-fetches any
        # raw .mp4 URL repeatedly to build an og:video preview, which is
        # what was hammering the server every few seconds in the logs.
        # The video itself was already delivered natively above (no link
        # needed for that), so we just skip exposing a second .mp4 URL.
        if base_url:
            audio_link = build_link(base_url, os.path.basename(path))

            send_message(
                client,
                thread_id,
                f"⬇️ Download ({title}) — 10 মিনিট valid:\n"
                f"🎧 Audio: {audio_link}"
            )
            threading.Timer(600, do_cleanup).start()
        else:
            do_cleanup()

        return
    except Exception as e:
        print(f"AUDIO SEND ERR: {e}", flush=True)

        # Fallback: if conversion/send fails for any reason, at least
        # give a link instead of nothing.
        try:
            if not base_url:
                raise Exception("no base url for fallback link")

            filename = os.path.basename(path)
            link = build_link(base_url, filename)

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

    # কেউ bot-এর কোনো message-এ reply করলে সেটাকে AI-এর জন্য
    # follow-up প্রশ্ন হিসেবে ধরা হয়।
    replied_id = getattr(message, "reply_to_id", None)

    if replied_id and replied_id in bot_msg_ids:
        if not get_ai_reply:
            send_message(client, thread_id, "❌ AI ফিচার এখন unavailable!")
            return

        try:
            ans = get_ai_reply(text)
        except Exception as e:
            print(f"AI REPLY ERR: {e}", flush=True)
            ans = "❌ AI reply দেওয়া যায়নি!"

        send_and_save(client, ans, thread_id)
        return

    if text.startswith(PREFIX):
        parts = text[len(PREFIX):].split()

        if parts:
            fun_cmd = parts[0].lower()

            if fun_cmd in FUN_COMMANDS:
                try:
                    reply = FUN_COMMANDS[fun_cmd](parts[1:], message)
                except Exception as e:
                    print(f"FUN COMMAND ERR: {e}", flush=True)
                    reply = "❌ Command error."

                send_and_save(client, reply, thread_id)
                return

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

    elif lower.startswith(".ai "):
        q = text[4:].strip()

        if not get_ai_reply:
            send_message(client, thread_id, "❌ AI ফিচার এখন unavailable!")
            return

        send_message(client, thread_id, "🤖 Likhtesi...")

        try:
            ans = get_ai_reply(q)
        except Exception as e:
            print(f"AI REPLY ERR: {e}", flush=True)
            ans = "❌ AI reply দেওয়া যায়নি!"

        send_message(client, thread_id, ans)
        return

    elif lower.startswith((".img ", ".pic ")):
        q = text.split(" ", 1)[1] if " " in text else ""

        if not generate_pic:
            send_message(client, thread_id, "❌ Image ফিচার এখন unavailable!")
            return

        send_message(client, thread_id, f"🎨 Banacchi: {q}...")

        try:
            p = generate_pic(q)
        except Exception as e:
            print(f"AI IMG ERR: {e}", flush=True)
            p = None

        if p and os.path.exists(p):
            try:
                with IG_LOCK:
                    client.direct_send_file(p, thread_ids=[thread_id])
            except Exception as e:
                print(f"AI IMG SEND ERR: {e}", flush=True)
                send_message(client, thread_id, "❌ Image পাঠানো যায়নি!")
            finally:
                try:
                    os.remove(p)
                except Exception:
                    pass
        else:
            send_message(client, thread_id, "❌ Image বানানো যায়নি!")

        return

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

        with IG_LOCK:
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
            with IG_LOCK:
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

                    # process_message() সরাসরি নতুন থ্রেডে না ছেড়ে একটা
                    # queue-তে জমা করা হচ্ছে — একটাই dedicated worker
                    # thread সেটা one-by-one process করবে (নিচে দেখো)।
                    # এতে Instagram-এর সাথে একসাথে একাধিক (parallel) request
                    # যাওয়ার ঝুঁকি থাকে না (যেটা session logout ঘটাতে পারে),
                    # অথচ ভারী কাজ চলাকালীনও polling loop আটকে থাকে না।
                    MESSAGE_QUEUE.put((client, thread, message))

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
# MESSAGE WORKER (serial)
# =========================

def message_worker():
    while True:
        client, thread, message = MESSAGE_QUEUE.get()

        try:
            process_message(client, thread, message)
        except Exception as e:
            print(f"⚠️ MESSAGE PROCESS ERR: {repr(e)}", flush=True)
        finally:
            MESSAGE_QUEUE.task_done()


# =========================
# START
# =========================

threading.Thread(
    target=run_bot,
    daemon=True
).start()

threading.Thread(
    target=message_worker,
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

