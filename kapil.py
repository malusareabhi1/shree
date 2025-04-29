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
        "Dashboard", "Get Stock Data", "Doctor Strategy", "Trade Log", "Strategy Detail", "Project Detail", "KITE API", "Live Algo Trading"
    ],
    #options=[
      #  "Dashboard", "Get Stock Data", "Doctor Strategy","Doctor1.0 Strategy","Doctor2.0 Strategy","Doctor3.0 Strategy", "Swing Trade Strategy","New Nifty Strategy",
       # "Intraday Stock Finder", "Trade Log", "Account Info", "Candle Chart", "Strategy Detail","Strategy2.0 Detail", "Project Detail", "KITE API", "API","Alpha Vantage API","Live Algo Trading"
    #],
    icons=[
        "bar-chart", "search", "cpu","arrow-repeat","file-earmark","file-earmark", "code-slash", "code-slash"
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
                        'Stop_Loss': stop_loss,
                        'Profit_Target': profit_target,
                        'Exit_Time': None,
                        'Exit_Price': None,
                        'Brokerage'     : 20 ,   # ₹20 per trade
                        'PnL': None,
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


  
    



elif selected == "KITE API":
    st.subheader("🔐 Kite Connect API (Zerodha) Integration")

    api_key = st.text_input("Enter your API Key", type="password")
    api_secret = st.text_input("Enter your API Secret", type="password")

    if api_key and api_secret:
        try:
            kite = KiteConnect(api_key=api_key)
            login_url = kite.login_url()

            st.markdown(f"👉 [Click here to login with Zerodha and get your request token]({login_url})")
            request_token = st.text_input("🔑 Paste the Request Token after login")

            if request_token:
                try:
                    data = kite.generate_session(request_token, api_secret=api_secret)
                    kite.set_access_token(data["access_token"])

                    st.success("✅ Login successful!")
                    st.session_state.kite = kite

                    # Create tabs
                    tab1, tab2, tab3 = st.tabs(["👤 Profile", "📈 Holdings", "📝 Orders"])

                    # Tab 1: Profile
                    with tab1:
                        profile = kite.profile()
                        profile_flat = {
                            "User ID": profile.get("user_id"),
                            "User Name": profile.get("user_name"),
                            "Email": profile.get("email"),
                            "User Type": profile.get("user_type"),
                            "Broker": profile.get("broker"),
                            "Exchanges": ", ".join(profile.get("exchanges", [])),
                            "Products": ", ".join(profile.get("products", [])),
                            "Order Types": ", ".join(profile.get("order_types", [])),
                        }
                        df_profile = pd.DataFrame(profile_flat.items(), columns=["Field", "Value"])
                        st.table(df_profile)

                    # Tab 2: Holdings
                    with tab2:
                        holdings = kite.holdings()
                        if holdings:
                            df_holdings = pd.DataFrame(holdings)
                            st.dataframe(df_holdings, use_container_width=True)
                        else:
                            st.info("No holdings available.")

                    # Tab 3: Orders
                    with tab3:
                        orders = kite.orders()
                        if orders:
                            df_orders = pd.DataFrame(orders)
                            st.dataframe(df_orders, use_container_width=True)
                        else:
                            st.info("No orders found.")

                except Exception as e:
                    st.error(f"Login failed: {e}")
        except Exception as e:
            st.error(f"Error generating login URL: {e}")
    else:
        st.info("Please enter your API Key and Secret to continue.")
      
       
      

elif selected == "Live Algo Trading":
    st.title("🤖 Live Algo Trading (Paper/Real Mode) Hello ")
    from dotenv import load_dotenv

    # ─── LOAD ENVIRONMENT VARIABLES ───────────────────────────────────────────────
    load_dotenv()
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # ─── TELEGRAM ALERT FUNCTION ──────────────────────────────────────────────────
    def send_telegram(msg: str):
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        try:
            requests.post(url, data=payload)
        except Exception as e:
            st.error(f"Telegram Error: {e}")
    
    # ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
    #st.set_page_config(page_title="📈 Nifty EMA20 Breakout", layout="wide")
    st.title("📊 Nifty 5-min EMA20 + Volume Breakout Monitor")
    
    # ─── STRATEGY TEST STARTED ─────────────────────────────────────────────────────
    start_msg = "🟢 Strategy Test Started"
    st.info(start_msg)
    send_telegram(start_msg)
    
    # ─── FETCH DATA ───────────────────────────────────────────────────────────────
    @st.cache_data(ttl=60)
    def fetch_data(ticker: str) -> pd.DataFrame:
        df = yf.download(ticker, interval="5m", period="15d", progress=False)
        df.reset_index(inplace=True)
        #df.reset_index(inplace=True)          # moves the old index into a 'Date' column
        df['Date'] = pd.to_datetime(df['Datetime'], errors='coerce')
        #st.write("Columns after read:", df.columns.tolist())
        df.index = pd.to_datetime(df.index)
       
        if df.index.tz is None:
            df = df.tz_localize("UTC").tz_convert("Asia/Kolkata")
        else:
            df = df.tz_convert("Asia/Kolkata")
    
        df = df.between_time("09:15", "15:30")
    
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
    
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
        df["VMA20"] = df["Volume"].rolling(20).mean()
        
        return df
    
    symbol = "^NSEI"
    df = fetch_data(symbol)
    st.write("Columns after read:", df.columns.tolist())
    if not df.empty:
        if len(df) > 0:
            latest = df.iloc[-1]
            now = latest.name 
    st.write(letest)
    st.write(now)
    #latest = df.iloc[-1]
    if len(df) >= 2:
        prev = df.iloc[-2]  # Access second-to-last row
    #prev = df.iloc[-2]
    
    # ─── MARKET OPEN/CLOSE MESSAGE ────────────────────────────────────────────────
    #now = latest.name
    now = datetime.now()
    if now.hour == 9 and now.minute == 15:
        market_msg = "📈 Market Opened at 09:15 But My Doctor Stratergy will Start 09:30 "
        st.success(market_msg)
        send_telegram(market_msg)

    if now.hour == 14 and now.minute == 30:
        market_close_msg = "📉 Doctor Stratergy will  not take Trade after 02:30"
        st.warning(market_close_msg)
        send_telegram(market_close_msg)

     

    if now.hour == 15 and now.minute == 30:
        market_close_msg = "📉 Market Closed at 15:30 Bye ! See you Tomorrow 9:30"
        st.warning(market_close_msg)
        send_telegram(market_close_msg)



    # ─── STRATEGY LOGIC ───────────────────────────────────────────────────────────
    def generate_signals(df: pd.DataFrame, iv_data: float, iv_threshold: float) -> pd.DataFrame:
        # 0a) See what columns you have:
        st.write("Columns before normalize:", df.columns.tolist())
        
        # 0b) Normalize your date column to 'Date'
        if 'Date' not in df.columns:
            if 'date' in df.columns:                 # lowercase
                df = df.rename(columns={'date':'Date'})
            elif 'timestamp' in df.columns:         # maybe it's timestamp?
                df = df.rename(columns={'timestamp':'Date'})
            else:
                raise KeyError("No 'Date' (or 'date' / 'timestamp') column found in your DataFrame")
        
        # 0c) Convert to datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        if df['Date'].isna().any():
            raise ValueError("Some 'Date' values could not be parsed as datetime")
        
        # 1) Now safe to sort
        df = df.sort_values('Date').reset_index(drop=True)
    
        # … the rest of your logic …
        df['SMA_20']   = df['Close'].rolling(20).mean()
        df['Upper_BB'] = df['SMA_20'] + 2 * df['Close'].rolling(20).std()
        df['Lower_BB'] = df['SMA_20'] - 2 * df['Close'].rolling(20).std()
        df['Ref_Candle_Up'] = (
            (df['Close'] > df['SMA_20']) &
            (df['Close'].shift(1) > df['SMA_20'].shift(1))
        )
        
        # Vectorized BUY signal:
        df['Signal'] = np.where(
            (df['Ref_Candle_Up']) &
            (iv_data  >= iv_threshold) &
            (df['Close'] > df['Close'].shift(1)),
            'BUY', None
        )
        return df
        #_________________________________________________________________________________________________________________
        def get_live_iv(symbol, expiry_date, strike_price, option_type):
            # Initialize the NSE object
            nse = Nse()
        
            # Get Option chain data (you'll need the symbol, expiry, strike, and type)
            option_data = nse.get_stock_option_chain(symbol)
        
            # Extract IV data (example; adapt depending on actual data structure)
            for option in option_data['records']['data']:
                if option['expiryDate'] == expiry_date and option['strikePrice'] == strike_price:
                    if option_type == 'CE':  # Call option
                        iv_value = option['CE']['impliedVolatility']
                    elif option_type == 'PE':  # Put option
                        iv_value = option['PE']['impliedVolatility']
                    return iv_value
            
            return None
        
        # Example Usage
        symbol = 'NIFTY'
        expiry_date = '2025-04-30'  # expiry date
        strike_price = 18000  # example strike price
        option_type = 'CE'  # 'CE' for Call, 'PE' for Put
        
        iv_value = get_live_iv(symbol, expiry_date, strike_price, option_type)
        if iv_value:
            st.write(f"The live IV for {symbol} {expiry_date} {strike_price} {option_type} is: {iv_value}")
        else:
            st.write("IV data not available")
    
    signal = "No Signal"
    # Check if DataFrame has enough data
    if len(df) >= 2:
        latest = df.iloc[-1]  # Get the latest row
        prev = df.iloc[-2]    # Get the previous row
    st.write(df.shape)  # Shows the number of rows and columns
    st.write(df.columns)  # Lists all the columns
    if (prev["Close"] < prev["EMA20"]) and (latest["Close"] > prev["EMA20"]) and (latest["Volume"] > latest["VMA20"]):
        signal = "BUY"
        entry_price = round(latest["Close"], 2)
        msg = (
            f"📥 <b>LIVE BUY SIGNAL</b>\n"
            f"<b>Symbol:</b> {symbol}\n"
            f"<b>Entry:</b> ₹{entry_price}\n"
            f"<b>Volume:</b> {latest['Volume']:,}\n"
            f"<b>Time:</b> {latest.name.strftime('%H:%M')}"
        )
        send_telegram(msg)

    
    
    # ─── DISPLAY ──────────────────────────────────────────────────────────────────
    st.subheader("📊 Last 5 Candles")
    st.dataframe(df.tail(5))
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🔹 Close", f"₹{latest['Close']:.2f}")
    col2.metric("🔸 EMA20", f"₹{latest['EMA20']:.2f}")
    col3.metric("📌 Signal", signal)
    #---------------------------------------------------------------------------------------
     #____________________________________________________________________________________________________________________   

    live_iv_value=17.06
    signals_df = generate_signals(df, iv_data=live_iv_value, iv_threshold=16)
    st.write(signals_df[['Date','Close','Signal']].dropna(subset=['Signal']))
    #_________________________________________________________________________________________________________________
    import plotly.graph_objects as go
    from datetime import datetime
    
    # ─── filter for today's date ──────────────────────────────────────
    # assume df.index is timezone-aware in IST
    today = datetime.now().astimezone(df.index.tz).date()
    df_today = df[df.index.date == today]
    
    # Calculate 20 EMA
    df_today['EMA20'] = df_today['Close'].ewm(span=20, adjust=False).mean()
    
    st.subheader("🕯️ Today's 5-Min Candle Chart with 20 EMA")
    
    # Plot the candlestick chart with 20 EMA
    fig = go.Figure(data=[
        go.Candlestick(
            x=df_today.index,
            open=df_today["Open"],
            high=df_today["High"],
            low=df_today["Low"],
            close=df_today["Close"],
            increasing_line_color="green",
            decreasing_line_color="red",
            name="Candles"
        ),
        go.Scatter(
            x=df_today.index,
            y=df_today['EMA20'],
            mode='lines',
            line=dict(color='blue', width=2),
            name='20 EMA'
        )
    ])
    
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        xaxis_title="Time",
        yaxis_title="Price (₹)",
        template="plotly_dark",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    #---------------------------------------------------------------------------------------
    st.subheader("📈 Price vs EMA20")
    st.line_chart(df[["Close", "EMA20"]])
    
    # ─── STRATEGY TEST STOPPED ────────────────────────────────────────────────────
    stop_msg = "🔴 Strategy Test Ended (for current run)"
    st.info(stop_msg)
    send_telegram(stop_msg)
    
    # ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
    st.markdown("⏱️ Auto-refresh every 30 seconds")
    with st.spinner("⏳ Refreshing in 30 seconds..."):
        time.sleep(30)
        st.rerun() 



    else:
        st.warning("📴 Please upload a valid CSV file to backtest the strategy.")  
   
