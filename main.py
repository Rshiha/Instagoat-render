import os
import time
import random
import threading
import traceback
import tempfile
import shutil
import glob
import math
import urllib.parse

from datetime import datetime

from flask import Flask

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

BOT_NAME = "Your Father Shihab"
PREFIX = os.environ.get("BOT_PREFIX", ".")

START_TIME = time.time()


# =========================================================
# BASIC COMMANDS
# =========================================================

def cmd_hi(args, ctx):
    return f"👋 Hello! I am {BOT_NAME} 🐐"


def cmd_hello(args, ctx):
    return f"👋 Hello from {BOT_NAME} ❤️"


def cmd_ping(args, ctx):
    return "🏓 Pong!"


def cmd_time(args, ctx):
    return f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


def cmd_date(args, ctx):
    return f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}"


def cmd_uptime(args, ctx):
    seconds = int(time.time() - START_TIME)

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return (
        f"⏱️ Bot Uptime\n\n"
        f"Days: {days}\n"
        f"Hours: {hours}\n"
        f"Minutes: {minutes}\n"
        f"Seconds: {secs}"
    )


# =========================================================
# MENU
# =========================================================

def cmd_menu(args, ctx):
    commands = sorted(COMMANDS.keys())

    page = 1

    if args:
        try:
            page = max(1, int(args[0]))
        except:
            page = 1

    per_page = 50

    total_pages = max(1, math.ceil(len(commands) / per_page))

    if page > total_pages:
        page = total_pages

    start = (page - 1) * per_page
    end = start + per_page

    selected = commands[start:end]

    lines = []

    for i, name in enumerate(selected, start=start + 1):
        lines.append(f"{i}. {PREFIX}{name}")

    return (
        f"🐐 {BOT_NAME}\n\n"
        f"📚 COMMAND MENU\n"
        f"━━━━━━━━━━━━━━\n"
        f"Page {page}/{total_pages}\n\n"
        + "\n".join(lines)
        +
        f"\n\n━━━━━━━━━━━━━━\n"
        f"Total Commands: {len(commands)}\n"
        f"Next: {PREFIX}menu {page + 1 if page < total_pages else 1}"
    )


def cmd_help(args, ctx):
    return cmd_menu(args, ctx)


# =========================================================
# INSTAGRAM USER INFO
# =========================================================

def cmd_info(args, ctx):
    try:
        user = ctx.get("user")

        if not user:
            return (
                f"👤 {BOT_NAME}\n\n"
                f"Username: @{ctx.get('username', 'Unknown')}\n"
                f"ID: {ctx.get('user_id', 'Unknown')}"
            )

        full_name = getattr(user, "full_name", "Unknown")
        username = getattr(user, "username", "Unknown")
        pk = getattr(user, "pk", ctx.get("user_id", "Unknown"))

        followers = getattr(user, "follower_count", "Unknown")
        following = getattr(user, "following_count", "Unknown")
        posts = getattr(user, "media_count", "Unknown")

        biography = getattr(user, "biography", "") or "No bio"

        is_private = getattr(user, "is_private", False)
        is_verified = getattr(user, "is_verified", False)

        return (
            f"👤 Instagram Profile\n"
            f"━━━━━━━━━━━━━━\n"
            f"Name: {full_name}\n"
            f"Username: @{username}\n"
            f"User ID: {pk}\n"
            f"Followers: {followers}\n"
            f"Following: {following}\n"
            f"Posts: {posts}\n"
            f"Private: {'Yes 🔒' if is_private else 'No 🔓'}\n"
            f"Verified: {'Yes ✅' if is_verified else 'No ❌'}\n"
            f"Bio: {biography}"
        )

    except Exception as e:
        print(f"INFO ERROR: {e}", flush=True)

        return (
            f"👤 {BOT_NAME}\n\n"
            f"Username: @{ctx.get('username', 'Unknown')}\n"
            f"ID: {ctx.get('user_id', 'Unknown')}"
        )


# =========================================================
# PAIR
# =========================================================

def cmd_pair(args, ctx):
    return (
        "🔗 PAIRING SYSTEM\n\n"
        "💚 Pair request started!\n"
        f"Next step: {PREFIX}pair2"
    )


