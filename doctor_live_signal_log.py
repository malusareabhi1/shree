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
    df = yf.download(tickers=symbol, interval=interval, period="1d", progress=False)
   
    if isinstance(df.columns, pd.MultiIndex):  # This checks if the columns are a MultiIndex
            df.columns = df.columns.get_level_values(0)
             # Ensure datetime index is timezone-aware in UTC and then convert to IST
            df.index = df.index.tz_convert("Asia/Kolkata")
        # Reset index to bring datetime into a column
            df.reset_index(inplace=True)
            df.rename(columns={"index": "Date"}, inplace=True)  # Ensure column name is 'Date'
        
            for col in ["Open","High","Low","Close"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df.dropna(subset=["Open","High","Low","Close"], inplace=True)
    return df

def doctor_strategy_signals(df, iv_threshold=16, capital=50000):
    """
    Applies Doctor Strategy on a 5-minute OHLC DataFrame and returns trades with signals and PnL.

    Parameters:
        df (pd.DataFrame): Must contain 'Date', 'Open', 'High', 'Low', 'Close'
        iv_threshold (float): IV threshold for trade confirmation
        capital (float): Capital allocated per trade

    Returns:
        pd.DataFrame: Original DataFrame with Signal column
        list of dicts: Trade log with entry/exit and PnL
    """

    # Ensure Date column is timezone-aware
    df['Date'] = pd.to_datetime(df['Date'])
    if df['Date'].dt.tz is None:
        df['Date'] = df['Date'].dt.tz_localize("UTC").dt.tz_convert("Asia/Kolkata")
    else:
        df['Date'] = df['Date'].dt.tz_convert("Asia/Kolkata")

    df = df[df['Date'].dt.time.between(pd.to_datetime('09:30:00').time(), pd.to_datetime('13:30:00').time())]
    df = df.sort_values('Date').reset_index(drop=True)

    # Bollinger Bands and SMA 20
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Upper_BB'] = df['SMA_20'] + 2 * df['Close'].rolling(window=20).std()
    df['Lower_BB'] = df['SMA_20'] - 2 * df['Close'].rolling(window=20).std()

    # Entry Logic
    df['Crossed_SMA_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) < df['SMA_20'].shift(1))
    df['Ref_Candle_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) > df['SMA_20'].shift(1))

    df['Signal'] = None
    for i in range(1, len(df)):
        if df['Ref_Candle_Up'].iloc[i] and iv_threshold >= 16:
            if df['Close'].iloc[i] > df['Close'].iloc[i - 1]:
                df.at[i, 'Signal'] = 'BUY'

    # Trade simulation
    trades = []
    for i in range(len(df)):
        if df['Signal'].iloc[i] == 'BUY':
            entry_time = df['Date'].iloc[i]
            entry_price = df['Close'].iloc[i]
            stop_loss = entry_price * 0.90
            profit_target = entry_price * 1.05
            exit_time = None
            exit_price = None
            exit_reason = None
            pnl = None

            for j in range(i + 1, min(i + 12, len(df))):  # 10-minute window after entry
                price = df['Close'].iloc[j]
                if price >= profit_target:
                    exit_time = df['Date'].iloc[j]
                    exit_price = profit_target
                    exit_reason = "Target Hit"
                    break
                elif price <= stop_loss:
                    exit_time = df['Date'].iloc[j]
                    exit_price = stop_loss
                    exit_reason = "Stop Loss Hit"
                    break
            else:
                # Time-based exit
                if i + 10 < len(df):
                    exit_time = df['Date'].iloc[i + 10]
                    exit_price = df['Close'].iloc[i + 10]
                    exit_reason = "Time Exit"

            if exit_price:
                turnover = entry_price + exit_price
                pnl = (exit_price - entry_price) * (capital // entry_price) - 20  # ₹20 brokerage
                trades.append({
                    "Entry_Time": entry_time,
                    "Entry_Price": entry_price,
                    "Exit_Time": exit_time,
                    "Exit_Price": exit_price,
                    "Stop_Loss": stop_loss,
                    "Profit_Target": profit_target,
                    "Exit_Reason": exit_reason,
                    "Brokerage": 20,
                    "PnL": round(pnl, 2),
                    "Turnover": round(turnover, 2)
                })

    return df, trades



if __name__ == "__main__":
    df = get_nifty_data()
    df.rename(columns={df.columns[0]: "Date"}, inplace=True)
    st.write("DATA")
    st.write(df.head(5))
    #st.write(df.columns)
    # Assuming your df_5min has 'Date', 'Open', 'High', 'Low', 'Close'
    df_result, trade_log = doctor_strategy_signals(df)
    
    # Show signals on chart
    st.dataframe(df_result[['Date', 'Close', 'SMA_20', 'Signal']].dropna(subset=['Signal']))
    
    # Show trade summary
    st.write.dataframe(pd.DataFrame(trade_log))
    #st.write(df)
    st.write("Tradelog")
    st.write(trade_log.head(5))
    
