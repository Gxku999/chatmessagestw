import os
import time
import socket
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# ------------------------------
# 1. Fake Web Server for Render
# ------------------------------
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

# Запускаем веб-сервер в отдельном потоке
threading.Thread(target=start_web_server, daemon=True).start()


# ------------------------------
# 2. Announcement (опционально)
# ------------------------------
def print_announcement():
    try:
        url = "https://raw.githubusercontent.com/Kichi779/Twitch-Chat-Bot/main/announcement.txt"
        r = requests.get(url, headers={"Cache-Control": "no-cache"})
        return r.content.decode("utf-8").strip()
    except:
        return ""

announcement = print_announcement()
if announcement:
    print("[ANNOUNCEMENT]")
    print(announcement)
    print()


# ------------------------------
# 3. Settings from Environment Variables
# ------------------------------
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")
BOT_MODE = os.getenv("BOT_MODE")         # "1" или "2"
MESSAGE_INTERVAL = os.getenv("MESSAGE_INTERVAL") # сек, для режима 1
MESSAGE_TEXT = os.getenv("MESSAGE_TEXT")         # для режима 2
BOT_CHOICE = os.getenv("BOT_CHOICE")             # для режима 2

if not TWITCH_CHANNEL:
    raise Exception("TWITCH_CHANNEL not set")
if BOT_MODE not in ["1", "2"]:
    raise Exception("BOT_MODE must be '1' or '2'")


# ------------------------------
# 4. IRC Settings
# ------------------------------
IRC_SERVER = "irc.chat.twitch.tv"
IRC_PORT = 6667


# ------------------------------
# 5. Bot loop function
# ------------------------------
def bot_loop():
    if BOT_MODE == "1":
        # ----------------- Mode 1 -----------------
        if not MESSAGE_INTERVAL:
            MESSAGE_INTERVAL = 20
        else:
            MESSAGE_INTERVAL = int(MESSAGE_INTERVAL)

        # Load messages
        with open("messages.txt", "r") as f:
            messages = [m.strip() for m in f.readlines()]

        # Load oauths
        with open("oauths.txt", "r") as f:
            oauths = [x.strip() for x in f.readlines()]

        index = 0
        print(f"[BOT] Mode 1 started. Sending messages every {MESSAGE_INTERVAL}s to channel {TWITCH_CHANNEL}")

        while True:
            message = messages[index % len(messages)]
            oauth = oauths[index % len(oauths)]
            nickname = f"bot_{index % len(oauths) + 1}"

            print(f"[{time.strftime('%X')}] Sending message: '{message}' using {nickname}")

            try:
                irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                irc.connect((IRC_SERVER, IRC_PORT))
                irc.send(f"PASS {oauth}\n".encode())
                irc.send(f"NICK {nickname}\n".encode())
                irc.send(f"JOIN #{TWITCH_CHANNEL}\n".encode())
                irc.send(f"PRIVMSG #{TWITCH_CHANNEL} :{message}\n".encode())
                irc.close()
            except Exception as e:
                print(f"[ERROR] Failed to send message: {e}")

            index += 1
            time.sleep(MESSAGE_INTERVAL)

    else:
        # ----------------- Mode 2 -----------------
        if not MESSAGE_TEXT or not BOT_CHOICE:
            raise Exception("MESSAGE_TEXT and BOT_CHOICE are required for BOT_MODE=2")

        bot_index = int(BOT_CHOICE) - 1

        # Load oauths
        with open("oauths.txt", "r") as f:
            oauths = [x.strip() for x in f.readlines()]

        if bot_index >= len(oauths):
            raise Exception("BOT_CHOICE larger than number of oauths available")

        oauth = oauths[bot_index]
        nickname = f"bot_{bot_index+1}"
        message = MESSAGE_TEXT

        print(f"[BOT] Mode 2 started. Sending message once to channel {TWITCH_CHANNEL} using {nickname}")
        print(f"[{time.strftime('%X')}] Message: '{message}'")

        try:
            irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            irc.connect((IRC_SERVER, IRC_PORT))
            irc.send(f"PASS {oauth}\n".encode())
            irc.send(f"NICK {nickname}\n".encode())
            irc.send(f"JOIN #{TWITCH_CHANNEL}\n".encode())
            irc.send(f"PRIVMSG #{TWITCH_CHANNEL} :{message}\n".encode())
            irc.close()
            print("[BOT] Message sent successfully")
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")

        # Держим бот живым
        while True:
            time.sleep(999999)


# ------------------------------
# 6. Start bot loop in separate thread
# ------------------------------
threading.Thread(target=bot_loop, daemon=True).start()

# ------------------------------
# 7. Keep main thread alive for Render
# ------------------------------
while True:
    time.sleep(9999)
