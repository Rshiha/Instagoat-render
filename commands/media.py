import os
import json
import yt_dlp

def get_audio(song_name):
    # আপনার দেওয়া JSON কুকিজ সরাসরি ডিকশনারি আকারে এখানে সেট করা হলো
    cookies_data = [
      {
        "domain": ".youtube.com",
        "expirationDate": 1789240784.182746,
        "hostOnly": False,
        "httpOnly": True,
        "name": "GPS",
        "path": "/",
        "sameSite": "unspecified",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "1"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800446.992407,
        "hostOnly": False,
        "httpOnly": False,
        "name": "PREF",
        "path": "/",
        "sameSite": "unspecified",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "f6=40000000&tz=Asia.Dhaka"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800140.337416,
        "hostOnly": False,
        "httpOnly": True,
        "name": "HSID",
        "path": "/",
        "sameSite": "unspecified",
        "secure": False,
        "session": False,
        "storeId": "0",
        "value": "AVYebjZ6LbbYnyGFS"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800140.338001,
        "hostOnly": False,
        "httpOnly": True,
        "name": "SSID",
        "path": "/",
        "sameSite": "unspecified",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "AiR-sPgSEwExRfTna"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800140.338259,
        "hostOnly": False,
        "httpOnly": False,
        "name": "APISID",
        "path": "/",
        "sameSite": "unspecified",
        "secure": False,
        "session": False,
        "storeId": "0",
        "value": "rhUeVDmPAZTrqfjc/AFrWxmjt-J9G6GPiN"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800140.338566,
        "hostOnly": False,
        "httpOnly": False,
        "name": "SAPISID",
        "path": "/",
        "sameSite": "unspecified",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "W2FV2--9AVnLCy3K/A384UjidPTuoZSo73"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800140.338753,
        "hostOnly": False,
        "httpOnly": False,
        "name": "__Secure-1PAPISID",
        "path": "/",
        "sameSite": "unspecified",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "W2FV2--9AVnLCy3K/A384UjidPTuoZSo73"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800140.338962,
        "hostOnly": False,
        "httpOnly": False,
        "name": "__Secure-3PAPISID",
        "path": "/",
        "sameSite": "no_restriction",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "W2FV2--9AVnLCy3K/A384UjidPTuoZSo73"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800140.339173,
        "hostOnly": False,
        "httpOnly": True,
        "name": "SID",
        "path": "/",
        "sameSite": "unspecified",
        "secure": False,
        "session": False,
        "storeId": "0",
        "value": "g.a000Cgkk3r3pdxvvx4rXEZj4G1DFZ8IzNkhIZGedd_uYhlsm6My6aWd27AucMQZ9BpyzaAdP4gACgYKAUoSARcSFQHGX2MiqTDhzuQf9yFAj1kFNijxdBoVAUF8yKrG778lY-5wCJSUr9csx5c20076"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800140.339367,
        "hostOnly": False,
        "httpOnly": True,
        "name": "__Secure-1PSID",
        "path": "/",
        "sameSite": "unspecified",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "g.a000Cgkk3r3pdxvvx4rXEZj4G1DFZ8IzNkhIZGedd_uYhlsm6My6bijiVaug5CBxqF8EIdjGjAACgYKAWoSARcSFQHGX2MiNoT3g3AHQIrYbKeV_6XVcBoVAUF8yKrYJDeFDGEfoN0CMvEJPHOP0076"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823800140.339597,
        "hostOnly": False,
        "httpOnly": True,
        "name": "__Secure-3PSID",
        "path": "/",
        "sameSite": "no_restriction",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "g.a000Cgkk3r3pdxvvx4rXEZj4G1DFZ8IzNkhIZGedd_uYhlsm6My6iJGexTXxABpVwYYAZHPfCQACgYKAWsSARcSFQHGX2Mi_j4W1_aNSNac1gpSr32rKxoVAUF8yKrPsLB202WeD6Uiqdv5RWJ_0076"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1823799369.972414,
        "hostOnly": False,
        "httpOnly": True,
        "name": "LOGIN_INFO",
        "path": "/",
        "sameSite": "no_restriction",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "AFmmF2swRgIhAMY1p-XK42D5OETgkoPyVI2XkAADgwgC57lyiD9qZ7i6AiEA_PySlD5Ub-9K1Dm8m0pXVaqd2TmiIP9i6ROlnb_NKzw:QUQ3MjNmd254ank4NGh2OXpkY2NCUlBzVC1ORWdoN2VvSGNFOUdSa295Rk9tcTBDeXM5bkcxRzdNQkhaQjVZdXdad1AxWnV5dUxYcjJ0RE5EdHNER3RSQnZKQWQ1bUdsMm14NENhNFlZamtuQWE5aTdERlF6RFk3YmstVHV2RHBkc0ZOTUVtSEFQM1l5aHhnYXg0VXpNeGtWRTNVQl9Ib3l3"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1820776140.336521,
        "hostOnly": False,
        "httpOnly": True,
        "name": "__Secure-1PSIDTS",
        "path": "/",
        "sameSite": "unspecified",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "sidts-CjQBXMw41VFWYYCmI7mIdl7QK0PQ4KgYG3ERjY9eRDRInFAG5geOj8ZOM7Q8pxHfySKC7GhWEAA"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1820776140.336984,
        "hostOnly": False,
        "httpOnly": True,
        "name": "__Secure-3PSIDTS",
        "path": "/",
        "sameSite": "no_restriction",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "sidts-CjQBXMw41VFWYYCmI7mIdl7QK0PQ4KgYG3ERjY9eRDRInFAG5geOj8ZOM7Q8pxHfySKC7GhWEAA"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1820776449.168452,
        "hostOnly": False,
        "httpOnly": False,
        "name": "SIDCC",
        "path": "/",
        "sameSite": "unspecified",
        "secure": False,
        "session": False,
        "storeId": "0",
        "value": "AKEyXzV861_en9LJBn-0_SFijXcedoZLHOTYuQTy2hubzZNYOriKnJWLEXJEHAipZi5m6x-wBQ"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1820776449.168644,
        "hostOnly": False,
        "httpOnly": True,
        "name": "__Secure-1PSIDCC",
        "path": "/",
        "sameSite": "unspecified",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "AKEyXzUXVVliQYB6f3uoHsurbcqtSmCOFy8XPV-EeovVjx0ebJFTDp9bs5MbF9rfAhN5cSP5"
      },
      {
        "domain": ".youtube.com",
        "expirationDate": 1820776449.168938,
        "hostOnly": False,
        "httpOnly": True,
        "name": "__Secure-3PSIDCC",
        "path": "/",
        "sameSite": "no_restriction",
        "secure": True,
        "session": False,
        "storeId": "0",
        "value": "AKEyXzUbky7QXOT3qsweTSHevkKdzw_vL9aDKOWMhXqTxzIc6_Pn7QdiocKKyWmyxKUTBvJm"
      }
    ]

    # தற்காலிகভাবে কুকিজগুলো Netscape ফরম্যাটে একটি ফাইলে সেভ করে yt-dlp কে দেওয়া হবে
    cookie_file_path = "temp_cookies.txt"
    with open(cookie_file_path, "w", encoding="utf-8") as f:
        f.write("# Netscape HTTP Cookie File\n")
        for cookie in cookies_data:
            domain = cookie.get("domain", ".youtube.com")
            flag = "TRUE" if domain.startswith(".") else "FALSE"
            path = cookie.get("path", "/")
            secure = "TRUE" if cookie.get("secure", False) else "FALSE"
            expires = str(int(cookie.get("expirationDate", 1823800000)))
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'cookiefile': cookie_file_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=True)
            filename = ydl.prepare_filename(info)
            final_file = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            return final_file
    finally:
        # কাজ শেষে টেম্পোরারি ফাইল রিমুভ করে দেওয়া
        if os.path.exists(cookie_file_path):
            os.remove(cookie_file_path)

def play(a, c):
    if not a:
        return "🎵 Usage: .play song name"
    
    song_name = " ".join(a)
    
    try:
        file_path = get_audio(song_name)
    except Exception as e:
        print(f"AUDIO DOWNLOAD ERROR: {e}", flush=True)
        return "❌ গান ডাউনলোড করতে সমস্যা হয়েছে। দয়া করে আবার চেষ্টা করুন।"
    
    return {
        "type": "audio",
        "path": file_path,
        "title": song_name,
        "cleanup": lambda: os.remove(file_path) if os.path.exists(file_path) else None
    }

MEDIA_COMMANDS = {
    "play": play,
    "song": play,
            }
        
