import random
def joke(a,c): return random.choice(["😂 Computer went to doctor: it had a virus!","🤣 Programmer's favorite place? The coffee shop.","😎 My bot needs more processing."])
def quote(a,c): return random.choice(["✨ Keep going.","🔥 Build. Test. Improve.","💫 Focus today."])
def dice(a,c): return f"🎲 {random.randint(1,6)}"
def truth(a,c): return random.choice(["❤️ Who do you text most?","😏 Biggest secret?","😂 Funniest mistake?"])
def dare(a,c): return random.choice(["😎 Send a funny emoji.","😂 Say something random.","🔥 Make someone laugh."])
def ball8(a,c): return random.choice(["🎱 Yes.","🎱 No.","🎱 Maybe.","🎱 Definitely!"])
FUN_COMMANDS={"joke":joke,"quote":quote,"dice":dice,"truth":truth,"dare":dare,"8ball":ball8}
