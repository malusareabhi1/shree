import streamlit as st
import yfinance as yf
import pandas as pd

# Set Streamlit page config first!
st.set_page_config(page_title="📈 NIFTY 100 Stocks", layout="wide")

# Title
st.title("📊 NIFTY 100 Stock Overview")
st.caption("Live Close, % Change, and Volume")

# NIFTY 100 stock symbols (partial for example, full list recommended)
nifty100_symbols = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "LT.NS",
    "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
    "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS", "ULTRACEMCO.NS", "NESTLEIND.NS"
    # Add remaining NIFTY 100 tickers here...
]

# Progress bar
progress = st.progress(0)

# Empty list for storing data
stock_data = []

for i, symbol in enumerate(nifty100_symbols):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='1d', interval='1m')
        if not df.empty:
            last = df.iloc[-1]
            first = df.iloc[0]
            close = round(last['Close'], 2)
            change_pct = round(((last['Close'] - first['Close']) / first['Close']) * 100, 2)
            volume = int(last['Volume'])
            stock_data.append({
                "Symbol": symbol.replace(".NS", ""),
                "Close": close,
                "Change %": change_pct,
                "Volume": volume
            })
    except Exception as e:
        st.warning(f"Failed to fetch {symbol}: {e}")

    progress.progress((i + 1) / len(nifty100_symbols))

# Create DataFrame
df_final = pd.DataFrame(stock_data)
df_final = df_final.sort_values(by="Change %", ascending=False)

# Show data table
st.dataframe(df_final, use_container_width=True)
