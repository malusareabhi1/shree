import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Define time range (last 30 days)
end_date = datetime.today()
start_date = end_date - timedelta(days=30)

# Download NIFTY 50 data at 5-minute interval
nifty = yf.download("^NSEI", 
                    end=end_date.strftime('%Y-%m-%d'),
                interval='5m',
                    progress=False)
#symbol = "TATAMOTORS.NS"

#nifty = yf.download(tickers=symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'),interval='5m', progress=False)

# Reset index for convenience
nifty.reset_index(inplace=True)

# Show sample
print(nifty.head())

# Save to CSV (optional)
nifty.to_csv("new_Nifty_5min_last_60days.csv", index=False)


##
# 
from pathlib import Path  
filepath = Path('lo_5min_last_60days.csv')  #C:/Users/abhi/Documents/Python_ALGo_BOT/
filepath.parent.mkdir(parents=True, exist_ok=True)  
nifty.to_csv(filepath) 