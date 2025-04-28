import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ---------- Define Strategy Functions ----------

def calculate_performance(trades, brokerage_per_trade=20):
    total_trades = len(trades)
    winning_trades = trades[trades['Profit'] > 0].shape[0]
    losing_trades = trades[trades['Profit'] <= 0].shape[0]
    gross_profit = trades['Profit'].sum()
    total_turnover = trades['Entry_Price'].sum() + trades['Exit_Price'].sum()
    total_brokerage = total_trades * brokerage_per_trade  # Assuming 20 Rs per trade
    risk_to_reward = (gross_profit / abs(trades['Profit'][trades['Profit'] < 0].sum())) if losing_trades > 0 else np.nan

    return {
        "Total Trades": total_trades,
        "Winning Trades": winning_trades,
        "Losing Trades": losing_trades,
        "Gross Profit": gross_profit,
        "Total Turnover": total_turnover,
        "Total Brokerage": total_brokerage,
        "Risk to Reward Ratio": risk_to_reward
    }
    
def strategy_moving_average(df):
    df = df.copy()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['Signal'] = np.where(df['Close'] > df['SMA20'], 1, -1)
    df['Position'] = df['Signal'].shift(1)  # Lag signal for execution

    # Create Trade Log
    trades = []
    position = 0
    entry_price = 0

    for index, row in df.iterrows():
        if row['Position'] == 1 and position == 0:
            entry_price = row['Close']
            entry_date = index
            position = 1
        elif row['Position'] == -1 and position == 1:
            exit_price = row['Close']
            exit_date = index
            profit = exit_price - entry_price
            trades.append({
                "Entry_Date": entry_date,
                "Entry_Price": entry_price,
                "Exit_Date": exit_date,
                "Exit_Price": exit_price,
                "Profit": profit
            })
            position = 0

    trade_log = pd.DataFrame(trades)

    # Strategy Cumulative Returns
    df['Strategy_Return'] = df['Position'] * df['Close'].pct_change()
    cumulative_returns = df['Strategy_Return'].cumsum()

    # Performance Summary
    performance = calculate_performance(trade_log)

    return df, cumulative_returns, trade_log, performance

# Strategy 2: RSI
def strategy_rsi(df, lower=30, upper=70):
    df = df.copy()
    delta = df['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['Signal'] = np.where(df['RSI'] < lower, 1, np.where(df['RSI'] > upper, -1, 0))
    df['Position'] = df['Signal'].shift(1)

    trades = []
    position = 0
    entry_price = 0

    for index, row in df.iterrows():
        if row['Position'] == 1 and position == 0:
            entry_price = row['Close']
            entry_date = index
            position = 1
        elif row['Position'] == -1 and position == 1:
            exit_price = row['Close']
            exit_date = index
            profit = exit_price - entry_price
            trades.append({
                "Entry_Date": entry_date,
                "Entry_Price": entry_price,
                "Exit_Date": exit_date,
                "Exit_Price": exit_price,
                "Profit": profit
            })
            position = 0

    trade_log = pd.DataFrame(trades)
    df['Strategy_Return'] = df['Position'] * df['Close'].pct_change()
    cumulative_returns = df['Strategy_Return'].cumsum()
    performance = calculate_performance(trade_log)

    return df, cumulative_returns, trade_log, performance

# Strategy 3: Bollinger Bands
def strategy_bollinger_bands(df):
    df = df.copy()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['UpperBand'] = df['SMA20'] + (df['STD20'] * 2)
    df['LowerBand'] = df['SMA20'] - (df['STD20'] * 2)

    df['Signal'] = np.where(df['Close'] < df['LowerBand'], 1, np.where(df['Close'] > df['UpperBand'], -1, 0))
    df['Position'] = df['Signal'].shift(1)

    trades = []
    position = 0
    entry_price = 0

    for index, row in df.iterrows():
        if row['Position'] == 1 and position == 0:
            entry_price = row['Close']
            entry_date = index
            position = 1
        elif row['Position'] == -1 and position == 1:
            exit_price = row['Close']
            exit_date = index
            profit = exit_price - entry_price
            trades.append({
                "Entry_Date": entry_date,
                "Entry_Price": entry_price,
                "Exit_Date": exit_date,
                "Exit_Price": exit_price,
                "Profit": profit
            })
            position = 0

    trade_log = pd.DataFrame(trades)
    df['Strategy_Return'] = df['Position'] * df['Close'].pct_change()
    cumulative_returns = df['Strategy_Return'].cumsum()
    performance = calculate_performance(trade_log)

    return df, cumulative_returns, trade_log, performance

# Streamlit App
st.title("📈 Trading Strategy Dashboard")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, index_col='Date', parse_dates=True)
    st.success("File Uploaded Successfully!")
    
    tab1, tab2, tab3 = st.tabs(["Moving Average", "RSI", "Bollinger Bands"])

    with tab1:
        st.header("Strategy 1: Moving Average Crossover")
        if st.button("Run Moving Average Strategy"):
            strat1_df, strat1_cumsum, strat1_trades, strat1_performance = strategy_moving_average(df)
            st.line_chart(strat1_cumsum)

            st.subheader("🔍 Trade Log")
            st.dataframe(strat1_trades)

            st.subheader("📈 Performance Summary")
            for k, v in strat1_performance.items():
                st.write(f"**{k}:** {round(v, 2)}")

    with tab2:
        st.header("Strategy 2: RSI Strategy")
        if st.button("Run RSI Strategy"):
            strat2_df, strat2_cumsum, strat2_trades, strat2_performance = strategy_rsi(df)
            st.line_chart(strat2_cumsum)

            st.subheader("🔍 Trade Log")
            st.dataframe(strat2_trades)

            st.subheader("📈 Performance Summary")
            for k, v in strat2_performance.items():
                st.write(f"**{k}:** {round(v, 2)}")

    with tab3:
        st.header("Strategy 3: Bollinger Bands")
        if st.button("Run Bollinger Bands Strategy"):
            strat3_df, strat3_cumsum, strat3_trades, strat3_performance = strategy_bollinger_bands(df)
            st.line_chart(strat3_cumsum)

            st.subheader("🔍 Trade Log")
            st.dataframe(strat3_trades)

            st.subheader("📈 Performance Summary")
            for k, v in strat3_performance.items():
                st.write(f"**{k}:** {round(v, 2)}")

# ---- Compare All Strategies ----
    with tab4:
        st.header("📊 Compare All Strategies")
        if st.button("Compare Strategies"):
            strat1_df, strat1_cumsum = strategy_moving_average(df)
            strat2_df, strat2_cumsum = strategy_rsi(df)
            strat3_df, strat3_cumsum = strategy_bollinger_bands(df)

            # Plot all strategies together
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(strat1_cumsum, label='Moving Average')
            ax.plot(strat2_cumsum, label='RSI Strategy')
            ax.plot(strat3_cumsum, label='Bollinger Bands')
            ax.set_title('Strategy Cumulative Returns Comparison')
            ax.legend()
            st.pyplot(fig)

            # Show Final Returns
            final_returns = {
                "Strategy": ["Moving Average", "RSI", "Bollinger Bands"],
                "Final Return (%)": [
                    strat1_cumsum.iloc[-1] * 100,
                    strat2_cumsum.iloc[-1] * 100,
                    strat3_cumsum.iloc[-1] * 100
                ]
            }
            final_returns_df = pd.DataFrame(final_returns)
            st.dataframe(final_returns_df)

    # ---- Show Raw Data ----
    with tab5:
        st.header("Raw Uploaded Data")
        st.dataframe(df)

else:
    st.warning("👆 Please upload a CSV file to start.")
