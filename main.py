import os, threading, time, traceback
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home(): return "Goat Bot Live!"

def run_bot():
    print("--- Bot starting ---")
    sid = os.environ.get("IG_SESSIONID")
    print(f"SESSION Found: {bool(sid)} Length: {len(sid) if sid else 0}")
    if not sid:
        print("IG_SESSIONID Missing!")
        return
    sid = sid.strip().strip('"').strip("'")
    # Decode %3A -> :
    try:
        import urllib.parse
        sid = urllib.parse.unquote(sid)
        print(f"Decoded Length: {len(sid)}")
    except: pass

    try:
        from instagrapi import Client
        cl = Client()
        print("Trying login_by_sessionid...")
        cl.login_by_sessionid(sid)
        print(f"✅ LOGIN SUCCESS! Username: {cl.username}")
        print("Bot is now listening for DMs...")

        last_id = None
        while True:
            for thread in cl.direct_threads(amount=5):
                if thread.messages and thread.messages[0].user_id!= cl.user_id:
                    msg = thread.messages[0]
                    if last_id!= msg.id:
                        print(f"New DM: {msg.text}")
                        if "hi" in msg.text.lower():
                            cl.direct_send("🐐 Goat Bot Online! Type menu", thread_ids=[thread.id])
                            last_id = msg.id
            time.sleep(5)
    except Exception as e:
        print(f"❌ LOGIN FAILED: {e}")
        traceback.print_exc()

threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
