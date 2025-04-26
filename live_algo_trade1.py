import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# ---- Config ----
CAPITAL = 100000
RISK_PER_TRADE = 0.02
BROKERAGE_PER_TRADE = 20  # ₹20 per trade assumed

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

def run_paper_trading(df):
    position_size = CAPITAL * RISK_PER_TRADE
    trades = []
    in_position = False
    entry_price, entry_time = None, None

    for i in range(1, len(df)):
        row_prev = df.iloc[i - 1]
        row = df.iloc[i]

        if not in_position and row_prev['Close'] > row_prev['Open']:
            entry_price = row['Open']
            entry_time = row.name
            in_position = True
            trades.append({
                'Type': 'BUY',
                'Entry Time': entry_time,
                'Entry Price': entry_price
            })

        elif in_position and row_prev['Close'] < row_prev['Open']:
            exit_price = row['Open']
            exit_time = row.name
            pnl = (exit_price - entry_price) * (position_size / entry_price)
            trades[-1].update({
                'Exit Time': exit_time,
                'Exit Price': exit_price,
                'PnL': round(pnl, 2)
            })
            in_position = False

    return pd.DataFrame(trades)

def calculate_metrics(trades_df):
    total_pnl = trades_df['PnL'].sum()
    success_trades = trades_df[trades_df['PnL'] > 0]
    fail_trades = trades_df[trades_df['PnL'] <= 0]
    total_trades = len(trades_df)
    success_ratio = (len(success_trades) / total_trades * 100) if total_trades > 0 else 0
    turnover = trades_df['Entry Price'].sum() + trades_df['Exit Price'].sum()
    taxes = total_trades * BROKERAGE_PER_TRADE * 2  # Entry + Exit per trade
    net_pnl = total_pnl - taxes
    
    metrics = {
        'Total Trades': total_trades,
        'Success Trades': len(success_trades),
        'Fail Trades': len(fail_trades),
        'Success Ratio (%)': round(success_ratio, 2),
        'Total Turnover': round(turnover, 2),
        'Total Taxes': round(taxes, 2),
        'Gross PnL': round(total_pnl, 2),
        'Net PnL': round(net_pnl, 2)
    }
    return metrics

def download_link(df):
    csv = df.to_csv(index=False)
    st.download_button("Download Trade Log as CSV", data=csv, file_name="paper_trades.csv", mime="text/csv")

def display_results(trades_df, metrics):
    st.subheader("📋 Trade Summary")
    st.dataframe(trades_df)
    st.subheader("📈 Performance Metrics")
    for key, value in metrics.items():
        st.write(f"**{key}:** {value}")
    download_link(trades_df)

# ---- Main App ----
def main():
    st.header("📊 Intraday ORB Strategy (Opening Range Breakout)")
    df = load_data()

    if df is not None:
        datetime_col = st.selectbox("Select your Datetime column", df.columns)
        df = convert_timezone(df, datetime_col)
        trades_df = run_paper_trading(df)
        metrics = calculate_metrics(trades_df)
        display_results(trades_df, metrics)

if __name__ == "__main__":
    main()
