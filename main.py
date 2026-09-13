import os
import time
import threading
import traceback
import urllib.parse

from flask import Flask
from instagrapi import Client

from commands import COMMANDS, AUTO_REPLIES, BOT_NAME

# =========================================================
# CONFIG
# =========================================================

app = Flask(__name__)

PREFIX = os.environ.get("BOT_PREFIX", ".")
START_TIME = time.time()


# =========================================================
# BOT STATUS
# =========================================================

BOT_RUNNING = False
BOT_USERNAME = "Unknown"


# =========================================================
# FLASK
# =========================================================

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


# =========================================================
# SEND TEXT
# =========================================================

def send_text(cl, thread_id, text):
    if not text:
        return

    text = str(text)

    # Split long messages
    max_length = 1800

    chunks = [
        text[i:i + max_length]
        for i in range(0, len(text), max_length)
    ]

    for chunk in chunks:
        try:
            cl.direct_send(
                chunk,
                thread_ids=[thread_id]
            )

            time.sleep(0.5)

        except Exception as e:
            print(
                f"❌ SEND ERROR: {e}",
                flush=True
            )


# =========================================================
# GET USER INFO
# =========================================================

def get_user(cl, user_id):
    try:
        return cl.user_info(user_id)
    except Exception as e:
        print(
            f"⚠️ USER INFO ERROR: {e}",
            flush=True
        )
        return None


# =========================================================
# COMMAND CONTEXT
# =========================================================

def make_context(cl, msg, thread_id):
    user = get_user(
        cl,
        msg.user_id
    )

    username = "Unknown"

    if user:
        username = getattr(
            user,
            "username",
            "Unknown"
        )

    return {
    "client": cl,
    "user": user,
    "user_id": str(msg.user_id),
    "username": username,
    "thread_id": thread_id,
    "thread": thread,
    "message": msg
    }


# =========================================================
# PROCESS MESSAGE
# =========================================================

