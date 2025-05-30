import yfinance as yf
import pandas as pd
import streamlit as st
from ta.trend import EMAIndicator

# -----------------------------
# Streamlit App Configuration
# -----------------------------
st.set_page_config(page_title="Momentum Pullback Swing Strategy", layout="wide")
st.title("📈 Momentum Pullback Swing Strategy Backtest")

# -----------------------------
# Input Section
# -----------------------------
symbol = st.sidebar.text_input("Enter stock symbol", value="RELIANCE.NS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2022-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2023-01-01"))
capital = st.sidebar.number_input("Initial Capital", value=100000, step=10000)

if st.sidebar.button("Run Backtest"):
    # -----------------------------
    # Fetch Data
    # -----------------------------
    df = yf.download(symbol, start=start_date, end=end_date, progress=False)

    if df.empty:
        st.error("No data found. Please check the stock symbol or date range.")
        st.stop()

    if 'Close' not in df.columns or df['Close'].isna().all():
        st.error("❌ Error: 'Close' column missing or contains all NaNs.")
        st.stop()

    df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(map(str, col)).strip() for col in df.columns]
    else:
        df.columns = df.columns.str.strip()


       # -----------------------------
    # Calculate Indicators Safely
    # -----------------------------
    if 'Close' in df.columns and not df['Close'].isnull().all():
        ema20 = EMAIndicator(close=df['Close'], window=20).ema_indicator()
        ema200 = EMAIndicator(close=df['Close'], window=200).ema_indicator()
        
        # Convert to 1D if needed
        df['20EMA'] = pd.Series(ema20.values.ravel(), index=df.index)
        df['200EMA'] = pd.Series(ema200.values.ravel(), index=df.index)
    else:
        st.error("❌ Error: 'Close' column missing or contains all NaNs.")
        st.stop()
    

    # -----------------------------
    # Momentum Pullback Logic
    # -----------------------------
    df['Signal'] = 0
    for i in range(1, len(df)):
        if (
            df['20EMA'].iloc[i] > df['200EMA'].iloc[i] and
            df['Close'].iloc[i] < df['20EMA'].iloc[i] and
            df['Close'].iloc[i-1] < df['20EMA'].iloc[i-1]
        ):
            df['Signal'].iloc[i] = 1  # BUY
        elif df['Close'].iloc[i] < df['200EMA'].iloc[i]:
            df['Signal'].iloc[i] = -1  # EXIT

    # -----------------------------
    # Backtest Execution
    # -----------------------------
    df['Position'] = df['Signal'].replace(to_replace=0, method='ffill')
    df['Daily Return'] = df['Close'].pct_change()
    df['Strategy Return'] = df['Daily Return'] * df['Position'].shift(1)

    df['Equity Curve'] = (1 + df['Strategy Return']).cumprod() * capital

    # -----------------------------
    # Output Section
    # -----------------------------
    st.subheader(f"Backtest Result for {symbol}")
    st.line_chart(df[['Close', '20EMA', '200EMA']])
    st.line_chart(df[['Equity Curve']])
    st.write(df.tail(10))

    total_return = df['Equity Curve'].iloc[-1] - capital
    st.success(f"Total Return: ₹{total_return:.2f}")
    st.info(f"Final Equity: ₹{df['Equity Curve'].iloc[-1]:.2f}")
