import time
from datetime import datetime
BOT_NAME="Your Father Shihab"
def hi(a,c): return f"👋 Hello {c.get('username','Friend')}!\n🐐 {BOT_NAME} is here!"
def hello(a,c): return hi(a,c)
def ping(a,c): return "🏓 Pong!\n🤖 Bot is online."
def menu(a,c): return "🐐 YOUR FATHER SHIHAB\n━━━━━━━━━━━━\n📚 .hi .hello .ping .time .date .uptime\n👤 .info .profile .uid\n🎮 .joke .quote .dice .8ball\n💬 .say .reverse .upper .lower\n💖 .love .hug .kiss\n💰 .balance .daily .work .shop .slot\n🎵 .play .song .music"
def get_time(a,c): return "🕐 "+datetime.now().strftime("%I:%M:%S %p")
def get_date(a,c): return "📅 "+datetime.now().strftime("%d %B %Y")
def uptime(a,c):
 s=int(time.time()-c.get("start_time",time.time())); return f"⏱️ {s//3600}h {(s%3600)//60}m {s%60}s"
BASIC_COMMANDS={"hi":hi,"hello":hello,"ping":ping,"menu":menu,"help":menu,"time":get_time,"date":get_date,"uptime":uptime}
