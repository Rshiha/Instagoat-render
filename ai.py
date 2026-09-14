import requests, random, urllib.parse, os

def ai_reply(text):
    prompt = f"You are a funny Bengali friend. Reply short in Banglish: {text}"

    # 1. Pollinations - kono key lage na, unlimited
    try:
        r = requests.get(
            f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}?model=openai",
            timeout=30
        )
        if r.status_code == 200 and len(r.text) > 2:
            return r.text
    except:
        pass

    # 2. Ollama public server - no key
    try:
        r = requests.post(
            "https://ollama.com/api/chat",
            json={
                "model": "nemotron-3-nano:30b",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=10
        )
        if r.status_code == 200:
            return r.json().get('message', {}).get('content', '')
    except:
        pass

    # 3. Last fallback - bot kokhono chup thakbe na
    return random.choice([
        "Bolo bolo shunchi 🖤",
        "Areh tai naki? 😅 bolo",
        "Hmm bujlam re, tarpor?",
        "Ki hoise bolo na 🥲"
    ])


def generate_pic(prompt):
    try:
        seed = random.randint(1, 999999)
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?seed={seed}&nologo=true&model=flux&width=1024&height=1024"
        r = requests.get(url, timeout=40)
        if r.status_code == 200:
            path = f"/tmp/{seed}.jpg"
            with open(path, 'wb') as f:
                f.write(r.content)
            return path
    except:
        pass
    return None
