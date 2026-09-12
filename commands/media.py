import os
import yt_dlp

def get_audio(song_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt',  # কুকিজ ফাইল যুক্ত করা হলো
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{song_name}", download=True)
        filename = ydl.prepare_filename(info)
        return filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')

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
