import requests
import datetime
import time
import streamlit as st
import yfinance as yf
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_demo")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID_demo")

st.write(BOT_TOKEN)
st.write(CHAT_ID)

# Function to send a Telegram message
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    r = requests.post(url, data=payload)
    return r.ok

# Get stock/index data using yfinance
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
    market_list = []

    for name, symbol in indices.items():
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("regularMarketPrice")
        change = info.get("regularMarketChange")
        percent = info.get("regularMarketChangePercent")

        if price is not None:
            row = {
                "Name": name,
                "Price (₹)": round(price, 2),
                "Change": f"{change:+.2f}",
                "Change %": f"{percent:+.2f}%"
            }
            market_list.append(row)
            message += f"*{name}*: ₹{price:.2f} ({change:+.2f}, {percent:+.2f}%)\n"
        else:
            message += f"*{name}*: Data not available\n"

    return market_list, message

# --- Streamlit App ---
st.set_page_config(page_title="Indian Market Dashboard", layout="centered")
st.title("📈 Indian Market Dashboard")
st.caption("Live stock/index prices + Telegram update")

market_data, message = get_market_data()

# Display table
st.table(market_data)

# Button to send message to Telegram
if st.button("📤 Send Market Data to Telegram"):
    success = send_telegram_message(message)
    if success:
        st.success("Message sent to Telegram successfully!")
    else:
        st.error("Failed to send message. Check bot token and chat ID.")
