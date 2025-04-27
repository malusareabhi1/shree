import time
import requests
import yfinance as yf
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get bot details from environment variables
bot_token = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    requests.post(url, data=payload)

def get_nifty_price():
    nifty = yf.Ticker("^NSEI")  # "^NSEI" is the Yahoo Finance code for NIFTY 50
    data = nifty.history(period="1d", interval="5m")
    if not data.empty:
        latest_price = data['Close'].iloc[-1]
        return latest_price
    else:
        return None

def main():
    while True:
        price = get_nifty_price()
        if price:
            message = f"📈 NIFTY 50 Update:\nCurrent Price: {price:.2f} 🏦"
            send_telegram_message(bot_token, chat_id, message)
            print(f"Sent: {message}")
        else:
            print("Could not fetch NIFTY price.")
        
        time.sleep(300)  # Wait for 5 minutes

if __name__ == "__main__":
    main()
