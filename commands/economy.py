import random
def balance(a,c): return "💰 Balance: 1,000 coins\n🏦 Bank: 0 coins"
def daily(a,c): return "🎁 Daily reward: +500 coins!"
def work(a,c): return f"💼 Earned {random.randint(100,500)} coins!"
def shop(a,c): return "🛒 SHOP\n🍫 Chocolate — 100\n🎁 Gift — 250\n💎 Diamond — 1000"
def buy(a,c): return "🛍️ Demo purchase system."
def slot(a,c):
 x=[random.choice(["🍒","🍋","💎","7️⃣"]) for _ in range(3)]
 return f"🎰 {' | '.join(x)}\n{'🎉 JACKPOT!' if x[0]==x[1]==x[2] else '😅 Try again!'}"
def bank(a,c): return "🏦 Bank balance: 0 coins"
ECONOMY_COMMANDS={"balance":balance,"daily":daily,"work":work,"shop":shop,"buy":buy,"slot":slot,"bank":bank}
