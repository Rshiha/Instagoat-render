import os
import time
import random
import traceback
import threading
import tempfile
import glob
from datetime import datetime

from flask import Flask

app = Flask(__name__)

BOT_NAME = "Your Father Shihab"
PREFIX = os.environ.get("BOT_PREFIX", ".")
START_TIME = time.time()

# =========================================================
# COMMAND SYSTEM
# =========================================================

ALL_COMMANDS = {}


def simple(text):
    return lambda a: text


# =========================================================
# 👤 INSTAGRAM PROFILE
# =========================================================

def profile_command(args, ctx):
    user = ctx.get("user")

    if not user:
        return (
            "👤 PROFILE\n\n"
            f"Username: @{ctx.get('username', 'Unknown')}\n"
            f"User ID: {ctx.get('user_id', 'Unknown')}"
        )

    username = getattr(user, "username", None) or "Unknown"
    full_name = getattr(user, "full_name", None) or "Unknown"
    user_id = getattr(user, "pk", None) or ctx.get("user_id", "Unknown")

    followers = getattr(user, "follower_count", None)
    following = getattr(user, "following_count", None)
    posts = getattr(user, "media_count", None)

    private = getattr(user, "is_private", None)
    verified = getattr(user, "is_verified", None)

    bio = getattr(user, "biography", None) or "No bio"

    return (
        "╭━━━〔 👤 PROFILE 〕━━━╮\n"
        f"┃ Name: {full_name}\n"
        f"┃ Username: @{username}\n"
        f"┃ User ID: {user_id}\n"
        f"┃ Followers: {followers if followers is not None else 'Unknown'}\n"
        f"┃ Following: {following if following is not None else 'Unknown'}\n"
        f"┃ Posts: {posts if posts is not None else 'Unknown'}\n"
        f"┃ Private: {'Yes' if private else 'No'}\n"
        f"┃ Verified: {'Yes' if verified else 'No'}\n"
        f"┃ Bio: {bio}\n"
        "╰━━━━━━━━━━━━━━━━━━╯"
    )


def info_command(args, ctx):
    return profile_command(args, ctx)


ALL_COMMANDS["profile"] = profile_command
ALL_COMMANDS["info"] = info_command
ALL_COMMANDS["userinfo"] = profile_command
ALL_COMMANDS["whois"] = profile_command


def uid_command(args, ctx):
    return f"🆔 Instagram User ID: {ctx.get('user_id', 'Unknown')}"


ALL_COMMANDS["uid"] = uid_command


# =========================================================
# 🐐 BASIC
# =========================================================

ALL_COMMANDS["hi"] = simple("👋 Hello! 🐐 I am Your Father Shihab.")
ALL_COMMANDS["hello"] = ALL_COMMANDS["hi"]
ALL_COMMANDS["hey"] = ALL_COMMANDS["hi"]

ALL_COMMANDS["ping"] = simple("🏓 Pong!")
ALL_COMMANDS["pong"] = ALL_COMMANDS["ping"]

ALL_COMMANDS["bot"] = simple("🐐 Your Father Shihab Bot is online!")
ALL_COMMANDS["status"] = simple("🟢 Bot Status: ONLINE")
ALL_COMMANDS["rules"] = simple(
    "📜 RULES\n\n"
    "1. No spam\n"
    "2. No abuse\n"
    "3. Respect everyone\n"
    "4. Have fun 🐐"
)

ALL_COMMANDS["owner"] = simple("👑 Owner: @amiwho015")
ALL_COMMANDS["prefix"] = simple(f"🔧 Prefix: {PREFIX}")

ALL_COMMANDS["about"] = simple(
    "🐐 Your Father Shihab\n"
    "Instagram DM Bot\n"
    "Powered by Python + Instagrapi"
)


def uptime_command(args):
    seconds = int(time.time() - START_TIME)

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return (
        f"⏱️ UPTIME\n\n"
        f"{days}d {hours}h {minutes}m {secs}s"
    )


ALL_COMMANDS["uptime"] = uptime_command


def time_command(args):
    return f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


ALL_COMMANDS["time"] = time_command


def date_command(args):
    return f"📅 Date: {datetime.now().strftime('%Y-%m-%d')}"


