import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("📈 44-MA Strategy Tester (Live & CSV)")

# Sidebar input
data_source = st.sidebar.radio("Select Data Source", ["Live (yFinance)", "CSV Upload"])

# Function to calculate 44 MA strategy
def apply_strategy(df):
    # Ensure 'Close' and 'Date' exist
    required_cols = ['Close']
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Missing column: {col}. Please upload a CSV with a '{col}' column.")
            st.stop()

    df["MA44"] = df["Close"].rolling(window=44).mean()
    df["Buy"] = (df["Close"] > df["MA44"]) & (df["Close"].shift(1) <= df["MA44"].shift(1))
    df["Sell"] = (df["Close"] < df["MA44"]) & (df["Close"].shift(1) >= df["MA44"].shift(1))
    return df


# Load live data
if data_source == "Live (yFinance)":
    #import datetime
    #from datetime import datetime, timedelta
    nifty_50_stocks = ["^NSEI","^NIFTYBANK","^BSEI","TCS.NS","ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE",
        "BAJAJFINSV", "BPCL", "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY",
        "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR",
        "ICICIBANK", "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT", "M&M", "MARUTI", "NTPC",
        "NESTLEIND", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SUNPHARMA", "TCS", "TATACONSUM",
        "TATAMOTORS", "TATASTEEL", "TECHM", "TITAN", "UPL", "ULTRACEMCO", "WIPRO","YESBANK",# Additional Large/Mid Cap Stocks
    "ABB", "ADANIGREEN", "ADANIPOWER", "AMBUJACEM", "AUROPHARMA", "BANDHANBNK", "BANKBARODA", 
    "BERGEPAINT", "BHEL", "BIOCON", "BOSCHLTD", "CANBK", "CHOLAFIN", "COLPAL", 
    "DLF", "DABUR", "ESCORTS", "GAIL", "GODREJCP", "HAL", "HAVELLS", "ICICIPRULI", 
    "IDFCFIRSTB", "INDIGO", "L&TFH", "LICI", "MUTHOOTFIN", "NAUKRI", "PAGEIND", 
    "PEL", "PIDILITIND", "PNB", "RECLTD", "SAIL", "SHREECEM", "SRF", "SIEMENS", 
    "TATACHEM", "TRENT", "TVSMOTOR", "TORNTPHARM", "UBL", "VOLTAS", "ZYDUSLIFE", 
    "IRCTC", "INDIACEM", "IOC", "MPHASIS", "COFORGE", "CROMPTON","IDEA",# Nifty Next 50 and other liquid stocks
    "ABB", "ADANIGREEN", "ADANIPOWER", "AMBUJACEM", "AUROPHARMA", "BANDHANBNK",
    "BANKBARODA", "BERGEPAINT", "BHEL", "BIOCON", "BOSCHLTD", "CANBK", "CHOLAFIN",
    "COLPAL", "DABUR", "DLF", "ESCORTS", "GAIL", "GODREJCP", "HAVELLS", "HAL",
    "ICICIGI", "ICICIPRULI", "IDFCFIRSTB", "INDIGO", "IRCTC", "JSPL", "LICI", "MCDOWELL-N",
    "MPHASIS", "MUTHOOTFIN", "NAUKRI", "PAGEIND", "PEL", "PIDILITIND", "PNB", "RECLTD",
    "SAIL", "SHREECEM", "SIEMENS", "SRF", "TATACHEM", "TORNTPHARM", "TRENT", "TVSMOTOR",
    "UBL", "VOLTAS", "ZYDUSLIFE", "COFORGE", "CROMPTON", "AARTIIND", "ABFRL", "ACC",
    "ALOKINDS", "AMARAJABAT", "ASTRAL", "BALRAMCHIN", "BEL", "BEML", "CAMLINFINE",
    "CENTURYTEX", "CONCOR", "COROMANDEL", "DEEPAKNTR", "EIDPARRY", "EXIDEIND", "FEDERALBNK",
    "FINCABLES", "FORTIS", "GLENMARK", "GRINDWELL", "GUJGASLTD", "HEG", "IDBI",
    "IIFL", "INDHOTEL", "INDIAMART", "IRFC", "JINDALSTEL", "JUBLFOOD", "KAJARIACER",
    "LALPATHLAB", "LTI", "LTTS", "MAHLOG", "MANAPPURAM", "MCX", "METROPOLIS", "NATIONALUM",
    "NHPC", "NMDC", "OBEROIRLTY", "PFC", "POLYCAB", "RADICO", "RAJESHEXPO", "RAMCOCEM",
    "RBLBANK", "SANOFI", "SCHAEFFLER", "SUPREMEIND", "SUNTV", "SYNGENE", "TATACOMM",
    "THERMAX", "UNIONBANK", "UJJIVANSFB", "VINATIORGA", "WHIRLPOOL", "YESBANK"
    ]
    st.sidebar.title("📊 TradingView-style Stock Dashboard")
    #symbol = st.selectbox("Select NIFTY 50 stock or Index (^NSEI)", options=nifty_50_stocks, index=nifty_50_stocks.index("TCS.NS"))
    selected_stock = st.selectbox("Select a NIFTY 50 Stock", sorted(nifty_50_stocks))
    # Handle the symbol based on selection
    #if selected_symbol in nifty_50_stocks:
    symbol = selected_stock  + ".NS"  # For NIFTY 50 stocks, append ".NS"
    #else:
    #symbol = selected_symbol  # For indices, don't append anything
    #symbol = selected_stock + ".NS"
    start_date = st.date_input("From Date", datetime(2025, 1, 1))
    end_date = st.date_input("To Date", datetime.today())
    interval = st.selectbox("Select Interval", ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"], index=5)
    
    
    def plot_candles_with_sma(df):
        df['20-SMA'] = df['Close'].rolling(window=20).mean()
        fig = go.Figure(data=[go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Candlesticks"
        )])
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['20-SMA'],
            mode='lines',
            name='20-SMA',
            line=dict(color='orange', width=2)
        ))
        fig.update_layout(
            title=f"{symbol} 5‑Minute Candles with 20-SMA (Today)",
            xaxis_title="Time",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False
        )
        return fig
    
    # Fetch data
    #df = yf.download(symbol, start=start_date, end=end_date)
    df = yf.download(symbol, start=start_date, end=end_date, interval=interval)
    # Flatten MultiIndex columns (e.g., ('Open', 'BHARTIARTL.NS') → 'Open')
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    
    if df.empty:
        st.error("No data found. Please check symbol or date.")
        st.stop()
    
    #st.write(df.head())
    # Technical Indicators
    df['20_SMA'] = df['Close'].rolling(window=20).mean()
    df['BB_std'] = df['Close'].rolling(window=20).std()
    df['BB_upper'] = df['20_SMA'] + 2 * df['BB_std']
    df['BB_lower'] = df['20_SMA'] - 2 * df['BB_std']
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Drop NaNs from indicators
    df.dropna(inplace=True)
    
    # Plot Candlestick with Bollinger Bands
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        name='Candlestick'
    ))
    fig.add_trace(go.Scatter(x=df.index, y=df['20_SMA'], name='20 SMA', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_upper'], name='BB Upper', line=dict(color='lightblue')))
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_lower'], name='BB Lower', line=dict(color='lightblue')))
    
    fig.update_layout(title=f"{symbol} Price Chart", xaxis_title='Date', yaxis_title='Price', xaxis_rangeslider_visible=False, height=700)
    st.plotly_chart(fig, use_container_width=True)
    # Display candlestick chart
    #st.plotly_chart(plot_candles_with_sma(df), use_container_width=True)
    #st.divider()
    # RSI Plot
    
    rsi_fig = go.Figure()
    rsi_fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple'), name='RSI'))
    rsi_fig.update_layout(yaxis=dict(range=[0, 100]), height=300)
    st.plotly_chart(rsi_fig, use_container_width=True)
    st.subheader("📉 RSI Indicator")
    #df = apply_strategy(df)

# Load CSV data
elif data_source == "CSV Upload":
    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        
        # Try to normalize column names
        df.columns = [col.strip().capitalize() for col in df.columns]
        
        # Try to parse and sort date column
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.sort_values('Date').reset_index(drop=True)

        # Apply strategy only if Close exists
        if 'Close' not in df.columns:
            st.error("CSV must contain a 'Close' column.")
        else:
            df = apply_strategy(df)


# Display chart and signals
if 'df' in locals():
    st.subheader("📊 Price Chart with 44 MA")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df['Date'], df['Close'], label='Close Price', color='black')
    ax.plot(df['Date'], df['MA44'], label='44 MA', color='orange')

    buy_signals = df[df['Buy']]
    sell_signals = df[df['Sell']]
    ax.plot(buy_signals['Date'], buy_signals['Close'], '^', markersize=10, color='green', label='Buy Signal')
    ax.plot(sell_signals['Date'], sell_signals['Close'], 'v', markersize=10, color='red', label='Sell Signal')

    ax.set_title("44 MA Strategy Backtest")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    st.subheader("📋 Signal Table")
    signals = df[df['Buy'] | df['Sell']][['Date', 'Close', 'Buy', 'Sell']]
    st.dataframe(signals.reset_index(drop=True))

    st.subheader("📈 Strategy Summary")
    total_signals = len(signals)
    buy_count = df['Buy'].sum()
    sell_count = df['Sell'].sum()
    st.markdown(f"""
    - ✅ Total Signals: **{total_signals}**
    - 🟢 Buy Signals: **{buy_count}**
    - 🔴 Sell Signals: **{sell_count}**
    """)
