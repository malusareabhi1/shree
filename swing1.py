import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📈 NIFTY 50 Swing Trade Signal Finder")

# NIFTY 50 symbols
nifty_50_symbols = [
    "ADANIENT.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS",
    "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS",
    "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS", "INDUSINDBK.NS",
    "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "M&M.NS", "MARUTI.NS",
    "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBIN.NS",
    "SHREECEM.NS", "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TCS.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "WIPRO.NS"
]

# Fetch data function
def fetch_stock_data(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        df.dropna(inplace=True)
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        df['RSI'] = df['Close'].rolling(14).apply(lambda x: 100 - 100/(1 + (x.diff().clip(lower=0).mean() / abs(x.diff().clip(upper=0)).mean())) if abs(x.diff().clip(upper=0)).mean() != 0 else 0, raw=False)
        df['Volume_SMA'] = df['Volume'].rolling(20).mean()
        df['ATR'] = df['High'] - df['Low']
        return df
    except:
        return None

# Strategy logic
def check_trade_signal(df):
    if df is None or len(df) < 60:
        return False, None

    row = df.iloc[-1]
    prev = df.iloc[-2]

    try:
        if (
            float(row['Close']) > float(row['SMA20']) > float(row['SMA50']) and
            50 <= float(row['RSI']) <= 65 and
            float(row['Volume']) > float(row['Volume_SMA']) and
            float(row['Close']) > float(prev['Close'])
        ):
            return True, row['Close']
    except:
        return False, None

    return False, None

# Scan NIFTY 50 stocks
st.info("🔍 Scanning NIFTY 50 stocks for swing trade signals...")
results = []

for symbol in nifty_50_symbols:
    data = fetch_stock_data(symbol)
    found, entry = check_trade_signal(data)
    if found:
        results.append({"Symbol": symbol, "Entry Price": round(entry, 2), "Date": datetime.today().strftime("%Y-%m-%d")})

# Show results
if results:
    df_result = pd.DataFrame(results)
    st.success(f"✅ {len(df_result)} trade signals found!")
    st.dataframe(df_result, use_container_width=True)

    # Show list of stock names
    stock_list = df_result['Symbol'].str.replace('.NS', '', regex=False).tolist()
    st.markdown("### 📌 Stocks with Valid Signals:")
    st.write(", ".join(stock_list))
else:
    st.warning("❌ No valid trade signals found today.")
