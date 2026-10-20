import os
import time
import json
import threading
import websocket
from flask import Flask

# Initialize a tiny web server to satisfy Render's Web Service requirements
app = Flask(__name__)

@app.route('/')
def home():
    return "Discord 24/7 Status Bot is running cleanly!", 200

# Read secure settings directly from Render Environment Variables
TOKEN = os.getenv("TOKEN")
STATUS = os.getenv("STATUS", "online")
CUSTOM_STATUS = os.getenv("CUSTOM_STATUS", "Hey!")

def on_open(ws):
    print("Connecting to Discord Gateway...")
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
    print("Authentication payload sent to Discord Gateway.")

def on_message(ws, message):
    data = json.loads(message)
    if data.get("op") == 10:
        heartbeat_interval = data["d"]["heartbeat_interval"] / 1000
        print(f"Heartbeat established at {heartbeat_interval}s.")
        while True:
            time.sleep(heartbeat_interval)
            try:
                ws.send(json.dumps({"op": 1, "d": None}))
            except Exception as e:
                print(f"Failed to send heartbeat: {e}")
                break

def on_error(ws, error):
    print(f"Connection issue: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Session disconnected. Reconnecting in 5 seconds...")
    time.sleep(5)
    run_gateway()

def run_gateway():
    ws = websocket.WebSocketApp(
        "wss://gateway.discord.gg/?v=9&encoding=json",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

def start_discord_thread():
    if not TOKEN:
        print("Error: TOKEN environment variable is missing on Render!")
        return
    # Run the Discord websocket in a separate thread so it doesn't block Flask
    discord_thread = threading.Thread(target=run_gateway, daemon=True)
    discord_thread.start()

if __name__ == "__main__":
    start_discord_thread()
    # Web services on Render bind to port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