def cmd_pair2(args, ctx):
    return (
        "🔗 PAIR 2\n\n"
        "⚡ Pairing step 2 completed!\n"
        f"Next step: {PREFIX}pair3"
    )


def cmd_pair3(args, ctx):
    return (
        "🔗 PAIR 3\n\n"
        "✅ Pairing completed!\n"
        "❤️ Connection ready."
    )


# =========================================================
# FUN
# =========================================================

def cmd_joke(args, ctx):
    jokes = [
        "😂 Why did the computer go to the doctor? It had a virus!",
        "🤣 I told my Wi-Fi we need space. Now we are not connected.",
        "😆 My code works... I have no idea why.",
        "😂 Programmer: I have no bugs. Also programmer: *creates bugs*"
    ]

    return random.choice(jokes)


def cmd_quote(args, ctx):
    quotes = [
        "✨ Believe in yourself.",
        "🔥 Stay strong and keep going.",
        "💫 Small steps can create big changes.",
        "❤️ Be kind, even when nobody is watching.",
        "🚀 Your future is created by what you do today."
    ]

    return random.choice(quotes)


def cmd_dice(args, ctx):
    return f"🎲 You rolled: {random.randint(1, 6)}"


def cmd_coinflip(args, ctx):
    return f"🪙 Result: {random.choice(['HEADS', 'TAILS'])}"


def cmd_8ball(args, ctx):
    answers = [
        "🎱 Yes.",
        "🎱 No.",
        "🎱 Definitely!",
        "🎱 Maybe.",
        "🎱 Ask again later.",
        "🎱 Most likely.",
        "🎱 I don't think so.",
        "🎱 Absolutely."
    ]

    return random.choice(answers)


def cmd_truth(args, ctx):
    return (
        "😈 TRUTH\n\n"
        "Who is the person you secretly miss the most?"
    )


def cmd_dare(args, ctx):
    return (
        "🔥 DARE\n\n"
        "Send your funniest selfie to your best friend 😂"
    )


def cmd_luck(args, ctx):
    return f"🍀 Your luck today: {random.randint(1, 100)}%"


def cmd_fortune(args, ctx):
    fortunes = [
        "🔮 Something good is coming.",
        "🔮 You will receive good news soon.",
        "🔮 Your hard work will pay off.",
        "🔮 Today is a lucky day.",
        "🔮 Someone is thinking about you."
    ]

    return random.choice(fortunes)


def cmd_fact(args, ctx):
    facts = [
        "🐐 Goats can recognize familiar faces.",
        "🌍 Earth is the only known planet with life.",
        "🐙 Octopuses have three hearts.",
        "🌙 The Moon has no atmosphere like Earth's.",
        "🧠 The human brain uses a lot of energy."
    ]

    return random.choice(facts)


# =========================================================
# TEXT TOOLS
# =========================================================

def cmd_say(args, ctx):
    if not args:
        return f"Usage: {PREFIX}say hello"

    return " ".join(args)


def cmd_reverse(args, ctx):
    if not args:
        return f"Usage: {PREFIX}reverse hello"

    return " ".join(args)[::-1]


def cmd_upper(args, ctx):
    if not args:
        return f"Usage: {PREFIX}upper hello"

    return " ".join(args).upper()


def cmd_lower(args, ctx):
    if not args:
        return f"Usage: {PREFIX}lower HELLO"

    return " ".join(args).lower()


def cmd_count(args, ctx):
    text = " ".join(args)

    return (
        f"🔢 Characters: {len(text)}\n"
        f"📝 Words: {len(text.split())}"
    )


def cmd_font(args, ctx):
    if not args:
        return f"Usage: {PREFIX}font hello"

    text = " ".join(args)

    return f"✨ 𝙵𝙾𝙽𝚃: {text}"


# =========================================================
# MATH
# =========================================================

def cmd_math(args, ctx):
    if not args:
        return f"Usage: {PREFIX}math 10+20"

    expression = "".join(args)

    allowed = "0123456789+-*/().% "

    if any(char not in allowed for char in expression):
        return "❌ Invalid math expression."

    try:
        result = eval(
            expression,
            {
                "__builtins__": {}
            },
            {}
        )

        return f"🧮 Result: {result}"

    except Exception:
        return "❌ Could not calculate."


# =========================================================
# ECONOMY / FUN COMMANDS
# =========================================================

