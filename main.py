import os
import threading
import time
import traceback
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "🐐 Goat Bot Login Test Live!"


def run_bot():
    print("================================")
    print("🐐 BOT LOGIN TEST STARTING")
    print("================================", flush=True)

    # 1. Session check
    sid = os.environ.get("IG_SESSIONID")

    print(
        f"1️⃣ SESSION FOUND: {bool(sid)} | LENGTH: {len(sid) if sid else 0}",
        flush=True
    )

    if not sid:
        print("❌ IG_SESSIONID is missing!", flush=True)
        return

    sid = sid.strip().strip('"').strip("'")

    # 2. Decode
    try:
        import urllib.parse
        sid = urllib.parse.unquote(sid)
        print(
            f"2️⃣ SESSION READY | LENGTH: {len(sid)}",
            flush=True
        )
    except Exception as e:
        print(f"❌ Session decode error: {e}", flush=True)
        return

    # 3. Import instagrapi
    try:
        print("3️⃣ Loading instagrapi...", flush=True)

        from instagrapi import Client

        print("✅ instagrapi loaded!", flush=True)

    except Exception as e:
        print(f"❌ INSTAGRAPI IMPORT FAILED: {e}", flush=True)
        traceback.print_exc()
        return

    # 4. Create client
    try:
        print("4️⃣ Creating Instagram client...", flush=True)

        cl = Client()

        print("✅ Client created!", flush=True)

    except Exception as e:
        print(f"❌ CLIENT ERROR: {e}", flush=True)
        traceback.print_exc()
        return

    # 5. Login
    try:
        print("5️⃣ Trying Instagram login...", flush=True)

        cl.login_by_sessionid(sid)

        print("🎉 LOGIN SUCCESS!", flush=True)
        print(f"👤 Username: {cl.username}", flush=True)
        print(f"🆔 User ID: {cl.user_id}", flush=True)

    except Exception as e:
        print(f"❌ LOGIN FAILED: {type(e).__name__}: {e}", flush=True)
        traceback.print_exc()
        return

    # Keep bot alive
    while True:
        time.sleep(60)


threading.Thread(target=run_bot, daemon=True).start()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
