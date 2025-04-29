import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Function for Breakout Strategy ---
def breakout_strategy(data):
    data['High_20'] = data['High'].rolling(window=20).max()
    data['Low_20'] = data['Low'].rolling(window=20).min()
    data['Signal'] = 0
    high_shifted = data['High_20'].shift(1)
    low_shifted = data['Low_20'].shift(1)
    
    # Long signal: close price breaks above the previous 20-day high
    mask_long = (data['Close'] > high_shifted) & high_shifted.notna()
    # Short signal: close price breaks below the previous 20-day low
    mask_short = (data['Close'] < low_shifted) & low_shifted.notna()
    
    data.loc[mask_long, 'Signal'] = 1
    data.loc[mask_short, 'Signal'] = -1
    data.dropna(inplace=True)
    
    return data

# --- Function for Moving Average Crossover ---
def moving_average_crossover(data):
    data['SMA_9'] = data['Close'].rolling(window=9).mean()
    data['SMA_21'] = data['Close'].rolling(window=21).mean()
    data['Signal'] = 0
    data.loc[data['SMA_9'] > data['SMA_21'], 'Signal'] = 1
    data.loc[data['SMA_9'] < data['SMA_21'], 'Signal'] = -1
    data.dropna(inplace=True)
    return data

# --- Backtest function ---
def backtest(data):
    data['Returns'] = data['Close'].pct_change()
    data['Strategy'] = data['Signal'].shift(1) * data['Returns']
    data.dropna(subset=['Strategy'], inplace=True)
    return data['Strategy'].cumsum()

# --- Streamlit UI ---
st.title("🏦 Backtest Trading Strategy")

# Sidebar: Upload CSV file
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

# Sidebar: Select strategy
selected_strategy = st.sidebar.selectbox(
    "Select a strategy to backtest",
    ["Breakout Strategy", "Moving Average Strategy"]
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
                    st.subheader("Performance Summary")
                    st.write(f"Total Profit: {pnl[-1]:.2f}")
                    st.write(f"Annualized Return: {pnl[-1] / len(df) * 252:.2f}%")

                    # Trade Log
                    st.subheader("Trade Log")
                    trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                    trade_log['Date'] = trade_log.index
                    trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                    st.write(trade_log)

                except Exception as e:
                    st.error(f"Backtest failed: {str(e)}")
                    
        elif selected_strategy == "Moving Average Strategy":
            # Apply Moving Average Crossover Strategy
            df = moving_average_crossover(data)
            
            # Check if 'Signal' column was generated
            if 'Signal' not in df.columns:
                st.error("Signal column not found. Ensure the strategy logic is correct.")
            else:
                # Run Backtest
                try:
                    pnl = backtest(df)
                    
                    # Displaying results
                    st.subheader("Moving Average Strategy - Cumulative Returns")
                    plt.figure(figsize=(10, 6))
                    plt.plot(pnl, label="Cumulative Returns", color='blue')
                    plt.title("Cumulative Returns of Moving Average Strategy")
                    plt.xlabel("Date")
                    plt.ylabel("Cumulative Return")
                    plt.legend()
                    st.pyplot(plt.gcf())
                    plt.clf()

                    # Performance Summary
                    st.subheader("Performance Summary")
                    st.write(f"Total Profit: {pnl[-1]:.2f}")
                    st.write(f"Annualized Return: {pnl[-1] / len(df) * 252:.2f}%")

                    # Trade Log
                    st.subheader("Trade Log")
                    trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                    trade_log['Date'] = trade_log.index
                    trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                    st.write(trade_log)

                except Exception as e:
                    st.error(f"Backtest failed: {str(e)}")

else:
    st.error("Please upload a CSV file to proceed.")
