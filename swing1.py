import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
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
        return False, None, None

    row = df.iloc[-1]
    prev = df.iloc[-2]

    try:
        if (
            float(row['Close']) > float(row['SMA20']) > float(row['SMA50']) and
            50 <= float(row['RSI']) <= 65 and
            float(row['Volume']) > float(row['Volume_SMA']) and
            float(row['Close']) > float(prev['Close'])
        ):
            return True, row['Close'], df[-30:]  # return recent data for chart
    except:
        return False, None, None

    return False, None, None

# Scan NIFTY 50 stocks
st.info("🔍 Scanning NIFTY 50 stocks for swing trade signals...")
results = []

for symbol in nifty_50_symbols:
    data = fetch_stock_data(symbol)
    found, entry, chart_data = check_trade_signal(data)
    if found:
        results.append({"Symbol": symbol, "Entry Price": round(entry, 2), "Date": datetime.today().strftime("%Y-%m-%d"), "Chart": chart_data})

# Show results
if results:
    df_result = pd.DataFrame([ {k: v for k, v in row.items() if k != 'Chart'} for row in results ])
    st.success(f"✅ {len(df_result)} trade signals found!")
    st.dataframe(df_result, use_container_width=True)

    # Show list of stock names
    stock_list = df_result['Symbol'].str.replace('.NS', '', regex=False).tolist()
    st.markdown("### 📌 Stocks with Valid Signals:")
    st.write(", ".join(stock_list))

    # 📈 Show mini charts
    st.markdown("### 📉 Mini Charts")
    for result in results:
        symbol = result['Symbol']
        chart_df = result['Chart'].copy()
        st.subheader(f"{symbol.replace('.NS', '')}")
        fig = go.Figure(data=[go.Candlestick(
            x=chart_df.index,
            open=chart_df['Open'], high=chart_df['High'],
            low=chart_df['Low'], close=chart_df['Close'],
            increasing_line_color='green', decreasing_line_color='red'
        )])
        fig.update_layout(xaxis_rangeslider_visible=False, height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # 📤 Optional: Telegram or Email Alert
    # NOTE: This is a placeholder. Replace with your bot/email logic.
    st.info("📤 Alerts would be sent via Telegram/Email for above stocks (feature placeholder)")

    # 🧪 Summary of Strategy
    total_trades = len(df_result)
    avg_entry = pd.to_numeric(df_result['Entry Price'], errors='coerce').mean()
    st.markdown("### 📊 Backtest Summary")
    st.write(f"Total Signals: {total_trades}")
    st.write(f"Average Entry Price: ₹{avg_entry:.2f}")
else:
    st.warning("❌ No valid trade signals found today.")
