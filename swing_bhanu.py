import yfinance as yf
import pandas as pd
import streamlit as st
def scan_bhanushali_strategy(stock):
    # Download historical stock data
    df = yf.download(stock, period='90d', interval='1d')
    if df.empty:
        return None  # Skip if no data returned

    # Calculate the 44-period SMA
    df['SMA44'] = df['Close'].rolling(window=44).mean()

    # Drop rows with NaN values (if any)
    df.dropna(inplace=True)

    if len(df) < 2:
        return None  # Not enough data

    last_candle = df.iloc[-1]  # Get the most recent candle (row)
    prev_candle = df.iloc[-2]  # Get the previous candle (row)

    # Ensure you're working with scalar values
    low = last_candle['Low']
    close = last_candle['Close']
    sma44 = last_candle['SMA44']

    # Ensure values are scalar (individual numbers)
    if isinstance(low, pd.Series): low = low.values[0]
    if isinstance(close, pd.Series): close = close.values[0]
    if isinstance(sma44, pd.Series): sma44 = sma44.values[0]

    # Condition: low < SMA44 < close (candle near rising 44 SMA)
    if low < sma44 < close:
        # Buy above the high of the candle, stoploss below the low of the candle
        #entry = last_candle['High']
        #stoploss = low
        entry = float(last_candle['High'])       # entry as scalar
        stoploss = float(last_candle['Low'])     # stoploss as scalar


        # Calculate targets based on a 1:2 and 1:3 risk-reward ratio
        target1 = entry + (entry - stoploss) * 2
        target2 = entry + (entry - stoploss) * 3

        # Return a dictionary with the results
        return {
            'symbol': stock,
            'entry': round(entry, 2),
            'stoploss': round(stoploss, 2),
            'target_1_2': round(target1, 2),
            'target_1_3': round(target2, 2)
        }

    return None

# Example usage with a list of NIFTY 100 stocks
nifty_100 = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
    'KOTAKBANK.NS', 'ITC.NS', 'LT.NS', 'SBIN.NS', 'BHARTIARTL.NS',
    'ASIANPAINT.NS', 'HINDUNILVR.NS', 'BAJFINANCE.NS', 'AXISBANK.NS', 'HCLTECH.NS',
    'MARUTI.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'WIPRO.NS', 'ULTRACEMCO.NS',
    'NTPC.NS', 'POWERGRID.NS', 'NESTLEIND.NS', 'TECHM.NS', 'BAJAJFINSV.NS'
    
    
]

# Scan and collect results
results = []
for stock in nifty_100:
    try:
        res = scan_bhanushali_strategy(stock)
        if res:
            results.append(res)
    except Exception as e:
        st.write(f"Error with {stock}: {e}")

# Create a DataFrame to display the results in table format


# Display results
if results:
    df_results = pd.DataFrame(results)
    st.dataframe(df_results)
    st.write(df_results)

    # Selection box
    selected_stock = st.selectbox("Select a stock to view chart:", df_results['symbol'].tolist())

    # If a stock is selected, fetch its data and plot chart
    if selected_stock:
        stock_data = yf.download(selected_stock, period='60d', interval='1d')
        stock_data.reset_index(inplace=True)

        # Get entry/SL/target from result
        selected_row = df_results[df_results['symbol'] == selected_stock].iloc[0]
        entry = selected_row['entry']
        stoploss = selected_row['stoploss']
        target1 = selected_row['target_1_2']
        target2 = selected_row['target_1_3']

        # Create candlestick chart
        fig = go.Figure(data=[
            go.Candlestick(
                x=stock_data['Date'],
                open=stock_data['Open'],
                high=stock_data['High'],
                low=stock_data['Low'],
                close=stock_data['Close'],
                name='Candles'
            ),
            go.Scatter(x=stock_data['Date'], y=[entry]*len(stock_data), mode='lines', name='Entry', line=dict(color='blue', dash='dash')),
            go.Scatter(x=stock_data['Date'], y=[stoploss]*len(stock_data), mode='lines', name='Stoploss', line=dict(color='red', dash='dash')),
            go.Scatter(x=stock_data['Date'], y=[target1]*len(stock_data), mode='lines', name='Target 1:2', line=dict(color='green', dash='dot')),
            go.Scatter(x=stock_data['Date'], y=[target2]*len(stock_data), mode='lines', name='Target 1:3', line=dict(color='darkgreen', dash='dot'))
        ])

        fig.update_layout(title=f"{selected_stock} Chart with Entry, SL & Targets", xaxis_title="Date", yaxis_title="Price", height=600)
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("No stocks meet the strategy criteria.")







