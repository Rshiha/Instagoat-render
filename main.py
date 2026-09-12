from flask import Flask
from instagrapi import Client
from threading import Thread
import time, os, requests, random

app = Flask(__name__)
USERNAME = os.getenv("IG_USER")
PASSWORD = os.getenv("IG_PASS")
cl = Client()

def get_dl(url):
    try:
        r = requests.get(f"https://api.vreden.my.id/api/ytmp3?url={url}").json()
        if 'data' in r:
            d = r['data']
            return d.get('url') or d.get('data')
    except: pass
    return None

def goat_logic(text, sender_id, thread_id):
    text = text.lower()
    if "goat" in text or "bot" in text:
        return "Yes boss? 🐐 1-249 Ready!"
    if "song" in text or "gan" in text or "https://" in text:
        dl = get_dl(text)
        if dl:
            return f"Here is your song boss 🎵\n{dl}"
        else:
            return "Link ta dao, download kore dicchi 🎶"
    # Add your other 1-249 commands here
    responses = ["Hmm 😏", "Bolo boss 🐐", "Goat is here!", "Ki lagbe?"]
    return random.choice(responses)

def bot_loop():
    print("Bot starting...")
    print(f"USER Found: {bool(USERNAME)}")
    while True:
        try:
            if USERNAME and PASSWORD:
                cl.login(USERNAME, PASSWORD)
                print("Login Success! ✅")
            else:
                print("IG_USER / IG_PASS not set!")
                time.sleep(30)
                continue

            print("Bot is listening for messages...")
            while True:
                try:
                    threads = cl.direct_threads(20)
                    for thread in threads:
                        if not thread.messages: continue
                        msg = thread.messages[0]
                        if msg.user_id == cl.user_id: continue

                        txt = msg.text or ""
                        if not txt: continue

                        # To avoid replying twice
                        # (simple check)
                        time.sleep(2)
                        reply = goat_logic(txt, msg.user_id, thread.id)
                        if reply:
                            cl.direct_send(reply, thread_ids=[thread.id])
                            print(f"Replied to {msg.user_id}: {txt}")
                    time.sleep(5)
                except Exception as e:
                    print(f"Loop error: {e}")
                    time.sleep(10)
        except Exception as e:
            print(f"Login Fail: {e}")
            time.sleep(60)

# THIS IS THE FIX - Must be outside __main__ for Render
Thread(target=bot_loop, daemon=True).start()

@app.route('/')
def home():
    return "Goat Bot 1-249 Running 🐐🔥"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
