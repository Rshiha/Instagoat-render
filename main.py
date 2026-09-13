import os,time,threading,traceback,urllib.parse,urllib.request,urllib.error,json
from flask import Flask
from instagrapi import Client
from commands import COMMANDS,BOT_NAME
from commands.downloader import auto_detect,download_video

app=Flask(__name__)
PREFIX=os.getenv("BOT_PREFIX",".")
START_TIME=time.time()
BOT_RUNNING=False
BOT_USERNAME="Unknown"

GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-3.8-flash").strip()

# ================= TEACH =================

TEACH_FILE="bby_teachings.json"
TEACHINGS={}

def load_teachings():
    try:
        if os.path.exists(TEACH_FILE):
            with open(TEACH_FILE,"r",encoding="utf-8") as f:
                x=json.load(f)
                return x if isinstance(x,dict) else {}
    except Exception as e:
        print("TEACH LOAD ERR:",e)
    return {}

def save_teachings():
    try:
        with open(TEACH_FILE,"w",encoding="utf-8") as f:
            json.dump(TEACHINGS,f,ensure_ascii=False,indent=2)
        return True
    except Exception as e:
        print("TEACH SAVE ERR:",e)
        return False

TEACHINGS.update(load_teachings())

def teach_command(text):
    learned=[]
    failed=[]

    for line in text.splitlines():
        line=line.strip()
        if not line.lower().startswith(".bby teach "):
            continue

        data=line[len(".bby teach "):].strip()

        if " - " not in data:
            failed.append(line)
            continue

        q,a=data.split(" - ",1)
        q=q.strip().lower()
        a=a.strip()

        if not q or not a:
            failed.append(line)
            continue

        TEACHINGS[q]=a
        learned.append((q,a))

    if not learned:
        return "🥹 ঠিকভাবে teach করা হয়নি!\n\nExample:\n.bby teach hi - hello"

    if not save_teachings():
        return "❌ Teach save করতে পারলাম না!"

    out=[f"🥹 {len(learned)}টা কথা শিখে নিলাম! ❤️",""]
    out += [f"👤 {q} → 🤖 {a}" for q,a in learned]

    if failed:
        out += ["",f"⚠️ {len(failed)}টা line বাদ গেছে।"]

    return "\n".join(out)

def taught_reply(text):
    return TEACHINGS.get(text.strip().lower())

# ================= GEMINI =================

def ask_gemini(text,ctx=None):
    if not GEMINI_API_KEY:
        print("⚠️ GEMINI_API_KEY missing")
        return None

    username=ctx.get("username","Unknown") if ctx else "Unknown"

    system="""You are an Instagram group chatbot.
Reply naturally, briefly and friendly.
If the user writes Bangla/Banglish, reply in Bangla/Banglish.
Do not reveal passwords, cookies, session IDs or API keys.
If someone asks you to find a boyfriend or girlfriend, say exactly:
Age Shihab boss ke mingle banao 😎❤️
Keep group-chat replies short."""

    payload={
        "contents":[{"role":"user","parts":[{"text":
            system+"\n\nUsername: @"+str(username)+
            "\nMessage: "+text+"\nReply:"
        }]}],
        "generationConfig":{
            "maxOutputTokens":300,
            "temperature":0.8
        }
    }

    url=("https://generativelanguage.googleapis.com/v1beta/models/"+
         urllib.parse.quote(GEMINI_MODEL,safe="")+":generateContent")

    try:
        req=urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type":"application/json",
                "x-goog-api-key":GEMINI_API_KEY
            },
            method="POST"
        )

        with urllib.request.urlopen(req,timeout=45) as r:
            data=json.loads(r.read().decode())

        parts=data.get("candidates",[{}])[0].get(
            "content",{}).get("parts",[])

        ans="".join(p.get("text","") for p in parts).strip()
        return ans or None

    except urllib.error.HTTPError as e:
        try: body=e.read().decode(errors="ignore")
        except: body=str(e)
        print(f"❌ GEMINI HTTP {e.code}: {body}")
        return None
    except Exception as e:
        print("❌ GEMINI ERROR:",e)
        return None

# ================= FLASK =================

@app.route("/")
def home():
    return f"🐐 {BOT_NAME} LIVE! @{BOT_USERNAME}"

@app.route("/health")
def health():
    return {
        "status":"online",
        "bot":BOT_NAME,
        "username":BOT_USERNAME,
        "running":BOT_RUNNING,
        "ai":"Gemini",
        "taught":len(TEACHINGS)
    }

# ================= SEND =================

def send_text(cl,tid,text):
    if not text:return

    if isinstance(text,dict) and "photo" in text:
        try:
            cl.direct_send_photo(text["photo"],thread_ids=[tid])
            if text.get("caption"):
                cl.direct_send(text["caption"],thread_ids=[tid])
            return
        except Exception as e:
            print("PHOTO ERR:",e)
            text=text.get("caption","❌ Photo fail")

    text=str(text)

    for i in range(0,len(text),1800):
        try:
            cl.direct_send(text[i:i+1800],thread_ids=[tid])
            time.sleep(.5)
        except Exception as e:
            print("SEND ERR:",e)

# ================= USER =================

def get_user(cl,uid):
    try:return cl.user_info(int(uid))
    except:return None

def user_data(u):
    if not u:return None
    return {
        "user_id":str(u.pk),
        "username":u.username,
        "full_name":u.full_name,
        "profile_pic_url":str(u.profile_pic_url),
        "followers":u.follower_count,
        "following":u.following_count,
        "posts":u.media_count,
        "bio":u.biography
    }

