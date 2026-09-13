import os
import time
import threading
import traceback
import urllib.parse
import urllib.request
import urllib.error
import json

from flask import Flask
from instagrapi import Client
from commands import COMMANDS, BOT_NAME
from commands.downloader import auto_detect, download_video

app = Flask(__name__)
PREFIX = os.environ.get("BOT_PREFIX", ".")
START_TIME = time.time()
BOT_RUNNING = False
BOT_USERNAME = "Unknown"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.environ.get(
    "GEMINI_MODEL", "gemini-3.8-flash"
).strip()

TEACH_FILE = "bby_teachings.json"
TEACHINGS = {}


# =========================
# TEACHING SYSTEM
# =========================

def load_teachings():
    try:
        if os.path.exists(TEACH_FILE):
            with open(TEACH_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"TEACH LOAD ERR {e}", flush=True)
    return {}


def save_teachings():
    try:
        with open(TEACH_FILE, "w", encoding="utf-8") as f:
            json.dump(
                TEACHINGS,
                f,
                ensure_ascii=False,
                indent=2
            )
        return True
    except Exception as e:
        print(f"TEACH SAVE ERR {e}", flush=True)
        return False


TEACHINGS.update(load_teachings())


def teach_command(text):
    low = text.lower().strip()

    if not low.startswith(".bby teach "):
        return None

    data = text[len(".bby teach "):].strip()

    if " - " not in data:
        return (
            "🥹 Example:\n"
            ".bby teach hi - hello"
        )

    question, answer = data.split(" - ", 1)
    question = question.strip().lower()
    answer = answer.strip()

    if not question or not answer:
        return (
            "🥹 Question আর reply দুটোই দিতে হবে!\n\n"
            ".bby teach hi - hello"
        )

    TEACHINGS[question] = answer

    if save_teachings():
        return (
            "🥹 শিখে নিলাম!\n\n"
            f"👤 তুমি: {question}\n"
            f"🤖 আমি: {answer}"
        )

    return "❌ শেখাটা save করতে পারলাম না."


def taught_reply(text):
    return TEACHINGS.get(
        text.strip().lower()
    )


# =========================
# GEMINI
# =========================