ALL_COMMANDS["date"] = date_command


# =========================================================
# 💰 ECONOMY
# =========================================================

ALL_COMMANDS["balance"] = simple("💰 Balance: $5,230 Goat Coins")
ALL_COMMANDS["bal"] = ALL_COMMANDS["balance"]

ALL_COMMANDS["daily"] = simple("🎁 Daily Claimed! +$500")
ALL_COMMANDS["work"] = simple("💼 You worked at Goat Farm and earned $150!")
ALL_COMMANDS["job"] = ALL_COMMANDS["work"]

ALL_COMMANDS["rob"] = simple("🦹 You tried to rob and got $0! Police caught you!")
ALL_COMMANDS["bank"] = simple("🏦 Bank Balance: $0")

ALL_COMMANDS["deposit"] = simple("✅ Deposited $100")
ALL_COMMANDS["dep"] = ALL_COMMANDS["deposit"]

ALL_COMMANDS["withdraw"] = simple("✅ Withdrawn $100")
ALL_COMMANDS["with"] = ALL_COMMANDS["withdraw"]

ALL_COMMANDS["shop"] = simple(
    "🛒 SHOP\n\n"
    "1. 🐐 Goat - $100\n"
    "2. 🍖 Food - $20\n"
    "3. 🧸 Toy - $50\n"
    "4. 🏠 House - $5000"
)

ALL_COMMANDS["market"] = ALL_COMMANDS["shop"]
ALL_COMMANDS["store"] = ALL_COMMANDS["shop"]

ALL_COMMANDS["buy"] = lambda a: (
    f"✅ You bought {' '.join(a) if a else 'Goat'}!"
)

ALL_COMMANDS["sell"] = simple("✅ Sold item for $50!")
ALL_COMMANDS["sellall"] = simple("✅ Sold all items for $500!")

ALL_COMMANDS["inventory"] = simple(
    "🎒 INVENTORY\n\n🐐 Goat x1\n🍖 Food x5\n🧸 Toy x2"
)

ALL_COMMANDS["inv"] = ALL_COMMANDS["inventory"]

ALL_COMMANDS["level"] = simple("⭐ Level: 10\nXP: 1250/2000")

ALL_COMMANDS["leaderboard"] = simple(
    "🏆 LEADERBOARD\n\n"
    "🥇 @goatking — $100k\n"
    "🥈 You — $5230\n"
    "🥉 @goatboy — $4000"
)

ALL_COMMANDS["top"] = ALL_COMMANDS["leaderboard"]

ALL_COMMANDS["pay"] = simple("💸 Payment request completed!")
ALL_COMMANDS["gift"] = simple("🎁 Gift sent!")
ALL_COMMANDS["beg"] = simple("🥺 A kind person gave you $10!")
ALL_COMMANDS["crime"] = simple("🚨 Crime completed! +$200")
ALL_COMMANDS["fish"] = simple("🎣 Golden Goat Fish caught! +$100")
ALL_COMMANDS["hunt"] = simple("🏹 You hunted successfully! +Meat x1")
ALL_COMMANDS["mine"] = simple("⛏️ Mined 5 Goat Coins!")
ALL_COMMANDS["chop"] = simple("🪓 Chopped wood x10!")
ALL_COMMANDS["farm"] = simple("🌾 Farm harvested +$200!")
ALL_COMMANDS["cook"] = simple("🍳 Cooked Goat Meat!")
ALL_COMMANDS["craft"] = simple("🔨 Crafted Goat Toy!")
ALL_COMMANDS["rich"] = simple("💎 You are 45% richer than others!")
ALL_COMMANDS["loan"] = simple("🏦 Loan taken: $1000")
ALL_COMMANDS["salary"] = simple("💵 Salary: $100/day")
ALL_COMMANDS["bonus"] = simple("🎉 Bonus: +$1000!")


# =========================================================
# 🎮 GAMES
# =========================================================

def dice_command(args):
    return f"🎲 You rolled: {random.randint(1, 6)}"


ALL_COMMANDS["dice"] = dice_command
ALL_COMMANDS["roll"] = dice_command


def coin_command(args):
    return "🪙 Coin: " + random.choice(["HEADS", "TAILS"])