def cmd_balance(args, ctx):
    return "💰 Balance: $5230 Goat Coins"


def cmd_daily(args, ctx):
    return "🎁 Daily reward: +$500 Goat Coins"


def cmd_work(args, ctx):
    jobs = [
        "💻 Programmer",
        "👨‍🍳 Chef",
        "🚕 Driver",
        "🧑‍🚀 Astronaut",
        "🐐 Goat Farmer"
    ]

    money = random.randint(100, 1000)

    return (
        f"💼 Job: {random.choice(jobs)}\n"
        f"💰 Earned: ${money}"
    )


def cmd_shop(args, ctx):
    return (
        "🛒 GOAT SHOP\n\n"
        "1. 🥕 Carrot - $100\n"
        "2. 🍎 Apple - $150\n"
        "3. 🐐 Baby Goat - $1000\n"
        "4. 👑 Goat Crown - $5000\n\n"
        f"Use {PREFIX}buy <item>"
    )


def cmd_buy(args, ctx):
    if not args:
        return f"Usage: {PREFIX}buy carrot"

    return f"✅ Purchased: {' '.join(args)}"


def cmd_slot(args, ctx):
    symbols = ["🐐", "🍎", "💎", "⭐", "7️⃣"]

    result = [
        random.choice(symbols),
        random.choice(symbols),
        random.choice(symbols)
    ]

    text = " | ".join(result)

    if result[0] == result[1] == result[2]:
        return f"🎰 {text}\n\n🎉 JACKPOT!"

    return f"🎰 {text}\n\n😅 Try again!"


def cmd_goat(args, ctx):
    return "🐐 Meeeeeeh!"


def cmd_love(args, ctx):
    return f"❤️ Love Level: {random.randint(1, 100)}%"


def cmd_hug(args, ctx):
    return "🤗 *Sending a big virtual hug*"


def cmd_kiss(args, ctx):
    return "😘 *Kiss sent*"


def cmd_slap(args, ctx):
    return "👋 *Slap!* 😂"


def cmd_pat(args, ctx):
    return "🥰 *Pat pat*"


def cmd_meme(args, ctx):
    memes = [
        "😂 When the bot finally works!",
        "🤣 Me: one command. Bot: 300 commands.",
        "🐐 Goat is the real boss.",
        "💻 Code: works on my machine."
    ]

    return random.choice(memes)


# =========================================================
# SOCIAL / FUN
# =========================================================

def cmd_howgay(args, ctx):
    return f"🏳️‍🌈 Gay meter: {random.randint(0, 100)}%"


def cmd_iq(args, ctx):
    return f"🧠 Your IQ: {random.randint(80, 200)}"


def cmd_ship(args, ctx):
    if len(args) >= 2:
        a = args[0]
        b = args[1]
        return f"❤️ {a} + {b} = {random.randint(1,100)}%"

    return "❤️ Ship two names!\nExample: .ship Alice Bob"


def cmd_wanted(args, ctx):
    name = " ".join(args) if args else ctx.get("username", "Unknown")

    return (
        "🚨 WANTED 🚨\n\n"
        f"👤 {name}\n"
        "💰 Reward: $10,000,000\n"
        "🐐 Crime: Being too cute 😂"
    )


def cmd_rps(args, ctx):
    choices = ["✊ Rock", "📄 Paper", "✂️ Scissors"]

    return f"🎮 You: {random.choice(choices)}"


def cmd_fight(args, ctx):
    return random.choice([
        "⚔️ You won the fight!",
        "💥 Critical hit!",
        "🥊 Victory!",
        "😂 You ran away!"
    ])


def cmd_guess(args, ctx):
    return f"🎯 Number of the day: {random.randint(1, 100)}"


def cmd_quiz(args, ctx):
    return (
        "🧠 QUIZ\n\n"
        "What sound does a goat make?\n\n"
        "A) Woof\n"
        "B) Mehh\n"
        "C) Meow"
    )


# =========================================================
# PLAY / SONG / MUSIC
# =========================================================

