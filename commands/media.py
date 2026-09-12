def play(a,c): return "🎵 Usage: .play song name" if not a else "🎵 Requested: "+" ".join(a)+"\n⚠️ Audio attachment depends on Instagram client support."
def song(a,c): return play(a,c)
def music(a,c): return play(a,c)
MEDIA_COMMANDS={"play":play,"song":song,"music":music}
