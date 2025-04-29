import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

def fibonacci_pullback(data):
    data = data.copy()
    data['Signal'] = 0
    for i in range(20, len(data)):
        high = data['High'][i-20:i].max()
        low = data['Low'][i-20:i].min()
        diff = high - low
        fib_61 = high - 0.618 * diff
        fib_50 = high - 0.5 * diff
        fib_38 = high - 0.382 * diff
        close = data['Close'].iloc[i]
        if np.isclose(close, [fib_38, fib_50, fib_61], atol=0.01).any():
            data.loc[data.index[i], 'Signal'] = 1
    data.dropna(inplace=True)
    return data

def rsi_strategy(data):
    data = data.copy()
    delta = data['Close'].diff()
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(window=14).mean()
    avg_loss = pd.Series(loss).rolling(window=14).mean()
    rs = avg_gain / avg_loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data['Signal'] = 0
    data.loc[data['RSI'] < 30, 'Signal'] = 1
    data.loc[data['RSI'] > 70, 'Signal'] = -1
    data.dropna(inplace=True)
    return data

def volume_price_action(data):
    data = data.copy()
    data['Volume_SMA'] = data['Volume'].rolling(window=20).mean()
    data['Signal'] = 0
    mask = (data['Volume'] > data['Volume_SMA']) & (data['Close'] > data['Open'])
    data.loc[mask, 'Signal'] = 1
    data.dropna(inplace=True)
    return data

def ichimoku_cloud(data):
    data = data.copy()
    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    tenkan_sen = (high_9 + low_9) / 2

    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    kijun_sen = (high_26 + low_26) / 2

    data['Signal'] = 0
    mask_long = (tenkan_sen > kijun_sen) & tenkan_sen.notna() & kijun_sen.notna()
    mask_short = (tenkan_sen < kijun_sen) & tenkan_sen.notna() & kijun_sen.notna()

    data.loc[mask_long, 'Signal'] = 1
    data.loc[mask_short, 'Signal'] = -1
    data.dropna(inplace=True)
    return data

def macd_strategy(data):
    data = data.copy()
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=9, adjust=False).mean()
    data['Signal'] = 0
    mask_long = (macd > signal_line) & macd.notna() & signal_line.notna()
    mask_short = (macd < signal_line) & macd.notna() & signal_line.notna()
    data.loc[mask_long, 'Signal'] = 1
    data.loc[mask_short, 'Signal'] = -1
    data.dropna(inplace=True)
    return data


# --- Streamlit UI ---
st.title("🏦 Backtest Trading Strategy")

# Sidebar: Upload CSV file
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])