def download_audio(query):
    """
    Downloads audio using yt-dlp.

    Use only for content you are allowed to download.
    """

    try:
        import yt_dlp
    except ImportError:
        return None, "❌ yt-dlp is not installed."

    temp_dir = tempfile.mkdtemp(prefix="igbot_audio_")

    output_template = os.path.join(
        temp_dir,
        "%(title).80s.%(ext)s"
    )

    if query.startswith("http://") or query.startswith("https://"):
        target = query
    else:
        target = f"ytsearch1:{query}"

    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "restrictfilenames": True,
        "socket_timeout": 30,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                target,
                download=True
            )

            if "entries" in info:
                entries = info.get("entries")

                if not entries:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    return None, "❌ No result found."

                info = entries[0]

            title = info.get("title", "Audio")

        files = []

        for path in glob.glob(
            os.path.join(temp_dir, "*")
        ):
            if os.path.isfile(path):
                files.append(path)

        if not files:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None, "❌ Audio file was not created."

        audio_file = files[0]

        return {
            "type": "audio",
            "path": audio_file,
            "title": title,
            "temp_dir": temp_dir
        }, None

    except Exception as e:

        print(
            f"AUDIO DOWNLOAD ERROR: {e}",
            flush=True
        )

        traceback.print_exc()

        shutil.rmtree(
            temp_dir,
            ignore_errors=True
        )

        return None, f"❌ Download failed: {str(e)[:300]}"


def cmd_play(args, ctx):
    if not args:
        return (
            f"🎵 Usage:\n"
            f"{PREFIX}play <song name>\n\n"
            f"Example:\n"
            f"{PREFIX}play your song"
        )

    query = " ".join(args)

    result, error = download_audio(query)

    if error:
        return error

    return result


def cmd_song(args, ctx):
    return cmd_play(args, ctx)


def cmd_music(args, ctx):
    return cmd_play(args, ctx)


# =========================================================
# EXTRA COMMANDS
# =========================================================

def cmd_bank(args, ctx):
    return "🏦 Bank Balance: $0"


def cmd_dep(args, ctx):
    return "🏦 Deposit completed."


def cmd_with(args, ctx):
    return "🏦 Withdrawal completed."


def cmd_inv(args, ctx):
    return "🎒 Inventory:\n\n🐐 Goat x1\n🥕 Carrot x3"


def cmd_top(args, ctx):
    return (
        "🏆 LEADERBOARD\n\n"
        "1. GoatKing\n"
        "2. Shihab\n"
        "3. GoatMaster"
    )


def cmd_pay(args, ctx):
    return "💸 Payment completed."


def cmd_rob(args, ctx):
    return f"💰 You robbed ${random.randint(0, 500)}!"


def cmd_fish(args, ctx):
    fish = ["🐟 Fish", "🐠 Tropical Fish", "🦈 Shark", "🐡 Pufferfish"]

    return f"🎣 You caught: {random.choice(fish)}"


def cmd_hunt(args, ctx):
    return random.choice([
        "🏹 You hunted a rabbit!",
        "🏹 You found nothing!",
        "🏹 You caught a deer!"
    ])


# =========================================================
# AUTO RESPONSES
# =========================================================

AUTO_REPLIES = {

    "bby": "❤️ Yes bby?",
    "baby": "🥰 Yes baby?",
    "jan": "❤️ Yes jaan?",
    "jaan": "🥰 Haan jaan?",
    "love": "❤️ Love you too!",
    "miss": "🥺 I miss you too!",
    "thanks": "😊 You're welcome!",
    "thank you": "❤️ Anytime!",
    "sorry": "😊 It's okay.",
    "wow": "😲 Wow indeed!",
    "good morning": "🌅 Good morning!",
    "good night": "🌙 Good night! Sweet dreams ❤️",
    "gm": "🌅 Good morning!",
    "gn": "🌙 Good night!",
    "haha": "😂😂",
    "lol": "🤣",
    "😂": "😂😂",
    "❤️": "❤️",
    "love you": "❤️ Love you too!",
    "i love you": "❤️ Aww! Love you too!",
}


# =========================================================
# COMMAND REGISTRY
# =========================================================