ALL_COMMANDS["coinflip"] = coin_command
ALL_COMMANDS["cf"] = coin_command
ALL_COMMANDS["flip"] = coin_command


def slot_command(args):
    symbols = ["🐐", "🍒", "⭐", "💎", "🍋"]
    result = [random.choice(symbols) for _ in range(3)]

    if result[0] == result[1] == result[2]:
        return f"🎰 {' | '.join(result)}\n🎉 JACKPOT!"

    return f"🎰 {' | '.join(result)}"


ALL_COMMANDS["slot"] = slot_command
ALL_COMMANDS["slots"] = slot_command

ALL_COMMANDS["rps"] = simple("✊ Rock vs 📄 Paper - You Lose!")
ALL_COMMANDS["fight"] = simple("⚔️ You fought and WON! +$100")
ALL_COMMANDS["battle"] = ALL_COMMANDS["fight"]
ALL_COMMANDS["duel"] = ALL_COMMANDS["fight"]

ALL_COMMANDS["lottery"] = simple("🎟️ Lottery ticket bought!")
ALL_COMMANDS["jackpot"] = simple("💰 Jackpot: $10,000!")
ALL_COMMANDS["blackjack"] = simple("🃏 You 18 vs Dealer 17 — You Win!")
ALL_COMMANDS["bj"] = ALL_COMMANDS["blackjack"]
ALL_COMMANDS["poker"] = simple("♠️ Poker hand: Pair of Goats!")
ALL_COMMANDS["quiz"] = simple("❓ Quiz: What does a Goat say?\nAnswer: Meeeh!")
ALL_COMMANDS["trivia"] = ALL_COMMANDS["quiz"]

ALL_COMMANDS["guess"] = simple("🤔 Guess a number between 1-10!")

ALL_COMMANDS["fasttype"] = simple("⌨️ Type: goat is king")
ALL_COMMANDS["hangman"] = simple("🔤 Hangman: _ O A T")
ALL_COMMANDS["tictactoe"] = simple("⭕❌ Tic Tac Toe started!")
ALL_COMMANDS["connect4"] = simple("🔴🟡 Connect 4 started!")
ALL_COMMANDS["snake"] = simple("🐍 Snake score: 10")
ALL_COMMANDS["tetris"] = simple("🧱 Tetris: Line cleared!")
ALL_COMMANDS["race"] = simple("🏁 Goat Race started! You are 1st!")
ALL_COMMANDS["run"] = ALL_COMMANDS["race"]

ALL_COMMANDS["jump"] = simple("🦘 Goat jumped 5ft!")
ALL_COMMANDS["fly"] = simple("🕊️ Goat is flying!")
ALL_COMMANDS["swim"] = simple("🏊 Goat is swimming!")
ALL_COMMANDS["climb"] = simple("🧗 Goat climbed the mountain!")
ALL_COMMANDS["explore"] = simple("🗺️ You explored Goat Village!")
ALL_COMMANDS["adventure"] = ALL_COMMANDS["explore"]

ALL_COMMANDS["quest"] = simple("📜 Quest: Find 5 Golden Goats!")
ALL_COMMANDS["mission"] = ALL_COMMANDS["quest"]

ALL_COMMANDS["boss"] = simple("👹 Boss Goat appeared! HP: 1000")
ALL_COMMANDS["heal"] = simple("❤️ Healed +50 HP!")
ALL_COMMANDS["attack"] = simple("💥 Damage: 100!")
ALL_COMMANDS["defend"] = simple("🛡️ Defense activated!")
ALL_COMMANDS["magic"] = simple("✨ Magic spell cast!")
ALL_COMMANDS["spell"] = ALL_COMMANDS["magic"]

ALL_COMMANDS["pet"] = simple("🐾 Pet Goat: Happy ❤️")
ALL_COMMANDS["feed"] = simple("🥕 Goat fed! +10 Happiness")
ALL_COMMANDS["train"] = simple("🏋️ Goat trained! +5 Strength")
ALL_COMMANDS["evolve"] = simple("🌟 Goat evolved into Super Goat!")
ALL_COMMANDS["catch"] = simple("🤲 Wild Goat caught!")
ALL_COMMANDS["release"] = simple("🕊️ Goat released!")
ALL_COMMANDS["trade"] = simple("🔄 Trade request sent!")
ALL_COMMANDS["gamble"] = simple("🎲 Gambled $100 and won $200!")
ALL_COMMANDS["bet"] = ALL_COMMANDS["gamble"]


