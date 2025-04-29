import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Breakout Strategy ---
def breakout_strategy(data):
    data = data.copy()
    
    # Calculate High and Low rolling windows
    data['High_20'] = data['High'].rolling(window=20).max()
    data['Low_20'] = data['Low'].rolling(window=20).min()
    
    # Shift the high/low values by 1 for comparison
    high_shifted = data['High_20'].shift(1)
    low_shifted = data['Low_20'].shift(1)

    # Initialize 'Signal' column
    data['Signal'] = 0
    
    # Mask for long (buy) signals where Close > shifted High_20
    mask_long = (data['Close'] > high_shifted) & high_shifted.notna()
    
    # Mask for short (sell) signals where Close < shifted Low_20
    mask_short = (data['Close'] < low_shifted) & low_shifted.notna()
    
    # Apply the signals
    data.loc[mask_long, 'Signal'] = 1
    data.loc[mask_short, 'Signal'] = -1
    
    # Drop NaN values that may appear during the rolling window calculations
    data.dropna(subset=['Signal'], inplace=True)
    
    return data

# --- Backtest function ---
def backtest(data):
    data = data.copy()

    # Ensure 'Signal' column exists before backtesting
    if 'Signal' not in data.columns:
        raise ValueError("Signal column is missing. Please run a strategy first.")

    # Calculate Returns and Strategy columns
    data['Returns'] = data['Close'].pct_change()
    data['Strategy'] = data['Signal'].shift(1) * data['Returns']
    
    # Drop NaN values to avoid errors in calculations
    data.dropna(inplace=True)

    # Check if 'Strategy' column is created successfully
    if 'Strategy' not in data.columns:
        raise ValueError("Strategy column not found. Backtest failed.")
    
    return data['Strategy'].cumsum()

# --- Performance Summary ---
def performance_summary(data):
    # Ensure 'Strategy' column exists before calculating performance
    if 'Strategy' not in data.columns:
        return {"Error": "Strategy column not found. Please check if the backtest ran properly."}

    # Calculate total profit
    total_profit = data['Strategy'].iloc[-1]  # Cumulative return at the end
    
    # Number of trades
    trades = data[data['Signal'] != 0]
    num_trades = len(trades)
    
    # Win rate: percentage of positive trades
    win_rate = len(trades[trades['Strategy'] > 0]) / num_trades * 100 if num_trades > 0 else 0
    
    # Average return per trade
    avg_trade_return = data['Strategy'].pct_change().mean() * 100
    
    # Maximum drawdown
    running_max = data['Strategy'].cummax()
    drawdown = (data['Strategy'] - running_max).min()

    # Sharpe ratio
    risk_free_rate = 0.01  # Assuming a 1% risk-free rate
    excess_returns = data['Returns'] - risk_free_rate / 252  # Daily excess returns
    sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)  # Annualized Sharpe ratio

    return {
        "Total Profit": total_profit,
        "Number of Trades": num_trades,
        "Win Rate (%)": win_rate,
        "Average Return per Trade (%)": avg_trade_return,
        "Max Drawdown": drawdown,
        "Sharpe Ratio": sharpe_ratio
    }

# --- Streamlit UI ---
st.title("🏦 Backtest Trading Strategy")

# Sidebar: Upload CSV file
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

# Sidebar: Select strategy
selected_strategy = st.sidebar.selectbox(
    "Select a strategy to backtest",
    ["Breakout Strategy"]
)

if uploaded_file is not None:
    # Load the CSV file into a DataFrame
    data = pd.read_csv(uploaded_file)
    
    # Convert the 'Date' column to datetime format if it exists
    if 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'])
        data.set_index('Date', inplace=True)
    
    # Check if necessary columns are present
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required_columns):
        st.error(f"The CSV file must contain the following columns: {required_columns}")
    else:
        if selected_strategy == "Breakout Strategy":
            # Apply Breakout Strategy
            df = breakout_strategy(data)
            
            # Check if 'Signal' column was generated
            if 'Signal' not in df.columns:
                st.error("Signal column not found. Ensure the strategy logic is correct.")
            else:
                # Run Backtest
                try:
                    pnl = backtest(df)
                    
                    # Displaying results
                    st.subheader("Breakout Strategy - Cumulative Returns")
                    plt.figure(figsize=(10, 6))
                    plt.plot(pnl, label="Cumulative Returns", color='blue')
                    plt.title("Cumulative Returns of Breakout Strategy")
                    plt.xlabel("Date")
                    plt.ylabel("Cumulative Return")
                    plt.legend()
                    st.pyplot(plt.gcf())
                    plt.clf()

                    # Performance Summary
                    summary = performance_summary(df)
                    if "Error" in summary:
                        st.error(summary["Error"])
                    else:
                        st.subheader("Performance Summary")
                        summary_df = pd.DataFrame(list(summary.items()), columns=["Metric", "Value"])
                        st.table(summary_df)

                    # Trade Log
                    if 'Strategy' in df.columns:
                        st.subheader("Trade Log")
                        trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                        trade_log['Date'] = trade_log.index
                        trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                        st.write(trade_log)
                    else:
                        st.error("The strategy column was not generated correctly. Please check the backtest.")
                except Exception as e:
                    st.error(f"Backtest failed: {str(e)}")
else:
    st.error("Please upload a CSV file to proceed.")
