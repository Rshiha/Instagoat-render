import requests, random, urllib.parse

def get_ai_reply(text):
    prompt = f"You are a funny Bengali friend. Reply short in Banglish: {text}"

    # 1. Pollinations - key chara, model param chara (free)
    try:
        r = requests.get(f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}", timeout=15)
        if r.status_code == 200 and len(r.text) > 5 and "budget" not in r.text.lower():
            return r.text.strip()
    except: pass

    # 2. Ollama free models - try 3 ta best model
    for model_name in ["openrouter/free", "nemotron-3-nano:30b", "models/gemini-3.1-flash-lite"]:
        try:
            r = requests.post("https://ollama.com/api/chat",
                json={"model": model_name, "messages": [{"role": "user", "content": prompt}], "stream": False},
                timeout=15)
            if r.status_code == 200:
                msg = r.json().get('message',{}).get('content','')
                if msg: return msg.strip()
        except: continue

    return random.choice(["Bolo bolo shunchi 🖤", "Areh tai naki? 😅 bolo", "Hmm bujlam re, tarpor?"])
