import os,time,json,threading,traceback,urllib.parse
from flask import Flask
from instagrapi import Client
from commands import COMMANDS,BOT_NAME
from commands.downloader import auto_detect,download_video

try:
    from commands.media import select_song,download_selected_song
except Exception as e:
    print(f"MEDIA LOAD ERR: {e}",flush=True)
    select_song=download_selected_song=None

app=Flask(__name__)
PREFIX=os.getenv("BOT_PREFIX",".")
START_TIME=time.time()
BOT_RUNNING=False
BOT_USERNAME="Unknown"
TEACH_FILE="bby_teachings.json"


def cookies():
    for p in ["/etc/secrets/cookies.txt",
              os.path.join(os.path.dirname(__file__),"cookies.txt"),
              "cookies.txt"]:
        try:
            if os.path.isfile(p) and os.path.getsize(p)>0:
                os.environ["YTDLP_COOKIES"]=p
                print(f"🍪 YouTube Cookies: LOADED",flush=True)
                return p
        except: pass
    print("⚠️ YouTube Cookies: MISSING",flush=True)
    return None


COOKIE_FILE=cookies()


def load_teach():
    try:
        if not os.path.exists(TEACH_FILE): return {}
        with open(TEACH_FILE,"r",encoding="utf-8") as f:
            d=json.load(f)
        if isinstance(d,dict): return d
        r={}
        for x in d if isinstance(d,list) else []:
            if isinstance(x,dict) and x.get("question") and x.get("answer"):
                r[str(x["question"])]=str(x["answer"])
        return r
    except Exception as e:
        print(f"TEACH LOAD ERR: {e}",flush=True)
        return {}


TEACHINGS=load_teach()


def save_teach():
    try:
        with open(TEACH_FILE,"w",encoding="utf-8") as f:
            json.dump(TEACHINGS,f,ensure_ascii=False,indent=2)
        return True
    except Exception as e:
        print(f"TEACH SAVE ERR: {e}",flush=True)
        return False


def norm(s):
    if not s:return ""
    s=" ".join(str(s).strip().lower().split())
    for c in "!?।,.;:'\"“”‘’`~":
        s=s.replace(c,"")
    return s.strip()


def teach(text):
    ok=0
    for line in text.splitlines():
        if not line.lower().startswith(".bby teach "):continue
        x=line[11:].strip()
        if " - " not in x:continue
        q,a=x.split(" - ",1)
        q=norm(q);a=a.strip()
        if q and a:
            TEACHINGS[q]=a
            ok+=1
    if not ok:
        return "🥹 ঠিকভাবে teach করা হয়নি!\n\nExample:\n.bby teach hi - hello"
    if not save_teach():
        return "❌ Teach save করা যায়নি!"
    return f"🥹 {ok}টা কথা শিখে নিলাম! ❤️"


def taught(text):
    q=norm(text)
    if not q:return None
    if q in TEACHINGS:return TEACHINGS[q]
    for k,v in TEACHINGS.items():
        k=norm(k)
        if len(k)>=3 and k in q:return v
    return None


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
        "ai":"OFF",
        "taught":len(TEACHINGS),
        "youtube_cookies":bool(COOKIE_FILE),
        "music":bool(select_song)
    }


def ctx(cl,msg,thread):
    try:u=cl.user_info(int(msg.user_id))
    except:u=None
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
        "message":msg
    }


def send(cl,tid,text):
    if text is None:return
    if isinstance(text,dict) and text.get("photo"):
        try:
            cl.direct_send_photo(text["photo"],thread_ids=[tid])
            if text.get("caption"):
                cl.direct_send(text["caption"],thread_ids=[tid])
            return
        except:
            text=text.get("caption","❌ Photo failed")
    text=str(text)
    for i in range(0,len(text),1800):
        try:
            cl.direct_send(text[i:i+1800],thread_ids=[tid])
            time.sleep(.3)
        except Exception as e:
            print(f"SEND ERR: {e}",flush=True)


