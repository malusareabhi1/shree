import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
# List of NIFTY 50 stocks (you can expand this as needed)
nifty_50 = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
    'KOTAKBANK.NS', 'LT.NS', 'AXISBANK.NS', 'SBIN.NS', 'ITC.NS',
    'HINDUNILVR.NS', 'HCLTECH.NS', 'WIPRO.NS', 'SUNPHARMA.NS', 'TECHM.NS',
    'BAJFINANCE.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS'
]
from io import StringIO

url = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"

# Add browser-like headers
headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
data = response.text

# Load CSV into DataFrame
df = pd.read_csv(StringIO(data))

# Create array with '.NS' suffix
nifty_200 = [symbol + ".NS" for symbol in df['Symbol'].tolist()]



# Example output
st.write("nifty_200 =", nifty_200)
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

st.write("📈 Most Volatile NIFTY 50 Stocks (Last 1 Month):")
st.write(vol_df.head(5))
