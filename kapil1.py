import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
#from utils import generate_mock_data
import random
import requests
from kiteconnect import KiteConnect
import time
import threading
import datetime
from datetime import datetime, timedelta
import os
import pytz  # ✅ Add this



# Global kite object placeholder
if 'kite' not in st.session_state:
    st.session_state.kite = None
# Page configuration
st.set_page_config(layout="wide", page_title="Trade Strategy Dashboard")
    
# Sidebar navigation
with st.sidebar:
    selected = option_menu(
    menu_title="ALGO BOT  ",
    options=[
        "Dashboard", "Get Stock Data", "Doctor Strategy","Doctor1.0 Strategy","Doctor2.0 Strategy","Doctor3.0 Strategy", "Swing Trade Strategy","New Nifty Strategy",
        "Intraday Stock Finder", "Trade Log", "Account Info", "Candle Chart", "Strategy Detail","Strategy2.0 Detail", "Project Detail", "KITE API", "API","Alpha Vantage API","Live Algo Trading"
    ],
    icons=[
        "bar-chart", "search", "cpu","cpu", "cpu","cpu","cpu", "arrow-repeat",
        "search", "clipboard-data", "wallet2", "graph-up", "info-circle", "file-earmark","file-earmark", "code-slash", "code-slash", "code-slash","journal-text"
    ],
    menu_icon="cast",
    default_index=0,
)   

# Main area rendering
st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .card {
            background-color: white;
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            padding: 20px;
            margin: 10px 0;
        }
        .card-title {
            font-size: 18px;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)


if selected == "Dashboard":
    st.subheader("📊 Dashboard - Zerodha Account Overview")       
    # Get current time in UTC
    #utc_now = datetime.datetime.utcnow()
    
    # Define the Indian time zone
    #ist_timezone = pytz.timezone('Asia/Kolkata')
    
    # Localize the UTC time to IST
    #ist_now = utc_now.replace(tzinfo=pytz.utc).astimezone(ist_timezone)
    
    # Display the time in Streamlit
    #st.write("Current time in IST:", ist_now.strftime("%Y-%m-%d %H:%M:%S %Z%z"))
    if "kite" in st.session_state and st.session_state.kite is not None:
        kite = st.session_state.kite

        # ✅ Funds
        try:
            funds = kite.margins(segment="equity")
            available_cash = funds['available']['cash']
            st.metric("💰 Available Fund", f"₹ {available_cash:,.2f}")
        except Exception as e:
            st.error(f"Failed to fetch funds: {e}")

        # ✅ Holdings
        try:
            holdings = kite.holdings()
            if holdings:
                df_holdings = pd.DataFrame(holdings)
                df_holdings = df_holdings[["tradingsymbol", "quantity", "average_price", "last_price", "pnl"]]
                df_holdings["holding_value"] = df_holdings["quantity"] * df_holdings["last_price"]

                total_holding_value = df_holdings["holding_value"].sum()
                total_pnl = df_holdings["pnl"].sum()

                st.metric("📦 Total Holding Value", f"₹ {total_holding_value:,.2f}")
                st.metric("📈 Total P&L", f"₹ {total_pnl:,.2f}", delta_color="normal")

                st.write("📄 Your Holdings:")
                st.dataframe(
                    df_holdings.style.format({
                        "average_price": "₹{:.2f}",
                        "last_price": "₹{:.2f}",
                        "pnl": "₹{:.2f}",
                        "holding_value": "₹{:.2f}"
                    }),
                    use_container_width=True
                )
            else:
                st.info("No holdings available.")
        except Exception as e:
            st.error(f"Failed to fetch holdings: {e}")
            # ✅ Orders
        try:
            st.subheader("🧾 Recent Orders")
            orders = kite.orders()
            if orders:
                df_orders = pd.DataFrame(orders)
                df_orders = df_orders[["order_id", "tradingsymbol", "transaction_type", "quantity", "price", "status", "order_timestamp"]]
                df_orders = df_orders.sort_values(by="order_timestamp", ascending=False)
                st.dataframe(df_orders.head(10), use_container_width=True)
            else:
                st.info("No recent orders found.")
        except Exception as e:
            st.error(f"Failed to fetch orders: {e}")

        # ✅ Positions
        try:
            st.subheader("📌 Net Positions")
            positions = kite.positions()
            net_positions = positions['net']
            if net_positions:
                df_positions = pd.DataFrame(net_positions)
                df_positions = df_positions[["tradingsymbol", "quantity", "average_price", "last_price", "pnl"]]
                st.dataframe(
                    df_positions.style.format({
                        "average_price": "₹{:.2f}",
                        "last_price": "₹{:.2f}",
                        "pnl": "₹{:.2f}"
                    }),
                    use_container_width=True
                )
            else:
                st.info("No open positions.")
        except Exception as e:
            st.error(f"Failed to fetch positions: {e}")

                    # 📈 Live NIFTY 50 Price Chart
        st.subheader("📈 Live NIFTY 50 Chart")

       

        # Setup live prices tracking
        if 'live_prices' not in st.session_state:
            st.session_state.live_prices = []

        if 'ws_started' not in st.session_state:
            def start_websocket():
                try:
                    kws = KiteTicker(api_key, st.session_state.access_token)
                    
                    def on_ticks(ws, ticks):
                        for tick in ticks:
                            price = tick['last_price']
                            timestamp = datetime.now()
                            st.session_state.live_prices.append((timestamp, price))
                            if len(st.session_state.live_prices) > 100:
                                st.session_state.live_prices.pop(0)

                    def on_connect(ws, response):
                        ws.subscribe([256265])  # Token for NIFTY 50 spot

                    def on_close(ws, code, reason):
                        print("WebSocket closed:", reason)

                    kws.on_ticks = on_ticks
                    kws.on_connect = on_connect
                    kws.on_close = on_close
                    kws.connect(threaded=True)
                except Exception as e:
                    print("WebSocket Error:", e)

            thread = threading.Thread(target=start_websocket, daemon=True)
            thread.start()
            st.session_state.ws_started = True

        # Display the chart
        def show_chart():
            if st.session_state.live_prices:
                df = pd.DataFrame(st.session_state.live_prices, columns=["Time", "Price"])
                fig = go.Figure(data=[go.Scatter(x=df["Time"], y=df["Price"], mode="lines+markers")])
                fig.update_layout(title="NIFTY 50 Live Price", xaxis_title="Time", yaxis_title="Price", height=400)
                st.plotly_chart(fig, use_container_width=True)

        show_chart()


    else:
        st.warning("Please login to Kite Connect first.")
        
