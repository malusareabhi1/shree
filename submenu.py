import streamlit as st

# Main menu
main_menu = st.sidebar.selectbox("Main Menu", ["Dashboard", "Trading", "Settings"])

# Submenu based on main menu
if main_menu == "Dashboard":
    submenu = st.sidebar.radio("Dashboard Options", ["Overview", "Performance"])
    if submenu == "Overview":
        st.title("📈 Overview")
    elif submenu == "Performance":
        st.title("📉 Performance")

elif main_menu == "Trading":
    submenu = st.sidebar.radio("Trading Options", ["Backtest", "Live"])
    if submenu == "Backtest":
        st.title("🔁 Backtest")
    elif submenu == "Live":
        st.title("📡 Live Trading")

elif main_menu == "Settings":
    st.title("⚙️ Settings")
    st.write("Update config, alerts, and preferences.")

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def check_swing_trade(stock_symbol='RELIANCE.NS', days=90):
    df = yf.download(stock_symbol, period=f"{days}d", interval='1d')
    df['EMA44'] = df['Close'].ewm(span=44).mean()
    df['Signal'] = df['Close'] > df['EMA44']

    # Detect crossover
    df['Crossover'] = df['Signal'] & (~df['Signal'].shift(1).fillna(False))

    # Filter last 10 days for potential swing entry
    recent = df.tail(10)
    signals = recent[recent['Crossover']]

    if not signals.empty:
        print(f"\n📈 Swing Buy Setup Detected in {stock_symbol} on:")
        print(signals[['Close', 'EMA44']])
    else:
        print(f"\n❌ No Swing Trade Signal Found in {stock_symbol} (last 10 days).")

    # Optional plot
    recent[['Close', 'EMA44']].plot(title=f"{stock_symbol} Price & EMA44")
    plt.show()

# Example usage
check_swing_trade('TCS.NS')

