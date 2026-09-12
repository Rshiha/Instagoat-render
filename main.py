import os
import threading
import time
import traceback
import random
from datetime import datetime

from flask import Flask

app = Flask(__name__)

BOT_NAME = "Your Father Shihab"
PREFIX = os.environ.get("BOT_PREFIX", ".")

# =========================
# COMMANDS
# =========================

def cmd_hi(args, ctx):
    return f"👋 Hello! I am {BOT_NAME} 🐐"

def cmd_hello(args, ctx):
    return f"👋 Hello from {BOT_NAME} ❤️"

def cmd_ping(args, ctx):
    return "🏓 Pong!"

def cmd_time(args, ctx):
    return f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

def cmd_uptime(args, ctx):
    seconds = int(time.time() - START_TIME)
    return f"⏱️ Bot uptime: {seconds} seconds"

def cmd_menu(args, ctx):
    return (
        f"🐐 {BOT_NAME}\n\n"
        "📌 AVAILABLE COMMANDS\n\n"
        ".ping\n"
        ".hi\n"
        ".hello\n"
        ".menu\n"
        ".help\n"
        ".info\n"
        ".pair\n"
        ".pair2\n"
        ".pair3\n"
        ".time\n"
        ".uptime\n"
        ".joke\n"
        ".quote\n"
        ".dice\n"
        ".coinflip\n"
        ".8ball\n"
        ".math\n"
        ".say <text>\n"
        ".reverse <text>\n"
        ".upper <text>\n"
        ".lower <text>\n"
        ".count <text>\n"
        ".font <text>\n"
    )

def cmd_help(args, ctx):
    return cmd_menu(args, ctx)

def cmd_info(args, ctx):
    """
    Shows public information available from the Instagram
    message sender/profile.
    """
    try:
        user = ctx.get("user")

        if user:
            username = getattr(user, "username", None) or "Unknown"
            full_name = getattr(user, "full_name", None) or "Unknown"
            user_id = getattr(user, "pk", None) or ctx.get("user_id", "Unknown")
            followers = getattr(user, "follower_count", None)
            following = getattr(user, "following_count", None)
            posts = getattr(user, "media_count", None)
            private = getattr(user, "is_private", None)
            verified = getattr(user, "is_verified", None)
            bio = getattr(user, "biography", None) or "No bio"

            return (
                f"👤 {BOT_NAME}\n\n"
                f"Name: {full_name}\n"
                f"Username: @{username}\n"
                f"User ID: {user_id}\n"
                f"Followers: {followers if followers is not None else 'Unknown'}\n"
                f"Following: {following if following is not None else 'Unknown'}\n"
                f"Posts: {posts if posts is not None else 'Unknown'}\n"
                f"Private: {'Yes' if private else 'No'}\n"
                f"Verified: {'Yes' if verified else 'No'}\n"
                f"Bio: {bio}"
            )

        return (
            f"👤 {BOT_NAME}\n\n"
            f"Username: @{ctx.get('username', 'Unknown')}\n"
            f"User ID: {ctx.get('user_id', 'Unknown')}"
        )

    except Exception as e:
        print(f"INFO ERROR: {e}", flush=True)
        return "❌ Could not get Instagram profile information."

# =========================
# PAIR COMMANDS
# =========================

def cmd_pair(args, ctx):
    return (
        "🔗 PAIR\n\n"
        "Pairing system started.\n"
        "Use .pair2 for the next step."
    )

def cmd_pair2(args, ctx):
    return (
        "🔗 PAIR 2\n\n"
        "Second pairing step started.\n"
        "Use .pair3 to continue."
    )

def cmd_pair3(args, ctx):
    return (
        "🔗 PAIR 3\n\n"
        "✅ Pairing sequence completed."
    )

# =========================
# FUN COMMANDS
# =========================

def cmd_joke(args, ctx):
    jokes = [
        "😂 Why did the computer go to the doctor? It had a virus!",
        "😂 Why was the math book sad? It had too many problems.",
        "😂 Programmers don't like nature because it has too many bugs."
    ]
    return random.choice(jokes)

def cmd_quote(args, ctx):
    quotes = [
        "✨ Progress is better than perfection.",
        "🔥 Keep going.",
        "💫 Small steps become big results."
    ]
    return random.choice(quotes)

def cmd_dice(args, ctx):
    return f"🎲 You rolled: {random.randint(1, 6)}"

def cmd_coinflip(args, ctx):
    return "🪙 " + random.choice(["Heads!", "Tails!"])

def cmd_8ball(args, ctx):
    return "🎱 " + random.choice([
        "Yes.",
        "No.",
        "Definitely.",
        "Probably.",
        "Ask again later."
    ])

def cmd_math(args, ctx):
    expression = " ".join(args)

    if not expression:
        return f"🧮 Usage: {PREFIX}math 10+20"

    allowed = "0123456789+-*/(). %"

    if any(c not in allowed for c in expression):
        return "❌ Only basic mathematics is allowed."

    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"🧮 {expression} = {result}"
    except Exception:
        return "❌ Invalid calculation."

# =========================
# TEXT COMMANDS
# =========================

def cmd_say(args, ctx):
    return " ".join(args) if args else f"Usage: {PREFIX}say <text>"

def cmd_reverse(args, ctx):
    text = " ".join(args)
    return text[::-1] if text else f"Usage: {PREFIX}reverse <text>"

def cmd_upper(args, ctx):
    text = " ".join(args)
    return text.upper() if text else f"Usage: {PREFIX}upper <text>"

def cmd_lower(args, ctx):
    text = " ".join(args)
    return text.lower() if text else f"Usage: {PREFIX}lower <text>"

def cmd_count(args, ctx):
    text = " ".join(args)

    return (
        f"🔢 Characters: {len(text)}\n"
        f"Words: {len(text.split())}"
    )