# =========================================================
# 😂 FUN
# =========================================================

JOKES = [
    "😂 Why did the goat cross the road? To reach the other farm!",
    "😂 Programmers have bugs. Goats have horns.",
    "😂 Goat entered a coding contest and won because it had great RAM!",
]

QUOTES = [
    "✨ Progress is better than perfection.",
    "🔥 Keep going.",
    "💫 Small steps become big results.",
    "🐐 Be a GOAT, not a sheep.",
]


def joke_command(args):
    return random.choice(JOKES)


def quote_command(args):
    return random.choice(QUOTES)


ALL_COMMANDS["joke"] = joke_command
ALL_COMMANDS["jokes"] = joke_command
ALL_COMMANDS["quote"] = quote_command
ALL_COMMANDS["quotes"] = quote_command

ALL_COMMANDS["meme"] = simple("😂 Meme: Goat says BAAAAA!")
ALL_COMMANDS["love"] = simple("❤️ Love Meter: 100%")
ALL_COMMANDS["goat"] = simple("🐐 Meeeeeeh!")
ALL_COMMANDS["moo"] = simple("🐄 Moo? No! 🐐 Meeeeh!")
ALL_COMMANDS["baa"] = simple("🐐 Baaaaaaa!")

ALL_COMMANDS["roast"] = simple("🔥 You are as useless as a goat without horns!")
ALL_COMMANDS["compliment"] = simple("😊 You are amazing like a Golden Goat!")
ALL_COMMANDS["insult"] = ALL_COMMANDS["roast"]

ALL_COMMANDS["hug"] = simple("🤗 *hugs you*")
ALL_COMMANDS["kiss"] = simple("😘 *kiss*")
ALL_COMMANDS["slap"] = simple("👋 *slap with goat*")
ALL_COMMANDS["pat"] = simple("🥰 *pats goat*")
ALL_COMMANDS["cuddle"] = simple("🤗 *cuddles goat*")

ALL_COMMANDS["howcute"] = simple("🥺 Cute: 100%")
ALL_COMMANDS["howdumb"] = simple("🧠 Dumb: 0%")
ALL_COMMANDS["wanted"] = simple("🚨 WANTED: Goat Thief!")
ALL_COMMANDS["drake"] = simple("👎 Goat Farm\n👍 Goat Palace")
ALL_COMMANDS["fact"] = simple("🧠 Fact: Goats can have different accents!")
ALL_COMMANDS["advice"] = simple("💡 Always feed your goat!")

ALL_COMMANDS["truth"] = simple("🤥 Truth: Have you ever talked to a goat?")
ALL_COMMANDS["dare"] = simple("😈 Dare: Send a goat picture to your friend!")
ALL_COMMANDS["wouldyou"] = simple("🤔 Would you rather be a Goat or Sheep?")
ALL_COMMANDS["wyr"] = ALL_COMMANDS["wouldyou"]

ALL_COMMANDS["ship"] = simple("💞 You + Goat = 100%")
ALL_COMMANDS["simp"] = simple("💘 You are simping for Goat!")
ALL_COMMANDS["clown"] = simple("🤡 Honk honk! Clown Goat!")
ALL_COMMANDS["iq"] = simple("🧠 IQ: 200 — Goat Genius!")
ALL_COMMANDS["smart"] = ALL_COMMANDS["iq"]
ALL_COMMANDS["dumb"] = simple("🤪 Dumb: 1%")
ALL_COMMANDS["emojify"] = simple("🐐🐑🐐 Goat emojified!")

ALL_COMMANDS["mock"] = simple("MoCkInG gOaT 😂")
ALL_COMMANDS["owo"] = simple("OwO Goat is cute!")
ALL_COMMANDS["uwu"] = simple("UwU Goat wuv you!")
ALL_COMMANDS["lenny"] = simple("( ͡° ͜ʖ ͡°) Goat")
ALL_COMMANDS["tableflip"] = simple("(╯°□°）╯︵ ┻━┻")
ALL_COMMANDS["shrug"] = simple("¯\\_(ツ)_/¯")
ALL_COMMANDS["ascii"] = simple("(\\_/)\n( •_•)\n/ >🐐")

