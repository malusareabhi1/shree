import pandas as pd  # Add this import
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.title("📊 Live NIFTY 5‑Minute Candle")

def fetch_5min_data(symbol):
    df = yf.download(tickers=symbol, interval="5m", period="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):  # This checks if the columns are a MultiIndex
        df.columns = df.columns.get_level_values(0)
    for col in ["Open","High","Low","Close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["Open","High","Low","Close"], inplace=True)
    return df

def plot_candles(df):
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
    )])
    fig.update_layout(
        title="NIFTY 5‑Minute Candles (Today)",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False
    )
    return fig

symbol = "^NSEI"
df = fetch_5min_data(symbol)

if df.empty:
    st.warning("No data available for today’s 5‑min bars.")
else:
    st.plotly_chart(plot_candles(df), use_container_width=True)
