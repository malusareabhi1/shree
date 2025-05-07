import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
import os
import streamlit as st

# Configuration
symbol = "^NSEI"  # NIFTY 50 index symbol for Yahoo Finance
interval = "5m"
lookback_minutes = 1000  # Lookback for 3-4 days for rolling SMA
iv_threshold = 16  # Placeholder; replace with live IV if needed
log_file = "doctor_signal_log.csv"

# Load previous log if exists
if os.path.exists(log_file):
    signal_log = pd.read_csv(log_file)
else:
    signal_log = pd.DataFrame(columns=[
        "Date", "Close", "SMA_20", "Upper_BB", "Lower_BB",
        "Signal", "Entry_Price", "IV"
    ])

def get_nifty_data():
    df = yf.download(tickers=symbol, interval=interval, period="5d", progress=False)
   
    if isinstance(df.columns, pd.MultiIndex):  # This checks if the columns are a MultiIndex
            df.columns = df.columns.get_level_values(0)
             # Ensure datetime index is timezone-aware in UTC and then convert to IST
            df.index = df.index.tz_convert("Asia/Kolkata")
            for col in ["Open","High","Low","Close"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df.dropna(subset=["Open","High","Low","Close"], inplace=True)
    return df

def apply_doctor_strategy(df):
    df = df.copy()

    # Minimum 20 rows required for Bollinger Band calculation
    if len(df) < 20:
        return df

    # Indicators
    df["SMA_20"] = df["Close"].rolling(window=20).mean()
    df["STD_20"] = df["Close"].rolling(window=20).std()

    # Drop rows with NaNs in required columns (only after creating them)
    df.dropna(subset=["SMA_20", "STD_20"], inplace=True)

    # Bollinger Bands
    df["Upper_BB"] = df["SMA_20"] + 2 * df["STD_20"]
    df["Lower_BB"] = df["SMA_20"] - 2 * df["STD_20"]

    # Example strategy logic
    df["Ref_Candle_Up"] = (df["Close"] > df["SMA_20"]) & (df["Close"].shift(1) > df["SMA_20"].shift(1))

    df["Signal"] = None
    iv_threshold = 16  # placeholder: replace with your live IV logic

    for i in range(1, len(df)):
        if df["Ref_Candle_Up"].iloc[i] and iv_threshold >= 16:
            if df["Close"].iloc[i] > df["Close"].iloc[i - 1]:
                df.at[i, "Signal"] = "BUY"

    return df


def update_log(df_latest, existing_log):
    new_signals = df_latest[df_latest["Signal"].notna()]
    for _, row in new_signals.iterrows():
        if row["Date"].strftime("%Y-%m-%d %H:%M:%S") not in existing_log["Date"].astype(str).values:
            new_entry = {
                "Date": row["Date"],
                "Close": row["Close"],
                "SMA_20": row["SMA_20"],
                "Upper_BB": row["Upper_BB"],
                "Lower_BB": row["Lower_BB"],
                "Signal": row["Signal"],
                "Entry_Price": row["Close"],
                "IV": iv_threshold
            }
            existing_log = pd.concat([existing_log, pd.DataFrame([new_entry])], ignore_index=True)
    return existing_log

if __name__ == "__main__":
    df = get_nifty_data()
    st.write(df)
    df = apply_doctor_strategy(df)
    #signal_log = update_log(df, signal_log)
    #signal_log.to_csv(log_file, index=False)
    #print(signal_log.tail())