def cmd_font(args, ctx):
    text = " ".join(args)

    if not text:
        return f"Usage: {PREFIX}font <text>"

    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    fancy = (
        "𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"
        "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫"
    )

    table = str.maketrans(normal, fancy)
    return text.translate(table)

# =========================
# COMMAND TABLE
# =========================

COMMANDS = {
    "hi": cmd_hi,
    "hello": cmd_hello,
    "ping": cmd_ping,
    "time": cmd_time,
    "uptime": cmd_uptime,
    "menu": cmd_menu,
    "help": cmd_help,
    "info": cmd_info,

    "pair": cmd_pair,
    "pair2": cmd_pair2,
    "pair3": cmd_pair3,

    "joke": cmd_joke,
    "quote": cmd_quote,
    "dice": cmd_dice,
    "coinflip": cmd_coinflip,
    "8ball": cmd_8ball,
    "math": cmd_math,

    "say": cmd_say,
    "reverse": cmd_reverse,
    "upper": cmd_upper,
    "lower": cmd_lower,
    "count": cmd_count,
    "font": cmd_font,
}

START_TIME = time.time()

# =========================
# INSTAGRAM BOT
# =========================

def run_bot():

    print("================================", flush=True)
    print(f"🐐 {BOT_NAME}", flush=True)
    print("================================", flush=True)

    sid = os.environ.get("IG_SESSIONID")

    print(
        f"SESSION FOUND: {bool(sid)} "
        f"Length: {len(sid) if sid else 0}",
        flush=True
    )

    if not sid:
        print("❌ IG_SESSIONID missing!", flush=True)
        return

    sid = sid.strip().strip('"').strip("'")

    try:
        import urllib.parse
        sid = urllib.parse.unquote(sid)
    except Exception:
        pass

    # Load Instagram library
    try:
        print("Loading instagrapi...", flush=True)

        from instagrapi import Client

        print("✅ instagrapi loaded.", flush=True)

    except Exception as e:
        print(f"❌ INSTAGRAPI ERROR: {e}", flush=True)
        traceback.print_exc()
        return

    # Create client
    try:
        cl = Client()

        print("✅ Instagram client created.", flush=True)

    except Exception as e:
        print(f"❌ CLIENT ERROR: {e}", flush=True)
        traceback.print_exc()
        return

    # Login
    try:
        print("🔐 Trying Instagram login...", flush=True)

        cl.login_by_sessionid(sid)

        print(
            f"🎉 LOGIN SUCCESS: @{cl.username}",
            flush=True
        )

        print(
            f"🆔 User ID: {cl.user_id}",
            flush=True
        )

    except Exception as e:
        print(
            f"❌ LOGIN FAILED: {type(e).__name__}: {e}",
            flush=True
        )

        traceback.print_exc()
        return

    print(
        f"✅ {len(COMMANDS)} Instagram commands loaded.",
        flush=True
    )

    last_message = {}

    while True:

        try:

            threads = cl.direct_threads(amount=20)

            for thread in threads:

                if not thread.messages:
                    continue

                msg = thread.messages[0]

                # Don't reply to ourselves
                if str(msg.user_id) == str(cl.user_id):
                    continue

                # Don't process same message again
                if last_message.get(thread.id) == msg.id:
                    continue

                text = getattr(msg, "text", "") or ""
                text = text.strip()

                if not text:
                    last_message[thread.id] = msg.id
                    continue

                print(
                    f"📩 DM: {text}",
                    flush=True
                )

                # Try to get sender profile
                sender = None

                try:
                    sender = cl.user_info(msg.user_id)
                except Exception as e:
                    print(
                        f"Profile lookup failed: {e}",
                        flush=True
                    )

                ctx = {
                    "user_id": str(msg.user_id),
                    "username": getattr(
                        sender,
                        "username",
                        "Unknown"
                    ) if sender else "Unknown",
                    "user": sender,
                }

                # Natural greetings
                low = text.lower()

                if low in ["hi", "hello", "hey"]:
                    reply = cmd_hi([], ctx)

                elif low in ["menu", "help"]:
                    reply = cmd_menu([], ctx)

                elif text.startswith(PREFIX):

                    body = text[len(PREFIX):].strip()

                    if not body:
                        reply = cmd_menu([], ctx)

                    else:

                        parts = body.split()

                        command = parts[0].lower()
                        args = parts[1:]

                        if command in COMMANDS:

                            try:
                                reply = COMMANDS[
                                    command
                                ](args, ctx)

                            except Exception as e:

                                print(
                                    f"Command error: {e}",
                                    flush=True
                                )

                                traceback.print_exc()

                                reply = "❌ Command error."

                        else:

                            reply = (
                                f"❌ Unknown command: "
                                f"{command}\n"
                                f"Use {PREFIX}menu"
                            )

                else:
                    reply = None

                if reply:

                    cl.direct_send(
                        reply,
                        thread_ids=[thread.id]
                    )

                    print(
                        f"↩️ Reply sent: {reply[:100]}",
                        flush=True
                    )

                last_message[thread.id] = msg.id

        except Exception as e:

            print(
                f"⚠️ DM LOOP ERROR: "
                f"{type(e).__name__}: {e}",
                flush=True
            )

            traceback.print_exc()

        time.sleep(4)


# =========================
# FLASK
# =========================

@app.route("/")
def home():

    return (
        f"🐐 {BOT_NAME} is LIVE! "
        f"{len(COMMANDS)} Instagram commands."
    )


@app.route("/health")
def health():

    return {
        "status": "online",
        "bot": BOT_NAME,
        "commands": len(COMMANDS)
    }


threading.Thread(
    target=run_bot,
    daemon=True
).start()


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get("PORT", "10000")
        )
)
