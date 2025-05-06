import yfinance as yf
import pandas as pd
import numpy as np

# List of NIFTY 50 stocks (you can expand this as needed)
nifty_50 = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
    'KOTAKBANK.NS', 'LT.NS', 'AXISBANK.NS', 'SBIN.NS', 'ITC.NS',
    'HINDUNILVR.NS', 'HCLTECH.NS', 'WIPRO.NS', 'SUNPHARMA.NS', 'TECHM.NS',
    'BAJFINANCE.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS'
]

def get_volatility(symbol):
    try:
        df = yf.download(symbol, period="1mo", interval="1d", progress=False)
        df['Return'] = df['Adj Close'].pct_change()
        volatility = df['Return'].std()  # Standard deviation of returns
        return volatility
    except:
        return None

volatility_data = []

for stock in nifty_50:
    vol = get_volatility(stock)
    if vol is not None:
        volatility_data.append((stock, vol))

# Sort by highest volatility
vol_df = pd.DataFrame(volatility_data, columns=['Stock', 'Volatility'])
vol_df.sort_values(by='Volatility', ascending=False, inplace=True)

print("📈 Most Volatile NIFTY 50 Stocks (Last 1 Month):")
print(vol_df.head(5))
