import requests, re, random

def pin_command(args, ctx):
    if not args:
        return "❌ Usage:.pin cat"
    query = " ".join(args).replace("-", "").strip() or "cat"
    cl = ctx.get("client")
    thread_id = ctx.get("thread_id")
    try:
        cl.direct_send(f"📌 Searching Pinterest: {query}...", thread_ids=[thread_id])
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(f"https://www.pinterest.com/search/pins/?q={query}", headers=headers, timeout=15)
        images = re.findall(r'https://i\.pinimg\.com/236x[^\s"\\]+', r.text)
        images = list(set([u.replace('236x','736x') for u in images]))[:20]
        if not images:
            return f"❌ '{query}' pic pailam na!"
        for img in images[:10]:
            try: cl.direct_send_image(img, thread_ids=[thread_id])
            except: pass
        return f"✅ {len(images)} ta {query} pic sent!"
    except Exception as e:
        print(f"PIN ERROR {e}")
        return "❌ Pinterest error!"

PINTEREST_COMMANDS = {"pin": pin_command, "pinterest": pin_command}