import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import datetime

st.set_page_config(page_title="Supertrend + Pivot + 200 EMA Strategy", layout="wide")
st.title("📈 Supertrend + Pivot + 200 EMA Strategy")

# --- Sidebar Inputs ---
file = st.sidebar.file_uploader("Upload CSV File", type=["csv"])

stop_loss_pct = st.sidebar.number_input("Stop Loss %", min_value=0.1, max_value=20.0, value=1.0, step=0.1)
target_profit_pct = st.sidebar.number_input("Target Profit %", min_value=0.1, max_value=50.0, value=2.0, step=0.1)

@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df.columns = [col.strip() for col in df.columns]
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df.set_index('Datetime', inplace=True)
    return df

@st.cache_data
def calculate_indicators(df):
    required_cols = ['High', 'Low', 'Close']
    if not all(col in df.columns for col in required_cols):
        st.error("Missing required columns in the CSV file. Expected: High, Low, Close.")
        st.stop()

    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()

    # ATR Calculation
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(10).mean()

    hl2 = (df['High'] + df['Low']) / 2
    multiplier = 3
    df['UpperBand'] = hl2 + (multiplier * df['ATR'])
    df['LowerBand'] = hl2 - (multiplier * df['ATR'])
    df['in_uptrend'] = True

    # Drop NaNs and reset index to ensure iat works properly
    df = df.dropna(subset=['Close', 'LowerBand', 'UpperBand', 'ATR', 'EMA_200']).reset_index(drop=True)

    col_in_uptrend = df.columns.get_loc('in_uptrend')
    col_lowerband = df.columns.get_loc('LowerBand')
    col_upperband = df.columns.get_loc('UpperBand')

    for current in range(1, len(df)):
        previous = current - 1

        if current >= len(df) or previous < 0:
            continue

        try:
            if df['Close'].iat[current] > df['UpperBand'].iat[previous]:
                df.iat[current, col_in_uptrend] = True
            elif df['Close'].iat[current] < df['LowerBand'].iat[previous]:
                df.iat[current, col_in_uptrend] = False
            else:
                df.iat[current, col_in_uptrend] = df.iat[previous, col_in_uptrend]

                if df.iat[current, col_in_uptrend] and df['LowerBand'].iat[current] < df['LowerBand'].iat[previous]:
                    df.iat[current, col_lowerband] = df['LowerBand'].iat[previous]

                if not df.iat[current, col_in_uptrend] and df['UpperBand'].iat[current] > df['UpperBand'].iat[previous]:
                    df.iat[current, col_upperband] = df['UpperBand'].iat[previous]
        except Exception as e:
            st.error(f"Error at index {current}: {e}")
            break

    return df


@st.cache_data
def run_backtest(df, stop_loss_pct, target_profit_pct):
    position = False
    entry_price = 0.0
    trades = []

    stop_loss_price = None
    target_price = None

    for i in range(1, len(df)):
        if not position:
            # Entry Condition
            pivot_high = df['High'].rolling(3).max().iloc[i-1]
            if (df['in_uptrend'].iloc[i] and
                df['Close'].iloc[i] > df['EMA_200'].iloc[i] and
                df['Close'].iloc[i] > pivot_high):
                position = True
                entry_price = df['Close'].iloc[i]
                stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
                target_price = entry_price * (1 + target_profit_pct / 100)
                trades.append({'Type': 'Buy', 'Price': entry_price, 'Time': df.index[i]})

        elif position:
            current_price = df['Close'].iloc[i]
            exit_trade = False
            exit_reason = ''

            # Exit conditions
            if current_price <= stop_loss_price:
                exit_trade = True
                exit_reason = 'Stop Loss Hit'
            elif current_price >= target_price:
                exit_trade = True
                exit_reason = 'Target Hit'
            elif (not df['in_uptrend'].iloc[i]) or (current_price < df['EMA_200'].iloc[i]):
                exit_trade = True
                exit_reason = 'Trend Reversal'

            if exit_trade:
                trades.append({'Type': 'Sell', 'Price': current_price, 'Time': df.index[i], 'PnL': current_price - entry_price, 'Exit Reason': exit_reason})
                position = False
                stop_loss_price = None
                target_price = None

    # Close position at the end if still open
    if position:
        last_price = df['Close'].iloc[-1]
        trades.append({'Type': 'Sell', 'Price': last_price, 'Time': df.index[-1], 'PnL': last_price - entry_price, 'Exit Reason': 'End of Data'})
        position = False

    return trades

def plot_chart(df, trades):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'], name='Candlestick'))

    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_200'], line=dict(color='orange', width=1), name='EMA 200'))

    for trade in trades:
        if trade['Type'] == 'Buy':
            fig.add_trace(go.Scatter(x=[trade['Time']], y=[trade['Price']], mode='markers', marker=dict(color='green', size=10), name='Buy'))
        elif trade['Type'] == 'Sell':
            fig.add_trace(go.Scatter(x=[trade['Time']], y=[trade['Price']], mode='markers', marker=dict(color='red', size=10), name='Sell'))

    fig.update_layout(title='Supertrend + Pivot + 200 EMA Strategy', xaxis_rangeslider_visible=False)
    return fig

def plot_equity_curve(trades):
    pnl = 0
    equity = []
    times = []

    for trade in trades:
        if trade['Type'] == 'Sell':
            pnl += trade['PnL']
            equity.append(pnl)
            times.append(trade['Time'])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=equity, mode='lines+markers', name='Equity Curve'))
    fig.update_layout(title='Equity Curve (Cumulative PnL)', xaxis_title='Time', yaxis_title='Profit/Loss')
    return fig

if file:
    df = load_data(file)
    df = calculate_indicators(df)
    trades = run_backtest(df, stop_loss_pct, target_profit_pct)

    st.plotly_chart(plot_chart(df, trades), use_container_width=True)

    if trades:
        st.subheader("📋 Trade Log")
        trades_df = pd.DataFrame(trades)
        st.dataframe(trades_df)

        total_pnl = trades_df.loc[trades_df['Type'] == 'Sell', 'PnL'].sum()
        win_trades = trades_df[(trades_df['Type'] == 'Sell') & (trades_df['PnL'] > 0)]
        win_rate = len(win_trades) / len(trades_df[trades_df['Type'] == 'Sell']) * 100 if len(trades_df[trades_df['Type'] == 'Sell']) > 0 else 0
        avg_pnl = trades_df.loc[trades_df['Type'] == 'Sell', 'PnL'].mean()

        st.metric(label="Total Profit/Loss", value=f"{total_pnl:.2f}")
        st.metric(label="Win Rate (%)", value=f"{win_rate:.2f}")
        st.metric(label="Average PnL per Trade", value=f"{avg_pnl:.2f}")

        st.plotly_chart(plot_equity_curve(trades), use_container_width=True)
    else:
        st.info("No trades generated for the selected data.")
else:
    st.info("Please upload a CSV file to begin.")
