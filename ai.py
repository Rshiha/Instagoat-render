import requests, urllib.parse, random

def get_ai_reply(prompt):
    try:
        # No API key, direct URL
        url = f"https://text.pollinations.ai/{urllib.parse.quote(prompt)}?model=openai-large"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return "Try again bro, server busy"

def generate_pic(prompt):
    try:
        seed = random.randint(1, 9999999)
        url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}?seed={seed}&nologo=true&model=turbo"
        r = requests.get(url, timeout=40)
        if r.status_code == 200:
            p = f"/tmp/{seed}.jpg"
            open(p,'wb').write(r.content)
            return p
    except:
        pass
    return None
