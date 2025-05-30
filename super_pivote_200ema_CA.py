import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Set Streamlit page config
st.set_page_config(page_title="Supertrend + Pivot + 200 EMA Strategy", layout="wide")

st.title("📊 Supertrend + Pivot Points + 200 EMA Strategy Backtest")

# Upload CSV
uploaded_file = st.file_uploader("Upload OHLCV CSV file (5min/15min data)", type=["csv"])

@st.cache_data
def calculate_indicators(df):
    # Calculate 200 EMA
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # Pivot Points
    df['PP'] = (df['High'].shift(1) + df['Low'].shift(1) + df['Close'].shift(1)) / 3
    df['R1'] = 2 * df['PP'] - df['Low'].shift(1)
    df['S1'] = 2 * df['PP'] - df['High'].shift(1)

    # ATR
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(10).mean()

    # Supertrend
    factor = 3.0
    df['UpperBand'] = ((df['High'] + df['Low']) / 2) + (factor * df['ATR'])
    df['LowerBand'] = ((df['High'] + df['Low']) / 2) - (factor * df['ATR'])

    df['in_uptrend'] = True
    for current in range(1, len(df.index)):
        previous = current - 1

        if df['Close'][current] > df['UpperBand'][previous]:
            df.at[current, 'in_uptrend'] = True
        elif df['Close'][current] < df['LowerBand'][previous]:
            df.at[current, 'in_uptrend'] = False
        else:
            df.at[current, 'in_uptrend'] = df['in_uptrend'][previous]
            if df['in_uptrend'][current] and df['LowerBand'][current] < df['LowerBand'][previous]:
                df.at[current, 'LowerBand'] = df['LowerBand'][previous]
            if not df['in_uptrend'][current] and df['UpperBand'][current] > df['UpperBand'][previous]:
                df.at[current, 'UpperBand'] = df['UpperBand'][previous]

    return df

# Backtest logic
def run_backtest(df):
    trades = []
    position = None
    entry_price = 0
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]

        # Buy Signal
        if row['Close'] > row['EMA_200'] and row['in_uptrend'] and row['Close'] > row['PP'] and position is None:
            entry_price = row['Close']
            position = 'long'
            trades.append({'Type': 'Buy', 'Price': entry_price, 'Time': row['Datetime']})

        # Sell Signal
        elif row['Close'] < row['EMA_200'] and not row['in_uptrend'] and row['Close'] < row['PP'] and position is None:
            entry_price = row['Close']
            position = 'short'
            trades.append({'Type': 'Sell', 'Price': entry_price, 'Time': row['Datetime']})

        # Exit long position
        elif position == 'long' and (row['Close'] < row['LowerBand'] or row['Close'] < row['EMA_200']):
            trades.append({'Type': 'Exit', 'Price': row['Close'], 'Time': row['Datetime']})
            position = None

        # Exit short position
        elif position == 'short' and (row['Close'] > row['UpperBand'] or row['Close'] > row['EMA_200']):
            trades.append({'Type': 'Exit', 'Price': row['Close'], 'Time': row['Datetime']})
            position = None

    return trades

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = [col.strip().capitalize() for col in df.columns]
    if 'Datetime' in df.columns:
        df['Datetime'] = pd.to_datetime(df['Datetime'])
        df.set_index('Datetime', inplace=True)
    df = calculate_indicators(df)
    df.reset_index(inplace=True)

    trades = run_backtest(df)
    st.subheader("📌 Backtest Trade Log")
    st.dataframe(pd.DataFrame(trades))

    # Plot
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df['Datetime'],
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'], name='Candles'))
    fig.add_trace(go.Scatter(x=df['Datetime'], y=df['EMA_200'], line=dict(color='blue', width=1), name='EMA 200'))
    fig.add_trace(go.Scatter(x=df['Datetime'], y=df['UpperBand'], line=dict(color='green', width=1), name='UpperBand'))
    fig.add_trace(go.Scatter(x=df['Datetime'], y=df['LowerBand'], line=dict(color='red', width=1), name='LowerBand'))

    for trade in trades:
        color = 'green' if trade['Type'] == 'Buy' else ('red' if trade['Type'] == 'Sell' else 'black')
        symbol = 'arrow-up' if trade['Type'] == 'Buy' else ('arrow-down' if trade['Type'] == 'Sell' else 'x')
        fig.add_trace(go.Scatter(x=[trade['Time']], y=[trade['Price']],
                                 mode='markers', marker=dict(color=color, size=10, symbol=symbol),
                                 name=trade['Type']))

    fig.update_layout(title='Strategy Chart with Signals', xaxis_rangeslider_visible=False, height=700)
    st.plotly_chart(fig, use_container_width=True)

    # Performance summary
    df_trades = pd.DataFrame(trades)
    if len(df_trades) >= 2:
        profits = []
        for i in range(1, len(df_trades), 2):
            entry = df_trades.iloc[i-1]
            exit = df_trades.iloc[i]
            pl = (exit['Price'] - entry['Price']) if entry['Type'] == 'Buy' else (entry['Price'] - exit['Price'])
            profits.append(pl)
        st.metric("📈 Total Trades", len(profits))
        st.metric("💰 Net P/L", round(sum(profits), 2))
        st.metric("✅ Win Rate", f"{round((np.sum([1 for p in profits if p > 0]) / len(profits)) * 100, 2)} %")
