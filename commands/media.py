import os
import requests

def get_saavn_audio(song_name):
    # JioSaavn API ব্যবহার করে গান সার্চ করা (কোনো কুকিজ বা ইউটিউব প্রটেকশন নেই)
    search_url = f"https://jiosaavn-api-private-zeta.vercel.app/search/songs?query={song_name}"
    response = requests.get(search_url).json()
    
    if response.get("success") and response.get("data", {}).get("results"):
        song_data = response["data"]["results"][0]
        title = song_data.get("name", song_name)
        
        # সবথেকে ভালো কোয়ালিটির অডিও লিংক বের করা
        download_url = None
        for quality in song_data.get("downloadUrl", []):
            if quality.get("quality") == "320kbps" or quality.get("quality") == "160kbps":
                download_url = quality.get("link")
                break
        
        if not download_url and song_data.get("downloadUrl"):
            download_url = song_data["downloadUrl"][-1].get("link")
            
        if download_url:
            # অডিও ফাইলটি সাময়িকভাবে ডাউনলোড করে নেওয়া
            audio_response = requests.get(download_url)
            file_path = f"downloads/{title}.mp3"
            os.makedirs("downloads", exist_ok=True)
            
            with open(file_path, "wb") as f:
                f.write(audio_response.content)
            return file_path, title
            
    return None, None

def play(a, c):
    if not a:
        return "🎵 Usage: .play song name"
    
    song_name = " ".join(a)
    
    try:
        file_path, title = get_saavn_audio(song_name)
        if not file_path:
            return "❌ গানটি খুঁজে পাওয়া যায়নি। অন্য নাম দিয়ে চেষ্টা করুন।"
    except Exception as e:
        print(f"AUDIO DOWNLOAD ERROR: {e}", flush=True)
        return "❌ গান ডাউনলোড করতে সমস্যা হয়েছে।"
    
    return {
        "type": "audio",
        "path": file_path,
        "title": title,
        "cleanup": lambda: os.remove(file_path) if os.path.exists(file_path) else None
    }

MEDIA_COMMANDS = {
    "play": play,
    "song": play,
    "music": play,
}
