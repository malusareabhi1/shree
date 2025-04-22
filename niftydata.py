from nsepython import *
import pandas as pd
from datetime import datetime

# Get intraday data for NIFTY
df = indices_oi("NIFTY")

# Get historical data (5-minute intervals)
symbol = "NIFTY"
interval = "5minute"
day = "2024-04-18"  # change as needed

data = equity_intraday_data(symbol, interval)

# Convert to DataFrame
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])

# Filter for a specific date and market hours
df = df[df['date'].dt.date == pd.to_datetime(day).date()]
df = df[(df['date'].dt.time >= pd.to_datetime("09:15:00").time()) &
        (df['date'].dt.time <= pd.to_datetime("15:30:00").time())]

# Save to CSV
df.to_csv("nifty_5min_data.csv", index=False)
print("✅ Data saved to nifty_5min_data.csv")
