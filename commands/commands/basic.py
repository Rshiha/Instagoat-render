import time
from datetime import datetime

BOT_NAME = "Your Father Shihab"


def hi(args, ctx):
    username = ctx.get("username", "Friend")
    return f"👋 Hello {username}!\n\n🐐 {BOT_NAME} is here!"


def hello(args, ctx):
    return hi(args, ctx)


def ping(args, ctx):
    return "🏓 Pong!\n\n🤖 Bot is online."


def menu(args, ctx):
    return (
        "🐐 YOUR FATHER SHIHAB\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "📚 BASIC COMMANDS\n"
        "• .hi\n"
        "• .hello\n"
        "• .ping\n"
        "• .time\n"
        "• .date\n"
        "• .uptime\n\n"
        "👤 PROFILE\n"
        "• .info\n"
        "• .profile\n"
        "• .uid\n\n"
        "🎮 FUN\n"
        "• .joke\n"
        "• .quote\n"
        "• .dice\n"
        "• .8ball\n\n"
        "💬 TEXT\n"
        "• .say\n"
        "• .reverse\n"
        "• .upper\n"
        "• .lower\n\n"
        "💖 SOCIAL\n"
        "• .love\n"
        "• .hug\n"
        "• .kiss\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Use .help or .menu"
    )


def get_time(args, ctx):
    return f"🕐 Current time: {datetime.now().strftime('%I:%M:%S %p')}"


def get_date(args, ctx):
    return f"📅 Date: {datetime.now().strftime('%d %B %Y')}"


def uptime(args, ctx):
    start = ctx.get("start_time")

    if not start:
        return "⏱️ Bot is running."

    seconds = int(time.time() - start)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"⏱️ Uptime: {hours}h {minutes}m {secs}s"


BASIC_COMMANDS = {
    "hi": hi,
    "hello": hello,
    "ping": ping,
    "menu": menu,
    "help": menu,
    "time": get_time,
    "date": get_date,
    "uptime": uptime,
}
