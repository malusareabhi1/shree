import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import time as dtime

# --- Define stocks ---
nifty_stocks = ["RELIANCE", "TCS", "INFY", "ICICIBANK", "HDFCBANK", "SBIN", "ITC", "AXISBANK", "WIPRO", "LT"]
symbol_list = st.sidebar.multiselect("Select Stocks", nifty_stocks, default=nifty_stocks)

# --- Time window ---
st.sidebar.subheader("Time Settings")
or_start = st.sidebar.time_input("Opening Range Start", value=dtime(9, 15))
or_end = st.sidebar.time_input("Opening Range End", value=dtime(9, 30))
exit_time = st.sidebar.time_input("Exit Time", value=dtime(14, 30))

# --- Volume filter ---
st.sidebar.subheader("Volume Filter")
vol_thresh = st.sidebar.slider("Min Volume × Avg", 0.5, 5.0, 1.0, step=0.1)

# --- Indicator logic ---
st.sidebar.subheader("Indicators")
use_sma = st.sidebar.checkbox("Use SMA", value=True)
sma_period = st.sidebar.number_input("SMA Period", 5, 50, 20)

# --- Risk management ---
st.sidebar.subheader("Risk Management")
use_sl = st.sidebar.checkbox("Enable Stop Loss", True)
sl_pct = st.sidebar.slider("Stop Loss %", 0.5, 10.0, 1.0)
target_pct = st.sidebar.slider("Target %", 0.5, 20.0, 2.0)

# --- Signal logic ---
st.sidebar.subheader("Signal Logic")
signal_type = st.sidebar.selectbox("Signal Type", ["Long Only", "Short Only", "Both"])

# --- Strategy execution ---
st.title("🧠 Customizable Intraday Strategy Scanner")

results = []
for stock in symbol_list:
    df = yf.download(stock + ".NS", interval="5m", period="1d", progress=False)
    if df.empty:
        continue
    df.index = df.index.tz_convert("Asia/Kolkata")
    df.dropna(inplace=True)

    or_df = df.between_time(str(or_start), str(or_end))
    if len(or_df) < 2:
        continue

    or_high, or_low = or_df["High"].max(), or_df["Low"].min()
    avg_vol = or_df["Volume"].mean()
    or_close_time = or_df.index[-1]

    post_or = df[df.index > or_close_time]
    sl_triggered = False

    for idx, row in post_or.iterrows():
        if idx.time() > exit_time:
            break
        # Example LONG condition
        if signal_type in ["Long Only", "Both"]:
            if row["Close"] > or_high and row["Volume"] > avg_vol * vol_thresh:
                entry = row["Close"]
                sl = entry * (1 - sl_pct / 100) if use_sl else None
                target = entry * (1 + target_pct / 100)
                results.append({
                    "Stock": stock, "Signal": "Long", "Time": idx.strftime("%H:%M"),
                    "Entry": round(entry, 2), "SL": round(sl, 2) if sl else "-", "Target": round(target, 2)
                })
                break
        # Example SHORT condition
        if signal_type in ["Short Only", "Both"]:
            if row["Close"] < or_low and row["Volume"] > avg_vol * vol_thresh:
                entry = row["Close"]
                sl = entry * (1 + sl_pct / 100) if use_sl else None
                target = entry * (1 - target_pct / 100)
                results.append({
                    "Stock": stock, "Signal": "Short", "Time": idx.strftime("%H:%M"),
                    "Entry": round(entry, 2), "SL": round(sl, 2) if sl else "-", "Target": round(target, 2)
                })
                break

# --- Display Results ---
st.subheader("📋 Strategy Output")
if results:
    df_res = pd.DataFrame(results)
    st.dataframe(df_res)
    st.download_button("Download CSV", df_res.to_csv(index=False).encode(), "strategy_log.csv", "text/csv")
else:
    st.info("No signals generated for selected parameters.")