def process_message(cl, thread, msg):

    text = (
        getattr(
            msg,
            "text",
            ""
        )
        or ""
    ).strip()

    if not text:
        return

    thread_id = thread.id

    ctx = make_context(
        cl,
        msg,
        thread_id
    )

    low = text.lower()

    reply = None

    # =====================================================
    # AUTO REPLY
    # =====================================================

    if low in AUTO_REPLIES:

        try:
            reply = AUTO_REPLIES[low]

        except Exception as e:
            print(
                f"❌ AUTO REPLY ERROR: {e}",
                flush=True
            )

    # =====================================================
    # NORMAL WORDS
    # =====================================================

    elif low in [
        "hi",
        "hello",
        "hey"
    ]:

        if "hi" in COMMANDS:
            reply = COMMANDS["hi"](
                [],
                ctx
            )

    elif low in [
        "menu",
        "help"
    ]:

        if "menu" in COMMANDS:
            reply = COMMANDS["menu"](
                [],
                ctx
            )

    # =====================================================
    # PREFIX COMMAND
    # =====================================================

    elif text.startswith(PREFIX):

        body = text[
            len(PREFIX):
        ].strip()

        if not body:

            if "menu" in COMMANDS:
                reply = COMMANDS["menu"](
                    [],
                    ctx
                )

        else:

            parts = body.split()

            command = (
                parts[0].lower()
            )

            args = parts[1:]

            # ---------------------------------------------
            # COMMAND FOUND
            # ---------------------------------------------

            if command in COMMANDS:

                try:

                    reply = COMMANDS[
                        command
                    ](
                        args,
                        ctx
                    )

                except Exception as e:

                    print(
                        f"❌ COMMAND ERROR "
                        f"[{command}]: {e}",
                        flush=True
                    )

                    traceback.print_exc()

                    reply = (
                        "❌ Command error.\n"
                        "Please try again."
                    )

            # ---------------------------------------------
            # UNKNOWN COMMAND
            # ---------------------------------------------

            else:

                reply = (
                    f"❌ Unknown command: `{command}`\n\n"
                    f"📚 Use `{PREFIX}menu`"
                )

    # =====================================================
    # SEND REPLY
    # =====================================================

    if reply is None:
        return

    # -----------------------------------------------------
    # AUDIO RESULT
    # -----------------------------------------------------

    if isinstance(reply, dict):

        if reply.get("type") == "audio":

            try:

                path = reply.get("path")
                title = reply.get(
                    "title",
                    "Audio"
                )

                if not path:
                    send_text(
                        cl,
                        thread_id,
                        "❌ Audio file not found."
                    )
                    return

                # Try Instagram file upload
                if hasattr(
                    cl,
                    "direct_send_file"
                ):

                    try:

                        cl.direct_send_file(
                            path,
                            thread_ids=[
                                thread_id
                            ]
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

                # If upload is unavailable
                send_text(
                    cl,
                    thread_id,
                    (
                        f"🎵 {title}\n\n"
                        "⚠️ Audio downloaded successfully, "
                        "but this Instagram client cannot "
                        "send the audio attachment."
                    )
                )

            finally:

                # Cleanup downloaded file
                try:
                    cleanup = reply.get(
                        "cleanup"
                    )

                    if cleanup:
                        cleanup()

                except Exception as e:

                    print(
                        f"⚠️ CLEANUP ERROR: {e}",
                        flush=True
                    )

            return

    # -----------------------------------------------------
    # NORMAL TEXT
    # -----------------------------------------------------

    send_text(
        cl,
        thread_id,
        reply
    )

    print(
        f"↩️ Sent: {str(reply)[:100]}",
        flush=True
    )


# =========================================================
# INSTAGRAM BOT
# =========================================================

def run_bot():

    global BOT_RUNNING
    global BOT_USERNAME

    print(
        "================================",
        flush=True
    )

    print(
        f"🐐 {BOT_NAME}",
        flush=True
    )

    print(
        f"📚 Commands: {len(COMMANDS)}",
        flush=True
    )

    print(
        "================================",
        flush=True
    )

    # =====================================================
    # SESSION
    # =====================================================

    sid = os.environ.get(
        "IG_SESSIONID"
    )

    print(
        f"SESSION FOUND: {bool(sid)} "
        f"Length: {len(sid) if sid else 0}",
        flush=True
    )

    if not sid:

        print(
            "❌ IG_SESSIONID is missing.",
            flush=True
        )

        return

    # Clean session value
    sid = sid.strip()

    sid = sid.strip('"')
    sid = sid.strip("'")

    try:

        sid = urllib.parse.unquote(
            sid
        )

    except Exception:
        pass

    # =====================================================
    # LOGIN
    # =====================================================

    try:

        print(
            "🔐 Trying Instagram login...",
            flush=True
        )

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
            f"🎉 LOGIN SUCCESS: "
            f"@{BOT_USERNAME}",
            flush=True
        )

        print(
            f"🆔 User ID: {cl.user_id}",
            flush=True
        )

        print(
            f"✅ {len(COMMANDS)} commands loaded.",
            flush=True
        )

    except Exception as e:

        BOT_RUNNING = False

        print(
            f"❌ LOGIN FAILED: {e}",
            flush=True
        )

        traceback.print_exc()

        return

    # =====================================================
    # MESSAGE CACHE (Initial sync to ignore old messages)
    # =====================================================

    last_messages = {}
    try:
        initial_threads = cl.direct_threads(amount=20)
        for thread in initial_threads:
            if thread.messages:
                last_messages[thread.id] = str(thread.messages[0].id)
    except Exception:
        pass

    # =====================================================
    # DM LOOP
    # =====================================================

    while True:

        try:

            threads = cl.direct_threads(
                amount=20
            )

            for thread in threads:

                try:

                    # No messages
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

                    thread_id = thread.id

                    # =================================================
                    # IGNORE BOT'S OWN MESSAGE
                    # =================================================

                    sender_id = str(
                        getattr(
                            msg,
                            "user_id",
                            ""
                        )
                    )

                    if sender_id == str(
                        cl.user_id
                    ):
                        continue

                    # =================================================
                    # DUPLICATE CHECK
                    # =================================================

                    if (
                        last_messages.get(
                            thread_id
                        )
                        == message_id
                    ):
                        continue

                    # Mark immediately
                    last_messages[
                        thread_id
                    ] = message_id

                    # =================================================
                    # TEXT
                    # =================================================

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

                    # =================================================
                    # PROCESS
                    # =================================================

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

                    traceback.print_exc()

        except Exception as e:

            print(
                f"⚠️ DM LOOP ERROR: {e}",
                flush=True
            )

            traceback.print_exc()

            # Prevent aggressive retry
            time.sleep(5)

        time.sleep(3)


# =========================================================
# START BOT THREAD
# =========================================================

def start_bot():

    thread = threading.Thread(
        target=run_bot,
        daemon=True
    )

    thread.start()


# =========================================================
# START
# =========================================================

start_bot()


# =========================================================
# RENDER SERVER
# =========================================================

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

    
