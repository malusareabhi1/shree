import requests
import datetime
import time

from dotenv import load_dotenv
import os



load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_demo")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID_demo")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, data=payload)
    return response

def get_market_data():
    indices = {
        'NIFTY 50': '^NSEI',
        'BANK NIFTY': '^NSEBANK',
        'SENSEX': '^BSESN',
        'RELIANCE': 'RELIANCE.NS',
        'TCS': 'TCS.NS',
        'INFY': 'INFY.NS'
    }

    message = "*📊 Indian Market Snapshot 📈*\n\n"

    for name, symbol in indices.items():
        data = yf.Ticker(symbol)
        price = data.info.get("regularMarketPrice")
        change = data.info.get("regularMarketChange")
        percent = data.info.get("regularMarketChangePercent")

        if price is not None:
            message += f"*{name}*: ₹{price:.2f} ({change:+.2f}, {percent:+.2f}%)\n"
        else:
            message += f"*{name}*: Data not available\n"

    return message

# Fetch data and send
market_message = get_market_data()
send_telegram_message(market_message)
