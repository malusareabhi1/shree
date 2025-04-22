import yfinance as yf
import pandas as pd

# Define the symbol and date range
symbol = "^NSEI"  # NIFTY50 index symbol on Yahoo Finance
start_date = "2024-04-18"
end_date = "2024-04-18"

# Download data
df = yf.download(tickers=symbol, interval="5m", start=start_date, end=end_date)

# Filter only working hours (NSE: 09:15 - 15:30)
df = df.between_time("09:15", "15:30")

# Save to CSV
df.to_csv("nifty_5min_working_hours.csv")

print("✅ Saved to nifty_5min_working_hours.csv")
