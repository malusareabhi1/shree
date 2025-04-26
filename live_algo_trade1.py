import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# ---- Config ----
CAPITAL = 100000
RISK_PER_TRADE = 0.05
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

import ta

def run_paper_trading2(df):
    position_size = CAPITAL * RISK_PER_TRADE
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
                target = entry_price + 1.5 * risk
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
                target = entry_price - 1.5 * risk
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
                    pnl = (exit_price - last_trade['Entry Price']) * (position_size / last_trade['Entry Price'])
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
                    pnl = (exit_price - last_trade['Entry Price']) * (position_size / last_trade['Entry Price'])
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
                    pnl = (last_trade['Entry Price'] - exit_price) * (position_size / last_trade['Entry Price'])
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
                    pnl = (last_trade['Entry Price'] - exit_price) * (position_size / last_trade['Entry Price'])
                    last_trade.update({
                        'Exit Time': exit_time,
                        'Exit Price': exit_price,
                        'PnL': round(pnl, 2),
                        'Exit Reason': 'Target Hit'
                    })
                    in_position = False

    return pd.DataFrame(trades)


def run_paper_trading1(df):
    # 1) Precompute Indicators
    df['ATR14'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)
    df['VolAvg10'] = df['Volume'].rolling(10).mean()

    # 2) Compute Daily Trend via 50-EMA on daily closes
    df_daily = df.resample('1D').last()
    df_daily['EMA50'] = df_daily['Close'].ewm(span=50).mean()

    # 3) Extract date only for grouping
    df['DateOnly'] = df.index.date

    # 4) Opening Range (9:15–9:30) highs/lows per day
    or_df = (
        df.between_time('09:15','09:30')
          .groupby('DateOnly')
          .agg(or_high=('High','max'), or_low=('Low','min'))
    )

    position_size = CAPITAL * RISK_PER_TRADE
    trades = []

    # 5) Loop day by day
    for day, day_data in df.groupby('DateOnly'):
        # Skip if no OR
        if day not in or_df.index:
            continue
        or_high, or_low = or_df.loc[day,['or_high','or_low']]
        # ATR filter: skip narrow opening ranges
        if (or_high - or_low) < 0.5 * day_data['ATR14'].iloc[-1]:
            continue
        # Trend filter
        ts = pd.Timestamp(day)
        if ts not in df_daily.index:
            continue
        up_trend = df_daily.at[ts,'Close'] > df_daily.at[ts,'EMA50']

        in_position = False
        entry_price = entry_time = None

        # 6) Scan for breakouts AFTER 9:30
        for idx in day_data.between_time('09:31','15:30').index:
            row = day_data.loc[idx]
            prev = day_data.loc[:idx].iloc[-2]

            # Volume + Buffer
            buffer = or_high * 0.001  # 0.1%
            strong_break = row['High'] > or_high + buffer
            vol_ok = row['Volume'] > 1.2 * day_data.at[idx,'VolAvg10']

            # ENTRY
            if not in_position and up_trend and strong_break and vol_ok:
                in_position = True
                entry_price = row['Open']
                entry_time = idx
                trades.append({
                    'Type':'BUY','Entry Time':entry_time,'Entry Price':entry_price
                })

            # EXIT: simple opposite OR breakdown
            elif in_position and row['Low'] < or_low - buffer:
                exit_price = row['Open']
                exit_time = idx
                pnl = (exit_price - entry_price) * (position_size / entry_price)
                trades[-1].update({
                    'Exit Time': exit_time,
                    'Exit Price': exit_price,
                    'PnL': round(pnl,2)
                })
                in_position = False
                break

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

def calculate_metrics1(trades_df):
    if trades_df.empty or 'PnL' not in trades_df.columns:
        return {
            'Total PnL': 0,
            'Number of Trades': 0,
            'Success Ratio (%)': 0,
            'Average PnL per Trade': 0
        }

    total_pnl = trades_df['PnL'].sum()
    number_of_trades = len(trades_df)
    success_trades = trades_df[trades_df['PnL'] > 0]
    success_ratio = (len(success_trades) / number_of_trades) * 100
    avg_pnl_per_trade = trades_df['PnL'].mean()

    return {
        'Total PnL': round(total_pnl, 2),
        'Number of Trades': number_of_trades,
        'Success Ratio (%)': round(success_ratio, 2),
        'Average PnL per Trade': round(avg_pnl_per_trade, 2)
    }

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
        trades_df = run_paper_trading2(df)
        metrics = calculate_metrics1(trades_df)
        display_results(trades_df, metrics)

if __name__ == "__main__":
    main()