def send_video(cl,tid,path):
    if not path or not os.path.exists(path):
        send(cl,tid,"❌ Video download failed!")
        return
    try:
        if os.path.getsize(path)>90*1024*1024:
            send(cl,tid,"❌ Video 90MB-এর বেশি!")
            return
        cl.direct_send_video(path,thread_ids=[tid])
    except Exception as e:
        print(f"VIDEO SEND ERR: {e}",flush=True)
        send(cl,tid,"❌ Video send failed!")
    finally:
        try:os.remove(path)
        except:pass


def send_audio(cl,tid,r):
    if not isinstance(r,dict):
        send(cl,tid,r);return
    p=r.get("path")
    if not p or not os.path.exists(p):
        send(cl,tid,"❌ Audio file পাওয়া যায়নি!")
        return
    try:
        if os.path.getsize(p)>90*1024*1024:
            send(cl,tid,"❌ Audio 90MB-এর বেশি!")
            return
        print(f"🎵 Sending: {r.get('title','Song')}",flush=True)
        if hasattr(cl,"direct_send_file"):
            cl.direct_send_file(p,thread_ids=[tid])
        elif hasattr(cl,"direct_send_audio"):
            cl.direct_send_audio(p,thread_ids=[tid])
        else:
            raise Exception("Audio method unavailable")
        print("✅ AUDIO SENT",flush=True)
    except Exception as e:
        print(f"AUDIO SEND ERR: {e}",flush=True)
        send(cl,tid,"❌ গান পাঠানো যায়নি!")
    finally:
        try:
            if r.get("cleanup"):r["cleanup"]()
            elif os.path.exists(p):os.remove(p)
        except:pass


def song_number(cl,thread,msg):
    if not select_song or not download_selected_song:return False
    text=(getattr(msg,"text","") or "").strip()
    if not text.isdigit():return False
    n=int(text)
    if n<1 or n>5:return False

    try:
        r=select_song(n,ctx(cl,msg,thread))
    except Exception as e:
        print(f"SONG SELECT ERR: {e}",flush=True)
        return False

    if r is None:return False

    tid=thread.id

    if isinstance(r,str):
        send(cl,tid,r)
        return True

    if not isinstance(r,dict):
        send(cl,tid,"❌ Song selection failed!")
        return True

    send(cl,tid,"⏳ গান download হচ্ছে... 🎵")

    try:
        r=download_selected_song(r)
    except Exception as e:
        print(f"SONG DOWNLOAD ERR: {e}",flush=True)
        send(cl,tid,"❌ গান download করা যায়নি!")
        return True

    if isinstance(r,dict) and r.get("type")=="audio":
        send_audio(cl,tid,r)
    else:
        send(cl,tid,r or "❌ গান download করা যায়নি!")
    return True