# Sidebar: Select strategy
selected_strategy = st.sidebar.selectbox(
    "Select a strategy to backtest",
    ["Breakout Strategy", "Moving Average Strategy", "Fibonacci Pullback Strategy","RSI Strategy","Volume Price Strategy","MACD Strategy","Ichimoku Cloud Strategy"]
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
                    st.subheader("📊 Performance Summary")

                    # Calculate daily returns
                    df['Daily Return'] = df['Strategy'].pct_change()
                    df.dropna(inplace=True)
                    
                    # Metrics Calculation
                    total_profit = df['Strategy'].iloc[-1]
                    annualized_return = (df['Strategy'].iloc[-1] / df['Strategy'].iloc[0]) ** (252 / len(df)) - 1
                    volatility = df['Daily Return'].std() * (252 ** 0.5)
                    risk_free_rate = 0.03
                    
                    sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility != 0 else 0
                    downside_std = df[df['Daily Return'] < 0]['Daily Return'].std() * (252 ** 0.5)
                    sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std != 0 else 0
                    
                    cumulative = df['Strategy']
                    rolling_max = cumulative.cummax()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    max_drawdown = drawdown.min()
                    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
                    
                    trades = df[df['Signal'] != 0]
                    wins = trades[trades['Signal'] * trades['Daily Return'] > 0]
                    losses = trades[trades['Signal'] * trades['Daily Return'] <= 0]
                    num_trades = len(trades)
                    win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
                    profit_factor = wins['Daily Return'].sum() / abs(losses['Daily Return'].sum()) if len(losses) > 0 else float('inf')
                    expectancy = df['Daily Return'].mean() if num_trades > 0 else 0
                    avg_duration = (df['Signal'] != 0).sum() / num_trades if num_trades > 0 else 0
                    
                    # Create a summary dictionary
                    summary_metrics = {
                        "📈 Total Profit": [f"{total_profit:.2f}"],
                        "📅 Annualized Return (%)": [f"{annualized_return * 100:.2f}"],
                        "📊 Annualized Volatility": [f"{volatility:.2f}"],
                        "⚖️ Sharpe Ratio": [f"{sharpe_ratio:.2f}"],
                        "⚖️ Sortino Ratio": [f"{sortino_ratio:.2f}"],
                        "📉 Max Drawdown (%)": [f"{max_drawdown * 100:.2f}"],
                        "📏 Calmar Ratio": [f"{calmar_ratio:.2f}"],
                        "🔁 Number of Trades": [f"{num_trades}"],
                        "✅ Win Rate (%)": [f"{win_rate:.2f}"],
                        "📊 Profit Factor": [f"{profit_factor:.2f}"],
                        "📈 Expectancy per Trade": [f"{expectancy:.4f}"],
                        "⏱️ Avg. Trade Duration (days)": [f"{avg_duration:.2f}"]
                    }
                    
                    # Display as DataFrame
                    summary_df = pd.DataFrame.from_dict(summary_metrics, orient='columns')
                    st.dataframe(summary_df.T.rename(columns={0: "Value"}))


                    # Trade Log
                    st.subheader("Trade Log")
                    trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                    trade_log['Date'] = trade_log.index
                    trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                    st.write(trade_log)
                    # Download Button
                    csv = trade_log.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Trade Log as CSV",
                        data=csv,
                        file_name='trade_log.csv',
                        mime='text/csv',
                    )


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
                    #st.subheader("Performance Summary")
                    #st.write(f"Total Profit: {pnl[-1]:.2f}")
                    #st.write(f"Annualized Return: {pnl[-1] / len(df) * 252:.2f}%")
                    # Performance Summary
                    st.subheader("📊 Performance Summary")

                    # Calculate daily returns
                    df['Daily Return'] = df['Strategy'].pct_change()
                    df.dropna(inplace=True)
                    
                    # Metrics Calculation
                    total_profit = df['Strategy'].iloc[-1]
                    annualized_return = (df['Strategy'].iloc[-1] / df['Strategy'].iloc[0]) ** (252 / len(df)) - 1
                    volatility = df['Daily Return'].std() * (252 ** 0.5)
                    risk_free_rate = 0.03
                    
                    sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility != 0 else 0
                    downside_std = df[df['Daily Return'] < 0]['Daily Return'].std() * (252 ** 0.5)
                    sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std != 0 else 0
                    
                    cumulative = df['Strategy']
                    rolling_max = cumulative.cummax()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    max_drawdown = drawdown.min()
                    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
                    
                    trades = df[df['Signal'] != 0]
                    wins = trades[trades['Signal'] * trades['Daily Return'] > 0]
                    losses = trades[trades['Signal'] * trades['Daily Return'] <= 0]
                    num_trades = len(trades)
                    win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
                    profit_factor = wins['Daily Return'].sum() / abs(losses['Daily Return'].sum()) if len(losses) > 0 else float('inf')
                    expectancy = df['Daily Return'].mean() if num_trades > 0 else 0
                    avg_duration = (df['Signal'] != 0).sum() / num_trades if num_trades > 0 else 0
                    
                    # Create a summary dictionary
                    summary_metrics = {
                        "📈 Total Profit": [f"{total_profit:.2f}"],
                        "📅 Annualized Return (%)": [f"{annualized_return * 100:.2f}"],
                        "📊 Annualized Volatility": [f"{volatility:.2f}"],
                        "⚖️ Sharpe Ratio": [f"{sharpe_ratio:.2f}"],
                        "⚖️ Sortino Ratio": [f"{sortino_ratio:.2f}"],
                        "📉 Max Drawdown (%)": [f"{max_drawdown * 100:.2f}"],
                        "📏 Calmar Ratio": [f"{calmar_ratio:.2f}"],
                        "🔁 Number of Trades": [f"{num_trades}"],
                        "✅ Win Rate (%)": [f"{win_rate:.2f}"],
                        "📊 Profit Factor": [f"{profit_factor:.2f}"],
                        "📈 Expectancy per Trade": [f"{expectancy:.4f}"],
                        "⏱️ Avg. Trade Duration (days)": [f"{avg_duration:.2f}"]
                    }
                    
                    # Display as DataFrame
                    summary_df = pd.DataFrame.from_dict(summary_metrics, orient='columns')
                    st.dataframe(summary_df.T.rename(columns={0: "Value"}))


                    # Trade Log
                    st.subheader("Trade Log")
                    trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                    trade_log['Date'] = trade_log.index
                    trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                    st.write(trade_log)
                    # Download Button
                    csv = trade_log.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Trade Log as CSV",
                        data=csv,
                        file_name='trade_log.csv',
                        mime='text/csv',
                    )

                

                except Exception as e:
                    st.error(f"Backtest failed: {str(e)}")

        elif selected_strategy == "Fibonacci Pullback Strategy":
            # Apply Fibonacci Pullback Strategy
            df = fibonacci_pullback(data)
            
            # Check if 'Signal' column was generated
            if 'Signal' not in df.columns:
                st.error("Signal column not found. Ensure the strategy logic is correct.")
            else:
                try:
                    pnl = backtest(df)
        
                    # Cumulative Returns Plot
                    st.subheader("Fibonacci Pullback Strategy - Cumulative Returns")
                    plt.figure(figsize=(10, 6))
                    plt.plot(pnl, label="Cumulative Returns", color='purple')
                    plt.title("Cumulative Returns of Fibonacci Pullback Strategy")
                    plt.xlabel("Date")
                    plt.ylabel("Cumulative Return")
                    plt.legend()
                    st.pyplot(plt.gcf())
                    plt.clf()
        
                    # Performance Summary
                    st.subheader("📊 Performance Summary")
                    df['Daily Return'] = df['Strategy'].pct_change()
                    df.dropna(inplace=True)
        
                    total_profit = df['Strategy'].iloc[-1]
                    annualized_return = (df['Strategy'].iloc[-1] / df['Strategy'].iloc[0]) ** (252 / len(df)) - 1
                    volatility = df['Daily Return'].std() * (252 ** 0.5)
                    risk_free_rate = 0.03
                    sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility != 0 else 0
                    downside_std = df[df['Daily Return'] < 0]['Daily Return'].std() * (252 ** 0.5)
                    sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std != 0 else 0
                    cumulative = df['Strategy']
                    rolling_max = cumulative.cummax()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    max_drawdown = drawdown.min()
                    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
                    trades = df[df['Signal'] != 0]
                    wins = trades[trades['Signal'] * trades['Daily Return'] > 0]
                    losses = trades[trades['Signal'] * trades['Daily Return'] <= 0]
                    num_trades = len(trades)
                    win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
                    profit_factor = wins['Daily Return'].sum() / abs(losses['Daily Return'].sum()) if len(losses) > 0 else float('inf')
                    expectancy = df['Daily Return'].mean() if num_trades > 0 else 0
                    avg_duration = (df['Signal'] != 0).sum() / num_trades if num_trades > 0 else 0
        
                    summary_metrics = {
                        "📈 Total Profit": [f"{total_profit:.2f}"],
                        "📅 Annualized Return (%)": [f"{annualized_return * 100:.2f}"],
                        "📊 Annualized Volatility": [f"{volatility:.2f}"],
                        "⚖️ Sharpe Ratio": [f"{sharpe_ratio:.2f}"],
                        "⚖️ Sortino Ratio": [f"{sortino_ratio:.2f}"],
                        "📉 Max Drawdown (%)": [f"{max_drawdown * 100:.2f}"],
                        "📏 Calmar Ratio": [f"{calmar_ratio:.2f}"],
                        "🔁 Number of Trades": [f"{num_trades}"],
                        "✅ Win Rate (%)": [f"{win_rate:.2f}"],
                        "📊 Profit Factor": [f"{profit_factor:.2f}"],
                        "📈 Expectancy per Trade": [f"{expectancy:.4f}"],
                        "⏱️ Avg. Trade Duration (days)": [f"{avg_duration:.2f}"]
                    }
        
                    summary_df = pd.DataFrame.from_dict(summary_metrics, orient='columns')
                    st.dataframe(summary_df.T.rename(columns={0: "Value"}))
        
                    # Trade Log
                    st.subheader("Trade Log")
                    trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                    trade_log['Date'] = trade_log.index
                    trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                    st.write(trade_log)
        
                    # Download Button
                    csv = trade_log.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Trade Log as CSV",
                        data=csv,
                        file_name='fibonacci_trade_log.csv',
                        mime='text/csv',
                    )
        
                except Exception as e:
                    st.error(f"Backtest failed: {str(e)}")

        elif selected_strategy == "RSI Strategy":
            # Apply Fibonacci Pullback Strategy
            df = rsi_strategy(data)
            
            # Check if 'Signal' column was generated
            if 'Signal' not in df.columns:
                st.error("Signal column not found. Ensure the strategy logic is correct.")
            else:
                try:
                    pnl = backtest(df)
        
                    # Cumulative Returns Plot
                    st.subheader("RSI Strategy - Cumulative Returns")
                    plt.figure(figsize=(10, 6))
                    plt.plot(pnl, label="Cumulative Returns", color='purple')
                    plt.title("Cumulative Returns of Fibonacci Pullback Strategy")
                    plt.xlabel("Date")
                    plt.ylabel("Cumulative Return")
                    plt.legend()
                    st.pyplot(plt.gcf())
                    plt.clf()
        
                    # Performance Summary
                    st.subheader("📊 Performance Summary")
                    df['Daily Return'] = df['Strategy'].pct_change()
                    df.dropna(inplace=True)
        
                    total_profit = df['Strategy'].iloc[-1]
                    annualized_return = (df['Strategy'].iloc[-1] / df['Strategy'].iloc[0]) ** (252 / len(df)) - 1
                    volatility = df['Daily Return'].std() * (252 ** 0.5)
                    risk_free_rate = 0.03
                    sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility != 0 else 0
                    downside_std = df[df['Daily Return'] < 0]['Daily Return'].std() * (252 ** 0.5)
                    sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std != 0 else 0
                    cumulative = df['Strategy']
                    rolling_max = cumulative.cummax()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    max_drawdown = drawdown.min()
                    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
                    trades = df[df['Signal'] != 0]
                    wins = trades[trades['Signal'] * trades['Daily Return'] > 0]
                    losses = trades[trades['Signal'] * trades['Daily Return'] <= 0]
                    num_trades = len(trades)
                    win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
                    profit_factor = wins['Daily Return'].sum() / abs(losses['Daily Return'].sum()) if len(losses) > 0 else float('inf')
                    expectancy = df['Daily Return'].mean() if num_trades > 0 else 0
                    avg_duration = (df['Signal'] != 0).sum() / num_trades if num_trades > 0 else 0
        
                    summary_metrics = {
                        "📈 Total Profit": [f"{total_profit:.2f}"],
                        "📅 Annualized Return (%)": [f"{annualized_return * 100:.2f}"],
                        "📊 Annualized Volatility": [f"{volatility:.2f}"],
                        "⚖️ Sharpe Ratio": [f"{sharpe_ratio:.2f}"],
                        "⚖️ Sortino Ratio": [f"{sortino_ratio:.2f}"],
                        "📉 Max Drawdown (%)": [f"{max_drawdown * 100:.2f}"],
                        "📏 Calmar Ratio": [f"{calmar_ratio:.2f}"],
                        "🔁 Number of Trades": [f"{num_trades}"],
                        "✅ Win Rate (%)": [f"{win_rate:.2f}"],
                        "📊 Profit Factor": [f"{profit_factor:.2f}"],
                        "📈 Expectancy per Trade": [f"{expectancy:.4f}"],
                        "⏱️ Avg. Trade Duration (days)": [f"{avg_duration:.2f}"]
                    }
        
                    summary_df = pd.DataFrame.from_dict(summary_metrics, orient='columns')
                    st.dataframe(summary_df.T.rename(columns={0: "Value"}))
        
                    # Trade Log
                    st.subheader("Trade Log")
                    trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                    trade_log['Date'] = trade_log.index
                    trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                    st.write(trade_log)
        
                    # Download Button
                    csv = trade_log.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Trade Log as CSV",
                        data=csv,
                        file_name='fibonacci_trade_log.csv',
                        mime='text/csv',
                    )
        
                except Exception as e:
                    st.error(f"Backtest failed: {str(e)}")
                 
        elif selected_strategy == "Volume Price Strategy":
            # Apply Fibonacci Pullback Strategy
            df = volume_price_action(data)
            
            # Check if 'Signal' column was generated
            if 'Signal' not in df.columns:
                st.error("Signal column not found. Ensure the strategy logic is correct.")
            else:
                try:
                    pnl = backtest(df)
        
                    # Cumulative Returns Plot
                    st.subheader("Volume Price Strategy - Cumulative Returns")
                    plt.figure(figsize=(10, 6))
                    plt.plot(pnl, label="Cumulative Returns", color='purple')
                    plt.title("Cumulative Returns of Volume Price Strategy Strategy")
                    plt.xlabel("Date")
                    plt.ylabel("Cumulative Return")
                    plt.legend()
                    st.pyplot(plt.gcf())
                    plt.clf()
        
                    # Performance Summary
                    st.subheader("📊 Performance Summary")
                    df['Daily Return'] = df['Strategy'].pct_change()
                    df.dropna(inplace=True)
        
                    total_profit = df['Strategy'].iloc[-1]
                    annualized_return = (df['Strategy'].iloc[-1] / df['Strategy'].iloc[0]) ** (252 / len(df)) - 1
                    volatility = df['Daily Return'].std() * (252 ** 0.5)
                    risk_free_rate = 0.03
                    sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility != 0 else 0
                    downside_std = df[df['Daily Return'] < 0]['Daily Return'].std() * (252 ** 0.5)
                    sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std != 0 else 0
                    cumulative = df['Strategy']
                    rolling_max = cumulative.cummax()
                    drawdown = (cumulative - rolling_max) / rolling_max
                    max_drawdown = drawdown.min()
                    calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
                    trades = df[df['Signal'] != 0]
                    wins = trades[trades['Signal'] * trades['Daily Return'] > 0]
                    losses = trades[trades['Signal'] * trades['Daily Return'] <= 0]
                    num_trades = len(trades)
                    win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
                    profit_factor = wins['Daily Return'].sum() / abs(losses['Daily Return'].sum()) if len(losses) > 0 else float('inf')
                    expectancy = df['Daily Return'].mean() if num_trades > 0 else 0
                    avg_duration = (df['Signal'] != 0).sum() / num_trades if num_trades > 0 else 0
        
                    summary_metrics = {
                        "📈 Total Profit": [f"{total_profit:.2f}"],
                        "📅 Annualized Return (%)": [f"{annualized_return * 100:.2f}"],
                        "📊 Annualized Volatility": [f"{volatility:.2f}"],
                        "⚖️ Sharpe Ratio": [f"{sharpe_ratio:.2f}"],
                        "⚖️ Sortino Ratio": [f"{sortino_ratio:.2f}"],
                        "📉 Max Drawdown (%)": [f"{max_drawdown * 100:.2f}"],
                        "📏 Calmar Ratio": [f"{calmar_ratio:.2f}"],
                        "🔁 Number of Trades": [f"{num_trades}"],
                        "✅ Win Rate (%)": [f"{win_rate:.2f}"],
                        "📊 Profit Factor": [f"{profit_factor:.2f}"],
                        "📈 Expectancy per Trade": [f"{expectancy:.4f}"],
                        "⏱️ Avg. Trade Duration (days)": [f"{avg_duration:.2f}"]
                    }
        
                    summary_df = pd.DataFrame.from_dict(summary_metrics, orient='columns')
                    st.dataframe(summary_df.T.rename(columns={0: "Value"}))
        
                    # Trade Log
                    st.subheader("Trade Log")
                    trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                    trade_log['Date'] = trade_log.index
                    trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                    st.write(trade_log)
        
                    # Download Button
                    csv = trade_log.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Trade Log as CSV",
                        data=csv,
                        file_name='fibonacci_trade_log.csv',
                        mime='text/csv',
                    )
        
                except Exception as e:
                    st.error(f"Backtest failed: {str(e)}")

        
                    
        elif selected_strategy == "MACD Strategy":
             # Apply Fibonacci Pullback Strategy
             df = macd_strategy(data)
            
             # Check if 'Signal' column was generated
             if 'Signal' not in df.columns:
                st.error("Signal column not found. Ensure the strategy logic is correct.")
             else:
                 try:
                     pnl = backtest(df)
        
                     # Cumulative Returns Plot
                     st.subheader("MACD Strategy - Cumulative Returns")
                     plt.figure(figsize=(10, 6))
                     plt.plot(pnl, label="Cumulative Returns", color='purple')
                     plt.title("Cumulative Returns of MACD Strategy")
                     plt.xlabel("Date")
                     plt.ylabel("Cumulative Return")
                     plt.legend()
                     st.pyplot(plt.gcf())
                     plt.clf()
        
                     # Performance Summary
                     st.subheader("📊 Performance Summary")
                     df['Daily Return'] = df['Strategy'].pct_change()
                     df.dropna(inplace=True)
        
                     total_profit = df['Strategy'].iloc[-1]
                     annualized_return = (df['Strategy'].iloc[-1] / df['Strategy'].iloc[0]) ** (252 / len(df)) - 1
                     volatility = df['Daily Return'].std() * (252 ** 0.5)
                     risk_free_rate = 0.03
                     sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility != 0 else 0
                     downside_std = df[df['Daily Return'] < 0]['Daily Return'].std() * (252 ** 0.5)
                     sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std != 0 else 0
                     cumulative = df['Strategy']
                     rolling_max = cumulative.cummax()
                     drawdown = (cumulative - rolling_max) / rolling_max
                     max_drawdown = drawdown.min()
                     calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
                     trades = df[df['Signal'] != 0]
                     wins = trades[trades['Signal'] * trades['Daily Return'] > 0]
                     losses = trades[trades['Signal'] * trades['Daily Return'] <= 0]
                     num_trades = len(trades)
                     win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
                     profit_factor = wins['Daily Return'].sum() / abs(losses['Daily Return'].sum()) if len(losses) > 0 else float('inf')
                     expectancy = df['Daily Return'].mean() if num_trades > 0 else 0
                     avg_duration = (df['Signal'] != 0).sum() / num_trades if num_trades > 0 else 0
        
                     summary_metrics = {
                        "📈 Total Profit": [f"{total_profit:.2f}"],
                        "📅 Annualized Return (%)": [f"{annualized_return * 100:.2f}"],
                        "📊 Annualized Volatility": [f"{volatility:.2f}"],
                        "⚖️ Sharpe Ratio": [f"{sharpe_ratio:.2f}"],
                        "⚖️ Sortino Ratio": [f"{sortino_ratio:.2f}"],
                        "📉 Max Drawdown (%)": [f"{max_drawdown * 100:.2f}"],
                        "📏 Calmar Ratio": [f"{calmar_ratio:.2f}"],
                        "🔁 Number of Trades": [f"{num_trades}"],
                        "✅ Win Rate (%)": [f"{win_rate:.2f}"],
                        "📊 Profit Factor": [f"{profit_factor:.2f}"],
                        "📈 Expectancy per Trade": [f"{expectancy:.4f}"],
                        "⏱️ Avg. Trade Duration (days)": [f"{avg_duration:.2f}"]
                     }
        
                     summary_df = pd.DataFrame.from_dict(summary_metrics, orient='columns')
                     st.dataframe(summary_df.T.rename(columns={0: "Value"}))
        
                    # Trade Log
                     st.subheader("Trade Log")
                     trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                     trade_log['Date'] = trade_log.index
                     trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                     st.write(trade_log)
        
                    # Download Button
                     csv = trade_log.to_csv(index=False).encode('utf-8')
                     st.download_button(
                         label="📥 Download Trade Log as CSV",
                         data=csv,
                         file_name='fibonacci_trade_log.csv',
                         mime='text/csv',
                     )
        
                 except Exception as e:
                     st.error(f"Backtest failed: {str(e)}")

        elif selected_strategy == "Ichimoku Cloud Strategy":
             # Apply Fibonacci Pullback Strategy
             df = ichimoku_cloud(data)
            
             # Check if 'Signal' column was generated
             if 'Signal' not in df.columns:
                st.error("Signal column not found. Ensure the strategy logic is correct.")
             else:
                 try:
                     pnl = backtest(df)
        
                     # Cumulative Returns Plot
                     st.subheader("Ichimoku Cloud Strategy - Cumulative Returns")
                     plt.figure(figsize=(10, 6))
                     plt.plot(pnl, label="Cumulative Returns", color='purple')
                     plt.title("Cumulative Returns of Ichimoku Cloud Strategy")
                     plt.xlabel("Date")
                     plt.ylabel("Cumulative Return")
                     plt.legend()
                     st.pyplot(plt.gcf())
                     plt.clf()
        
                     # Performance Summary
                     st.subheader("📊 Performance Summary")
                     df['Daily Return'] = df['Strategy'].pct_change()
                     df.dropna(inplace=True)
        
                     total_profit = df['Strategy'].iloc[-1]
                     annualized_return = (df['Strategy'].iloc[-1] / df['Strategy'].iloc[0]) ** (252 / len(df)) - 1
                     volatility = df['Daily Return'].std() * (252 ** 0.5)
                     risk_free_rate = 0.03
                     sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility != 0 else 0
                     downside_std = df[df['Daily Return'] < 0]['Daily Return'].std() * (252 ** 0.5)
                     sortino_ratio = (annualized_return - risk_free_rate) / downside_std if downside_std != 0 else 0
                     cumulative = df['Strategy']
                     rolling_max = cumulative.cummax()
                     drawdown = (cumulative - rolling_max) / rolling_max
                     max_drawdown = drawdown.min()
                     calmar_ratio = annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
                     trades = df[df['Signal'] != 0]
                     wins = trades[trades['Signal'] * trades['Daily Return'] > 0]
                     losses = trades[trades['Signal'] * trades['Daily Return'] <= 0]
                     num_trades = len(trades)
                     win_rate = len(wins) / num_trades * 100 if num_trades > 0 else 0
                     profit_factor = wins['Daily Return'].sum() / abs(losses['Daily Return'].sum()) if len(losses) > 0 else float('inf')
                     expectancy = df['Daily Return'].mean() if num_trades > 0 else 0
                     avg_duration = (df['Signal'] != 0).sum() / num_trades if num_trades > 0 else 0
        
                     summary_metrics = {
                        "📈 Total Profit": [f"{total_profit:.2f}"],
                        "📅 Annualized Return (%)": [f"{annualized_return * 100:.2f}"],
                        "📊 Annualized Volatility": [f"{volatility:.2f}"],
                        "⚖️ Sharpe Ratio": [f"{sharpe_ratio:.2f}"],
                        "⚖️ Sortino Ratio": [f"{sortino_ratio:.2f}"],
                        "📉 Max Drawdown (%)": [f"{max_drawdown * 100:.2f}"],
                        "📏 Calmar Ratio": [f"{calmar_ratio:.2f}"],
                        "🔁 Number of Trades": [f"{num_trades}"],
                        "✅ Win Rate (%)": [f"{win_rate:.2f}"],
                        "📊 Profit Factor": [f"{profit_factor:.2f}"],
                        "📈 Expectancy per Trade": [f"{expectancy:.4f}"],
                        "⏱️ Avg. Trade Duration (days)": [f"{avg_duration:.2f}"]
                     }
        
                     summary_df = pd.DataFrame.from_dict(summary_metrics, orient='columns')
                     st.dataframe(summary_df.T.rename(columns={0: "Value"}))
        
                    # Trade Log
                     st.subheader("Trade Log")
                     trade_log = df[df['Signal'] != 0][['Signal', 'Close', 'Strategy']]
                     trade_log['Date'] = trade_log.index
                     trade_log = trade_log[['Date', 'Signal', 'Close', 'Strategy']]
                     st.write(trade_log)
        
                    # Download Button
                     csv = trade_log.to_csv(index=False).encode('utf-8')
                     st.download_button(
                         label="📥 Download Trade Log as CSV",
                         data=csv,
                         file_name='fibonacci_trade_log.csv',
                         mime='text/csv',
                     )
        
                 except Exception as e:
                     st.error(f"Backtest failed: {str(e)}")                   
                  

     

else:
    st.error("Please upload a CSV file to proceed.")
