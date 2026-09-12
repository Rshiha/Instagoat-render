import os, time, threading
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home(): return "Bot Live with Cookies!"

def run_bot():
    print("--- Bot starting with SESSION ---")
    SESSIONID = os.environ.get("IG_SESSIONID")
    print(f"SESSION Found: {bool(SESSIONID)}")
    if not SESSIONID:
        print("ERROR: IG_SESSIONID missing!")
        return
    try:
        from instagrapi import Client
        cl = Client()
        cl.login_by_sessionid(SESSIONID)
        print(f"Login Success with Cookies! ✅ User: {cl.username}")

        last_id = None
        while True:
            try:
                threads = cl.direct_threads(amount=5)
                for t in threads:
                    if t.messages and t.messages[0].user_id!= cl.user_id:
                        m = t.messages[0]
                        if last_id!= m.id and m.text.lower() in ["hi","hello","start","play"]:
                            cl.direct_send("🐐 Welcome to Goat Game!\n1. Play\n2. Help", thread_ids=[t.id])
                            last_id = m.id
                time.sleep(5)
            except Exception as e:
                print(f"Loop error: {e}"); time.sleep(10)
    except Exception as e:
        print(f"Login Failed with Cookies: {e}")

threading.Thread(target=run_bot, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
