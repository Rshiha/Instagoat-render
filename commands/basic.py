import time
from datetime import datetime

BOT_NAME="Your Father Shihab"

def hi(a,c): return f"👋 Hello {c.get('username','Friend')}!\n🐐 {BOT_NAME} is here!"
def hello(a,c): return hi(a,c)
def ping(a,c): return "🏓 Pong!\n🤖 Bot is online."
def menu(a,c): return "🐐 YOUR FATHER SHIHAB\n━━━━━━━━━━━━\n📚.hi.hello.ping.time.date.uptime\n👤.info.profile.uid\n🎮.joke.quote.dice.8ball\n💬.say.reverse.upper.lower\n💖.love.hug.kiss\n💰.balance.daily.work.shop.slot\n🎵.play.song.music"
def get_time(a,c): return "🕐 "+datetime.now().strftime("%I:%M:%S %p")
def get_date(a,c): return "📅 "+datetime.now().strftime("%d %B %Y")
def uptime(a,c): s=int(time.time()-c.get("start_time",time.time())); return f"⏱️ {s//3600}h {(s%3600)//60}m {s%60}s"

def profile(a,c):
    target = None
    if isinstance(c, dict) and c.get("replied_user"):
        target = c["replied_user"]
        print(f"✅ PROFILE USING REPLIED: {target.get('username')}", flush=True)
    else:
        target = c if isinstance(c, dict) else {}

    uid = str(target.get('user_id','0'))
    uname = target.get('username','unknown')
    name = target.get('full_name', uname)
    pic = target.get('profile_pic_url')
    followers = target.get('followers','N/A')
    following = target.get('following','N/A')
    posts = target.get('posts','N/A')
    bio = target.get('bio','N/A')

    caption = (
        f"👤 INSTAGRAM PROFILE\n"
        f"━━━━━━━━━━━━\n"
        f"👤 Name: {name}\n"
        f"🚩 Username: @{uname}\n"
        f"🆔 User ID: {uid}\n"
        f"👥 Followers: {followers}\n"
        f"➡️ Following: {following}\n"
        f"📸 Posts: {posts}\n"
        f"📝 Bio: {bio}\n"
        f"━━━━━━━━━━━━"
    )
    if pic:
        return {"photo": pic, "caption": caption}
    return caption

def uid(a,c):
    target = c.get("replied_user") if isinstance(c, dict) else None
    if target:
        return f"👤 User: {target.get('full_name')} (@{target.get('username')})\n🆔 User ID: {target.get('user_id')}"
    uid = c.get('user_id','0') if isinstance(c, dict) else '0'
    uname = c.get('username','unknown') if isinstance(c, dict) else 'unknown'
    return f"👤 You: @{uname}\n🆔 Your ID: {uid}"

def info(a,c): return profile(a,c)

BASIC_COMMANDS={"hi":hi,"hello":hello,"ping":ping,"menu":menu,"help":menu,"time":get_time,"date":get_date,"uptime":uptime,"profile":profile,"uid":uid,"id":uid,"info":info}
