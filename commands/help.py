COMMAND_HELP = {
    "pin": {"usage": ".pin <keyword>", "example": ".pin cat", "desc": "Pinterest theke 10 ta pic dibe."},
    "tik": {"usage": ".tik <keyword>", "example": ".tik funny", "desc": "TikTok theke video dibe."},
    "dl": {"usage": ".dl <link>", "example": ".dl https://youtu.be/...", "desc": "Video download korbe."},
}
def help_command(args, ctx):
    if args and args[0].lower() in COMMAND_HELP:
        i = COMMAND_HELP[args[0].lower()]
        return f"📖 {args[0].upper()} HELP\n\nKaj: {i['desc']}\nUse: {i['usage']}\nEx: {i['example']}"
    return "🤖 COMMAND LIST\n\n•.pin cat - Pinterest pic\n•.tik funny - TikTok video\n•.dl <link> - Download\n•.help pin - details"

HELP_COMMANDS = {"help": help_command, "menu": help_command}