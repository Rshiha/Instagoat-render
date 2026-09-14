import requests, random, urllib.parse, os

def get_ai_reply(prompt):
    prompt = (prompt or "").strip()

    if not prompt:
        return "❌ কিছু জিজ্ঞেস করো তো!"

    try:
        encoded = urllib.parse.quote(prompt)
        url = f"https://text.pollinations.ai/{encoded}?model=openai"
        r = requests.get(url, timeout=30)

        if r.status_code == 200 and r.text.strip():
            return r.text

    except Exception as e:
        print(f"AI REPLY ERR: {e}", flush=True)
        return f"Error: {e}"

    return "❌ Try again"


def generate_pic(prompt):
    prompt = (prompt or "").strip()

    if not prompt:
        return None

    try:
        seed = random.randint(1, 999999)
        url = (
            f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
            f"?seed={seed}&nologo=true&model=flux&width=1024&height=1024"
        )
        r = requests.get(url, timeout=40)

        content_type = r.headers.get("content-type", "")

        if r.status_code == 200 and content_type.startswith("image/"):
            path = f"/tmp/{seed}.jpg"

            with open(path, "wb") as f:
                f.write(r.content)

            return path

        print(
            f"AI IMG ERR: status={r.status_code} content-type={content_type}",
            flush=True
        )

    except Exception as e:
        print(f"AI IMG ERR: {e}", flush=True)

    return None