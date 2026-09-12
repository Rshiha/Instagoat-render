import yt_dlp

def get_audio(song_name):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
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
    file_path = get_audio(song_name)
    
    # আপনার মেইন কোডে যদি ডিকশনারি রিটার্ন করার অপশন থাকে (অডিও পাঠানোর জন্য), 
    # তবে সরাসরি ফাইল পাথ রিটার্ন করতে পারেন:
    return {
        "type": "audio",
        "path": file_path,
        "title": song_name,
        "cleanup": lambda: os.remove(file_path) if os.path.exists(file_path) else None
    }

# Render-এর ImportError এড়ানোর জন্য এই ডিকশনারিটা জরুরি
MEDIA_COMMANDS = {
    "play": play,
    "song": play,
}
