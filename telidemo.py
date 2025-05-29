import requests
import datetime
import time

from dotenv import load_dotenv
import os

load_dotenv()


# Replace with your Telegram bot token and chat ID
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # optionally, use .env for chat_id too

# Function to send message to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    r = requests.post(url, data=payload)
    return r.status_code

# Example signal generator (replace with real logic)
def simple_algo_strategy():
    # Example: Call every 30 seconds as mock trade signal
    while True:
        now = datetime.datetime.now().strftime('%H:%M:%S')
        signal = f"🟢 *BUY SIGNAL*\nStock: RELIANCE\nPrice: 2750\nTime: {now}"
        send_telegram_message(signal)
        time.sleep(30)  # Wait before next signal

# Run the strategy
simple_algo_strategy()
