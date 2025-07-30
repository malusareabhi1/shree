import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from datetime import datetime, timedelta

# -------------------------------
st.set_page_config(layout="wide")
st.title("\U0001F680 Intraday Strategy Dashboard")

# ------------------------------- Sidebar
st.sidebar.header("Settings")
ticker = st.sidebar.selectbox("Select Stock", ['RELIANCE.NS', 'INFY.NS', 'TCS.NS', 'ICICIBANK.NS', 'SBIN.NS'])
start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=5))
end_date = st.sidebar.date_input("End Date", datetime.now())
interval = st.sidebar.selectbox("Interval", ['5m', '15m'], index=0)

selected_strategy = st.sidebar.selectbox("Choose Strategy", [
    'Opening Range Breakout (ORB)',
    'VWAP Pullback',
    'EMA Crossover',
    'Bollinger Band Breakout',
    'CPR Breakout',
    'RSI Divergence',
    'Trendline Breakout'
])

# ------------------------------- Data Fetch
@st.cache_data(ttl=600)
def load_data(symbol, start, end, interval):
    df = yf.download(symbol, start=start, end=end + timedelta(days=1), interval=interval)
    if df.empty:
        return df
    df.columns = [str(col).capitalize() for col in df.columns]  # Ensure all column names are strings before capitalizing
    df.dropna(inplace=True)
    df.reset_index(inplace=True)
    return df

df = load_data(ticker, start_date, end_date, interval)

# ------------------------------- Common Plots
def plot_candles(df, signals=None):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df['Datetime'], open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close'], name='Candles'))
    if signals is not None:
        for signal in signals:
            fig.add_trace(go.Scatter(
                x=[signal['time']],
                y=[signal['price']],
                mode='markers+text',
                marker=dict(color='green' if signal['type']=='BUY' else 'red', size=10),
                text=[signal['type']],
                textposition='bottom center'
            ))
    fig.update_layout(title="Price Chart with Signals", height=600, xaxis_rangeslider_visible=False)
    return fig

# ------------------------------- Strategy Logic Placeholders
strategy_signals = []

if selected_strategy == 'Opening Range Breakout (ORB)':
    df['Time'] = df['Datetime'].dt.time
    if 'High' in df.columns and 'Low' in df.columns:
        opening_range = df[(df['Time'] >= datetime.strptime("09:15", "%H:%M").time()) &
                           (df['Time'] <= datetime.strptime("09:30", "%H:%M").time())]
        if not opening_range.empty:
            high = float(opening_range['High'].max())
            low = float(opening_range['Low'].min())

            for i in range(len(df)):
                candle_high = float(df.loc[i, 'High'])
                candle_low = float(df.loc[i, 'Low'])
                candle_time = df.loc[i, 'Datetime']

                if candle_high > high:
                    strategy_signals.append({'time': candle_time, 'price': candle_high, 'type': 'BUY'})
                    break
                elif candle_low < low:
                    strategy_signals.append({'time': candle_time, 'price': candle_low, 'type': 'SELL'})
                    break

elif selected_strategy == 'VWAP Pullback':
    if 'Volume' not in df.columns:
        st.error("Volume data not available in downloaded dataset.")
    else:
        df['vwap'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
        for i in range(1, len(df)):
            if df.loc[i, 'Close'] > df.loc[i, 'vwap'] and df.loc[i, 'Low'] < df.loc[i, 'vwap']:
                strategy_signals.append({'time': df.loc[i, 'Datetime'], 'price': df.loc[i, 'Close'], 'type': 'BUY'})

elif selected_strategy == 'EMA Crossover':
    df['EMA9'] = EMAIndicator(close=df['Close'], window=9).ema_indicator()
    df['EMA21'] = EMAIndicator(close=df['Close'], window=21).ema_indicator()
    for i in range(1, len(df)):
        if df['EMA9'][i-1] < df['EMA21'][i-1] and df['EMA9'][i] > df['EMA21'][i]:
            strategy_signals.append({'time': df['Datetime'][i], 'price': df['Close'][i], 'type': 'BUY'})
        elif df['EMA9'][i-1] > df['EMA21'][i-1] and df['EMA9'][i] < df['EMA21'][i]:
            strategy_signals.append({'time': df['Datetime'][i], 'price': df['Close'][i], 'type': 'SELL'})

elif selected_strategy == 'Bollinger Band Breakout':
    df['MA20'] = df['Close'].rolling(20).mean()
    df['STD20'] = df['Close'].rolling(20).std()
    df['Upper'] = df['MA20'] + 2 * df['STD20']
    df['Lower'] = df['MA20'] - 2 * df['STD20']
    for i in range(20, len(df)):
        if df['Close'][i] > df['Upper'][i]:
            strategy_signals.append({'time': df['Datetime'][i], 'price': df['Close'][i], 'type': 'BUY'})
        elif df['Close'][i] < df['Lower'][i]:
            strategy_signals.append({'time': df['Datetime'][i], 'price': df['Close'][i], 'type': 'SELL'})

elif selected_strategy == 'CPR Breakout':
    df['PP'] = (df['High'].shift(1) + df['Low'].shift(1) + df['Close'].shift(1)) / 3
    df['BC'] = (df['High'].shift(1) + df['Low'].shift(1)) / 2
    df['TC'] = 2 * df['PP'] - df['BC']
    for i in range(1, len(df)):
        if df['Close'][i] > df['TC'][i]:
            strategy_signals.append({'time': df['Datetime'][i], 'price': df['Close'][i], 'type': 'BUY'})
        elif df['Close'][i] < df['BC'][i]:
            strategy_signals.append({'time': df['Datetime'][i], 'price': df['Close'][i], 'type': 'SELL'})

elif selected_strategy == 'RSI Divergence':
    df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
    for i in range(2, len(df)):
        if df['Close'][i] < df['Close'][i-1] and df['RSI'][i] > df['RSI'][i-1]:
            strategy_signals.append({'time': df['Datetime'][i], 'price': df['Close'][i], 'type': 'BUY'})
        elif df['Close'][i] > df['Close'][i-1] and df['RSI'][i] < df['RSI'][i-1]:
            strategy_signals.append({'time': df['Datetime'][i], 'price': df['Close'][i], 'type': 'SELL'})

elif selected_strategy == 'Trendline Breakout':
    st.warning("Trendline logic requires drawing tools or manual marking. This is a placeholder.")

# ------------------------------- Display
if df.empty:
    st.error("No data loaded.")
else:
    st.plotly_chart(plot_candles(df, strategy_signals), use_container_width=True)
    st.dataframe(df.tail())
