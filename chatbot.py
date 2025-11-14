import os
import time
import socket
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pystyle import Center, Colors, Colorate


# ============================================================
#  1. Fake Web Server for Render (required for free plan)
# ============================================================

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Twitch bot is running on Render!")

def start_web_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"[WEB] Fake web server started on port {port}")
    server.serve_forever()

threading.Thread(target=start_web_server, daemon=True).start()


# ============================================================
#  2. Announcement Printing
# ============================================================

def print_announcement():
    try:
        url = "https://raw.githubusercontent.com/Kichi779/Twitch-Chat-Bot/main/announcement.txt"
        r = requests.get(url, headers={"Cache-Control": "no-cache"})
        return r.content.decode("utf-8").strip()
    except:
        return ""


print(Colorate.Vertical(Colors.red_to_yellow, Center.XCenter("""
Twitch Chat Bot starting on Render...
""")))

announcement = print_announcement()
print("\nANNOUNCEMENT:")
print(announcement)
print("\n")


# ============================================================
#  3. Load settings from Environment Variables
# ============================================================

channel = os.getenv("TWITCH_CHANNEL")
mode = os.getenv("BOT_MODE")             # "1" or "2"
interval = os.getenv("MESSAGE_INTERVAL") # required if mode 1
message_env = os.getenv("MESSAGE_TEXT")  # required if mode 2
bot_choice_env = os.getenv("BOT_CHOICE") # index if mode 2

if not channel:
    raise Exception("Environment variable TWITCH_CHANNEL not set")

if mode not in ["1", "2"]:
    raise Exception("Environment variable BOT_MODE must be '1' or '2'")


server = "irc.chat.twitch.tv"
port = 6667


# ============================================================
#  4. MODE 1 — automatic messages from messages.txt
# ============================================================

if mode == "1":
    with open("messages.txt", "r") as f:
        messages = [m.strip() for m in f.readlines()]

    interval = int(interval) if interval else 20
    index = 0

    print(f"[MODE 1] Sending messages every {interval} seconds")
    print(f"[CHANNEL] {channel}")

    while True:
        message = messages[index % len(messages)]
        index += 1

        with open("oauths.txt", "r") as f:
            oauths = [x.strip() for x in f.readlines()]

        oauth = oauths[index % len(oauths)]

        print(f"[{time.strftime('%X')}] Sending: {message}")

        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        irc.connect((server, port))
        irc.send(f"PASS {oauth}\n".encode())
        irc.send(f"NICK bot\n".encode())
        irc.send(f"JOIN #{channel}\n".encode())
        irc.send(f"PRIVMSG #{channel} :{message}\n".encode())
        irc.close()

        time.sleep(interval)


# ============================================================
#  5. MODE 2 — send a single custom message using selected bot
# ============================================================

elif mode == "2":
    if not message_env:
        raise Exception("MESSAGE_TEXT is required for BOT_MODE = 2")

    if not bot_choice_env:
        raise Exception("BOT_CHOICE is required for BOT_MODE = 2")

    bot_index = int(bot_choice_env) - 1

    with open("oauths.txt", "r") as f:
        oauths = [x.strip() for x in f.readlines()]

    if bot_index >= len(oauths):
        raise Exception("BOT_CHOICE is bigger than number of bots in oauths.txt")

    oauth = oauths[bot_index]
    nickname = f"bot_{bot_index+1}"
    message = message_env

    print(f"[MODE 2] Sending single message")
    print(f"[CHANNEL] {channel}")
    print(f"[BOT] {nickname}")
    print(f"[MESSAGE] {message}")

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    irc.connect((server, port))
    irc.send(f"PASS {oauth}\n".encode())
    irc.send(f"NICK {nickname}\n".encode())
    irc.send(f"JOIN #{channel}\n".encode())
    irc.send(f"PRIVMSG #{channel} :{message}\n".encode())
    irc.close()

    print("[DONE] Message sent. Bot will stay alive to keep Render active.")
    while True:
        time.sleep(999999)
