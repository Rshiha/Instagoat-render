import os
import time
import threading
import traceback
import urllib.parse

from flask import Flask
from instagrapi import Client
from commands import COMMANDS, AUTO_REPLIES, BOT_NAME

app = Flask(__name__)

PREFIX = os.environ.get("BOT_PREFIX", ".")
START_TIME = time.time()

BOT_RUNNING = False
BOT_USERNAME = "Unknown"


@app.route("/")
def home():
    return (
        f"🐐 {BOT_NAME} LIVE!\n"
        f"🤖 Username: @{BOT_USERNAME}\n"
        f"📚 Commands: {len(COMMANDS)}"
    )


@app.route("/health")
def health():
    return {
        "status": "online",
        "bot": BOT_NAME,
        "username": BOT_USERNAME,
        "commands": len(COMMANDS),
        "running": BOT_RUNNING,
        "uptime": int(time.time() - START_TIME)
    }


def send_text(cl, thread_id, text):
    if not text:
        return

    text = str(text)

    for i in range(0, len(text), 1800):
        try:
            cl.direct_send(
                text[i:i + 1800],
                thread_ids=[thread_id]
            )
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ SEND ERROR: {e}", flush=True)


def get_user(cl, user_id):
    try:
        return cl.user_info(user_id)
    except Exception as e:
        print(f"⚠️ USER INFO ERROR: {e}", flush=True)
        return None


def make_context(cl, msg, thread):
    user = get_user(cl, msg.user_id)

    return {
        "client": cl,
        "user": user,
        "user_id": str(msg.user_id),
        "username": getattr(user, "username", "Unknown"),
        "thread_id": thread.id,
        "thread": thread,
        "message": msg
    }


def process_message(cl, thread, msg):

    text = (getattr(msg, "text", "") or "").strip()

    if not text:
        return

    thread_id = thread.id
    ctx = make_context(cl, msg, thread)
    low = text.lower()

    reply = None

    # AUTO REPLY
    if low in AUTO_REPLIES:
        reply = AUTO_REPLIES[low]

    # NORMAL WORDS
    elif low in ("hi", "hello", "hey"):
        if "hi" in COMMANDS:
            reply = COMMANDS["hi"]([], ctx)

    elif low in ("menu", "help"):
        if "menu" in COMMANDS:
            reply = COMMANDS["menu"]([], ctx)

    # PREFIX COMMAND
    elif text.startswith(PREFIX):

        body = text[len(PREFIX):].strip()

        if not body:
            if "menu" in COMMANDS:
                reply = COMMANDS["menu"]([], ctx)

        else:
            parts = body.split()
            command = parts[0].lower()
            args = parts[1:]

            if command in COMMANDS:

                try:
                    print(
                        f"⚙️ Running: {command}",
                        flush=True
                    )

                    reply = COMMANDS[command](
                        args,
                        ctx
                    )

                except Exception as e:

                    print(
                        f"❌ COMMAND ERROR [{command}]: {e}",
                        flush=True
                    )

                    traceback.print_exc()

                    reply = "❌ Command error."

            else:
                reply = (
                    f"❌ Unknown command: `{command}`\n\n"
                    f"📚 Use `{PREFIX}menu`"
                )

    if reply is None:
        return

    # AUDIO
    if isinstance(reply, dict) and reply.get("type") == "audio":

        try:
            path = reply.get("path")
            title = reply.get("title", "Audio")

            if path and hasattr(cl, "direct_send_file"):

                try:
                    cl.direct_send_file(
                        path,
                        thread_ids=[thread_id]
                    )

                    print(
                        f"🎵 Audio sent: {title}",
                        flush=True
                    )

                    return

                except Exception as e:
                    print(
                        f"⚠️ AUDIO SEND ERROR: {e}",
                        flush=True
                    )

            send_text(
                cl,
                thread_id,
                f"🎵 {title}\n⚠️ Audio send failed."
            )

        finally:

            try:
                cleanup = reply.get("cleanup")

                if cleanup:
                    cleanup()

            except Exception:
                pass

        return

    # IMAGE
    if isinstance(reply, dict) and reply.get("type") == "image":

        try:
            path = reply.get("path")

            if path and hasattr(cl, "direct_send_photo"):

                try:
                    cl.direct_send_photo(
                        path,
                        thread_ids=[thread_id]
                    )

                    print(
                        "🖼️ Image sent.",
                        flush=True
                    )

                    if reply.get("caption"):
                        send_text(
                            cl,
                            thread_id,
                            reply["caption"]
                        )

                    return

                except Exception as e:
                    print(
                        f"⚠️ IMAGE SEND ERROR: {e}",
                        flush=True
                    )

            send_text(
                cl,
                thread_id,
                "🖼️ Image তৈরি হয়েছে কিন্তু send করা যায়নি."
            )

        finally:

            try:
                cleanup = reply.get("cleanup")

                if cleanup:
                    cleanup()

            except Exception:
                pass

        return

    # TEXT
    send_text(
        cl,
        thread_id,
        reply
    )

    print(
        f"↩️ Sent: {str(reply)[:100]}",
        flush=True
    )


