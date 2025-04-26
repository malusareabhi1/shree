import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO


# ---- Sidebar Config Inputs ----
st.sidebar.title("Trading Settings")

capital = st.sidebar.number_input("Capital (₹)", value=100000, step=1000)
risk_per_trade = st.sidebar.slider("Risk per Trade (%)", min_value=1, max_value=100, value=5) / 100
quantity_per_trade = st.sidebar.number_input("Quantity per Trade", value=1, step=1)
target_multiplier = st.sidebar.slider("Target Risk Reward (e.g., 1.5 means Target = 1.5 × Risk)", min_value=1.0, max_value=5.0, value=1.5, step=0.1)

brokerage_per_trade = 20  # Fixed ₹20 per trade for simplicity

# ---- Functions ----
def load_data():
    uploaded_file = st.file_uploader("Upload CSV file with OHLCV data", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        return df
    return None

def convert_timezone(df, datetime_col):
    df[datetime_col] = pd.to_datetime(df[datetime_col])
    df['Date'] = df[datetime_col]
    if df['Date'].dt.tz is None:
        df['Date'] = df['Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    else:
        df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata')
    df.set_index('Date', inplace=True)
    return df

def run_paper_trading2(df):
    position_size = capital * risk_per_trade
    trades = []
    in_position = False
    entry_price, entry_time, stoploss, target = None, None, None, None

    for i in range(1, len(df)):
        row_prev = df.iloc[i - 1]
        row = df.iloc[i]

        # Entry conditions
        if not in_position:
            # Bullish breakout
            if row_prev['Close'] > row_prev['Open'] and row['High'] > row_prev['High']:
                entry_price = row['Open']
                stoploss = row_prev['Low']
                risk = entry_price - stoploss
                target = entry_price + target_multiplier * risk
                entry_time = row.name
                in_position = True
                trades.append({
                    'Type': 'BUY',
                    'Entry Time': entry_time,
                    'Entry Price': entry_price,
                    'Stoploss': stoploss,
                    'Target': target
                })

            # Bearish breakdown
            elif row_prev['Close'] < row_prev['Open'] and row['Low'] < row_prev['Low']:
                entry_price = row['Open']
                stoploss = row_prev['High']
                risk = stoploss - entry_price
                target = entry_price - target_multiplier * risk
                entry_time = row.name
                in_position = True
                trades.append({
                    'Type': 'SELL',
                    'Entry Time': entry_time,
                    'Entry Price': entry_price,
                    'Stoploss': stoploss,
                    'Target': target
                })

        # Exit conditions
        elif in_position:
            last_trade = trades[-1]
            if last_trade['Type'] == 'BUY':
                # Hit Stoploss
                if row['Low'] <= last_trade['Stoploss']:
                    exit_price = last_trade['Stoploss']
                    exit_time = row.name
                    pnl = (exit_price - last_trade['Entry Price']) * quantity_per_trade
                    last_trade.update({
                        'Exit Time': exit_time,
                        'Exit Price': exit_price,
                        'PnL': round(pnl, 2),
                        'Exit Reason': 'Stoploss Hit'
                    })
                    in_position = False

                # Hit Target
                elif row['High'] >= last_trade['Target']:
                    exit_price = last_trade['Target']
                    exit_time = row.name
                    pnl = (exit_price - last_trade['Entry Price']) * quantity_per_trade
                    last_trade.update({
                        'Exit Time': exit_time,
                        'Exit Price': exit_price,
                        'PnL': round(pnl, 2),
                        'Exit Reason': 'Target Hit'
                    })
                    in_position = False

            elif last_trade['Type'] == 'SELL':
                # Hit Stoploss
                if row['High'] >= last_trade['Stoploss']:
                    exit_price = last_trade['Stoploss']
                    exit_time = row.name
                    pnl = (last_trade['Entry Price'] - exit_price) * quantity_per_trade
                    last_trade.update({
                        'Exit Time': exit_time,
                        'Exit Price': exit_price,
                        'PnL': round(pnl, 2),
                        'Exit Reason': 'Stoploss Hit'
                    })
                    in_position = False

                # Hit Target
                elif row['Low'] <= last_trade['Target']:
                    exit_price = last_trade['Target']
                    exit_time = row.name
                    pnl = (last_trade['Entry Price'] - exit_price) * quantity_per_trade
                    last_trade.update({
                        'Exit Time': exit_time,
                        'Exit Price': exit_price,
                        'PnL': round(pnl, 2),
                        'Exit Reason': 'Target Hit'
                    })
                    in_position = False

    return pd.DataFrame(trades)

# ---- Main App ----
st.title("Paper Trading Backtest")

df = load_data()
if df is not None:
    datetime_col = st.selectbox("Select Datetime Column", df.columns)
    df = convert_timezone(df, datetime_col)
    st.write("Data Sample:", df.head())

    if st.button("Run Backtest"):
        results = run_paper_trading2(df)
        st.subheader("Trade Results")
        st.dataframe(results)

        if not results.empty:
            total_pnl = results['PnL'].sum()
            st.metric("Total P&L", f"₹{total_pnl:.2f}")

            # Plotting Equity Curve
            results['Cumulative PnL'] = results['PnL'].cumsum()
            fig, ax = plt.subplots()
            ax.plot(results['Exit Time'], results['Cumulative PnL'], marker='o')
            ax.set_title("Equity Curve")
            ax.set_xlabel("Time")
            ax.set_ylabel("Cumulative PnL")
            st.pyplot(fig)