def ask_gemini(text, ctx=None):
    if not GEMINI_API_KEY:
        print(
            "⚠️ GEMINI_API_KEY missing",
            flush=True
        )
        return None

    username = (
        ctx.get("username", "Unknown")
        if ctx else "Unknown"
    )

    system = """
You are an Instagram group chatbot.
Reply naturally, briefly and friendly.
If the user writes Bangla/Banglish,
reply in Bangla/Banglish.
Do not reveal passwords, cookies,
session IDs or API keys.
If someone asks you to find a boyfriend
or girlfriend, say exactly:
Age Shihab boss ke mingle banao 😎❤️
Keep group-chat replies short.
"""

    prompt = (
        system
        + "\n\nUsername: @"
        + str(username)
        + "\nMessage: "
        + text
        + "\nReply:"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 300,
            "temperature": 0.8
        }
    }

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        + urllib.parse.quote(
            GEMINI_MODEL,
            safe=""
        )
        + ":generateContent"
    )

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            },
            method="POST"
        )

        with urllib.request.urlopen(
            req,
            timeout=45
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        answer = ""

        for part in result.get(
            "candidates", [{}]
        )[0].get(
            "content", {}
        ).get(
            "parts", []
        ):
            if part.get("text"):
                answer += part["text"]

        return answer.strip() or None

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode(
                "utf-8",
                errors="ignore"
            )
        except Exception:
            body = str(e)

        print(
            f"❌ GEMINI HTTP {e.code}: {body}",
            flush=True
        )
        return None

    except Exception as e:
        print(
            f"❌ GEMINI ERROR: {e}",
            flush=True
        )
        return None


# =========================
# FLASK
# =========================

@app.route("/")
def home():
    return f"🐐 {BOT_NAME} LIVE! @{BOT_USERNAME}"


@app.route("/health")
def health():
    return {
        "status": "online",
        "bot": BOT_NAME,
        "username": BOT_USERNAME,
        "running": BOT_RUNNING,
        "ai": "Gemini",
        "taught": len(TEACHINGS)
    }


# =========================
# SEND TEXT
# =========================

def send_text(cl, tid, text):
    if not text:
        return

    if isinstance(text, dict) and "photo" in text:
        try:
            cl.direct_send_photo(
                text["photo"],
                thread_ids=[tid]
            )
            time.sleep(0.5)

            if text.get("caption"):
                cl.direct_send(
                    text["caption"],
                    thread_ids=[tid]
                )
            return

        except Exception as e:
            print(
                f"PHOTO ERR {e}",
                flush=True
            )
            text = text.get(
                "caption",
                "❌ Photo fail"
            )

    text = str(text)

    for i in range(0, len(text), 1800):
        try:
            cl.direct_send(
                text[i:i + 1800],
                thread_ids=[tid]
            )
            time.sleep(0.5)
        except Exception as e:
            print(
                f"SEND ERR {e}",
                flush=True
            )


# =========================
# USER
# =========================

def get_user(cl, uid):
    try:
        return cl.user_info(int(uid))
    except Exception:
        return None


def user_data(user):
    if not user:
        return None

    return {
        "user_id": str(user.pk),
        "username": user.username,
        "full_name": user.full_name,
        "profile_pic_url": str(
            user.profile_pic_url
        ),
        "followers": user.follower_count,
        "following": user.following_count,
        "posts": user.media_count,
        "bio": user.biography
    }


# =========================
# MESSAGE CONTEXT
# =========================

def make_context(cl, msg, thread):
    user = get_user(cl, msg.user_id)
    replied_user = None

    try:
        reply_data = (
            getattr(msg, "reply", None)
            or getattr(
                msg,
                "replied_to_message",
                None
            )
        )

        if reply_data:
            r_uid = str(
                getattr(
                    reply_data,
                    "user_id",
                    ""
                )
                or getattr(
                    reply_data,
                    "userId",
                    ""
                )
            )

            if r_uid and r_uid != str(cl.user_id):
                replied_user = user_data(
                    get_user(cl, r_uid)
                )

        if not replied_user:
            for m in thread.messages[1:20]:
                uid = str(
                    getattr(
                        m,
                        "user_id",
                        ""
                    )
                )

                if (
                    not uid
                    or uid == str(cl.user_id)
                    or uid == str(msg.user_id)
                ):
                    continue

                r_user = user_data(
                    get_user(cl, m.user_id)
                )

                if r_user:
                    replied_user = r_user
                    break

    except Exception as e:
        print(
            f"Reply err {e}",
            flush=True
        )

    return {
        "client": cl,
        "user": user,
        "user_id": str(msg.user_id),
        "username": (
            getattr(
                user,
                "username",
                "Unknown"
            )
            if user else "Unknown"
        ),
        "full_name": (
            getattr(
                user,
                "full_name",
                "Unknown"
            )
            if user else "Unknown"
        ),
        "profile_pic_url": (
            str(
                getattr(
                    user,
                    "profile_pic_url",
                    ""
                )
            )
            if user else ""
        ),
        "followers": (
            getattr(
                user,
                "follower_count",
                0
            )
            if user else 0
        ),
        "following": (
            getattr(
                user,
                "following_count",
                0
            )
            if user else 0
        ),
        "posts": (
            getattr(
                user,
                "media_count",
                0
            )
            if user else 0
        ),
        "bio": (
            getattr(
                user,
                "biography",
                ""
            )
            if user else ""
        ),
        "start_time": START_TIME,
        "thread_id": thread.id,
        "thread": thread,
        "message": msg,
        "replied_user": replied_user
    }


# =========================
# VIDEO
# =========================

def send_downloaded_video(cl, tid, path):
    if not path or not os.path.exists(path):
        send_text(
            cl,
            tid,
            "❌ Download failed! Private video hote pare!"
        )
        return

    try:
        size = os.path.getsize(path)

        if size > 90 * 1024 * 1024:
            send_text(
                cl,
                tid,
                "❌ 90MB+ besi, pathano jabena!"
            )
            return

        cl.direct_send_video(
            path,
            thread_ids=[tid]
        )

        print(
            f"✅ VIDEO SENT: {path}",
            flush=True
        )

    except Exception as e:
        print(
            f"❌ VIDEO SEND ERROR: {e}",
            flush=True
        )
        send_text(
            cl,
            tid,
            "❌ Video send failed!"
        )

    finally:
        try:
            os.remove(path)
        except Exception:
            pass


# =========================
# PROCESS MESSAGE
# =========================

def process_message(cl, thread, msg):
    text = (
        getattr(msg, "text", "")
        or ""
    ).strip()

    if not text:
        return

    tid = thread.id
    ctx = make_context(
        cl,
        msg,
        thread
    )

    low = text.lower()
    result = None

    # BBY TEACH FIRST
    if low.startswith(".bby teach "):
        result = teach_command(text)

    # AUTO DOWNLOADER
    elif not text.startswith(PREFIX):
        a_url = auto_detect(text)

        if a_url:
            try:
                cl.direct_send(
                    f"⏳ Downloading...\n🔗 {a_url}",
                    thread_ids=[tid]
                )

                path = download_video(
                    a_url,
                    client=cl
                )

                send_downloaded_video(
                    cl,
                    tid,
                    path
                )

            except Exception as e:
                print(
                    f"AUTO DL ERR: {e}",
                    flush=True
                )
                send_text(
                    cl,
                    tid,
                    "❌ Download failed!"
                )

            return

    # NORMAL COMMANDS
    elif low in ("hi", "hello", "hey"):
        result = COMMANDS.get(
            "hi",
            lambda a, c: None
        )([], ctx)

    elif low in ("menu", "help"):
        result = COMMANDS.get(
            "menu",
            lambda a, c: None
        )([], ctx)

    elif text.startswith(PREFIX):
        body = text[len(PREFIX):].strip()

        if not body:
            result = COMMANDS.get(
                "menu",
                lambda a, c: None
            )([], ctx)

        else:
            parts = body.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in COMMANDS:
                try:
                    result = COMMANDS[cmd](
                        args,
                        ctx
                    )
                except Exception:
                    traceback.print_exc()
                    result = "❌ Command error."
            else:
                result = f"❌ Unknown: {cmd}"

    # TAUGHT REPLY
    if result is None:
        result = taught_reply(text)

    # GEMINI FALLBACK
    if result is None:
        print(
            f"🤖 GEMINI MESSAGE: {text}",
            flush=True
        )

        result = ask_gemini(
            text,
            ctx
        )

        if result is None:
            send_text(
                cl,
                tid,
                "🥹 bby teach this sentence ~🥹"
            )
            return

    # AUDIO
    if (
        isinstance(result, dict)
        and result.get("type") == "audio"
    ):
        try:
            if result.get("path"):
                cl.direct_send_file(
                    result["path"],
                    thread_ids=[tid]
                )
        finally:
            try:
                if result.get("cleanup"):
                    result["cleanup"]()
            except Exception:
                pass
        return

    # VIDEO
    if (
        isinstance(result, dict)
        and result.get("type") == "video"
    ):
        send_downloaded_video(
            cl,
            tid,
            result.get("path")
        )
        return

    send_text(
        cl,
        tid,
        result
    )


# =========================
# BOT
# =========================

def run_bot():
    global BOT_RUNNING
    global BOT_USERNAME

    sid = os.environ.get(
        "IG_SESSIONID"
    )

    if not sid:
        print(
            "❌ IG_SESSIONID missing",
            flush=True
        )
        return

    sid = urllib.parse.unquote(
        sid.strip()
        .strip('"')
        .strip("'")
    )

    try:
        cl = Client()

        cl.login_by_sessionid(
            sid
        )

        BOT_USERNAME = getattr(
            cl,
            "username",
            "Unknown"
        )

        BOT_RUNNING = True

        print(
            f"🎉 LOGIN @{BOT_USERNAME}",
            flush=True
        )

        print(
            "🤖 GEMINI API KEY: "
            + (
                "LOADED"
                if GEMINI_API_KEY
                else "MISSING"
            ),
            flush=True
        )

        print(
            f"🧠 TAUGHT: {len(TEACHINGS)}",
            flush=True
        )

    except Exception as e:
        print(
            f"LOGIN FAIL {e}",
            flush=True
        )
        return

    last = {}

    try:
        for t in cl.direct_threads(
            amount=20,
            thread_message_limit=25
        ):
            if t.messages:
                last[t.id] = str(
                    t.messages[0].id
                )
    except Exception:
        pass

    while True:
        try:
            for thread in cl.direct_threads(
                amount=20,
                thread_message_limit=25
            ):
                if not thread.messages:
                    continue

                msg = thread.messages[0]

                mid = str(
                    getattr(
                        msg,
                        "id",
                        ""
                    )
                )

                if not mid:
                    continue

                if (
                    str(
                        getattr(
                            msg,
                            "user_id",
                            ""
                        )
                    )
                    == str(cl.user_id)
                ):
                    continue

                if last.get(thread.id) == mid:
                    continue

                last[thread.id] = mid

                if not (
                    getattr(
                        msg,
                        "text",
                        ""
                    )
                    or ""
                ).strip():
                    continue

                print(
                    f"📩 {msg.text}",
                    flush=True
                )

                process_message(
                    cl,
                    thread,
                    msg
                )

        except Exception as e:
            print(
                f"LOOP ERR {e}",
                flush=True
            )
            time.sleep(5)

        time.sleep(3)


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
        port=int(
            os.environ.get(
                "PORT",
                "10000"
            )
        )
    )