def process(cl,thread,msg):
    text=(getattr(msg,"text","") or "").strip()
    if not text:return
    tid=thread.id
    low=text.lower()

    # 1/2/3/4/5 song selection
    if text.isdigit() and song_number(cl,thread,msg):
        return

    # Teaching
    if low.startswith(".bby teach "):
        send(cl,tid,teach(text))
        return

    # Learned reply
    r=taught(text)
    if r is not None:
        print(f"🧠 TAUGHT: {text}",flush=True)
        send(cl,tid,r)
        return

    # Automatic URL download
    if not text.startswith(PREFIX):
        try:url=auto_detect(text)
        except:url=None

        if url:
            try:
                send(cl,tid,f"⏳ Downloading...\n🔗 {url}")
                p=download_video(url,client=cl)
                send_video(cl,tid,p)
            except Exception as e:
                print(f"AUTO DL ERR: {e}",flush=True)
                send(cl,tid,"❌ Download failed!")
            return

    # Normal commands
    if low in ("hi","hello","hey"):
        cmd=COMMANDS.get("hi")
        if cmd:
            try:r=cmd([],ctx(cl,msg,thread))
            except:r="❌ Command error."
        else:r="Hello! ❤️"

    elif low in ("menu","help"):
        cmd=COMMANDS.get("menu")
        if cmd:
            try:r=cmd([],ctx(cl,msg,thread))
            except:r="❌ Command error."
        else:r="❌ Menu পাওয়া যায়নি!"

    elif text.startswith(PREFIX):
        body=text[len(PREFIX):].strip()
        if not body:
            cmd=COMMANDS.get("menu")
            if cmd:
                try:r=cmd([],ctx(cl,msg,thread))
                except:r="❌ Command error."
            else:r="❌ Menu পাওয়া যায়নি!"
        else:
            parts=body.split()
            name=parts[0].lower()
            args=parts[1:]
            cmd=COMMANDS.get(name)
            if not cmd:
                send(cl,tid,f"❌ Unknown command: {name}")
                return
            try:r=cmd(args,ctx(cl,msg,thread))
            except Exception as e:
                print(f"COMMAND ERR: {e}",flush=True)
                r="❌ Command error."
    else:
        print(f"ℹ️ No taught reply for: {text}",flush=True)
        return

    if isinstance(r,dict) and r.get("type")=="audio":
        send_audio(cl,tid,r)
    elif isinstance(r,dict) and r.get("type")=="video":
        send_video(cl,tid,r.get("path"))
    else:
        send(cl,tid,r)


def run_bot():
    global BOT_RUNNING,BOT_USERNAME

    sid=os.getenv("IG_SESSIONID")
    if not sid:
        print("❌ IG_SESSIONID missing",flush=True)
        return

    sid=urllib.parse.unquote(sid.strip().strip('"').strip("'"))

    try:
        cl=Client()
        cl.login_by_sessionid(sid)
        BOT_USERNAME=getattr(cl,"username","Unknown")
        BOT_RUNNING=True

        print(f"🎉 LOGIN @{BOT_USERNAME}",flush=True)
        print("🤖 Gemini: DISABLED",flush=True)
        print(
            "🍪 YouTube Cookies:",
            "LOADED" if COOKIE_FILE else "MISSING",
            flush=True
        )
        print(f"🧠 TAUGHT: {len(TEACHINGS)}",flush=True)
        print(
            "🎵 Music selection:",
            "ENABLED" if select_song else "DISABLED",
            flush=True
        )

    except Exception as e:
        print(f"LOGIN FAIL: {e}",flush=True)
        return

    last={}

    try:
        for t in cl.direct_threads(
            amount=20,
            thread_message_limit=25
        ):
            if t.messages:
                last[t.id]=str(t.messages[0].id)
    except Exception as e:
        print(f"INITIAL DM ERR: {e}",flush=True)

    errors=0

    while True:
        try:
            threads=cl.direct_threads(
                amount=20,
                thread_message_limit=25
            )
            errors=0

            for thread in threads:
                if not thread.messages:continue

                msg=thread.messages[0]
                mid=str(getattr(msg,"id",""))
                uid=str(getattr(msg,"user_id",""))

                if not mid or uid==str(cl.user_id):
                    continue

                if last.get(thread.id)==mid:
                    continue

                last[thread.id]=mid

                text=(getattr(msg,"text","") or "").strip()
                if not text:continue

                print(f"📩 {text}",flush=True)
                process(cl,thread,msg)

        except Exception as e:
            errors+=1
            err=str(e)

            if "1404006" in err or "item_ack" in err or "403" in err:
                wait=min(60,5+errors*5)
                print(
                    f"⚠️ Instagram 403/1404006 — retry {wait}s",
                    flush=True
                )
                time.sleep(wait)
            else:
                print(f"LOOP ERR: {e}",flush=True)
                time.sleep(8)

        time.sleep(3)


threading.Thread(target=run_bot,daemon=True).start()

if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT","10000"))
        )
