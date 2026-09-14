import requests, re, random
from bs4 import BeautifulSoup

def pin_command(args, ctx):
    if not args:
        return "❌ Usage: .pin cat"
    
    full_string = " ".join(args)
    # ইউজার ভুল করে ".pin cat - 10" বা ডেসক্রিপশনসহ দিলে শুধু মূল কিউয়ার্ড আলাদা করা
    if " - " in full_string:
        query = full_string.split(" - ")[0].strip()
    else:
        query = full_string.replace("-", "").strip()
        
    if not query:
        query = "cat"
        
    cl = ctx.get("client")
    thread_id = ctx.get("thread_id")
    
    try:
        cl.direct_send(f"📌 Searching Pinterest: {query}...", thread_ids=[thread_id])
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        r = requests.get(f"https://pinterest.com{query}", headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and 'pinimg.com' in src:
                # ছবির কোয়ালিটি বাড়িয়ে হাই-রেজোলিউশন (736x) করা
                high_res = src.replace('/236x/', '/736x/').replace('/474x/', '/736x/')
                images.append(high_res)
                
        images = list(set(images))[:10]
        
        if not images:
            return f"❌ '{query}' pic pailam na!"
            
        for img in images:
            try: 
                cl.direct_send_image(img, thread_ids=[thread_id])
            except: 
                pass
                
        return f"✅ {len(images)} ta {query} pic sent!"
        
    except Exception as e:
        print(f"PIN ERROR {e}")
        return "❌ Pinterest error!"

PINTEREST_COMMANDS = {"pin": pin_command, "pinterest": pin_command}
