import streamlit as st
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime, timedelta

st.set_page_config(page_title="Nifty/BankNifty Trend Checker", layout="centered")

st.title("📊 Nifty / Bank Nifty Trend Checker")

# --- Sidebar ---
index_choice = st.sidebar.selectbox("Select Index", ("NIFTY 50", "BANK NIFTY"))

symbol_map = {
    "NIFTY 50": "^NSEI",         # Yahoo Finance symbol for Nifty 50
    "BANK NIFTY": "^NSEBANK"     # Yahoo Finance symbol for Bank Nifty
}

symbol = symbol_map[index_choice]

# --- Fetch Data ---
@st.cache_data(ttl=300)
def get_data(symbol):
    df = yf.download(symbol, period="5d", interval="5m")
    df.dropna(inplace=True)
    return df

df = get_data(symbol)

if df.empty:
    st.error("Failed to fetch data.")
else:
    # --- Calculate Trend ---
    df["EMA20"] = ta.trend.ema_indicator(df["Close"], window=20)
    df["EMA50"] = ta.trend.ema_indicator(df["Close"], window=50)

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # --- Determine Trend ---
    if latest["EMA20"] > latest["EMA50"]:
        trend = "📈 Uptrend"
        trend_color = "green"
    elif latest["EMA20"] < latest["EMA50"]:
        trend = "📉 Downtrend"
        trend_color = "red"
    else:
        trend = "➖ Sideways"
        trend_color = "gray"

    # --- Display ---
    st.markdown(f"### 🔍 Current Trend: <span style='color:{trend_color}'>{trend}</span>", unsafe_allow_html=True)
    st.write(f"**Last Close:** ₹{latest['Close']:.2f}")
    st.write(f"**Time:** {latest.name}")
    st.write(f"**20 EMA:** {latest['EMA20']:.2f}")
    st.write(f"**50 EMA:** {latest['EMA50']:.2f}")

    st.line_chart(df[["Close", "EMA20", "EMA50"]])