ALL_COMMANDS["soulmate"] = simple("💘 Your soulmate is a Goat!")
ALL_COMMANDS["crush"] = simple("😍 Your crush likes goats!")
ALL_COMMANDS["luck"] = simple("🍀 Luck today: 99%")
ALL_COMMANDS["fortune"] = simple("🥠 You will own 100 goats!")
ALL_COMMANDS["horoscope"] = simple("♈ Goats will bring you luck!")
ALL_COMMANDS["zodiac"] = ALL_COMMANDS["horoscope"]
ALL_COMMANDS["magic8"] = simple("🎱 Yes, definitely!")


# =========================================================
# 📝 TEXT
# =========================================================

def say_command(args):
    return "📢 " + (" ".join(args) if args else "Goat!")


def reverse_command(args):
    text = " ".join(args)
    return "🔄 " + (text[::-1] if text else "taoG")


def upper_command(args):
    return "🔠 " + (" ".join(args).upper() if args else "TEXT")


def lower_command(args):
    return "🔡 " + (" ".join(args).lower() if args else "text")


def count_command(args):
    text = " ".join(args)

    return (
        f"🔢 Characters: {len(text)}\n"
        f"Words: {len(text.split())}"
    )


ALL_COMMANDS["say"] = say_command
ALL_COMMANDS["echo"] = say_command
ALL_COMMANDS["reverse"] = reverse_command
ALL_COMMANDS["rev"] = reverse_command
ALL_COMMANDS["upper"] = upper_command
ALL_COMMANDS["uppercase"] = upper_command
ALL_COMMANDS["lower"] = lower_command
ALL_COMMANDS["lowercase"] = lower_command
ALL_COMMANDS["count"] = count_command
ALL_COMMANDS["chars"] = count_command

ALL_COMMANDS["repeat"] = lambda a: (
    " ".join(a) if a else "Nothing to repeat."
)

ALL_COMMANDS["font"] = lambda a: (
    "𝔾𝕠𝕒𝕥 " + " ".join(a) if a else "𝔾𝕠𝕒𝕥"
)

ALL_COMMANDS["bold"] = lambda a: "𝗚𝗢𝗔𝗧 " + " ".join(a)
ALL_COMMANDS["style"] = lambda a: "✨ " + " ".join(a)
ALL_COMMANDS["binary"] = lambda a: (
    " ".join(format(ord(c), "08b") for c in " ".join(a))
    if a else "Usage: .binary text"
)


# =========================================================
# 🧮 MATH
# =========================================================

def math_command(args):
    expression = " ".join(args)

    if not expression:
        return f"🧮 Usage: {PREFIX}math 10+20"

    allowed = "0123456789+-*/(). %"

    if any(c not in allowed for c in expression):
        return "❌ Only basic mathematics is allowed."

    try:
        result = eval(
            expression,
            {"__builtins__": {}},
            {}
        )

        return f"🧮 {expression} = {result}"

    except Exception:
        return "❌ Invalid calculation."


ALL_COMMANDS["math"] = math_command
ALL_COMMANDS["calc"] = math_command
ALL_COMMANDS["calculate"] = math_command

ALL_COMMANDS["square"] = lambda a: (
    f"🔢 {a[0]}² = {int(a[0]) ** 2}"
    if a and a[0].isdigit()
    else "Usage: .square 5"
)

ALL_COMMANDS["cube"] = lambda a: (
    f"🔢 {a[0]}³ = {int(a[0]) ** 3}"
    if a and a[0].isdigit()
    else "Usage: .cube 5"
)


# =========================================================
# 🔐 PAIR
# =========================================================

ALL_COMMANDS["pair"] = simple(
    "🔗 PAIR\n\n"
    "Pairing sequence started.\n"
    f"Use {PREFIX}pair2"
)

ALL_COMMANDS["pair2"] = simple(
    "🔗 PAIR 2\n\n"
    "Second step completed.\n"
    f"Use {PREFIX}pair3"
)