COMMANDS = {

    # Basic
    "hi": cmd_hi,
    "hello": cmd_hello,
    "hey": cmd_hi,
    "ping": cmd_ping,
    "time": cmd_time,
    "date": cmd_date,
    "uptime": cmd_uptime,

    # Menu
    "menu": cmd_menu,
    "help": cmd_help,

    # Profile
    "info": cmd_info,
    "profile": cmd_info,
    "userinfo": cmd_info,
    "whois": cmd_info,
    "account": cmd_info,
    "instagram": cmd_info,
    "myinfo": cmd_info,

    # IDs
    "uid": cmd_info,
    "id": cmd_info,
    "userid": cmd_info,

    # Pair
    "pair": cmd_pair,
    "pair2": cmd_pair2,
    "pair3": cmd_pair3,

    # Fun
    "joke": cmd_joke,
    "quote": cmd_quote,
    "dice": cmd_dice,
    "coinflip": cmd_coinflip,
    "8ball": cmd_8ball,
    "truth": cmd_truth,
    "dare": cmd_dare,
    "luck": cmd_luck,
    "fortune": cmd_fortune,
    "fact": cmd_fact,

    # Text
    "say": cmd_say,
    "reverse": cmd_reverse,
    "upper": cmd_upper,
    "lower": cmd_lower,
    "count": cmd_count,
    "font": cmd_font,

    # Math
    "math": cmd_math,

    # Economy
    "balance": cmd_balance,
    "bal": cmd_balance,
    "daily": cmd_daily,
    "work": cmd_work,
    "shop": cmd_shop,
    "buy": cmd_buy,
    "slot": cmd_slot,
    "bank": cmd_bank,
    "dep": cmd_dep,
    "with": cmd_with,
    "inv": cmd_inv,
    "top": cmd_top,
    "pay": cmd_pay,
    "rob": cmd_rob,
    "fish": cmd_fish,
    "hunt": cmd_hunt,

    # Social
    "goat": cmd_goat,
    "love": cmd_love,
    "hug": cmd_hug,
    "kiss": cmd_kiss,
    "slap": cmd_slap,
    "pat": cmd_pat,
    "meme": cmd_meme,
    "howgay": cmd_howgay,
    "iq": cmd_iq,
    "ship": cmd_ship,
    "wanted": cmd_wanted,
    "rps": cmd_rps,
    "fight": cmd_fight,
    "guess": cmd_guess,
    "quiz": cmd_quiz,

    # Media
    "play": cmd_play,
    "song": cmd_song,
    "music": cmd_music,
}


# =========================================================
# EXTRA COMMANDS
# =========================================================

EXTRA_RESPONSES = {

    "reset": "🔄 Reset command executed.",
    "restart": "🔄 Restart requested.",
    "status": "✅ Bot is online.",
    "alive": "💚 Yes, I am alive!",
    "bot": f"🐐 I am {BOT_NAME}.",
    "owner": "👑 Owner: Shihab",
    "rules": "📜 Be respectful. No spam.",
    "prefix": f"🔧 Prefix: {PREFIX}",
    "support": "💬 Support command received.",
    "server": "🖥️ Bot server is running.",
    "version": "🤖 Bot Version: 3.0",
    "hello2": "👋 Hello again!",
    "welcome": "🎉 Welcome!",
    "thanks": "😊 You're welcome!",
    "sorry": "❤️ No problem.",
    "yes": "✅ Yes!",
    "no": "❌ No!",
    "ok": "👌 Okay!",
    "good": "🔥 Good!",
    "nice": "✨ Nice!",
    "cool": "😎 Cool!",
    "wow": "😲 Wow!",
    "lol": "😂 LOL!",
    "haha": "🤣 HAHAHA!",
}

for name, response in EXTRA_RESPONSES.items():

    def make_command(msg):
        def command(args, ctx):
            return msg

        return command

    COMMANDS[name] = make_command(response)


# =========================================================
# GENERATE EXTRA DEMO COMMANDS
# =========================================================

for i in range(1, 151):

    def make_cmd(n):
        def command(args, ctx):
            return f"✅ Command cmd{n} is working!"

        return command

    COMMANDS[f"cmd{i}"] = make_cmd(i)


for i in range(1, 151):

    def make_goat(n):
        def command(args, ctx):
            return f"🐐 Goat {n}: Meeeeeeh!"

        return command

    COMMANDS[f"goat{i}"] = make_goat(i)


# =========================================================
# CLEAN TEMP FILE
# =========================================================

def cleanup_audio(result):

    try:

        if not isinstance(result, dict):
            return

        temp_dir = result.get("temp_dir")

        if temp_dir and os.path.exists(temp_di
