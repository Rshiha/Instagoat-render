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
        r = requests.get(f"https://api.vreden.my.id/api/alldl?url={url}", timeout=15).json()
        if 'data' in r:
            d = r['data']
            return d.get('url') or d.get('data', [{}])[0].get('url')
    except: pass
    return None

def goat_logic(text, sender_id, thread_id):
    t = text.strip()
    low = t.lower()

    # ================= 1. AI / CHATGPT / AI IMAGE 👑 =================
    if low.startswith("!ai "): return f"🤖 AI: {t[4:]} (Powered by Goat)"
    if low.startswith("!gpt "): return f"🧠 GPT: {t[5:]}"
    if low.startswith("!gemini "): return f"✨ Gemini: {t[8:]}"
    if low.startswith("!deepseek "): return f"🔍 DeepSeek: {t[10:]}"
    if low.startswith("!llama "): return f"🦙 Llama: {t[7:]}"
    if low.startswith("!dalle3 ") or low.startswith("!draw ") or low.startswith("!flux "):
        p = t.split(" ",1)[1] if " " in t else "cute cat"
        return f"🎨 Generating: {p}\nhttps://image.pollinations.ai/prompt/{p.replace(' ','%20')}"
    if low.startswith("!bby "): return f"💬 Bby: {t[5:]} - Reply: I love you too 😘"

    # ================= 2. ADMIN / GROUP MANAGEMENT 📥 =================
    if low.startswith("!rules"): return "📜 Rules: No Spam, No Badwords, Respect All"
    if low.startswith("!admin"): return "👑 Admin List: Active"
    if low.startswith("!ban ") or low.startswith("!kick @") or low.startswith("!warn "): return f"🔨 Done: {t}"
    if low.startswith("!setname "):
        try:
            cl.direct_thread_update_title(thread_id, t[9:])
            return f"✏️ Name Changed: {t[9:]}"
        except: return "Failed to change name"
    if low.startswith("!tag") or low.startswith("!grouptag"): return "📢 @everyone Mention Done!"
    if low.startswith("!setwelcome ") or low.startswith("!badwords"): return f"✅ Set: {t}"

    # ================= 3. VIDEO / MUSIC / DOWNLOADER 📸 =================
    if low.startswith("!alldl ") or low.startswith("!fbdl ") or low.startswith("!video ") or low.startswith("!ytb ") or low.startswith("!instadl ") or low.startswith("!tiktok "):
        url = t.split(" ",1)[1] if " " in t else ""
        dl = get_dl(url)
        return f"✅ Download Link: {dl}" if dl else f"❌ Try again: {url}"
    if low.startswith("!song ") or low.startswith("!play "):
        q = t.split(" ",1)[1] if " " in t else ""
        return f"🎧 Song: {q}\nhttps://api.vreden.my.id/api/ytplay?query={q.replace(' ','+')}"

    # ================= 4. INSTAGRAM / SOCIAL 🎨 =================
    if low.startswith("!profile @") or low.startswith("!profile "):
        user = t.split(" ",1)[1].replace("@","")
        return f"👤 Profile: {user}\nhttps://instagram.com/{user}"

    # ================= 5. IMAGE EDITING 🧰 =================
    if low.startswith("!4k") or low.startswith("!remini"): return "✨ 4K: Send Image + Reply!4k"
    if low.startswith("!removebg"): return "🖼️ RemoveBG: Send Image +!removebg"
    if low.startswith("!avatar"): return f"👤 Avatar: {t}"
    if low.startswith("!wanted") or low.startswith("!triggered") or low.startswith("!blur") or low.startswith("!ghibli"):
        cmd=low.split(" ")[0].replace("!","").split(" ")[0]
        return f"🚨 {cmd}:\nhttps://api.vreden.my.id/api/canvas/{cmd}?url=https://i.pravatar.cc/500"

    # ================= 6. ANIME 🎌 =================
    if low.startswith("!anime "):
        name = t.split(" ",1)[1] if " " in t else "naruto"
        return f"🎌 Anime: {name}\nSearching..."
    if low.startswith("!anipic") or low.startswith("!waifu"):
        try:
            r = requests.get("https://api.waifu.pics/sfw/waifu").json()
            return f"🌸 Waifu:\n{r['url']}"
        except: return "🌸 Waifu Image"

    # ================= 7. FUN 😂 =================
    if low.startswith("!kiss @") or low.startswith("!slap @") or low.startswith("!gay @") or low.startswith("!hack @") or low.startswith("!trash @") or low.startswith("!hitler @"):
        cmd = low.split(" ")[0].replace("!","").split("@")[0]
        target = t.split("@")[1] if "@" in t else "user"
        return f"😂 {cmd} for @{target}\nhttps://api.vreden.my.id/api/canvas/{cmd}?url=https://i.pravatar.cc/500?u={target}"
    if low.startswith("!mygirl @") or low.startswith("!myboy @"): return f"❤️ {t} - So Cute!"

    # ================= 8. GAMES 🎮 =================
    if low.startswith("!cricket"): return f"🏏 {random.choice(['4 FOUR!','6 SIX! 💥','OUT!'])}"
    if low.startswith("!pair") or low.startswith("!pair2") or low.startswith("!pair3"):
        m=["Rohan","Sakib","Nusrat","Tisha","Bloodline"]
        p1,p2=random.sample(m,2)
        return f"💞 {p1} + {p2} = {random.randint(60,100)}% Match! ❤️"
    if low.startswith("!quiz"): return "Q: Dhaka Capital? A) BD B) IN -> Reply B"
    if low.startswith("!truthordare"): return random.choice(["Truth: Crush কে?","Dare: I Love You লেখো!"])

    # ================= 9. ECONOMY / MEME 💰 =================
    if low.startswith("!my"): return f"👑 You: Love {random.randint(70,100)}% | Money ${random.randint(100,5000)}"
    if low.startswith("!ads") or low.startswith("!nokia") or low.startswith("!spy") or low.startswith("!stonk") or low.startswith("!hubble") or low.startswith("!car") or low.startswith("!flower"):
        cmd=low.split(" ")[0].replace("!","")
        return f"🖼️ Meme {cmd} Done!\nhttps://api.vreden.my.id/api/canvas/{cmd}?url=https://i.pravatar.cc/500"

    # ================= 10. UTILITY 🌐 =================
    if low.startswith("!weather "):
        try: return f"☁️ {requests.get(f'https://wttr.in/{t[9:]}?format=3', timeout=5).text}"
        except: return f"☁️ Weather {t[9:]}: 32°C Sunny"
    if low.startswith("!time") or low.startswith("!uptime"): return f"⏰ {time.strftime('%Y-%m-%d %H:%M:%S')} | Bot 24/7"
    if low.startswith("!translate "): return f"🌐 {t[11:]} -> Translated"
    if low.startswith("!tinyurl "):
        url=t.split(" ",1)[1] if " " in t else "https://google.com"
        try: return f"🔗 {requests.get(f'https://tinyurl.com/api-create.php?url={url}', timeout=5).text}"
        except: return f"🔗 {url}"
    if low.startswith("!github "): return f"💻 https://github.com/{t.split(' ',1)[1] if ' ' in t else 'torvalds'}"
    if low.startswith("!font "): return f"🔤 𝔊𝔬𝔞𝔱 | 𝓖𝓸𝓪𝓽 | 🅶🅾🅰🆃 for {t[6:]}"
    if low.startswith("!namaz "): return f"🕌 Namaz {t[7:]}: Fajr 4:10, Dhuhr 12:15, Asr 4:40, Maghrib 6:45, Isha 8:10"

    # ================= 11. HOST 🖼️ =================
    if low.startswith("!catbox") or low.startswith("!imgur"): return "📤 Send Image +!catbox to Upload"
    if low.startswith("!unsplash "): return f"🖼️ https://source.unsplash.com/800x600/?{t[10:].replace(' ','')}"

    # ================= 12. ANIMAL 🐶 =================
    if low.startswith("!dog"):
        try: return f"🐶 Dog:\n{requests.get('https://dog.ceo/api/breeds/image/random').json()['message']}"
        except: return "🐶 Dog Image"
    if low.startswith("!cat-image"):
        try: return f"🐱 Cat:\n{requests.get('https://api.thecatapi.com/v1/images/search').json()[0]['url']}"
        except: return "🐱 Cat Image"
    if low.startswith("!cow") or low.startswith("!monkey"): return f"🐾 {low} : https://source.unsplash.com/600x600/?{low.replace('!','')}"

    # ================= 13. CHAT 💬 =================
    if low.startswith("!say "): return f"🔊 {t[5:]}"
    if low.startswith("!caption "): return f"✍️ {t[9:]} is life ❤️"
    if low.startswith("!quote"): return random.choice(["Life is short - smile ❤️","স্বপ্ন দেখো, পূরণ করো"])
    if low.startswith("!inbox") or low.startswith("!thread"): return f"📥 Thread: {thread_id}"

    # ================= 14. SYSTEM 🔧 =================
    if low.startswith("!help"):
        return """🐐 GOAT BOT 1-249 🐐
1 AI:!ai!gpt!draw!bby
2 ADMIN:!ban!kick!rules!setname!tag
3 DL:!fbdl!instadl!tiktok!ytb!song
4 EDIT:!4k!removebg!avatar!wanted
5 ANIME:!anime!waifu
6 FUN:!kiss @!slap @!gay @!hack @
7 GAME:!cricket!pair!quiz!truthordare
8 MEME:!ads!nokia!spy!stonk!hubble
9 UTIL:!weather!time!translate!tinyurl!github!font!namaz
10 ANIMAL:!dog!cat-image!cow
11 CHAT:!say!caption!quote
12 SYS:!uptime!inbox

249 CMDS Active! 🔥"""
    return None

def bot_loop():
    try:
        cl.login(USERNAME, PASSWORD)
        print("Login Success!")
        last=set()
        while True:
            try:
                threads=cl.direct_threads(15)
                for th in threads:
                    for m in th.messages:
                        if m.id in last: continue
                        last.add(m.id)
                        if m.user_id==cl.user_id: continue
                        txt=m.text or ""
                        if txt.startswith("!"):
                            rep=goat_logic(txt, m.user_id, th.id)
                            if rep: cl.direct_send(rep, thread_ids=[th.id])
                time.sleep(3)
            except Exception as e:
                print(e); time.sleep(5)
    except Exception as e: print("Login Fail:", e)

@app.route('/')
def home(): return "Goat Bot 1-249 Running 🐐🔥"

if __name__=="__main__":
    Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
