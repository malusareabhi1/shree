import yfinance as yf
import pandas as pd
import streamlit as st

# Nifty 50 stock symbols (add ".NS" for NSE)
nifty_50 = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'LT.NS',
    'SBIN.NS', 'HINDUNILVR.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'BAJFINANCE.NS', 'BHARTIARTL.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
    'NESTLEIND.NS', 'ULTRACEMCO.NS', 'TITAN.NS', 'ASIANPAINT.NS', 'WIPRO.NS',
    'HCLTECH.NS', 'NTPC.NS', 'POWERGRID.NS', 'ADANIENT.NS', 'TATASTEEL.NS',
    'TECHM.NS', 'COALINDIA.NS', 'ONGC.NS', 'UPL.NS', 'JSWSTEEL.NS',
    'BPCL.NS', 'GRASIM.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'BAJAJFINSV.NS',
    'HDFCLIFE.NS', 'SBILIFE.NS', 'EICHERMOT.NS', 'INDUSINDBK.NS', 'HEROMOTOCO.NS',
    'BAJAJ-AUTO.NS', 'CIPLA.NS', 'BRITANNIA.NS', 'APOLLOHOSP.NS', 'HINDALCO.NS',
    'ADANIPORTS.NS', 'SHREECEM.NS', 'M&M.NS'
]

volatilities = []

# Check volatility for each stock
for symbol in nifty_50:
    try:
        df = yf.download(symbol, period='15d', interval='1d')
        df['returns'] = df['Close'].pct_change()
        volatility = df['returns'].std()
        volatilities.append((symbol, volatility))
    except Exception as e:
        print(f"Error for {symbol}: {e}")

# Sort by highest volatility
vol_df = pd.DataFrame(volatilities, columns=['Symbol', 'Volatility'])
vol_df = vol_df.sort_values(by='Volatility', ascending=False)

st.write("🔍 Most Volatile NIFTY 50 Stocks (Last 14 Days):")
st.write(vol_df.head(5))
