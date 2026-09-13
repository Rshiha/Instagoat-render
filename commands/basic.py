import time
from datetime import datetime

BOT_NAME="Your Father Shihab"

def hi(a,c): return f"👋 Hello {c.get('username','Friend')}!\n🐐 {BOT_NAME} is here!"
def hello(a,c): return hi(a,c)
def ping(a,c): return "🏓 Pong!\n🤖 Bot is online."
def menu(a,c): return "🐐 YOUR FATHER SHIHAB\n━━━━━━━━━━━━\n📚.hi.hello.ping.time.date.uptime\n👤.info.profile.uid\n🎮.joke.quote.dice.8ball\n💬.say.reverse.upper.lower\n💖.love.hug.kiss\n💰.balance.daily.work.shop.slot\n🎵.play.song.music"
def get_time(a,c): return "🕐 "+datetime.now().strftime("%I:%M:%S %p")
def get_date(a,c): return "📅 "+datetime.now().strftime("%d %B %Y")
def uptime(a,c):
    s=int(time.time()-c.get("start_time",time.time()))
    return f"⏱️ {s//3600}h {(s%3600)//60}m {s%60}s"

def profile(a,c):
    if isinstance(c, dict) and c.get("replied_user"):
        u = c["replied_user"]
        uid = str(u.get('user_id','0')); uname = u.get('username','unknown'); name = u.get('full_name', uname)
        pic = u.get('profile_pic_url'); followers = u.get('followers','N/A'); following = u.get('following','N/A'); posts = u.get('posts','N/A'); bio = u.get('bio','N/A')
    else:
        if isinstance(c, dict):
            uid = str(c.get('user_id','0')); uname = c.get('username','unknown'); name = c.get('full_name', uname)
            pic = c.get('profile_pic_url'); followers = c.get('followers', 428); following = c.get('following', 62); posts = c.get('posts', 150); bio = c.get('bio', 'bdc_royal_family {EE~04} <23> @squad_bangladesh')
        else:
            uid=str(c); uname="unknown"; name="Unknown"; pic=None; followers=following=posts="N/A"; bio="N/A"
    caption = f"👤 INSTAGRAM PROFILE\n━━━━━━━━━━━━\n👤 Name: {name}\n🚩 Username: @{uname}\n🆔 User ID: {uid}\n👥 Followers: {followers}\n➡️ Following: {following}\n📸 Posts: {posts}\n📝 Bio: {bio}\n━━━━━━━━━━━━"
    if pic:
        return {"photo": pic, "caption": caption}
    return caption

def uid(a,c): return profile(a,c)
def info(a,c): return profile(a,c)

BASIC_COMMANDS={"hi":hi,"hello":hello,"ping":ping,"menu":menu,"help":menu,"time":get_time,"date":get_date,"uptime":uptime,"profile":profile,"uid":uid,"id":uid,"info":info}