def make_context(cl,msg,thread):
    u=get_user(cl,msg.user_id)

    return {
        "client":cl,
        "user":u,
        "user_id":str(msg.user_id),
        "username":getattr(u,"username","Unknown") if u else "Unknown",
        "full_name":getattr(u,"full_name","Unknown") if u else "Unknown",
        "profile_pic_url":str(getattr(u,"profile_pic_url","")) if u else "",
        "followers":getattr(u,"follower_count",0) if u else 0,
        "following":getattr(u,"following_count",0) if u else 0,
        "posts":getattr(u,"media_count",0) if u else 0,
        "bio":getattr(u,"biography","") if u else "",
        "start_time":START_TIME,
        "thread_id":thread.id,
        "thread":thread,
        "message":msg,
        "replied_user":None
    }

# ================= VIDEO =================

def send_downloaded_video(cl,tid,path):
    if not path or not os.path.exists(path):
        send_text(cl,tid,"❌ Download failed! Private video hote pare!")
        return

    try:
        if os.path.getsize(path)>90*1024*1024:
            send_text(cl,tid,"❌ 90MB+ besi, pathano jabena!")
            return

        cl.direct_send_video(path,thread_ids=[tid])
    except Exception as e:
        print("VIDEO SEND ERROR:",e)
        send_text(cl,tid,"❌ Video send failed!")
    finally:
        try:os.remove(path)
        except:pass

# ================= PROCESS =================

def process_message(cl,thread,msg):
    text=(getattr(msg,"text","") or "").strip()
    if not text:return

    tid=thread.id
    ctx=make_context(cl,msg,thread)
    low=text.lower()
    result=None

    # TEACH FIRST
    if low.startswith(".bby teach "):
        result=teach_command(text)

    # AUTO DOWNLOAD
    elif not text.startswith(PREFIX):
        url=auto_detect(text)

        if url:
            try:
                cl.direct_send(
                    f"⏳ Downloading...\n🔗 {url}",
                    thread_ids=[tid]
                )
                path=download_video(url,client=cl)
                send_downloaded_video(cl,tid,path)
            except Exception as e:
                print("AUTO DL ERR:",e)
                send_text(cl,tid,"❌ Download failed!")
            return

    # NORMAL COMMANDS
    elif low in ("hi","hello","hey"):
        result=COMMANDS.get("hi",lambda a,c:None)([],ctx)

    elif low in ("menu","help"):
        result=COMMANDS.get("menu",lambda a,c:None)([],ctx)

    elif text.startswith(PREFIX):
        body=text[len(PREFIX):].strip()

        if not body:
            result=COMMANDS.get("menu",lambda a,c:None)([],ctx)
        else:
            parts=body.split()
            cmd=parts[0].lower()
            args=parts[1:]

            if cmd in COMMANDS:
                try:
                    result=COMMANDS[cmd](args,ctx)
                except Exception:
                    traceback.print_exc()
                    result="❌ Command error."
            else:
                result=f"❌ Unknown: {cmd}"

    # TAUGHT REPLY
    if result is None:
        result=taught_reply(text)

    # GEMINI
    if result is None:
        result=ask_gemini(text,ctx)

        if result is None:
            # Gemini fail হলে শুধু error; teach বলবে না
            send_text(cl,tid,"🥲 এখন AI reply দিতে পারছে না। একটু পরে আবার try করো!")
            return

    # AUDIO
    if isinstance(result,dict) and result.get("type")=="audio":
        try:
            if result.get("path"):
                cl.direct_send_file(result["path"],thread_ids=[tid])
        finally:
            try:
                if result.get("cleanup"):result["cleanup"]()
            except:pass
        return

    # VIDEO
    if isinstance(result,dict) and result.get("type")=="video":
        send_downloaded_video(cl,tid,result.get("path"))
        return

    send_text(cl,tid,result)

# ================= BOT =================

def run_bot():
    global BOT_RUNNING,BOT_USERNAME

    sid=os.getenv("IG_SESSIONID")

    if not sid:
        print("❌ IG_SESSIONID missing")
        return

    sid=urllib.parse.unquote(sid.strip().strip('"').strip("'"))

    try:
        cl=Client()
        cl.login_by_sessionid(sid)

        BOT_USERNAME=getattr(cl,"username","Unknown")
        BOT_RUNNING=True

        print(f"🎉 LOGIN @{BOT_USERNAME}")
        print("🤖 GEMINI API KEY:",
              "LOADED" if GEMINI_API_KEY else "MISSING")
        print(f"🧠 TAUGHT: {len(TEACHINGS)}")

    except Exception as e:
        print("LOGIN FAIL:",e)
        return

    last={}

    try:
        for t in cl.direct_threads(amount=20,thread_message_limit=25):
            if t.messages:
                last[t.id]=str(t.messages[0].id)
    except:pass

    while True:
        try:
            for thread in cl.direct_threads(
                amount=20,thread_message_limit=25
            ):
                if not thread.messages:continue

                msg=thread.messages[0]
                mid=str(getattr(msg,"id",""))

                if not mid:continue

                if str(getattr(msg,"user_id",""))==str(cl.user_id):
                    continue

                if last.get(thread.id)==mid:
                    continue

                last[thread.id]=mid

                if not (getattr(msg,"text","") or "").strip():
                    continue

                print(f"📩 {msg.text}")
                process_message(cl,thread,msg)

        except Exception as e:
            print("LOOP ERR:",e)
            time.sleep(5)

        time.sleep(3)

threading.Thread(target=run_bot,daemon=True).start()

if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT","10000"))
)