ALL_COMMANDS["pair3"] = simple(
    "🔗 PAIR 3\n\n"
    "✅ Pairing sequence completed!"
)


# =========================================================
# 🎵 PLAY / SONG
# =========================================================

def download_media(query):
    """
    Downloads audio using yt-dlp.
    Intended for content the user owns or is authorized to download.
    """

    try:
        import yt_dlp
    except ImportError:
        return None, "❌ yt-dlp is not installed."

    temp_dir = tempfile.mkdtemp(prefix="instagoat_")

    output = os.path.join(temp_dir, "%(title).80s.%(ext)s")

    options = {
        "format": "bestaudio/best",
        "outtmpl": output,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    # URL অথবা search
    if query.startswith(("http://", "https://")):
        target = query
    else:
        target = "ytsearch1:" + query

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(target, download=True)

            if "entries" in info:
                entries = info.get("entries") or []

                if not entries:
                    return None, "❌ Song not found."

                info = entries[0]

            title = info.get("title", "audio")

        files = glob.glob(os.path.join(temp_dir, "*"))

        if not files:
            return None, "❌ Download failed."

        return files[0], title

    except Exception as e:
        print("YT-DLP ERROR:", e, flush=True)
        traceback.print_exc()
        return None, "❌ Could not download media."


def play_command(args):
    if not args:
        return (
            f"🎵 PLAY\n\n"
            f"Usage:\n"
            f"{PREFIX}play song name\n"
            f"{PREFIX}play https://example.com/video"
        )

    query = " ".join(args)

    path, result = download_media(query)

    if not path:
        return result

    # File path temporaryভাবে store করা হচ্ছে।
    # DM loop attachment পাঠাবে।
    return {
        "type": "audio",
        "path": path,
        "title": result
    }


ALL_COMMANDS["play"] = play_command
ALL_COMMANDS["song"] = play_command
ALL_COMMANDS["music"] = play_command


# =========================================================
# 📋 MENU
# =========================================================

def menu_command(args):
    names = sorted(ALL_COMMANDS.keys())

    # Instagram DM message খুব বড় হয়ে যাওয়া আটকানো
    lines = [
        f"🐐 {BOT_NAME}",
        "",
        f"📚 Total Commands: {len(ALL_COMMANDS)}",
        "",
        "COMMAND LIST",
        "━━━━━━━━━━━━━━━━"
    ]

    for i, name in enumerate(names, 1):
        lines.append(f"{i}. {PREFIX}{name}")

        if i >= 240:
            lines.append("...")
            break

    return "\n".join(lines)


ALL_COMMANDS["menu"] = menu_command
ALL_COMMANDS["help"] = menu_command


# =========================================================
# AUTO TEST COMMANDS
# =========================================================

for i in range(1, 31):
    ALL_COMMANDS[f"cmd{i}"] = (
        lambda a, n=i:
        f"✅ Test Command {n} Working!"
    )

for i in range(1, 31):
    ALL_COMMANDS[f"goat{i}"] = (
        lambda a, n=i:
        f"🐐 Goat #{n} says Meeeh!"
    )


# =========================================================
# EXTRA ALIASES
# =========================================================

extra_aliases = {
    "start": "menu",
    "commands": "menu",
    "cmds": "menu",
    "list": "menu",
    "hello2": "hello",
    "good": "hi",
    "joke2": "joke",
    "fun": "joke",
    "game": "dice",
    "random": "dice",
    "coin": "coinflip",
    "roll": "dice",
    "shoplist": "shop",
    "items": "inventory",
    "myinfo": "profile",
    "account": "profile",
    "instagram": "profile",
    "iginfo": "profile",
    "id": "uid",
    "userid": "uid",
    "calculate": "math",
    "reverseit": "reverse",
    "uppertext": "upper",
    "lowertext": "lower",
}

for alias, target in extra_aliases.items():
    if target in ALL_COMMANDS:
        ALL_COMMANDS[alias] = ALL_COMMANDS[target]


print(
    f"🐐 Loaded {len(ALL_COMMANDS)} Instagram commands",
    flush=True
)


# =========================================================
# 🤖 BOT
# =========================================================

def run_bot():

    print("===
