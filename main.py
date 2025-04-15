

import yfinance as yf
import pandas as pd

# Define stock symbol for Tata Motors (NSE)
symbol = "TATAMOTORS.NS"

# Download last 30 days data at 5-minute interval
df = yf.download(tickers=symbol, period="30d", interval="5m")

# Reset index and save to CSV
df.reset_index(inplace=True)
df.to_csv("tatamotors_5min_last_30days.csv", index=False)

from pathlib import Path  
filepath = Path('C:/Users/abhi/Documents/Python_ALGo_BOT/tatamotors_5min_last_30days.csv')  
filepath.parent.mkdir(parents=True, exist_ok=True)  
df.to_csv(filepath) 


print("✅ Data downloaded and saved as 'tatamotors_5min_last_30days.csv'")
