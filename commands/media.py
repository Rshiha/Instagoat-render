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
    # Ekhane gaan download ba search korar function call korte hobe
    file_path = get_audio(song_name)
    
    # Tarpor bot diye file path-ti send korte hobe
    return f"🎵 Requested: {song_name}\n📂 File ready: {file_path}"
  
