import time
import requests
import yfinance as yf
from dotenv import load_dotenv
import os
import pytz
import datetime

# Load environment variables from .env file
load_dotenv()

# Get bot details from environment variables
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

# Set timezone
india_tz = pytz.timezone('Asia/Kolkata')

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    requests.post(url, data=payload)

def get_index_data(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d", interval="5m")
    if not data.empty:
        current_price = data['Close'].iloc[-1]
        previous_close = ticker.info['previousClose']
        percent_change = ((current_price - previous_close) / previous_close) * 100
        return current_price, percent_change
    else:
        return None, None

def is_market_open():
    now = datetime.now(india_tz)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close

def main():
    market_closed_message_sent = False  # Control flag

    while True:
        #now = datetime.now(india_tz)
        now = datetime.datetime.now(india_tz)
        
        if is_market_open():
            try:
                nifty_price, nifty_change = get_index_data("^NSEI")
                banknifty_price, banknifty_change = get_index_data("^NSEBANK")
                bse_price, bse_change = get_index_data("^BSESN")

                if None not in (nifty_price, banknifty_price, bse_price):
                    message = f"""
📊 *Market Update* 📊

🔵 NIFTY 50: {nifty_price:.2f} ({nifty_change:+.2f}%)
🟢 BANKNIFTY: {banknifty_price:.2f} ({banknifty_change:+.2f}%)
🔴 BSE Sensex: {bse_price:.2f} ({bse_change:+.2f}%)

⏰ Update Time: {now.strftime('%H:%M:%S')}
"""
                    send_telegram_message(bot_token, chat_id, message)
                    print("Sent Market Update!")
                    market_closed_message_sent = False  # Reset if reopened
                else:
                    print("Could not fetch data properly.")

            except Exception as e:
                print(f"Error: {e}")

        else:
            if not market_closed_message_sent:
                closed_message = f"""
📴 *Market Closed* 📴

Trading hours are over.
Will resume updates tomorrow at 9:15 AM.
"""
                send_telegram_message(bot_token, chat_id, closed_message)
                print("Sent Market Closed Message.")
                market_closed_message_sent = True
        
        time.sleep(300)  # Sleep for 5 minutes

if __name__ == "__main__":
    main()
