import requests
import datetime
import time
import streamlit as st
import yfinance as yf
import os
from dotenv import load_dotenv

# --- Streamlit App ---
st.set_page_config(page_title="Indian Market Dashboard", layout="centered")
st.title("📈 Indian Market Dashboard")
st.caption("Live stock/index prices + Telegram update")
# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN_demo")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID_demo")

#st.write(BOT_TOKEN)
#st.write(CHAT_ID)

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
    'ADANIENT': 'ADANIENT.NS',
    'ADANIPORTS': 'ADANIPORTS.NS',
    'ASIANPAINT': 'ASIANPAINT.NS',
    'AXISBANK': 'AXISBANK.NS',
    'BAJAJ-AUTO': 'BAJAJ-AUTO.NS',
    'BAJFINANCE': 'BAJFINANCE.NS',
    'BAJAJFINSV': 'BAJAJFINSV.NS',
    'BPCL': 'BPCL.NS',
    'BHARTIARTL': 'BHARTIARTL.NS',
    'BRITANNIA': 'BRITANNIA.NS',
    'CIPLA': 'CIPLA.NS',
    'COALINDIA': 'COALINDIA.NS',
    'DIVISLAB': 'DIVISLAB.NS',
    'DRREDDY': 'DRREDDY.NS',
    'EICHERMOT': 'EICHERMOT.NS',
    'GRASIM': 'GRASIM.NS',
    'HCLTECH': 'HCLTECH.NS',
    'HDFCBANK': 'HDFCBANK.NS',
    'HDFCLIFE': 'HDFCLIFE.NS',
    'HEROMOTOCO': 'HEROMOTOCO.NS',
    'HINDALCO': 'HINDALCO.NS',
    'HINDUNILVR': 'HINDUNILVR.NS',
    'ICICIBANK': 'ICICIBANK.NS',
    'ITC': 'ITC.NS',
    'INDUSINDBK': 'INDUSINDBK.NS',
    'INFY': 'INFY.NS',
    'JSWSTEEL': 'JSWSTEEL.NS',
    'KOTAKBANK': 'KOTAKBANK.NS',
    'LT': 'LT.NS',
    'M&M': 'M&M.NS',
    'MARUTI': 'MARUTI.NS',
    'NTPC': 'NTPC.NS',
    'NESTLEIND': 'NESTLEIND.NS',
    'ONGC': 'ONGC.NS',
    'POWERGRID': 'POWERGRID.NS',
    'RELIANCE': 'RELIANCE.NS',
    'SBILIFE': 'SBILIFE.NS',
    'SBIN': 'SBIN.NS',
    'SUNPHARMA': 'SUNPHARMA.NS',
    'TCS': 'TCS.NS',
    'TATACONSUM': 'TATACONSUM.NS',
    'TATAMOTORS': 'TATAMOTORS.NS',
    'TATASTEEL': 'TATASTEEL.NS',
    'TECHM': 'TECHM.NS',
    'TITAN': 'TITAN.NS',
    'UPL': 'UPL.NS',
    'ULTRACEMCO': 'ULTRACEMCO.NS',
    'WIPRO': 'WIPRO.NS'
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



market_data, message = get_market_data()
send_telegram_message(message)
# Display table
st.table(market_data)

# Button to send message to Telegram
if st.button("📤 Send Market Data to Telegram"):
    success = send_telegram_message(message)
    if success:
        st.success("Message sent to Telegram successfully!")
    else:
        st.error("Failed to send message. Check bot token and chat ID.")
