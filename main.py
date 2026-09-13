import os
import time
import threading
import traceback
import urllib.parse
import re
from flask import Flask
from instagrapi import Client
from commands import COMMANDS, BOT_NAME
from commands.downloader import auto_detect, download_video

app = Flask(__name__)
PREFIX = os.environ.get("BOT_PREFIX", ".")
START_TIME = time.time()
BOT_RUNNING = False
BOT_USERNAME = "Unknown"

@app.route("/")
def home():
    return f"🐐 {BOT_NAME} LIVE! @{BOT_USERNAME}"
@app.route("/health")
def health():
    return {"status":"online","bot":BOT_NAME,"username":BOT_USERNAME,"running":BOT_RUNNING}

def send_text(cl, tid, text):
    if not text: return
    if isinstance(text, dict) and "photo" in text:
        try:
            cl.direct_send_photo(text["photo"], thread_ids=[tid])
            time.sleep(0.5)
            if text.get("caption"):
                cl.direct_send(text["caption"], thread_ids=[tid])
            return
        except Exception as e:
            print(f"PHOTO ERR {e}", flush=True)
            text = text.get("caption", "❌ Photo fail")
    txt = str(text)
    for i in range(0, len(txt), 1800):
        try:
            cl.direct_send(txt[i:i+1800], thread_ids=[tid])
            time.sleep(0.5)
        except Exception as e:
            print(f"SEND ERR {e}", flush=True)

def get_user(cl, uid):
    try: return cl.user_info(int(uid))
    except: return None

def make_context(cl, msg, thread):
    user = get_user(cl, msg.user_id)
    replied_user = None
    try:
        # ✅ NEW REPLY FIX
        reply_data = getattr(msg, 'reply', None) or getattr(msg, 'replied_to_message', None)
        if reply_data:
            r_uid = str(getattr(reply_data, 'user_id', '') or getattr(reply_data, 'userId', ''))
            if r_uid and r_uid!= str(cl.user_id):
                r_user = get_user(cl, r_uid)
                if r_user:
                    replied_user = {
                        "user_id": str(r_user.pk), "username": r_user.username,
                        "full_name": r_user.full_name, "profile_pic_url": str(r_user.profile_pic_url),
                        "followers": r_user.follower_count, "following": r_user.following_count,
                        "posts": r_user.media_count, "bio": r_user.biography
                    }
                    print(f"✅ REPLY FOUND {r_user.username}", flush=True)

        if not replied_user:
            print(f"--- DEBUG {msg.text} len {len(thread.messages)}", flush=True)
            for m in thread.messages[1:20]:
                uid = str(getattr(m, 'user_id', ''))
                if not uid or uid == str(cl.user_id) or uid == str(msg.user_id): continue
                r_user = get_user(cl, m.user_id)
                if r_user:
                    replied_user = {
                        "user_id": str(r_user.pk), "username": r_user.username,
                        "full_name": r_user.full_name, "profile_pic_url": str(r_user.profile_pic_url),
                        "followers": r_user.follower_count, "following": r_user.following_count,
                        "posts": r_user.media_count, "bio": r_user.biography
                    }
                    print(f"✅ FOUND FALLBACK {r_user.username}", flush=True)
                    break
    except Exception as e:
        print(f"Reply err {e}", flush=True)

    return {
        "client": cl, "user": user, "user_id": str(msg.user_id),
        "username": getattr(user, "username", "Unknown") if user else "Unknown",
        "full_name": getattr(user, "full_name", "Unknown") if user else "Unknown",
        "profile_pic_url": str(getattr(user, "profile_pic_url", "")) if user else "",
        "followers": getattr(user, "follower_count", 0) if user else 0,
        "following": getattr(user, "following_count", 0) if user else 0,
        "posts": getattr(user, "media_count", 0) if user else 0,
        "bio": getattr(user, "biography", "") if user else "",
        "start_time": START_TIME, "thread_id": thread.id,
        "thread": thread, "message": msg, "replied_user": replied_user
    }

def process_message(cl, thread, msg):
    text = (getattr(msg, "text", "") or "").strip()
    if not text: return
    tid = thread.id
    ctx = make_context(cl, msg, thread)
    low = text.lower()

    # ✅ AUTO DOWNLOADER - jodi link hoy ar command na hoy
    if not text.startswith(PREFIX):
        a_url = auto_detect(text)
        if a_url:
            try:
                cl.direct_send(f"⏳ Downloading...\n🔗 {a_url}", thread_ids=[tid])
                path = download_video(a_url)
                if path and os.path.exists(path):
                    if os.path.getsize(path) > 90*1024*1024:
                        send_text(cl, tid, "❌ 90MB+ besi, pathano jabena!")
                    else:
                        cl.direct_send_file(path, thread_ids=[tid])
                    try: os.remove(path)
                    except: pass
                else:
                    send_text(cl, tid, "❌ Download failed! Private video hote pare!")
            except Exception as e:
                print(f"AUTO DL ERR {e}", flush=True)
            # auto er por command check korbona

    result = None
    if low in ("hi", "hello", "hey"):
        result = COMMANDS.get("hi", lambda a,c: None)([], ctx)
    elif low in ("menu", "help"):
        result = COMMANDS.get("menu", lambda a,c: None)([], ctx)
    elif text.startswith(PREFIX):
        body = text[len(PREFIX):].strip()
        if not body:
            result = COMMANDS.get("menu", lambda a,c: None)([], ctx)
        else:
            p = body.split()
            cmd, args = p[0].lower(), p[1:]
            if cmd in COMMANDS:
                try: result = COMMANDS[cmd](args, ctx)
                except: traceback.print_exc(); result = "❌ Command error."
            else:
                result = f"❌ Unknown: {cmd}"

    if result is None: return
    if isinstance(result, dict) and result.get("type") == "audio":
        try:
            if result.get("path"): cl.direct_send_file(result["path"], thread_ids=[tid])
        finally:
            try:
                if result.get("cleanup"): result["cleanup"]()
            except: pass
        return
    send_text(cl, tid, result)

def run_bot():
    global BOT_RUNNING, BOT_USERNAME
    sid = os.environ.get("IG_SESSIONID")
    if not sid: return
    sid = urllib.parse.unquote(sid.strip().strip('"').strip("'"))
    try:
        cl = Client()
        cl.login_by_sessionid(sid)
        BOT_USERNAME = getattr(cl, "username", "Unknown")
        BOT_RUNNING = True
        print(f"🎉 LOGIN @{BOT_USERNAME}", flush=True)
    except Exception as e:
        print(f"LOGIN FAIL {e}", flush=True)
        return

    last = {}
    try:
        for t in cl.direct_threads(amount=20, thread_message_limit=25):
            if t.messages: last[t.id] = str(t.messages[0].id)
    except: pass

    while True:
        try:
            for thread in cl.direct_threads(amount=20, thread_message_limit=25):
                if not thread.messages: continue
                msg = thread.messages[0]
                mid = str(getattr(msg, "id", ""))
                if not mid or str(getattr(msg, "user_id", "")) == str(cl.user_id): continue
                if last.get(thread.id) == mid: continue
                last[thread.id] = mid
                if not (getattr(msg, "text", "") or "").strip(): continue
                print(f"📩 {msg.text}", flush=True)
                process_message(cl, thread, msg)
        except Exception as e:
            print(f"LOOP ERR {e}", flush=True)
            time.sleep(5)
        time.sleep(3)

threading.Thread(target=run_bot, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
