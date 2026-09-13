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
    return {"status":"online","bot":BOT_NAME,"username":BOT_USERNAME,
            "commands":len(COMMANDS),"running":BOT_RUNNING,
            "uptime":int(time.time()-START_TIME)}

def send_text(cl, tid, text):
    if not text: return
    for i in range(0, len(str(text)), 1800):
        try:
            cl.direct_send(str(text)[i:i+1800], thread_ids=[tid])
            time.sleep(.5)
        except Exception as e: print(f"❌ SEND ERROR: {e}", flush=True)

def get_user(cl, uid):
    try: return cl.user_info(uid)
    except Exception as e:
        print(f"⚠️ USER INFO ERROR: {e}", flush=True)
        return None

def make_context(cl, msg, thread):
    user = get_user(cl, msg.user_id)
    return {"client":cl,"user":user,"user_id":str(msg.user_id),
            "username":getattr(user,"username","Unknown"),
            "thread_id":thread.id,"thread":thread,"message":msg}

def get_replied_message_id(msg):
    r = getattr(msg, "reply", None)
    if not r: return None
    for a in ("message_id","id"):
        v = getattr(r,a,None)
        if v: return str(v)
    n = getattr(r,"reply_to_message",None)
    if n:
        for a in ("message_id","id"):
            v = getattr(n,a,None)
            if v: return str(v)
    return None

def process_message(cl, thread, msg):
    text = (getattr(msg,"text","") or "").strip()
    if not text: return
    tid = thread.id
    ctx = make_context(cl,msg,thread)
    low = text.lower()

    # Reply to a bot message with "uns" to unsend it
    if low == "uns":
        target_id = get_replied_message_id(msg)
        if not target_id:
            send_text(cl,tid,"❌ Bot-er message-e reply kore `uns` likho.")
            return
        try:
            target = cl.direct_message(tid,int(target_id))
            if not getattr(target,"is_sent_by_viewer",False):
                send_text(cl,tid,"❌ Sudhu bot-er nijer message unsend kora jabe.")
            elif cl.direct_message_unsend(tid,int(target_id)):
                print(f"🗑️ Bot message unsent: {target_id}",flush=True)
            else:
                send_text(cl,tid,"❌ Message unsend kora jayni.")
        except Exception as e:
            print(f"❌ UNSEND ERROR: {e}",flush=True)
            send_text(cl,tid,"❌ Message unsend kora jayni.")
        return

    result = AUTO_REPLIES.get(low)

    if result is None and low in ("hi","hello","hey"):
        result = COMMANDS.get("hi",lambda a,c:None)([],ctx)
    elif result is None and low in ("menu","help"):
        result = COMMANDS.get("menu",lambda a,c:None)([],ctx)
    elif result is None and text.startswith(PREFIX):
        body = text[len(PREFIX):].strip()
        if not body:
            result = COMMANDS.get("menu",lambda a,c:None)([],ctx)
        else:
            p = body.split()
            cmd,args = p[0].lower(),p[1:]
            if cmd in COMMANDS:
                try: result = COMMANDS[cmd](args,ctx)
                except Exception:
                    traceback.print_exc(); result = "❌ Command error."
            else:
                result = f"❌ Unknown command: `{cmd}`\n\n📚 Use `{PREFIX}menu`"

    if result is None: return

    if isinstance(result,dict) and result.get("type")=="audio":
        path=result.get("path"); title=result.get("title","Audio")
        try:
            if path and hasattr(cl,"direct_send_file"):
                cl.direct_send_file(path,thread_ids=[tid]); return
            send_text(cl,tid,f"🎵 {title}\n⚠️ Audio send failed.")
        finally:
            try:
                if result.get("cleanup"): result["cleanup"]()
            except Exception: pass
        return

    if isinstance(result,dict) and result.get("type")=="image":
        path=result.get("path")
        try:
            if path and hasattr(cl,"direct_send_photo"):
                cl.direct_send_photo(path,thread_ids=[tid])
                if result.get("caption"): send_text(cl,tid,result["caption"])
                return
            send_text(cl,tid,"🖼️ Image তৈরি হয়েছে কিন্তু send করা যায়নি.")
        finally:
            try:
                if result.get("cleanup"): result["cleanup"]()
            except Exception: pass
        return

    send_text(cl,tid,result)

def run_bot():
    global BOT_RUNNING,BOT_USERNAME
    sid=os.environ.get("IG_SESSIONID")
    print(f"🐐 {BOT_NAME} starting... SESSION FOUND: {bool(sid)}",flush=True)
    if not sid: return
    sid=urllib.parse.unquote(sid.strip().strip('"').strip("'"))
    try:
        cl=Client()
        cl.login_by_sessionid(sid)
        BOT_USERNAME=getattr(cl,"username","Unknown")
        BOT_RUNNING=True
        print(f"🎉 LOGIN SUCCESS: @{BOT_USERNAME}",flush=True)
    except Exception as e:
        print(f"❌ LOGIN FAILED: {e}",flush=True); traceback.print_exc(); return

    last={}
    try:
        for t in cl.direct_threads(amount=20):
            if t.messages: last[t.id]=str(t.messages[0].id)
    except Exception as e: print(f"⚠️ Initial sync error: {e}",flush=True)

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
            print(f"⚠️ DM LOOP ERROR: {e}",flush=True); traceback.print_exc()
            time.sleep(5)
        time.sleep(3)

threading.Thread(target=run_bot,daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT","10000")))
    
