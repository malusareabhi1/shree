import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Define symbol and interval
symbol = "^NSEI"  # NIFTY Index symbol in Yahoo Finance
interval = "5m"   # Options: "1m", "5m", "15m"
period = "1d"     # For today’s data

# Fetch data
df = yf.download(tickers=symbol, interval=interval, period=period)

# Convert to IST
df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')

# Filter trading hours (NSE: 9:15 to 15:30 IST)
df = df.between_time("09:15", "15:30")

# Optional: Reset index and save
df = df.reset_index()
df.to_csv("nifty_intraday.csv", index=False)

print("✅ Nifty data saved to 'nifty_intraday.csv'")
