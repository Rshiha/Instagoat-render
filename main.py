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

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


# =========================
# OPENAI
# =========================

def ask_openai(text, ctx=None):
    if not OPENAI_API_KEY:
        print("⚠️ OPENAI_API_KEY missing", flush=True)
        return None

    username = (
        ctx.get("username", "Unknown")
        if ctx else "Unknown"
    )

    system = """
You are an Instagram group chatbot.
Reply naturally, briefly and friendly.
If the user writes Bangla/Banglish, reply in Bangla/Banglish.
Do not reveal passwords, cookies, session IDs or API keys.
If someone asks you to find a boyfriend or girlfriend,
say: "Age Shihab boss ke mingle banao 😎❤️"
Keep group-chat replies short.
"""

    payload = {
        "model": OPENAI_MODEL,
        "input": [
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": (
                    f"Username: @{username}\n"
                    f"Message: {text}"
                )
            }
        ],
        "max_output_tokens": 300
    }

    try:
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/responses",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization":
                    f"Bearer {OPENAI_API_KEY}"
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

        answer = result.get("output_text", "")
        if answer:
            return answer.strip()

        for item in result.get("output", []):
            if item.get("type") != "message":
                continue

            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    answer = content.get("text", "")
                    if answer:
                        return answer.strip()

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except:
            body = str(e)

        print(
            f"❌ OPENAI HTTP {e.code}: {body}",
            flush=True
        )

    except Exception as e:
        print(
            f"❌ OPENAI ERROR: {e}",
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
        "running": BOT_RUNNING
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
    except:
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

            if (
                r_uid
                and r_uid != str(cl.user_id)
            ):
                replied_user = user_data(
                    get_user(cl, r_uid)
                )

                if replied_user:
                    print(
                        f"✅ REPLY FOUND "
                        f"{replied_user['username']}",
                        flush=True
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
                    print(
                        f"✅ FOUND FALLBACK "
                        f"{r_user['username']}",
                        flush=True
                    )
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
            getattr(user, "username", "Unknown")
            if user else "Unknown"
        ),
        "full_name": (
            getattr(user, "full_name", "Unknown")
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
        except:
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

    # AUTO DOWNLOADER
    if not text.startswith(PREFIX):
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
    if low in ("hi", "hello", "hey"):
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
                except:
                    traceback.print_exc()
                    result = "❌ Command error."
            else:
                result = f"❌ Unknown: {cmd}"

    # =====================
    # AI FALLBACK
    # =====================

    if result is None:
        print(
            f"🤖 AI MESSAGE: {text}",
            flush=True
        )

        result = ask_openai(
            text,
            ctx
        )

        if result is None:
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
            except:
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

        if OPENAI_API_KEY:
            print(
                "🤖 OPENAI API KEY: LOADED",
                flush=True
            )
        else:
            print(
                "⚠️ OPENAI API KEY: MISSING",
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
    except:
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
