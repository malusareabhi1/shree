import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime

st.set_page_config(page_title="Supertrend + Pivot + 200 EMA Strategy", layout="wide")

st.title("📈 Supertrend + Pivot + 200 EMA Strategy")
st.markdown("""
### Strategy Explanation
- **Supertrend**: Uses ATR (Average True Range) to determine trend direction.
- **200 EMA**: Confirms trend direction. Buy signals only if price is above 200 EMA.
- **Pivot Breakout**: Entry when price breaks above recent high (3-bar high).
- **Buy Condition**: Supertrend in uptrend, Close > 200 EMA, Close > Pivot High.
- **Sell Condition**: Supertrend turns down OR Close < 200 EMA.
- Trades are shown on the chart with green (Buy) and red (Sell) dots.
""")

# --- File uploader ---
file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns]
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df.set_index('Datetime', inplace=False)
    return df

@st.cache_data
def calculate_indicators(df):
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # ATR Calculation
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(10).mean()

    # Supertrend Calculation
    df['UpperBand'] = ((df['High'] + df['Low']) / 2) + (3 * df['ATR'])
    df['LowerBand'] = ((df['High'] + df['Low']) / 2) - (3 * df['ATR'])
    df['in_uptrend'] = True

    for current in range(1, len(df)):
        previous = current - 1

        if df['Close'].iloc[current] > df['UpperBand'].iloc[previous]:
            df['in_uptrend'].iloc[current] = True
        elif df['Close'].iloc[current] < df['LowerBand'].iloc[previous]:
            df['in_uptrend'].iloc[current] = False
        else:
            df['in_uptrend'].iloc[current] = df['in_uptrend'].iloc[previous]
            if df['in_uptrend'].iloc[current] and df['LowerBand'].iloc[current] < df['LowerBand'].iloc[previous]:
                df['LowerBand'].iloc[current] = df['LowerBand'].iloc[previous]
            if not df['in_uptrend'].iloc[current] and df['UpperBand'].iloc[current] > df['UpperBand'].iloc[previous]:
                df['UpperBand'].iloc[current] = df['UpperBand'].iloc[previous]

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
        if trade['Type'] == 'Buy':
            fig.add_trace(go.Scatter(x=[trade['Time']], y=[trade['Price']], mode='markers', marker=dict(color='green', size=10), name='Buy'))
        elif trade['Type'] == 'Sell':
            fig.add_trace(go.Scatter(x=[trade['Time']], y=[trade['Price']], mode='markers', marker=dict(color='red', size=10), name='Sell'))

    fig.update_layout(title='Supertrend + Pivot + 200 EMA Strategy', xaxis_rangeslider_visible=False)
    return fig

if file:
    df = load_data(file)
    df = calculate_indicators(df)
    trades = run_backtest(df)

    st.plotly_chart(plot_chart(df, trades), use_container_width=True)

    if trades:
        st.subheader("📋 Trade Log")
        st.dataframe(pd.DataFrame(trades))

        total_pnl = sum([trade['PnL'] for trade in trades if trade['Type'] == 'Sell'])
        st.metric(label="Total Profit/Loss", value=f"{total_pnl:.2f}")
    else:
        st.info("No trades generated for the selected data.")
