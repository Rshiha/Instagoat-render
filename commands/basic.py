import time
from datetime import datetime

BOT_NAME="Your Father Shihab"

def hi(a,c):
    return f"👋 Hello {c.get('username','Friend')}!\n🐐 {BOT_NAME} is here!"

def hello(a,c):
    return hi(a,c)

def ping(a,c):
    return "🏓 Pong!\n🤖 Bot is online."

def menu(a,c):
    return "🐐 YOUR FATHER SHIHAB\n━━━━━━━━━━━━\n📚.hi.hello.ping.time.date.uptime\n👤.info.profile.uid\n🎮.joke.quote.dice.8ball\n💬.say.reverse.upper.lower\n💖.love.hug.kiss\n💰.balance.daily.work.shop.slot\n🎵.play.song.music"

def get_time(a,c):
    return "🕐 "+datetime.now().strftime("%I:%M:%S %p")

def get_date(a,c):
    return "📅 "+datetime.now().strftime("%d %B %Y")

def uptime(a,c):
    s=int(time.time()-c.get("start_time",time.time()))
    return f"⏱️ {s//3600}h {(s%3600)//60}m {s%60}s"

# ===== UID / PROFILE FIX - EKHANE ADD KORLAM =====
def profile(a,c):
    # 1. Reply korle onner ID asbe
    if isinstance(c, dict) and c.get("replied_user"):
        u = c["replied_user"]
        return f"👤 INSTAGRAM PROFILE\n━━━━━━━━━━━━\n👤 Name: {u.get('full_name','Unknown')}\n🚩 Username: @{u.get('username','unknown')}\n🆔 User ID: {u.get('user_id','0')}\n━━━━━━━━━━━━"

    # 2..uid 123456 dile
    if a and len(a)>0 and a[0].isdigit():
        return f"🆔 User ID: {a[0]}"

    # 3. Nijer ta
    if isinstance(c, dict):
        uid = str(c.get("user_id","0"))
        uname = c.get("username","unknown")
        name = c.get("full_name", uname)
        return f"👤 INSTAGRAM PROFILE\n━━━━━━━━━━━━\n👤 Name: {name}\n🚩 Username: @{uname}\n🆔 User ID: {uid}\n━━━━━━━━━━━━"
    return "❌ ID pawa jay nai!"

def uid(a,c):
    return profile(a,c)

def info(a,c):
    return profile(a,c)

BASIC_COMMANDS={
    "hi":hi,
    "hello":hello,
    "ping":ping,
    "menu":menu,
    "help":menu,
    "time":get_time,
    "date":get_date,
    "uptime":uptime,
    "profile":profile,
    "uid":uid,
    "id":uid,
    "info":info
}
