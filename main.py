import os
import time
import json
import threading
import websocket
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Discord 24/7 Status Bot is running cleanly!", 200

# Fetch secure environment variables
TOKEN = os.getenv("TOKEN")
STATUS = os.getenv("STATUS", "online")
CUSTOM_STATUS = os.getenv("CUSTOM_STATUS", "Hey!")

def send_heartbeat(ws, interval):
    print(f"[Discord] Heartbeat thread started. Interval: {interval}s")
    while True:
        time.sleep(interval)
        try:
            ws.send(json.dumps({"op": 1, "d": None}))
            print("[Discord] Heartbeat sent successfully.")
        except Exception as e:
            print(f"[Discord] Heartbeat failed: {e}")
            break

def on_open(ws):
    print("[Discord] Web socket opened. Sending authentication...")
    auth_payload = {
        "op": 2,
        "d": {
            "token": TOKEN,
            "properties": {
                "$os": "linux",
                "$browser": "Chrome",
                "$device": "desktop"
            },
            "presence": {
                "status": STATUS,
                "since": 0,
                "activities": [{
                    "name": "Custom Status",
                    "type": 4,
                    "state": CUSTOM_STATUS
                }],
                "afk": False
            }
        }
    }
    ws.send(json.dumps(auth_payload))
    print(f"[Discord] Auth payload pushed. Setting status to '{STATUS}'.")

def on_message(ws, message):
    data = json.loads(message)
    # Opcode 10 is the Hello event containing the heartbeat requirement
    if data.get("op") == 10:
        heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
        # Start heartbeat in a dedicated sub-thread to avoid blocking messages
        t = threading.Thread(target=send_heartbeat, args=(ws, heartbeat_interval), daemon=True)
        t.start()
    elif data.get("t") == "READY":
        print(f"[Discord] Successfully authenticated! Account is now ONLINE.")

def on_error(ws, error):
    print(f"[Discord] Socket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"[Discord] Connection lost ({close_status_code}: {close_msg}). Reconnecting in 5s...")
    time.sleep(5)
    start_discord_connection()

def run_gateway():
    ws = websocket.WebSocketApp(
        "wss://gateway.discord.gg/?v=9&encoding=json",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

def start_discord_connection():
    if not TOKEN:
        print("[Discord] ERROR: The 'TOKEN' environment variable is missing on Render!")
        return
    discord_thread = threading.Thread(target=run_gateway, daemon=True)
    discord_thread.start()

if __name__ == "__main__":
    start_discord_connection()
    # Bind to port provided by Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
