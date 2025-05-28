import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.title("📈 Trend Direction Change Strategy")

# Sidebar inputs
symbol = st.sidebar.text_input("Enter Stock Symbol", "NIFTY.NS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Fetch data
data = yf.download(symbol, start=start_date, end=end_date)
data['SMA20'] = data['Close'].rolling(window=20).mean()
data['SMA50'] = data['Close'].rolling(window=50).mean()

# Detect crossovers safely
data['Signal'] = (data['SMA20'] > data['SMA50']).astype(int)
data['Position'] = data['Signal'].diff()

# Plotting
fig = go.Figure()

fig.add_trace(go.Candlestick(x=data.index,
                open=data['Open'], high=data['High'],
                low=data['Low'], close=data['Close'],
                name="Candles"))

candle_fig.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name="Candles",
    increasing=dict(line=dict(color='lime'), fillcolor='lime'),
    decreasing=dict(line=dict(color='red'), fillcolor='red')
))


fig.add_trace(go.Scatter(x=data.index, y=data['SMA20'], line=dict(color='blue', width=1), name='SMA 20'))
fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], line=dict(color='orange', width=1), name='SMA 50'))

# Mark buy/sell signals
buy_signals = data[data['Position'] == 1]
sell_signals = data[data['Position'] == -1]

fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Close'], mode='markers',
                         marker=dict(symbol='triangle-up', size=10, color='green'), name='Buy'))

fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['Close'], mode='markers',
                         marker=dict(symbol='triangle-down', size=10, color='red'), name='Sell'))

fig.update_layout(title=f"{symbol} Trend Reversal Strategy", xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# Show signal log
st.subheader("📋 Signal Log")
st.write(data[data['Position'].isin([1, -1])][['Close', 'SMA20', 'SMA50', 'Position']])
