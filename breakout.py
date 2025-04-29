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
    data['Returns'] = data['Close'].pct_change()
    data['Strategy'] = data['Signal'].shift(1) * data['Returns']
    data.dropna(inplace=True)
    return data['Strategy'].cumsum()

# --- Streamlit UI ---
st.title("🏦 Breakout Strategy Backtest")

# Sidebar for CSV file upload
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

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
        # Sidebar for start and end date filter
        start_date = st.sidebar.date_input("Start Date", data.index.min().date())
        end_date = st.sidebar.date_input("End Date", data.index.max().date())
        
        # Filter data based on the selected date range
        filtered_data = data.loc[start_date:end_date]
        
        if filtered_data.empty:
            st.error("No data available for the selected date range.")
        else:
            # Apply Breakout Strategy
            df = breakout_strategy(filtered_data)
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
else:
    st.error("Please upload a CSV file to proceed.")
