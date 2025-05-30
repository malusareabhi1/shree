import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Supertrend + Pivot + 200 EMA Strategy", layout="wide")
st.title("📈 Supertrend + Pivot + 200 EMA Strategy")
st.markdown("""Strategy Explanation
Supertrend: Uses ATR (Average True Range) to determine trend direction.
200 EMA: Confirms trend direction. Buy signals only if price is above 200 EMA.
Pivot Breakout: Entry when price breaks above recent high (3-bar high).
Buy Condition: Supertrend in uptrend, Close > 200 EMA, Close > Pivot High.
Sell Condition: Supertrend turns down OR Close < 200 EMA.
Trades are shown on the chart with green (Buy) and red (Sell) dots.""")
# Sidebar: Select Stock and Interval
nifty100_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "LT.NS", "ITC.NS", "KOTAKBANK.NS"]
symbol = st.sidebar.selectbox("Select NIFTY 100 Stock", nifty100_stocks)
interval = st.sidebar.selectbox("Select Interval", ["5m", "15m", "1h"])
days = st.sidebar.slider("Number of past days", 1, 10, 5)

@st.cache_data
def fetch_data(symbol, interval, days):
    df = yf.download(tickers=symbol, interval=interval, period=f"{days}d")
    df.reset_index(inplace=True)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    return df

@st.cache_data
def calculate_indicators(df):
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(10).mean()

    df['UpperBand'] = ((df['High'] + df['Low']) / 2) + (3 * df['ATR'])
    df['LowerBand'] = ((df['High'] + df['Low']) / 2) - (3 * df['ATR'])
    df['in_uptrend'] = True

    for current in range(1, len(df)):
        previous = current - 1
        if df['Close'].iloc[current] > df['UpperBand'].iloc[previous]:
            df.at[current, 'in_uptrend'] = True
        elif df['Close'].iloc[current] < df['LowerBand'].iloc[previous]:
            df.at[current, 'in_uptrend'] = False
        else:
            df.at[current, 'in_uptrend'] = df.at[previous, 'in_uptrend']
            if df.at[current, 'in_uptrend'] and df['LowerBand'].iloc[current] < df['LowerBand'].iloc[previous]:
                df.at[current, 'LowerBand'] = df['LowerBand'].iloc[previous]
            if not df.at[current, 'in_uptrend'] and df['UpperBand'].iloc[current] > df['UpperBand'].iloc[previous]:
                df.at[current, 'UpperBand'] = df['UpperBand'].iloc[previous]
    return df

@st.cache_data
def run_backtest(df):
    position = False
    entry_price = 0.0
    trades = []

    for i in range(1, len(df)):
        if not position:
            if df['in_uptrend'].iloc[i] and df['Close'].iloc[i] > df['EMA_200'].iloc[i] and df['Close'].iloc[i] > df['High'].rolling(3).max().iloc[i - 1]:
                position = True
                entry_price = df['Close'].iloc[i]
                trades.append({'Type': 'Buy', 'Price': entry_price, 'Time': df['Datetime'].iloc[i]})

        elif position:
            if not df['in_uptrend'].iloc[i] or df['Close'].iloc[i] < df['EMA_200'].iloc[i]:
                exit_price = df['Close'].iloc[i]
                trades.append({'Type': 'Sell', 'Price': exit_price, 'Time': df['Datetime'].iloc[i], 'PnL': exit_price - entry_price})
                position = False
    return trades

def plot_chart(df, trades):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df['Datetime'],
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'], name='Candlestick'))
    fig.add_trace(go.Scatter(x=df['Datetime'], y=df['EMA_200'], line=dict(color='orange', width=1), name='EMA 200'))
    for trade in trades:
        color = 'green' if trade['Type'] == 'Buy' else 'red'
        fig.add_trace(go.Scatter(x=[trade['Time']], y=[trade['Price']],
                                 mode='markers', marker=dict(color=color, size=10), name=trade['Type']))
    fig.update_layout(title=f'{symbol} Strategy Backtest', xaxis_rangeslider_visible=False)
    return fig

# Run everything
df = fetch_data(symbol, interval, days)
df = calculate_indicators(df)
trades = run_backtest(df)

st.plotly_chart(plot_chart(df, trades), use_container_width=True)

if trades:
    st.subheader("📋 Trade Log")
    st.dataframe(pd.DataFrame(trades))
    total_pnl = sum([t['PnL'] for t in trades if t['Type'] == 'Sell'])
    st.metric(label="Total Profit/Loss", value=f"{total_pnl:.2f}")
else:
    st.info("No trades generated for this stock in selected time.")
