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
    return f"🐐 {BOT_NAME} LIVE!\n🤖 Username: @{BOT_USERNAME}\n📚 Commands: {len(COMMANDS)}"

@app.route("/health")
def health():
    return {"status":"online","bot":BOT_NAME,"username":BOT_USERNAME, "commands":len(COMMANDS),"running":BOT_RUNNING, "uptime":int(time.time()-START_TIME)}

def send_text(cl, tid, text):
    if not text: return
    for i in range(0, len(str(text)), 1800):
        try:
            cl.direct_send(str(text)[i:i+1800], thread_ids=[tid])
            time.sleep(.5)
        except Exception as e:
            print(f"❌ SEND ERROR: {e}", flush=True)

def get_user(cl, uid):
    try: return cl.user_info(uid)
    except: return None

def make_context(cl, msg, thread):
    user = get_user(cl, msg.user_id)
    return {"client":cl,"user":user,"user_id":str(msg.user_id), "username":getattr(user,"username","Unknown"), "thread_id":thread.id,"thread":thread,"message":msg}

def process_message(cl, thread, msg):
    text = (getattr(msg,"text","") or "").strip()
    if not text: return
    tid = thread.id
    ctx = make_context(cl,msg,thread)
    low = text.lower()

    # ====== EKHANE BOSHAISIIII - NUMBER 1,2,3 SYSTEM ======
    if text.strip().isdigit():
        try:
            from commands.media import PENDING_SEARCH, get_youtube_audio_by_url
            print(f"🔢 NUMBER SELECT: {text} | KEYS: {list(PENDING_SEARCH.keys())}", flush=True)
            if PENDING_SEARCH:
                last_key = list(PENDING_SEARCH.keys())[-1]
                results = PENDING_SEARCH[last_key]
                idx = int(text.strip()) - 1
                if 0 <= idx < len(results):
                    selected = results[idx]
                    PENDING_SEARCH.clear()
                    send_text(cl, tid, f"⏳ Downloading: {selected['title']}...")
                    file_path, title = get_youtube_audio_by_url(selected['id'], selected['title'])
                    if not file_path:
                        send_text(cl, tid, "❌ ডাউনলোড Fail! Cookies Expired!")
                        return
                    try:
                        cl.direct_send_file(file_path, thread_ids=[tid])
                    finally:
                        try: os.remove(file_path)
                        except: pass
                    return
        except Exception as e:
            print(f"SELECT ERROR: {e}", flush=True)
            traceback.print_exc()
    # ====== END ======

    result = None
    if low in ("hi","hello","hey"):
        result = COMMANDS.get("hi",lambda a,c:None)([],ctx)
    elif low in ("menu","help"):
        result = COMMANDS.get("menu",lambda a,c:None)([],ctx)
    elif text.startswith(PREFIX):
        body = text[len(PREFIX):].strip()
        if not body:
            result = COMMANDS.get("menu",lambda a,c:None)([],ctx)
        else:
            p = body.split()
            cmd,args = p[0].lower(),p[1:]
            if cmd in COMMANDS:
                try: result = COMMANDS[cmd](args,ctx)
                except: traceback.print_exc(); result = "❌ Command error."
            else:
                result = f"❌ Unknown: {cmd}"

    if result is None: return
    if isinstance(result,dict) and result.get("type")=="audio":
        path=result.get("path")
        try:
            if path: cl.direct_send_file(path,thread_ids=[tid])
        finally:
            try:
                if result.get("cleanup"): result["cleanup"]()
            except: pass
        return
    send_text(cl,tid,result)

def run_bot():
    global BOT_RUNNING,BOT_USERNAME
    sid=os.environ.get("IG_SESSIONID")
    if not sid: return
    sid=urllib.parse.unquote(sid.strip().strip('"').strip("'"))
    try:
        cl=Client()
        cl.login_by_sessionid(sid)
        BOT_USERNAME=getattr(cl,"username","Unknown")
        BOT_RUNNING=True
        print(f"🎉 LOGIN SUCCESS: @{BOT_USERNAME}",flush=True)
    except Exception as e:
        print(f"❌ LOGIN FAILED: {e}",flush=True); return
    last={}
    try:
        for t in cl.direct_threads(amount=20):
            if t.messages: last[t.id]=str(t.messages[0].id)
    except: pass
    while True:
        try:
            for thread in cl.direct_threads(amount=20):
                if not thread.messages: continue
                msg=thread.messages[0]
                mid=str(getattr(msg,"id",""))
                if not mid or str(getattr(msg,"user_id",""))==str(cl.user_id): continue
                if last.get(thread.id)==mid: continue
                last[thread.id]=mid
                if not (getattr(msg,"text","") or "").strip(): continue
                print(f"📩 DM: {msg.text}",flush=True)
                process_message(cl,thread,msg)
        except Exception as e:
            print(f"⚠️ DM LOOP ERROR: {e}",flush=True)
            time.sleep(5)
        time.sleep(3)

threading.Thread(target=run_bot,daemon=True).start()
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT","10000")))
