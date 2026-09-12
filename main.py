import os, threading
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Live!"

def run_bot():
    print("--- Bot starting ---")
    sid = os.environ.get("IG_SESSIONID")
    print(f"SESSION Found: {bool(sid)} Length: {len(sid) if sid else 0}")
    if not sid:
        print("ERROR: IG_SESSIONID missing in Render!")
        return
    try:
        from instagrapi import Client
        cl = Client()
        # sessionid এর সামনে-পিছনে space থাকলে কেটে দিবে
        cl.login_by_sessionid(sid.strip().strip('"').strip("'"))
        print(f"Login Success! User: {cl.username} ✅")
        import time
        last_id = None
        while True:
            try:
                for thread in cl.direct_threads(amount=5):
                    if thread.messages and thread.messages[0].user_id!= cl.user_id:
                        msg = thread.messages[0]
                        if last_id!= msg.id:
                            if "hi" in msg.text.lower() or "start" in msg.text.lower():
                                cl.direct_send("🐐 Goat Game Started!\nType: 1 to Play", thread_ids=[thread.id])
                                last_id = msg.id
                time.sleep(5)
            except Exception as e:
                print(f"Loop error: {e}"); time.sleep(10)
    except Exception as e:
        print(f"LOGIN FAILED: {e}")

threading.Thread(target=run_bot, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