if selected == "Get Stock Data":
    st.title("📈 Get Stock Data from NSE")

    nifty_50_stocks = [
        "^NSEI", "ADANIENT.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS",
        "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS",
        "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFC.NS",
        "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS",
        "INDUSINDBK.NS", "INFY.NS", "ITC.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LT.NS", "M&M.NS",
        "MARUTI.NS", "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS",
        "SBIN.NS", "SHREECEM.NS", "SUNPHARMA.NS", "TATACONSUM.NS", "TATAMOTORS.NS",
        "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "UPL.NS", "WIPRO.NS"
    ]

    stock = st.selectbox("Select NIFTY 50 stock or Index (^NSEI)", options=nifty_50_stocks, index=nifty_50_stocks.index("TCS.NS"))
    from_date = st.date_input("From Date", datetime(2025, 1, 1))
    to_date = st.date_input("To Date", datetime.today())
    interval = st.selectbox("Select Interval", ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"], index=5)

    if st.button("Fetch Data"):
        st.info(f"Fetching data for {stock.upper()} from {from_date} to {to_date} at interval {interval}")
        try:
            df = yf.download(stock, start=from_date, end=to_date, interval=interval)
    
            if df.empty:
                st.warning("No data returned. Check symbol or market hours for intraday intervals.")
            else:
                # Reset index to get 'Date' column
                df.reset_index(inplace=True)
                # Ensure proper column names and date
                if 'Datetime' in df.columns:
                    df.rename(columns={'Datetime': 'Date'}, inplace=True)
                elif 'Date' not in df.columns:
                    df.insert(0, 'Date', df.index)  # fallback
                
                # Rename OHLCV columns to match expected format
                df.rename(columns=lambda x: x.strip().capitalize(), inplace=True)  # e.g., "open" -> "Open"
    
                # Flatten multi-index columns if needed
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns]
    
                # Show the raw column names to debug
                st.write("📊 Columns:", df.columns.tolist())
    
                # Rename columns for consistency
                rename_map = {}
                for col in df.columns:
                    if "Open" in col and "Adj" not in col: rename_map[col] = "Open"
                    if "High" in col: rename_map[col] = "High"
                    if "Low" in col: rename_map[col] = "Low"
                    if "Close" in col and "Adj" not in col: rename_map[col] = "Close"
                    if "Volume" in col: rename_map[col] = "Volume"
                df.rename(columns=rename_map, inplace=True)
    
                # Show dataframe
                st.dataframe(df)
    
                # CSV download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{stock.upper()}_{interval}_data.csv",
                    mime="text/csv"
                )
    
                # Plot candlestick chart
                if {"Date", "Open", "High", "Low", "Close"}.issubset(df.columns):
                    fig = go.Figure(data=[
                        go.Candlestick(
                            x=df["Date"],
                            open=df["Open"],
                            high=df["High"],
                            low=df["Low"],
                            close=df["Close"],
                            increasing_line_color="green",
                            decreasing_line_color="red"
                        )
                    ])
                    fig.update_layout(
                        title=f"{stock.upper()} Candlestick Chart",
                        xaxis_title="Date",
                        yaxis_title="Price",
                        xaxis_rangeslider_visible=False,
                        template="plotly_dark"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                      st.warning("Could not find required columns to generate candlestick chart.")
                      # ✅ Add line chart for Close price
                      st.subheader("📈 Line Chart - Close Price")
                      st.line_chart(df.set_index("Date")["Close"])
    
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")




elif selected == "Doctor Strategy":
    st.title("⚙️ Test Doctor Trade Strategy")

    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    capital = st.number_input("Capital Allocation (₹)", value=50000)

    # Helper to ensure timezone consistency
    def align_timezone(dt):
        dt = pd.to_datetime(dt)  # Make sure it's a datetime object
        if dt.tzinfo is None:
            return dt.tz_localize("UTC").tz_convert("Asia/Kolkata")
        return dt.tz_convert("Asia/Kolkata")


    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully")

        # Convert 'Date' to datetime if it's not already
        df['Date'] = pd.to_datetime(df['Date'])

        # Check if the 'Date' column is timezone-aware
        if df['Date'].dt.tz is None:
            df['Date'] = df['Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        else:
            df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata')

        # Filter times for 9:30 AM to 1:30 PM market hours
        df = df[df['Date'].dt.time.between(pd.to_datetime('09:30:00').time(), pd.to_datetime('13:30:00').time())]

        # Display the final DataFrame
        st.write(df.head())
        #st.write(df.columns)  # Display the columns in the uploaded file

        if "Close" not in df.columns:
            st.error("CSV must contain a 'Close' column")
        else:
            # Step 1: Time Frame (5-minute chart)
            if df['Date'].diff().dt.total_seconds().median() < 300:
                df = df.resample('5T', on='Date').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'})
            df.dropna(inplace=True)
            #df.set_index('Date', inplace=True)

            # Step 2: Center Line (20 SMA) and Bollinger Bands
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['Upper_BB'] = df['SMA_20'] + 2 * df['Close'].rolling(window=20).std()
            df['Lower_BB'] = df['SMA_20'] - 2 * df['Close'].rolling(window=20).std()

            # Step 3: Cross and Confirm Closing Above SMA
            df['Crossed_SMA_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) < df['SMA_20'].shift(1))

            # Step 4: Reference Candle - Next Candle Close Above 20 SMA
            df['Ref_Candle_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) > df['SMA_20'].shift(1))

            # Step 5: Check IV Condition (only if IV data available)
            # Note: You should fetch IV data externally (example: using API), this is just a placeholder
            iv_data = 16  # Placeholder value, replace with actual API fetch for IV
            #___________________________________________________________________________________________________________________________
            import requests

            def get_live_nifty_iv():
                url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
                headers = {
                    "User-Agent": "Mozilla/5.0",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.nseindia.com/option-chain"
                }
            
                try:
                    session = requests.Session()
                    session.get("https://www.nseindia.com", headers=headers)  # Required to get cookies
            
                    response = session.get(url, headers=headers, timeout=5)
                    data = response.json()
            
                    underlying = data['records']['underlyingValue']
                    options = data['records']['data']
            
                    # Find ATM strike
                    atm_option = min(options, key=lambda x: abs(x['strikePrice'] - underlying))
            
                    ce_iv = atm_option.get('CE', {}).get('impliedVolatility', None)
                    pe_iv = atm_option.get('PE', {}).get('impliedVolatility', None)
            
                    return {
                        'Underlying': underlying,
                        'ATM Strike': atm_option['strikePrice'],
                        'CE_IV': ce_iv,
                        'PE_IV': pe_iv
                    }
            
                except Exception as e:
                    return {"error": str(e)}
            
            # Example usage
            iv_data = get_live_nifty_iv()
            ce_iv = iv_data.get('CE_IV')
            pe_iv = iv_data.get('PE_IV')
            
            st.write(iv_data)

            iv_data =  ce_iv
            iv_data =  17

            #_______________________________________________________________________________________________________________________________
            # Step 6: Trade Execution Based on Cross and IV Condition
            df['Signal'] = None
            for idx in range(1, len(df)):
                if df['Ref_Candle_Up'].iloc[idx] and iv_data >= 16:
                    if df['Close'].iloc[idx] > df['Close'].iloc[idx - 1]:  # Confirm Next Candle Cross
                        df.at[idx, 'Signal'] = 'BUY'

            # Step 7: Stop Loss Logic (10% below entry price)
            df['Stop_Loss'] = df['Close'] * 0.90

            # Step 8: Profit Booking and Trailing Stop Loss
            df['Initial_Stop_Loss'] = df['Close'] * 0.90
            df['Profit_Target'] = df['Close'] * 1.05

           # For trailing stop loss and profit booking logic
            trades = []
            for idx in range(1, len(df)):
                if idx < len(df) and df['Signal'].iloc[idx] == 'BUY':
                    # Your code logic here
            
                    entry_price = df['Close'].iloc[idx]
                    stop_loss = entry_price * 0.90
                    profit_target = entry_price * 1.05
                    trade = {
                        #'Entry_Time': df.index[idx],
                        'Entry_Time': df['Date'].iloc[idx],
                        'Entry_Price': entry_price,
                        'IV': iv_data,
                        'Stop_Loss': stop_loss,
                        'Profit_Target': profit_target,
                        'Exit_Time': None,
                        'Exit_Price': None,
                        'Brokerage'     : 20 ,   # ₹20 per trade
                        'PnL': None,
                        #'PnL_After_Brokerage':None,
                        'Turnover':None,
                        'Exit_Reason': None  # Add the Exit_Reason field
                    }
            
                    # Track the trade for 10-minute exit and trailing logic
                    trades.append(trade)
            
                    # Logic for trailing stop loss and profit booking
                    for trade in trades:
                        entry_time = trade['Entry_Time']
                        entry_price = trade['Entry_Price']
                        stop_loss = trade['Stop_Loss']
                        profit_target = trade['Profit_Target']
                        current_stop_loss = stop_loss
                        current_profit_target = profit_target
                        trailing_stop_loss_triggered = False
                        profit_booked = False
            
                        # Make sure Date is in the index and sorted
                        df = df.sort_values('Date').reset_index(drop=True)
            
                        # Find closest index to entry_time
                        entry_time = align_timezone(trade['Entry_Time'])
            
                        # Safely find the closest index
                        entry_idx = df['Date'].searchsorted(entry_time)
            
                        if entry_idx >= len(df):
                            continue  # Skip if entry time is beyond available data
            
                        # Now proceed
                        for idx in range(entry_idx + 1, len(df)):
                            current_time = df.at[idx, 'Date']
                            close_price = df.at[idx, 'Close']
            
                            # Check for profit booking
                            if close_price >= current_profit_target and not profit_booked:
                                trade['Exit_Time'] = current_time
                                trade['Exit_Price'] = current_profit_target
                                trade['Turnover'] = trade['Exit_Price'] + trade['Entry_Price']
                                trade['PnL'] = current_profit_target - entry_price
                                trade['PnL_After_Brokerage'] = trade['PnL'] - trade['Brokerage']
                                trade['Exit_Reason'] = 'Profit Booking'  # Add exit reason
                                profit_booked = True
                                break
            
                            # Check for trailing stop loss
                            if close_price >= entry_price * 1.04 and not trailing_stop_loss_triggered:
                                current_stop_loss = entry_price
                                trailing_stop_loss_triggered = True
            
                            if trailing_stop_loss_triggered:
                                if close_price >= entry_price * 1.10:
                                    current_stop_loss = entry_price * 1.04
                                elif close_price >= entry_price * 1.15:
                                    current_stop_loss = entry_price * 1.11
                                elif close_price >= entry_price * 1.20:
                                    trade['Exit_Time'] = current_time
                                    trade['Exit_Price'] = close_price
                                    trade['PnL'] = close_price - entry_price
                                    trade['Turnover'] = trade['Exit_Price'] + trade['Entry_Price']
                                    trade['PnL_After_Brokerage'] = trade['PnL'] - trade['Brokerage']
                                    trade['Exit_Reason'] = 'Profit Target Reached'  # Exit reason
                                    break
            
                            # Check for stop loss hit
                            if df.at[idx, 'Low'] <= current_stop_loss:
                                trade['Exit_Time'] = current_time
                                trade['Exit_Price'] = current_stop_loss
                                trade['PnL'] = current_stop_loss - entry_price
                                trade['Turnover'] = trade['Exit_Price'] + trade['Entry_Price']
                                trade['PnL_After_Brokerage'] = trade['PnL'] - trade['Brokerage']
                                trade['Exit_Reason'] = 'Stop Loss Hit'  # Exit reason
                                break
            
                        # Step 9: Time-Based Exit (after 10 minutes)
                        if not trade.get('Exit_Time'):
                            # Ensure 'Date' column is in datetime format, force errors to NaT if conversion fails
                            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
                            # Ensure 'entry_time' is also in datetime format, force errors to NaT if conversion fails
                            entry_time = pd.to_datetime(trade['Entry_Time'], errors='coerce')
            
                            # Check if the 'Date' column has any NaT (invalid) values and handle accordingly
                            if df['Date'].isnull().any():
                                print("Warning: Some 'Date' values are invalid (NaT). They will be excluded.")
                                df = df.dropna(subset=['Date'])
            
                            # Localize to 'Asia/Kolkata' timezone only if the column is naive (no timezone)
                            df['Date'] = df['Date'].apply(lambda x: x.tz_localize('Asia/Kolkata', ambiguous='NaT') if x.tzinfo is None else x)
            
                            # Ensure entry_time is timezone-aware, localize it if it's naive
                            if entry_time.tzinfo is None:
                                entry_time = entry_time.tz_localize('Asia/Kolkata', ambiguous='NaT')
            
                            # Now both df['Date'] and entry_time are timezone-aware, so we can safely use searchsorted()
                            entry_idx = df['Date'].searchsorted(entry_time)
            
                            # Ensure we don't go out of bounds
                            if entry_idx < len(df):
                                closest_entry = df.iloc[entry_idx]
                            else:
                                closest_entry = df.iloc[-1]  # If it's out of bounds, take the last available
            
                            # Time-based exit logic (after 10 minutes)
                            for idx in range(entry_idx + 1, len(df)):
                                current_time = df.at[idx, 'Date']
                                close_price = df.at[idx, 'Close']
                                if (current_time - entry_time).seconds >= 600:  # 600 seconds = 10 minutes
                                    trade['Exit_Time'] = current_time
                                    trade['Exit_Price'] = df.at[idx, 'Close']
                                    trade['PnL'] = df.at[idx, 'Close'] - entry_price
                                    trade['PnL_After_Brokerage'] = trade['PnL'] - trade['Brokerage']
                                    trade['Turnover'] = trade['Exit_Price'] + trade['Entry_Price']
                                    trade['Exit_Reason'] = 'Time-Based Exit'  # Exit reason
                                    break
                    # 2️⃣ If you didn't compute PnL_After_Brokerage per-trade, do it now:
                    #if 'PnL_After_Brokerage' not in trade_log.columns:
                        #trade_log['PnL_After_Brokerage'] = trade_log['PnL'] - trade_log['Brokerage']
                    # Add the trades to the DataFrame
                    #trade_log = pd.DataFrame(trades)
                    #total_net_pnl = trade_log['PnL_After_Brokerage'].sum()
                    #st.markdown(f"**Total Net P&L after Brokerage:** ₹{total_net_pnl:.2f}")
            
                     


                    

           
            
                    
            # Display chart with trade signals (optional)
            # Calculate the 20-period Simple Moving Average (SMA)
            df['20_SMA'] = df['Close'].rolling(window=20).mean()
            
            # Create the candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red',
            )])
            
            # Add buy signals
            buy_signals = df[df['Signal'] == 'BUY']
            fig.add_trace(go.Scatter(
                x=buy_signals['Date'],
                y=buy_signals['Close'],
                mode='markers',
                name='Buy Signal',
                marker=dict(symbol='triangle-up', color='green', size=12)
            ))
            
            # Add 20-period SMA to the chart
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['20_SMA'],
                mode='lines',
                name='20 SMA',
                line=dict(color='blue', width=2)
            ))
            
            # Display the chart
            st.subheader("Daily Chart")
            
            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Price (₹)',
                xaxis_rangeslider_visible=False,
                template='plotly_dark',
                hovermode='x unified',
            )
            
            st.plotly_chart(fig)
            # Display the trade log
             # Display the chart
            st.subheader("Trade Log ")
            st.dataframe(trades)

            # Create a DataFrame
            trade_log_df = pd.DataFrame(trades)
            st.write(trade_log_df.columns.tolist())
            
            # Ensure the CSV string is generated correctly
            csv = trade_log_df.to_csv(index=False)  # `csv` should hold the CSV data as a string
            #print(csv)  # This will print the CSV content in the console for debugging
            
            # Download Button
            st.download_button(
                label="📥 Download Trade Log",
                data=csv,  # Make sure `csv` is correctly defined here
                file_name="trade_log.csv",
                mime="text/csv",
                key="download_button"
            )
            # ── assume you already have: trade_log_df = pd.DataFrame(trades) ──
            if 'PnL_After_Brokerage' in trade_log_df.columns:
                wins = trade_log_df[trade_log_df['PnL_After_Brokerage'] > 0]
            else:
                print("Column 'PnL_After_Brokerage' not found in trade_log_df")
    # Optionally handle fallback here
            # 1️⃣ Compute summary stats
            total_trades = len(trade_log_df)
            wins        = trade_log_df[trade_log_df['PnL_After_Brokerage'] > 0]
            losses      = trade_log_df[trade_log_df['PnL_After_Brokerage'] < 0]
            
            num_wins    = len(wins)
            num_losses  = len(losses)
            win_rate    = (num_wins / total_trades * 100) if total_trades else 0
            
            gross_profit = wins['PnL_After_Brokerage'].sum()
            gross_loss   = losses['PnL_After_Brokerage'].sum()  # negative number
            profit_factor = (gross_profit / abs(gross_loss)) if gross_loss < 0 else float("inf")
            
            avg_win   = wins['PnL_After_Brokerage'].mean()  if num_wins   else 0
            avg_loss  = losses['PnL_After_Brokerage'].mean() if num_losses else 0

            # Total Turnover & Brokerage
            total_turnover = trade_log_df['Turnover'].sum()
            total_brokerage = trade_log_df['Brokerage'].sum()
            
            # Expectancy per trade
            expectancy = (win_rate/100) * avg_win + (1 - win_rate/100) * avg_loss
            
            # 2️⃣ Display in Streamlit
            st.markdown("## 📊 Performance Summary")
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Trades", total_trades)
            c2.metric("Winning Trades", num_wins, f"{win_rate:.1f}%")
            c3.metric("Losing Trades", num_losses)
            
            c4, c5, c6 = st.columns(3)
            c4.metric("Gross Profit", f"₹{gross_profit:.2f}")
            c5.metric("Gross Loss",   f"₹{gross_loss:.2f}")
            c6.metric("Profit Factor", f"{profit_factor:.2f}")
            
            c7, c8, c9 = st.columns(3)
            c7.metric("Avg. Win",   f"₹{avg_win:.2f}")
            c8.metric("Avg. Loss",  f"₹{avg_loss:.2f}")
            c9.metric("Expectancy", f"₹{expectancy:.2f}")

            c10, c11, c12 = st.columns(3)
            c10.metric("Total Turnover",   f"₹{total_turnover:.2f}")
            c11.metric("Total Brokerage",  f"₹{total_brokerage:.2f}")
            c12.metric("Expectancy", f"₹{expectancy:.2f}")
        
            # 3️⃣ (Optional) Equity curve
            st.markdown("### 📈 Equity Curve")
            st.line_chart(trade_log_df['PnL_After_Brokerage'].cumsum())
            
            # 4️⃣ Download full log
            csv = trade_log_df.to_csv(index=False)
            st.download_button(
                "📥 Download Trade Log",
                data=csv,
                file_name="trade_log_with_summary.csv",
                mime="text/csv",
                key="download_with_summary"
            )


  
    
