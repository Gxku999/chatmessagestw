import os
import time
import socket
import requests
from colorama import Fore
from pystyle import Center, Colors, Colorate

# -----------------------------
# Настройки через переменные окружения
# -----------------------------
channel = os.getenv("TWITCH_CHANNEL")
mode = os.getenv("BOT_MODE")               # "1" или "2"
interval = os.getenv("MESSAGE_INTERVAL")   # сек (для режима 1)
message_env = os.getenv("MESSAGE_TEXT")    # для режима 2
bot_choice_env = os.getenv("BOT_CHOICE")   # номер бота (режим 2)

# Проверка
if channel is None:
    raise Exception("TWITCH_CHANNEL is not set in Render Environment Variables")

if mode not in ["1", "2"]:
    raise Exception("BOT_MODE must be 1 or 2")

# Линукс-окружение (Render) — os.system('title ...') не поддерживается
def print_announcement():
    try:
        r = requests.get(
            "https://raw.githubusercontent.com/Kichi779/Twitch-Chat-Bot/main/announcement.txt",
            headers={"Cache-Control": "no-cache"}
        )
        return r.content.decode('utf-8').strip()
    except:
        return ""


print(Colorate.Vertical(Colors.red_to_yellow, Center.XCenter("""
Twitch Chat Bot is starting...
""")))

announcement = print_announcement()
print("")
print("ANNOUNCEMENT:")
print(announcement)
print("")
print("")


# -----------------------------
# Twitch server
# -----------------------------
server = "irc.chat.twitch.tv"
port = 6667

# -----------------------------
# Mode 1 — send messages from messages.txt every N seconds
# -----------------------------
if mode == "1":
    with open("messages.txt", "r") as file:
        messages = [m.strip() for m in file.readlines()]

    interval = int(interval) if interval else 10

    index = 0
    print(f"Bot started in MODE 1 — sending messages every {interval} seconds.")

    while True:
        message = messages[index % len(messages)]
        index += 1

        with open("oauths.txt", "r") as file:
            oauths = file.readlines()

        oauth = oauths[index % len(oauths)].strip()

        print(f"[{time.strftime('%X')}] Sending: {message}")

        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        irc.connect((server, port))
        irc.send(f"PASS {oauth}\n".encode("utf-8"))
        irc.send(f"NICK bot\n".encode("utf-8"))
        irc.send(f"JOIN #{channel}\n".encode("utf-8"))
        irc.send(f"PRIVMSG #{channel} :{message}\n".encode("utf-8"))
        irc.close()

        time.sleep(interval)

# -----------------------------
# Mode 2 — send a custom message with a selected bot
# -----------------------------
elif mode == "2":
    if not message_env:
        raise Exception("MESSAGE_TEXT is required in mode 2")
    if not bot_choice_env:
        raise Exception("BOT_CHOICE is required in mode 2")

    bot_index = int(bot_choice_env) - 1

    with open("oauths.txt", "r") as file:
        oauths = file.readlines()

    if bot_index >= len(oauths):
        raise Exception("BOT_CHOICE is larger than number of bots in oauths.txt")

    oauth = oauths[bot_index].strip()
    nickname = f"bot_{bot_index + 1}"
    message = message_env

    print(f"[{time.strftime('%X')}] Sending message one time: {message}")

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc.connect((server, port))
    irc.send(f"PASS {oauth}\n".encode("utf-8"))
    irc.send(f"NICK {nickname}\n".encode("utf-8"))
    irc.send(f"JOIN #{channel}\n".encode("utf-8"))
    irc.send(f"PRIVMSG #{channel} :{message}\n".encode("utf-8"))
    irc.close()

    print("Message sent. Bot will now sleep forever (Render keeps process alive).")
    while True:
        time.sleep(999999)