def run_bot():

    global BOT_RUNNING
    global BOT_USERNAME

    print(
        f"🐐 {BOT_NAME} starting...",
        flush=True
    )

    sid = os.environ.get("IG_SESSIONID")

    print(
        f"SESSION FOUND: {bool(sid)}",
        flush=True
    )

    if not sid:
        print(
            "❌ IG_SESSIONID missing.",
            flush=True
        )
        return

    sid = sid.strip()
    sid = sid.strip('"').strip("'")

    try:
        sid = urllib.parse.unquote(sid)
    except Exception:
        pass

    try:

        cl = Client()

        print(
            "🔐 Logging into Instagram...",
            flush=True
        )

        cl.login_by_sessionid(sid)

        BOT_USERNAME = getattr(
            cl,
            "username",
            "Unknown"
        )

        BOT_RUNNING = True

        print(
            f"🎉 LOGIN SUCCESS: @{BOT_USERNAME}",
            flush=True
        )

    except Exception as e:

        print(
            f"❌ LOGIN FAILED: {e}",
            flush=True
        )

        traceback.print_exc()

        return

    # Ignore old messages
    last_messages = {}

    try:

        for old_thread in cl.direct_threads(amount=20):

            if old_thread.messages:

                last_messages[
                    old_thread.id
                ] = str(
                    old_thread.messages[0].id
                )

    except Exception as e:

        print(
            f"⚠️ Initial sync error: {e}",
            flush=True
        )

    print(
        "👂 DM listener started...",
        flush=True
    )

    while True:

        try:

            threads = cl.direct_threads(
                amount=20
            )

            for thread in threads:

                try:

                    if not thread.messages:
                        continue

                    msg = thread.messages[0]

                    message_id = str(
                        getattr(
                            msg,
                            "id",
                            ""
                        )
                    )

                    if not message_id:
                        continue

                    thread_id = thread.id

                    sender_id = str(
                        getattr(
                            msg,
                            "user_id",
                            ""
                        )
                    )

                    # Ignore bot's own message
                    if sender_id == str(cl.user_id):
                        continue

                    # Ignore duplicate
                    if last_messages.get(thread_id) == message_id:
                        continue

                    last_messages[thread_id] = message_id

                    text = (
                        getattr(
                            msg,
                            "text",
                            ""
                        )
                        or ""
                    ).strip()

                    if not text:
                        continue

                    print(
                        f"📩 DM: {text}",
                        flush=True
                    )

                    print(
                        f"🧵 Thread: {thread_id}",
                        flush=True
                    )

                    process_message(
                        cl,
                        thread,
                        msg
                    )

                except Exception as e:

                    print(
                        f"⚠️ THREAD ERROR: {e}",
                        flush=True
                    )

        except Exception as e:

            print(
                f"⚠️ DM LOOP ERROR: {e}",
                flush=True
            )

            traceback.print_exc()

            time.sleep(5)

        time.sleep(3)


def start_bot():
    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()


start_bot()


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "10000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
