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
from datetime import datetime

import pytz  # ✅ Add this



# Global kite object placeholder
if 'kite' not in st.session_state:
    st.session_state.kite = None
# Page configuration
st.set_page_config(layout="wide", page_title="Trade Strategy Dashboard")
    
# Sidebar navigation
with st.sidebar:
    selected = option_menu(
    menu_title="ALGO BOT Trade ",
    options=[
        "Dashboard", "Get Stock Data", "Doctor Strategy","Doctor1.0 Strategy","Doctor2.0 Strategy","Doctor3.0 Strategy", "Swing Trade Strategy",
        "Intraday Stock Finder", "Trade Log", "Account Info", "Candle Chart", "Strategy Detail","Strategy2.0 Detail", "Project Detail", "KITE API", "API","Alpha Vantage API","Live Algo Trading"
    ],
    icons=[
        "bar-chart", "search", "cpu","cpu", "cpu","cpu", "arrow-repeat",
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
        


  
        
elif selected == "API":

    st.subheader("🔐 Fyers API Integration")

    from fyers_apiv3 import fyersModel
    from fyers_apiv3.FyersWebsocket import data_ws

    # --- User Inputs (you can also store these securely or load from .env)
    app_id = st.text_input("📌 App ID", type="password")
    access_token = st.text_input("🔑 Access Token", type="password")

    if app_id and access_token:
        try:
            # --- Initialize session
            fyers = fyersModel.FyersModel(client_id=app_id, token=access_token, log_path="")

            # --- Fetch Profile
            profile = fyers.get_profile()
            st.success("✅ Connected to Fyers!")
            st.json(profile)

            # --- Optional: Fetch Holdings
            holdings = fyers.holdings()
            st.subheader("📁 Holdings")
            st.json(holdings)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

    else:
        st.info("ℹ️ Please enter App ID and Access Token to continue.")


elif selected == "Get Stock Data":
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
    st.title("⚙️ Test Trade Strategy")

    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    capital = st.number_input("Capital Allocation (₹)", value=50000)

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully")

        # Convert 'Date' to datetime if it's not already
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Check if the 'Date' column is timezone-aware
        if df['Date'].dt.tz is None:
            # If naive (no timezone), localize to UTC and convert to Asia/Kolkata
            df['Date'] = df['Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
        else:
            # If already timezone-aware, just convert to Asia/Kolkata
            df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata')
        
        # Now you can filter the times for 9:15 AM to 3:30 PM market hours
        df = df[df['Date'].dt.time.between(pd.to_datetime('09:15:00').time(), pd.to_datetime('15:30:00').time())]
        
        # Display the final DataFrame
        print(df.head())
       

        if "Close" not in df.columns:
            st.error("CSV must contain a 'Close' column")
        else:
            # Example strategy: Buy if Close increases by 5 points, Sell if it decreases by 5 points
            df['Signal'] = df['Close'].diff().apply(lambda x: 'BUY' if x > 5 else 'SELL' if x < -5 else None)
            df.dropna(subset=['Signal'], inplace=True)

            # Generate the trade log
            trade_log = pd.DataFrame({
                "Date": df['Date'],
                "Stock": "TEST-STOCK",
                "Action": df['Signal'],
                "Price": df['Close'],
                "Qty": 10,
                "PnL": df['Close'].diff().fillna(0) * 10  # Example
            })

            # Calculate net PnL and other stats
            net_pnl = trade_log["PnL"].sum()
            win_trades = trade_log[trade_log["PnL"] > 0].shape[0]
            lose_trades = trade_log[trade_log["PnL"] < 0].shape[0]
            last_order = f"{trade_log.iloc[-1]['Action']} - TEST-STOCK - 10 shares @ {trade_log.iloc[-1]['Price']}"

            # Store to session state for Account Info
            st.session_state['net_pnl'] = float(net_pnl)
            st.session_state['used_capital'] = capital
            st.session_state['open_positions'] = {"TEST-STOCK": {"Qty": 10, "Avg Price": round(df['Close'].iloc[-1], 2)}}
            st.session_state['last_order'] = last_order

            # Results
            st.metric("Net PnL", f"₹{net_pnl:.2f}")
            st.metric("Winning Trades", win_trades)
            st.metric("Losing Trades", lose_trades)
            st.dataframe(trade_log)

            # CSV download button
            csv = trade_log.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Trade Log", data=csv, file_name="trade_log.csv", mime="text/csv")
            st.session_state['trade_log_df'] = trade_log  # Store trade log in session

            # Create a Candlestick chart
            fig = go.Figure(data=[go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red',
            )])
            

            # Mark BUY and SELL signals on the chart
            buy_signals = df[df['Signal'] == 'BUY']
            sell_signals = df[df['Signal'] == 'SELL']

            fig.add_trace(go.Scatter(
                x=buy_signals['Date'],
                y=buy_signals['Close'],
                mode='markers',
                name='Buy Signal',
                marker=dict(symbol='triangle-up', color='green', size=12)
            ))

            fig.add_trace(go.Scatter(
                x=sell_signals['Date'],
                y=sell_signals['Close'],
                mode='markers',
                name='Sell Signal',
                marker=dict(symbol='triangle-down', color='red', size=12)
            ))

            # Update the chart layout
            fig.update_layout(
                #title=f'{stock} Candlestick Chart with Trade Entries and Exits',
                #title=f' Candlestick Chart with Trade Entries and Exits',
                xaxis_title='Date',
                yaxis_title='Price (₹)',
                xaxis_rangeslider_visible=False,  # Hide the range slider
                template='plotly_dark',  # Use a dark template
                hovermode='x unified',  # Hover across x-axis to get details
            )

            # Display the interactive candlestick chart
            st.plotly_chart(fig)
            # Convert 'BUY'/'SELL' signals to numeric form for backtesting compatibility
            df['Signal_Code'] = df['Signal'].map({'BUY': 1, 'SELL': -1})
            
            # Save the DataFrame with signal for backtest/papertrade usage
            csv_with_signal = df[["Date", "Open", "High", "Low", "Close", "Signal_Code"]]
            csv_data = csv_with_signal.rename(columns={"Signal_Code": "Signal"}).to_csv(index=False).encode("utf-8")
            
            st.download_button(
                label="📥 Download CSV with Signals",
                data=csv_data,
                file_name="signal_output.csv",
                mime="text/csv"
            )

  
    


elif selected == "Doctor1.0 Strategy":
    st.title("⚙️ Test Doctor1.0 Strategy ")

    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    capital = st.number_input("Capital Allocation (₹)", value=50000)

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        required_columns = {'Date', 'Open', 'High', 'Low', 'Close', 'Volume'}
        if not required_columns.issubset(df.columns):
            st.error(f"CSV must contain the following columns: {required_columns}")
        else:
            st.success("File uploaded successfully")

            df['Signal'] = df['Close'].diff().apply(lambda x: 'BUY' if x > 5 else 'SELL' if x < -5 else None)
            df.dropna(subset=['Signal'], inplace=True)

            trade_log = pd.DataFrame({
                "Date": df['Date'],
                "Stock": "TEST-STOCK",
                "Action": df['Signal'],
                "Price": df['Close'],
                "Qty": 10,
                "PnL": df['Close'].diff().fillna(0) * 10
            })

            net_pnl = trade_log["PnL"].sum()
            win_trades = trade_log[trade_log["PnL"] > 0].shape[0]
            lose_trades = trade_log[trade_log["PnL"] < 0].shape[0]
            last_order = f"{trade_log.iloc[-1]['Action']} - TEST-STOCK - 10 shares @ {trade_log.iloc[-1]['Price']}"

            st.session_state['net_pnl'] = float(net_pnl)
            st.session_state['used_capital'] = capital
            st.session_state['open_positions'] = {"TEST-STOCK": {"Qty": 10, "Avg Price": round(df['Close'].iloc[-1], 2)}}
            st.session_state['last_order'] = last_order

            st.metric("Net PnL", f"₹{net_pnl:.2f}")
            st.metric("Winning Trades", win_trades)
            st.metric("Losing Trades", lose_trades)
            st.dataframe(trade_log)

            csv = trade_log.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Trade Log", data=csv, file_name="trade_log.csv", mime="text/csv")
            st.session_state['trade_log_df'] = trade_log

            fig = go.Figure(data=[go.Candlestick(
                x=df['Date'],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red',
            )])

            buy_signals = df[df['Signal'] == 'BUY']
            sell_signals = df[df['Signal'] == 'SELL']

            fig.add_trace(go.Scatter(
                x=buy_signals['Date'],
                y=buy_signals['Close'],
                mode='markers',
                name='Buy Signal',
                marker=dict(symbol='triangle-up', color='green', size=12)
            ))

            fig.add_trace(go.Scatter(
                x=sell_signals['Date'],
                y=sell_signals['Close'],
                mode='markers',
                name='Sell Signal',
                marker=dict(symbol='triangle-down', color='red', size=12)
            ))

            fig.update_layout(
                xaxis_title='Date',
                yaxis_title='Price (₹)',
                xaxis_rangeslider_visible=False,
                template='plotly_dark',
                hovermode='x unified',
            )

            st.plotly_chart(fig)

            df['Signal_Code'] = df['Signal'].map({'BUY': 1, 'SELL': -1})
            csv_with_signal = df[["Date", "Open", "High", "Low", "Close", "Signal_Code"]]
            csv_data = csv_with_signal.rename(columns={"Signal_Code": "Signal"}).to_csv(index=False).encode("utf-8")

            st.download_button(
                label="📥 Download CSV with Signals",
                data=csv_data,
                file_name="signal_output.csv",
                mime="text/csv"
            )

            
elif selected == "Trade Log":
    st.title("📘 Trade Log")

    # Check if trade_log_df exists
    if 'trade_log_df' in st.session_state and not st.session_state['trade_log_df'].empty:
        trade_log = st.session_state['trade_log_df']
        
        st.subheader("Trade Log Table")
        st.dataframe(trade_log)
        df=trade_log
         # ✅ Show key metrics
        if "PnL" in df.columns:
            total_pnl = df["PnL"].sum()
            win_trades = df[df["PnL"] > 0].shape[0]
            lose_trades = df[df["PnL"] < 0].shape[0]
    
            st.metric("💰 Net PnL", f"₹{total_pnl:.2f}")
            st.metric("✅ Winning Trades", win_trades)
            st.metric("❌ Losing Trades", lose_trades)
    
            # 📉 Line chart - PnL over time
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"])
                df.sort_values("Date", inplace=True)
                df["Cumulative PnL"] = df["PnL"].cumsum()
                st.subheader("📈 Cumulative PnL Over Time")
                st.line_chart(df.set_index("Date")["Cumulative PnL"])
    
            # 🥧 Pie chart - Win vs Loss
            st.subheader("📊 Win/Loss Distribution")
            win_loss_df = pd.DataFrame({
                "Result": ["Win", "Loss"],
                "Count": [win_trades, lose_trades]
            })
            fig = px.pie(win_loss_df, names="Result", values="Count", title="Win vs Loss")
            st.plotly_chart(fig, use_container_width=True)
    
            # 📤 Download button
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Clean Trade Log", csv, "clean_trade_log.csv", "text/csv")
        else:
            st.warning("No 'PnL' column found in CSV.")
    else:
        st.info("Upload a CSV file to view trade log.")
   
       
      

elif selected == "Account Info":
    st.title("💼 Account Information")

    # Get session values
    starting_capital = 100000
    net_pnl = st.session_state.get('net_pnl', 0)
    used_capital = st.session_state.get('used_capital', 0)
    available_capital = starting_capital + net_pnl

    open_positions = st.session_state.get('open_positions', {})
    last_order = st.session_state.get('last_order', "No order placed yet")

    # 📊 Display Funds Summary
    st.subheader("Funds Summary")
    funds_df = pd.DataFrame({
        "Metric": ["Available Capital", "Used Capital", "Net PnL"],
        "Value (₹)": [round(available_capital, 2), round(used_capital, 2), round(net_pnl, 2)],
    })
    st.table(funds_df)

    st.subheader("Open Positions")
    if open_positions:
        for stock, details in open_positions.items():
            st.write(f"{stock}: {details['Qty']} shares @ ₹{details['Avg Price']}")
    else:
        st.info("No open positions")

    st.subheader("Last Order")
    st.write(last_order)

elif selected == "Doctor3.0  Strategy":
    st.title("⚙️ Test Doctor3.0 Strategy")

    st.markdown("""
    ### 📋 Doctor 3.0 स्ट्रॅटेजी प्लॅन:

    ✅ **चार्ट सेटअप**: 5 मिनिटांचा कँडलस्टिक चार्ट + Bollinger Band (20 SMA). 

    ✅ **20 SMA क्रॉसिंग:**
    - कँडलने 20 SMA लाईन खालून वर क्रॉस करून क्लोज केली पाहिजे.
    - नंतरची कँडल ही 20 SMA ला touch न करता वर क्लोज झाली पाहिजे.

    ✅ **Reference Candle Setup:**
    - क्रॉस करणारी कँडल = Reference Candle
    - त्याच्या अगोदरची कँडल महत्त्वाची: तिचा High/Close दोन्हीपैकी जास्त किंमत मार्क करा.
    - नंतरची कँडल ह्या किमतीला खालून वर ब्रेक करत असल्यास ट्रेड एंटर करा.

    ✅ **Entry Condition:**
    - Reference candle नंतरच्या कँडलने prior candle चा High/Close cross केलं पाहिजे.
    - आणि IV > 16% असेल तर, त्या वेळी In the Money Call Option खरेदी करा.

    ✅ **Risk Management:**
    - Entry नंतर Stop Loss: Buy Price - 10%
    - Profit Target: 5%
    - Profit > 4% झाल्यावर Stop Loss ला Entry Price ला ट्रेल करा (No Loss Zone).
    - Profit > 10% = SL @ 4%, Profit > 15% = SL @ 11%, Profit > 20% = Book full profit

    ✅ **Time Based Exit:**
    - Trade घेतल्यावर 10 मिनिटात काहीही हिट न झाल्यास, नफा/तोटा न पाहता एक्झिट करा.

    ✅ **Trade Time:**
    - सकाळी 9:30 ते दुपारी 3:00 पर्यंतच ट्रेड सुरू करा.
    """)

    uploaded_file = st.file_uploader("Upload CSV file with OHLCV data", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()

        if {'Open', 'High', 'Low', 'Close', 'Volume', 'Date'}.issubset(df.columns):
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values("Date")
            st.success("✅ Data loaded successfully!")
            st.dataframe(df.tail())

            # Calculate 20 SMA and Bollinger Bands
            df['SMA20'] = df['Close'].rolling(window=20).mean()
            df['Upper'] = df['SMA20'] + 2 * df['Close'].rolling(window=20).std()
            df['Lower'] = df['SMA20'] - 2 * df['Close'].rolling(window=20).std()

            # Detect breakout condition
            breakout_signals = []
            entry_price = None
            sl_price = None
            tp_price = None

            for i in range(21, len(df) - 1):
                prev = df.iloc[i - 1]
                curr = df.iloc[i]
                next_candle = df.iloc[i + 1]
                iv = 18  # simulated implied volatility

                if (prev['Close'] < prev['SMA20']) and (curr['Close'] > curr['SMA20']) and (curr['Low'] > curr['SMA20']):
                    ref_price = max(prev['High'], prev['Close'])
                    if next_candle['Close'] > ref_price and iv > 16:
                        entry_price = next_candle['Close']
                        sl_price = entry_price * 0.90
                        tp_price = entry_price * 1.05
                        breakout_signals.append({
                            'Time': df.iloc[i + 1]['Date'],
                            'Entry': entry_price,
                            'SL': sl_price,
                            'TP': tp_price,
                            'IV': iv,
                            'Result': None
                        })

            # Paper Trading Simulation
            results = []
            for signal in breakout_signals:
                trade_open = False
                entry = signal['Entry']
                sl = signal['SL']
                tp = signal['TP']
                entry_time = signal['Time']
                exit_time = entry_time + pd.Timedelta(minutes=10)

                for idx, row in df.iterrows():
                    if row['Date'] < entry_time:
                        continue
                    if row['Date'] > exit_time:
                        results.append({**signal, 'Exit': row['Close'], 'Reason': 'Time Exit'})
                        break
                    if row['Low'] <= sl:
                        results.append({**signal, 'Exit': sl, 'Reason': 'Stop Loss Hit'})
                        break
                    if row['High'] >= tp:
                        results.append({**signal, 'Exit': tp, 'Reason': 'Profit Target Hit'})
                        break

            if results:
                result_df = pd.DataFrame(results)
                st.subheader("📊 Paper Trading Results")
                st.dataframe(result_df)
            else:
                st.info("🚫 No trades detected.")

        else:
            st.error("CSV must contain the following columns: Date, Open, High, Low, Close, Volume")



elif selected == "Strategy Detail":
    st.title("ℹ️ Strategy Details")

    st.markdown("""
    **Objective:** Implement a simple strategy based on basic moving averages and volatility.
    
    **Strategy Highlights:**
    - Buy when the price crosses above the moving average and volatility is low.
    - Sell when the price falls below the moving average and volatility is high.
    ✅ Doctor Algo-BOT Strategy – English Version
    1. Chart Setup
    Use Bollinger Bands (20 SMA, 2 SD) on the chart.
    
    Use Candlestick pattern, not line or Heikin-Ashi.
    
    Timeframe: 5-minute chart.
    
    Only take trades after 9:30 AM.
    
    2. Center Line (20 SMA) Crossing Logic
    The middle line of the Bollinger Band (20 SMA) should be crossed from below to above by Nifty or Bank Nifty.
    
    The candle that crosses the 20 SMA must also close above it.
    
    The next candle after the crossover should also close above the 20 SMA, without touching it.
    
    This second candle is marked as the "Reference Candle".
    
    The candle before the Reference Candle is called the "Pre-Reference Candle".
    
    3. Breakout and Trade Execution
    Identify:
    
    High of the Pre-Reference Candle
    
    Close of the Reference Candle
    
    Take the maximum of these two values = breakout_level
    
    Trade Trigger: If a future 5-minute candle crosses breakout_level from below, execute the trade (Call Option Buy).
    
    Stop Loss (SL): 10% below the entry price.
    
    4. Implied Volatility (IV) Check
    At the time of trade, Nifty/Bank Nifty IV should be ≥ 16.
    
    Only then the trade is valid.
    
    5. Option Selection
    On breakout, buy the nearest In-The-Money (ITM) Call Option for Nifty/Bank Nifty.
    
    6. Risk Management – SL and Trailing Logic
    
    Profit Reached	Trailing Stop Loss Moves To
    5%	Entry Price (No-Loss Zone)
    10%	Trail SL to 4% profit
    15%	Trail SL to 11% profit
    20%	Book full profit
    7. Time-Based Exit
    If none of SL or Target is hit within 10 minutes of trade initiation,
    
    Then exit the trade immediately, regardless of PnL.


    """)
    
elif selected == "Project Detail":
    st.title("📋 Project Details")

    st.markdown("""
    **Project Name:** Trade Strategy Automation System
    **Goal:** Automate strategy testing, risk management, and trade execution.
    
    **Components:**
    - Data Collection
    - Backtesting Framework
    - Trade Simulation
    - Capital & Risk Management
    """)
elif selected == "Candle Chart":
    st.title("📉 Candle Chart Viewer")

    try:
        stock = st.session_state.selected_stock
        from_date = st.session_state.from_date
        to_date = st.session_state.to_date
        interval = st.session_state.interval
    except KeyError:
        st.error("Please select a stock and date range in the sidebar first.")
        st.stop()

    st.markdown(f"### Showing Candle Chart for: **{stock.upper()}**")
    st.markdown(f"**Date Range:** {from_date} to {to_date}  \n**Interval:** {interval}")

    try:
        candle_df = yf.download(stock, start=from_date, end=to_date, interval=interval)

        if candle_df.empty:
            st.warning("No data found.")
        else:
            import plotly.graph_objects as go

            candle_df.reset_index(inplace=True)

            fig = go.Figure(data=[go.Candlestick(
                x=candle_df['Date'],
                open=candle_df['Open'],
                high=candle_df['High'],
                low=candle_df['Low'],
                close=candle_df['Close'],
                increasing_line_color='green',
                decreasing_line_color='red'
            )])

            fig.update_layout(title=f'{stock.upper()} Candlestick Chart', xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching data: {e}")

elif selected == "Swing Trade Strategy":
    st.subheader("📈 Swing Trade Strategy")
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        # Detect and set datetime index
        datetime_col = next((c for c in df.columns if 'date' in c.lower() or 'time' in c.lower()), None)
        if not datetime_col:
            st.error("❌ No datetime column found.")
            st.stop()
        df[datetime_col] = pd.to_datetime(df[datetime_col])
        df.set_index(datetime_col, inplace=True)
        st.success(f"✅ Using '{datetime_col}' as index.")

        # Ensure OHLC columns
        for col in ['Open','High','Low','Close']:
            if col not in df.columns:
                st.error(f"❌ '{col}' column missing.")
                st.stop()

        # Calculate indicators
        df['SMA_20'] = df['Close'].rolling(20).mean()
        df['SMA_50'] = df['Close'].rolling(50).mean()
        df['Signal'] = None
        df.loc[df['SMA_20'] > df['SMA_50'], 'Signal'] = 'BUY'
        df.loc[df['SMA_20'] < df['SMA_50'], 'Signal'] = 'SELL'

        # Build complete trade log on exits only
        trades = []
        in_trade = False
        entry_time = entry_price = None
        for time, row in df.iterrows():
            sig = row['Signal']
            price = row['Close']
            if sig == 'BUY' and not in_trade:
                in_trade = True
                entry_time = time
                entry_price = price
            elif sig == 'SELL' and in_trade:
                exit_time = time
                exit_price = price
                qty = 1  # or calculate based on capital/risk
                pnl = (exit_price - entry_price) * qty
                trades.append({
                    'Entry Time': entry_time,
                    'Entry Price': entry_price,
                    'Exit Time': exit_time,
                    'Exit Price': exit_price,
                    'Qty': qty,
                    'PnL': round(pnl,2)
                })
                in_trade = False

        trade_log = pd.DataFrame(trades)

        # Summary and download
        total_pnl = trade_log['PnL'].sum() if 'PnL' in trade_log.columns else 0
        st.metric("Total PnL", f"₹{total_pnl:.2f}")
        if not trade_log.empty:
            st.dataframe(trade_log)
            csv = trade_log.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Trade Log", data=csv, file_name="swing_trade_log.csv", mime="text/csv")

        # Candlestick + signals
        fig = go.Figure([go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']
        )])
        buys = df[df['Signal']=='BUY']
        sells= df[df['Signal']=='SELL']
        fig.add_trace(go.Scatter(x=buys.index, y=buys['Close'], mode='markers', marker=dict(symbol='triangle-up', color='green', size=12), name='BUY'))
        fig.add_trace(go.Scatter(x=sells.index, y=sells['Close'], mode='markers', marker=dict(symbol='triangle-down', color='red', size=12), name='SELL'))
        fig.update_layout(title="Swing Trade Chart", xaxis_rangeslider_visible=False, template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)      


elif selected == "Intraday Stock Finder":
    st.subheader("📊 Intraday Stock Finder (Simulated on NIFTY 50)")

    # --- Mock NIFTY 50 stock data for simulation ---
    nifty50_stocks = [
        "ADANIENT", "ADANIPORTS", "ASIANPAINT", "AXISBANK", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV",
        "BPCL", "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB", "DRREDDY", "EICHERMOT",
        "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
        "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK", "LT", "M&M", "MARUTI", "NTPC", "NESTLEIND",
        "ONGC", "POWERGRID", "RELIANCE", "SBILIFE", "SBIN", "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS",
        "TATASTEEL", "TECHM", "TITAN", "UPL", "ULTRACEMCO", "WIPRO"
    ]

    # --- Generate mock stock data ---
    def generate_mock_data():
        mock_data = []
        for symbol in nifty50_stocks:
            open_price = random.uniform(100, 1500)
            price = open_price * random.uniform(0.98, 1.05)
            prev_close = open_price * random.uniform(0.97, 1.03)
            volume = random.randint(400000, 1200000)
            mock_data.append({
                "symbol": symbol,
                "price": round(price, 2),
                "volume": volume,
                "open_price": round(open_price, 2),
                "prev_close": round(prev_close, 2)
            })
        return mock_data

    # --- Scanner configuration ---
    MIN_VOLUME = 500000
    PRICE_RANGE = (50, 1500)
    PRICE_CHANGE_THRESHOLD = 0.015  # 1.5%

    # --- Simulate technical conditions ---
    def simulate_technical_conditions(stock):
        rsi = random.randint(25, 75)
        vwap = stock['open_price'] + random.uniform(-10, 10)
        above_vwap = stock['price'] > vwap
        breakout_15min = stock['price'] > stock['open_price'] * 1.015
        return rsi, above_vwap, breakout_15min

    # --- Scan logic ---
    def scan_intraday_stocks(stocks):
        shortlisted = []
        for stock in stocks:
            if PRICE_RANGE[0] <= stock['price'] <= PRICE_RANGE[1] and stock['volume'] >= MIN_VOLUME:
                price_change = (stock['price'] - stock['prev_close']) / stock['prev_close']
                if abs(price_change) >= PRICE_CHANGE_THRESHOLD:
                    rsi, above_vwap, breakout_15min = simulate_technical_conditions(stock)

                    if above_vwap and breakout_15min:
                        shortlisted.append({
                            "symbol": stock['symbol'],
                            "price": stock['price'],
                            "rsi": rsi,
                            "above_vwap": above_vwap,
                            "breakout": breakout_15min,
                            "volume": stock['volume']
                        })
        return shortlisted

    # --- Run scanner ---
    mock_stocks = generate_mock_data()
    result = scan_intraday_stocks(mock_stocks)

    # --- Display results ---
    if result:
        df = pd.DataFrame(result)
        st.success(f"{len(df)} stocks shortlisted for intraday trading")
        st.dataframe(df, use_container_width=True)

        # --- CSV Export ---
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "intraday_shortlist.csv", "text/csv")

        # --- Stock line chart selection ---
        selected_symbol = st.selectbox("📈 Select stock to view mock intraday chart", df["symbol"].unique())

        if selected_symbol:
            # Generate mock intraday line chart
            times = pd.date_range("09:15", "15:30", freq="15min").strftime("%H:%M")
            base_price = df[df["symbol"] == selected_symbol]["price"].values[0]
            prices = [base_price * random.uniform(0.98, 1.02) for _ in times]

            st.line_chart(pd.DataFrame({"Time": times, "Price": prices}).set_index("Time"))

    else:
        st.warning("No suitable intraday stocks found based on current filters.")


elif selected == "Alpha Vantage API":
    st.subheader("📈 Stock Data from Alpha Vantage")

    # Input for API key and symbol 
    api_key = st.text_input("🔑 Enter your Alpha Vantage API Key- 10MY6CQY1UCYDAOB ")
    symbol = st.text_input("📌 Enter Stock Symbol (e.g., AAPL, MSFT, RELIANCE.BSE)")

    if st.button("Fetch Data") and api_key and symbol:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=15min&apikey={api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            if "Time Series (15min)" in data:
                df = pd.DataFrame.from_dict(data["Time Series (15min)"], orient='index')
                df = df.astype(float)
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()

                st.success(f"Showing intraday data for {symbol.upper()}")
                st.line_chart(df["4. close"])

                with st.expander("📋 Show Raw Data"):
                    st.dataframe(df)

                # CSV Export
                csv = df.to_csv().encode("utf-8")
                st.download_button("⬇️ Download CSV", csv, f"{symbol}_intraday.csv", "text/csv")
            else:
                st.warning("⚠️ No intraday data found. Check symbol or API limit.")
        else:
            st.error("❌ Failed to fetch data from Alpha Vantage.")


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
      
       
        #############################################################################################################################
elif selected == "PaperTrade":

    st.subheader("📊 Backtest + Paper Trading Simulator")

    st.markdown("Upload your stock data with `Date`, `Open`, `High`, `Low`, `Close`, and `Signal` columns.")
    
    uploaded_file = st.file_uploader("📁 Upload CSV File", type=["csv"])

    if uploaded_file:
        try:
            # Load and preprocess data
            df = pd.read_csv(uploaded_file, parse_dates=["Date"])
            df.set_index("Date", inplace=True)

            st.success("✅ File successfully uploaded and processed!")
            st.dataframe(df.head())

            # Initial balance input
            initial_balance = st.number_input("💰 Initial Capital (INR)", value=100000, step=1000)

            # Backtest logic
            def backtest_paper_trade(df, initial_balance=100000):
                balance = initial_balance
                position = 0
                trade_log = []

                for i in range(1, len(df)):
                    price = df['Close'].iloc[i]
                    signal = df['Signal'].iloc[i]
                    date = df.index[i]

                    if signal == 1 and position == 0:
                        shares = balance // price
                        cost = shares * price
                        position = shares
                        balance -= cost
                        trade_log.append({
                            'Date': date, 'Action': 'BUY', 'Shares': shares,
                            'Price': price, 'Balance': balance
                        })

                    elif signal == -1 and position > 0:
                        revenue = position * price
                        balance += revenue
                        trade_log.append({
                            'Date': date, 'Action': 'SELL', 'Shares': position,
                            'Price': price, 'Balance': balance
                        })
                        position = 0

                final_value = balance + (position * df['Close'].iloc[-1])
                returns = (final_value - initial_balance) / initial_balance * 100

                return pd.DataFrame(trade_log), final_value, returns

            # Run simulation
            trade_log, final_value, returns = backtest_paper_trade(df, initial_balance)

            # Display results
            st.subheader("📘 Trade Log")
            st.dataframe(trade_log)

            st.subheader("📈 Summary")
            st.write(f"**Final Portfolio Value**: ₹{final_value:,.2f}")
            st.write(f"**Total Return**: {returns:.2f}%")

        except Exception as e:
            st.error(f"❌ Error processing file: {e}")

    else:
        st.info("📌 Please upload a CSV file to begin the simulation.")
        st.subheader("🕯️ Live Chart (Candlestick + Buy/Sell Signals)")

        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price'
        ))
        
        # Buy signals
        buy_signals = df[df['Signal'] == 1]
        fig.add_trace(go.Scatter(
            x=buy_signals.index,
            y=buy_signals['Close'],
            mode='markers',
            marker=dict(symbol='triangle-up', color='green', size=10),
            name='Buy Signal'
        ))
        
        # Sell signals
        sell_signals = df[df['Signal'] == -1]
        fig.add_trace(go.Scatter(
            x=sell_signals.index,
            y=sell_signals['Close'],
            mode='markers',
            marker=dict(symbol='triangle-down', color='red', size=10),
            name='Sell Signal'
        ))
        
        # Layout settings
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            height=600,
            template="plotly_dark",
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)

elif selected == "Live Algo Trading":
    st.title("🤖 Live Algo Trading (Paper Mode Only)")

    # ========== Telegram Setup ==========
    bot_token = "7503952210:AAE5TLirqlW3OFuEIq7SJ1Fe0wFUZuKjd3E"
    chat_id = "1320205499"
    def send_telegram_message(msg):
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML"
        }
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data=payload)

    # ========== Check Kite Session ==========
   # ========== Check Kite Session ==========
    if "kite" not in st.session_state:
        st.error("🔌 Kite session not found. Please login through 'KITE API' tab first.")
        st.stop()

    kite = st.session_state.kite

    try:
        profile = kite.profile()
        st.success(f"✅ Connected to Zerodha: {profile['user_name']} ({profile['user_id']})")
        # 💰 Funds (Margins)
        margins = kite.margins()
        equity_funds = margins['equity']['available']['cash']
        st.metric("💰 Available Funds", f"₹{equity_funds:,.2f}")
    
        # 📦 Holdings Summary
        holdings = kite.holdings()
        holding_value = sum([h['last_price'] * h['quantity'] for h in holdings])
        st.metric("📈 Holdings Value", f"₹{holding_value:,.2f}")
    
        # 📝 Orders
        orders = kite.orders()
        st.metric("📝 Total Orders", len(orders))

    except Exception as e:
        st.error(f"❌ Failed to fetch profile: {e}")
        st.error(f"❌ Error: {str(e)}")  # Capture full error message
        send_telegram_message(f"❌ Error: {str(e)}")  # Optionally send the error to Telegram for logging
        st.stop()


    # ========== User Inputs ==========
    symbol = st.text_input("📈 Symbol (e.g., INFY)")
    capital = st.number_input("💰 Capital Allocation", value=50000)
    stop_loss_percent = st.slider("🔻 Stop Loss (%)", min_value=0.5, max_value=5.0, value=1.5)
    trailing_step = st.slider("📉 Trailing SL Step (%)", min_value=0.5, max_value=5.0, value=1.0)

    start_btn = st.button("🚀 Run Doctor Strategy")

    # ========== Strategy Execution ==========
    if start_btn and symbol:
        try:
            st.write("Looking for trade")
            ltp = kite.ltp(f"NSE:{symbol}")[f"NSE:{symbol}"]["last_price"]
            qty = int(capital / ltp)
            entry = ltp
            sl = round(entry - (entry * stop_loss_percent / 100), 2)
            trailing_sl = sl
            in_position = True

            # Entry Alert
            st.success(f"📥 Paper BUY executed at ₹{entry} | SL: ₹{sl}")
            send_telegram_message(f"📥 <b>Paper BUY</b>\n<b>Symbol:</b> {symbol}\n<b>Price:</b> ₹{entry}\n<b>SL:</b> ₹{sl}\n<b>Qty:</b> {qty}")

            placeholder = st.empty()
            while in_position:
                time.sleep(10)
                ltp = kite.ltp(f"NSE:{symbol}")[f"NSE:{symbol}"]["last_price"]

                # Update trailing SL
                if ltp > entry + (entry * trailing_step / 100):
                    new_trailing_sl = round(entry + (ltp - entry - (entry * trailing_step / 100)), 2)
                    if new_trailing_sl > trailing_sl:
                        trailing_sl = new_trailing_sl
                        st.info(f"🔁 Trailing SL Updated: ₹{trailing_sl}")
                        send_telegram_message(f"🔁 <b>Trailing SL Updated</b>\n<b>New SL:</b> ₹{trailing_sl}")

                # SL hit
                if ltp <= trailing_sl:
                    st.error(f"📤 Paper SELL executed at ₹{ltp} (SL Hit)")
                    send_telegram_message(f"📤 <b>Paper SELL</b>\n<b>Symbol:</b> {symbol}\n<b>Exit:</b> ₹{ltp}\n<b>Reason:</b> SL Hit")
                    in_position = False

                # Live Metrics
                with placeholder.container():
                    st.metric("📊 Live Price", f"₹{ltp}")
                    st.metric("📉 Trailing SL", f"₹{trailing_sl}")
                    st.metric("📦 Quantity", qty)

        except Exception as e:
            st.error(f"❌ Error: {e}")

elif selected == "Test Doctor2 Strategy":
    st.title("🤖 Test Doctor2 Strategy")
    # Trade log to store trade details
    trade_log = []
    import numpy as np
    
    def read_csv_data(uploaded_file):
        try:
            # Read CSV data into DataFrame
            data = pd.read_csv(uploaded_file)
            
            # Ensure the Date column is parsed as a datetime object
            data['Date'] = pd.to_datetime(data['Date'])
            data.set_index('Date', inplace=True)
    
            # Ensure correct column names for OHLCV
            expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in data.columns for col in expected_columns):
                raise ValueError("⚠️ Missing required columns in CSV. Ensure you have Open, High, Low, Close, and Volume columns.")
    
            data.dropna(inplace=True)  # Drop rows with missing data
            return data
    
        except Exception as e:
            st.error(f"⚠️ Error reading the CSV: {e}")
            return pd.DataFrame()
    
    def check_crossing(data):
        if 'Close' not in data.columns:
            raise KeyError("❌ 'Close' column is missing in the DataFrame!")
    
        # Calculate 20‑period SMA
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
    
        # Drop rows where SMA is NaN (first 19 rows)
        data.dropna(subset=['SMA_20'], inplace=True)
    
        # Mark crossings
        data['crossed'] = (data['Close'] > data['SMA_20']).astype(int)
        return data
    
    def check_iv(data, iv_threshold=16):
        # Mock IV — replace with real API call if available
        data['IV'] = 17
        data['iv_check'] = np.where(data['IV'] >= iv_threshold, 1, 0)
        return data
    
    def execute_trade(data):
        for i in range(1, len(data)):
            if data['crossed'].iat[i] == 1 and data['iv_check'].iat[i] == 1:
                entry = data['Close'].iat[i]
                sl = entry * 0.90
                tg = entry * 1.05
                entry_time = data.index[i]
                
                # Log the trade details
                trade_log.append({
                    'Entry Time': entry_time,
                    'Entry Price': entry,
                    'Stop Loss': sl,
                    'Target Price': tg,
                    'Status': 'Open'
                })
                
                st.success(f"✅ Trade @ ₹{entry:.2f}  SL: ₹{sl:.2f}  TG: ₹{tg:.2f}")
                return entry, sl, tg, entry_time
        st.info("ℹ️ No trade signal.")
        return None, None, None, None
    
    def manage_risk(entry, sl, tg, data):
        for price in data['Close']:
            if price >= tg:
                st.success(f"🎯 Target hit @ ₹{price:.2f}")
                close_trade('Target Hit')
                return True
            if price <= sl:
                st.error(f"🛑 SL hit @ ₹{price:.2f}")
                close_trade('Stop Loss Hit')
                return True
        return False
    
    def close_trade(status):
        # Update the last trade in the log to "Closed"
        if trade_log:
            trade_log[-1]['Status'] = status
    
    # --- Streamlit UI ---
    st.title("📊 Doctor Trade Strategy")
    
    # Sidebar inputs
    uploaded_file = st.file_uploader("Upload OHLCV CSV File", type=["csv"])
    
    # Handle CSV file upload
    if uploaded_file is not None:
        # Read data from CSV
        df = read_csv_data(uploaded_file)
        if not df.empty:
            st.subheader("Raw Data")
            st.dataframe(df.tail(20))
    
            try:
                df = check_crossing(df)
                df = check_iv(df)
    
                # Plot
                fig = go.Figure([
                    go.Candlestick(x=df.index,
                                   open=df['Open'], high=df['High'],
                                   low=df['Low'],   close=df['Close']),
                    go.Scatter(     x=df.index,
                                   y=df['SMA_20'],
                                   mode='lines',
                                   name='20 SMA')
                ])
                fig.update_layout(title="OHLCV Data with 20 SMA", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
    
                # Trade logic
                entry, sl, tg, t0 = execute_trade(df)
                if entry is not None:
                    if manage_risk(entry, sl, tg, df):
                        st.info("🔁 Trade Closed (SL/TG hit)")
    
            except Exception as e:
                st.error(f"❌ Strategy error: {e}")
    
            # Display trade log
            if trade_log:
                st.subheader("Trade Log")
                trade_df = pd.DataFrame(trade_log)
                st.dataframe(trade_df)
    
    else:
        st.warning("⚠️ Please upload a CSV file.")

elif selected == "Doctor2.0 Strategy":
    st.title("⚙️ Test Doctor2.0 Strategy")

    uploaded_file = st.file_uploader("Upload 5-minute Nifty/Bank Nifty CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        # Convert and prepare datetime
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        df.set_index('Date', inplace=True)

        # Calculate Bollinger Bands (20 SMA)
        df['20sma'] = df['Close'].rolling(window=20).mean()
        df['stddev'] = df['Close'].rolling(window=20).std()
        df['upper_band'] = df['20sma'] + 2 * df['stddev']
        df['lower_band'] = df['20sma'] - 2 * df['stddev']

        # Track trades
        trades = []

        for i in range(21, len(df)-2):
            candle = df.iloc[i]
            prev_candle = df.iloc[i-1]

            # Step 2-4: 20 SMA Cross & confirmation
            crossed_up = prev_candle['Close'] < prev_candle['20sma'] and candle['Close'] > candle['20sma']
            closed_above = candle['Close'] > candle['20sma'] and candle['Low'] > candle['20sma']

            if crossed_up and closed_above:
                reference_candle = candle
                prev2_candle = df.iloc[i-2]

                ref_level = max(prev2_candle['High'], prev2_candle['Close'])
                next_candle = df.iloc[i+1]

                if next_candle['High'] > ref_level:
                    entry_price = next_candle['Close']
                    sl_price = entry_price * 0.90
                    target1 = entry_price * 1.05
                    target2 = entry_price * 1.10
                    target3 = entry_price * 1.15
                    final_target = entry_price * 1.20

                    trades.append({
                        'Entry Time': next_candle.name,
                        'Entry Price': round(entry_price, 2),
                        'SL': round(sl_price, 2),
                        'T1': round(target1, 2),
                        'T2': round(target2, 2),
                        'T3': round(target3, 2),
                        'T4': round(final_target, 2),
                        'Reference High': round(ref_level, 2)
                    })

        # Display trades
        st.subheader("📈 Doctor2.0 Strategy Trades")
        if trades:
            trades_df = pd.DataFrame(trades)
            st.dataframe(trades_df)
        else:
            st.warning("No valid trades found based on strategy rules.")

elif selected == "Strategy2.0 Detail":
    st.title("📋 Project Details")

    st.markdown("""
        स्ट्रॅटेजीचा संपूर्ण प्लॅन खालील प्रमाणे आहे:

        📌 Step 1: चार्ट सेटअप
        चार्टवर बोलिंजर बँड (Bollinger Bands) वापरा.
        
        कँडलस्टिक पॅटर्न वापरा, लाईन/हायकन अश्यि नको.
        
        टाइम फ्रेम – ५ मिनिटांचा चार्ट.
        
        📌 Step 2: Center Line (20 SMA) क्रॉसिंग
        बोलिंजर बँडची मधली लाईन म्हणजेच 20 SMA.
        
        Nifty किंवा Bank Nifty ने ही लाईन खालून वर क्रॉस केली पाहिजे.
        
        📌 Step 3: क्रॉस झालेली कँडल त्याच कँडलमध्ये वर क्लोज झाली पाहिजे
        जेव्हा 20 SMA ला क्रॉस करणारी कँडल कॅन्डल उर्ध्वगामी क्लोज होते, तेव्हा त्याची खात्री करा.
        
        📌 Step 4: 20 SMA च्या वर कँडल क्लोज
        त्याच्या नंतरच्या कँडलने 20 SMA ला touch न करता, 20 SMA च्या वर क्लोज झाले पाहिजे.
        
        📌 Step 5: रेफरन्स कँडल मार्क करा
        20 SMA ला क्रॉस करणारी कँडल ही रेफरन्स कँडल म्हणून मार्क करा.
        
        📌 Step 6: रेफरन्स कँडलच्या अगोदरच्या कँडलचा हाय आणि क्लोज
        रेफरन्स कँडलच्या अगोदरच्या कँडलचा हाय आणि क्लोज दोन्हीमध्ये जे मोठे असेल, ते रेफरन्स कँडल नंतरच्या कँडलने खालून वर क्रॉस करत असताना ट्रेड एक्झिक्युट करा.
        
        स्टॉप लॉस त्याच्याखाली 10% असावा.
        
        📌 Step 7: रेफरन्स कँडलच्या अगोदरची कँडल
        रेफरन्स कँडलच्या अगोदरची कँडल ही 20 SMA ला क्रॉस करणारी कँडल म्हणून ओळखली जाईल.
        
        📌 Step 8: रेफरन्स कँडलच्या अगोदरच्या कँडलचा हाय किंवा क्लोज वरून ट्रेड एंटर करा
        रेफरन्स कँडल नंतरच्या कँडलने, त्याच्या अगोदरच्या कँडलचा हाय आणि क्लोज दोन्ही हिट केली पाहिजे.
        
        त्या स्थितीत In the Money Call Option खरेदी करा.
        
        📌 Step 9: प्रॉफिट बुकिंग आणि ट्रेलिंग स्टॉप लॉस
        ट्रेड घेतल्यावर:
        
        10% Stop Loss.
        
        5% Profit Target.
        
        जेव्हा Profit 4% पेक्षा जास्त जाईल, तेव्हा Stop Loss ला Buy Price पर्यंत ट्रेल करा (No Loss Zone).
        
        नंतर, प्रॉफिटमध्ये वाढ केल्यास:
        
        10% Profit वर Stop Loss ला 4% Profit वर ट्रेल करा.
        
        15% Profit वर Stop Loss ला 11% Profit वर ट्रेल करा.
        
        20% Profit झाल्यावर, संपूर्ण प्रॉफिट बुक करा.
        
        📌 Step 10: Implied Volatility चा तपास
        Nifty किंवा Bank Nifty चं Implied Volatility (IV) 16% किंवा त्याहून जास्त असावी, जेव्हा ट्रेड घेण्याचा निर्णय घेतला जातो.
        
        📌 Step 11: ब्रेकआउट आणि ट्रेड इनिशिएशन
        Reference Candle च्या High च्या वर जर पुढील कँडल गेली, तर लगेच त्या इंडेक्सचा सर्वात जवळचा In the Money Call Option खरेदी करा.
        
        📌 Step 12: Risk Management – Stop Loss आणि Profit Booking
        ट्रेड घेतल्यावर:
        
        10% Stop Loss.
        
        5% Profit Target.
        
        जेव्हा Profit 4% पेक्षा जास्त जाईल, तेव्हा Stop Loss ला Buy Price पर्यंत ट्रेल करा (No Loss Zone).
        
        नंतर 10% प्रॉफिट झाल्यावर Stop Loss ला 4% Profit वर ट्रेल करा.
        
        15% प्रॉफिट झाल्यावर Stop Loss ला 11% Profit वर ट्रेल करा.
        
        20% प्रॉफिट झाल्यावर, संपूर्ण प्रॉफिट बुक करा.
        
        📌 Step 13: Time-Based Exit
        ट्रेड इनिशिएट केल्यानंतर 10 मिनिटात, वरच्या पैकी कोणतीही Condition (Target/SL) हिट झाली नाही तर, त्या ट्रेडला तिथेच बुक करा, Profit Loss न पाहता.
        
        📌 Step 14: Trade Time from 9:30 AM to 3:00 PM
        ट्रेड फक्त 9:30 AM ते 3:00 PM दरम्यानच घेतला जावा.
        
        9:30 AM च्या आधी किंवा 3:00 PM नंतर ट्रेड सुरू होणार नाही.
        
        या स्टेप्समध्ये, प्रत्येक ट्रेडमध्ये तुम्ही सुरक्षितपणे आणि परिणामकारकपणे ट्रेड घेण्याचा प्रयत्न करू शकता. आपला Doctor Trade Strategy याप्रमाणे अधिक मजबूत आणि प्रॉफिटेबल होईल.

        ✅ Development Checklist:
        डेटा सोर्सिंग:
        
        5-minute candles for Nifty/Bank Nifty (live + historical).
        
        Bollinger Bands (20 SMA basis) calculation.
        
        IV value from NSE option chain or API.
        
        Reference Candle Logic:
        
        SMA cross check
        
        Close above 20 SMA without touching
        
        Identify reference and pre-reference candles
        
        Trigger check (next candle breaking pre-reference high/close)
        
        Trade Execution (Paper Trading / Live via Zerodha/Fyers API):
        
        ATM Call Option Buy
        
        SL/Target apply
        
        Trailing SL updates
        
        Time-based exit after 10 min if no SL/TP
        
        Trade Management Logic:
        
        Risk Management Module (as per Step 12)
        
        Trail logic:
        
        4% → No loss
        
        10% → SL @ 4%
        
        15% → SL @ 11%
        
        20% → Book full
        
        Streamlit Dashboard UI:
        
        Left Sidebar: Stock selection, Time range, Capital, Risk %, etc.
        
        Right Main: Chart view (candles + BB + markers), Live log, Trade Summary
        
        Telegram Alerts Integration:
        
        Entry/Exit alerts with levels
        
        IV alert (if below 16%, don’t trade)
                    """)

elif selected == "Doctor3.0 Strategy":
    st.title("⚙️ Test Doctor3.0 Strategy")

    st.markdown("""
    ### 📋 Doctor 3.0 स्ट्रॅटेजी प्लॅन:

    ✅ **चार्ट सेटअप**: 5 मिनिटांचा कँडलस्टिक चार्ट + Bollinger Band (20 SMA). 

    ✅ **20 SMA क्रॉसिंग:**
    - कँडलने 20 SMA लाईन खालून वर क्रॉस करून क्लोज केली पाहिजे.
    - नंतरची कँडल ही 20 SMA ला touch न करता वर क्लोज झाली पाहिजे.

    ✅ **Reference Candle Setup:**
    - क्रॉस करणारी कँडल = Reference Candle
    - त्याच्या अगोदरची कँडल महत्त्वाची: तिचा High/Close दोन्हीपैकी जास्त किंमत मार्क करा.
    - नंतरची कँडल ह्या किमतीला खालून वर ब्रेक करत असल्यास ट्रेड एंटर करा.

    ✅ **Entry Condition:**
    - Reference candle नंतरच्या कँडलने prior candle चा High/Close cross केलं पाहिजे.
    - आणि IV > 16% असेल तर, त्या वेळी In the Money Call Option खरेदी करा.

    ✅ **Risk Management:**
    - Entry नंतर Stop Loss: Buy Price - 10%
    - Profit Target: 5%
    - Profit > 4% झाल्यावर Stop Loss ला Entry Price ला ट्रेल करा (No Loss Zone).
    - Profit > 10% = SL @ 4%, Profit > 15% = SL @ 11%, Profit > 20% = Book full profit

    ✅ **Time Based Exit:**
    - Trade घेतल्यावर 10 मिनिटात काहीही हिट न झाल्यास, नफा/तोटा न पाहता एक्झिट करा.

    ✅ **Trade Time:**
    - सकाळी 9:30 ते दुपारी 3:00 पर्यंतच ट्रेड सुरू करा.
    """)

    uploaded_file = st.file_uploader("Upload CSV file with OHLCV data", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()

        if {'Open', 'High', 'Low', 'Close', 'Volume', 'Date'}.issubset(df.columns):
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values("Date")
            st.success("✅ Data loaded successfully!")
            st.dataframe(df.tail())

            # Calculate 20 SMA and Bollinger Bands
            df['SMA20'] = df['Close'].rolling(window=20).mean()
            df['Upper'] = df['SMA20'] + 2 * df['Close'].rolling(window=20).std()
            df['Lower'] = df['SMA20'] - 2 * df['Close'].rolling(window=20).std()

            # Detect breakout condition
            breakout_signals = []
            entry_price = None
            sl_price = None
            tp_price = None

            for i in range(21, len(df) - 1):
                prev = df.iloc[i - 1]
                curr = df.iloc[i]
                next_candle = df.iloc[i + 1]
                iv = 18  # simulated implied volatility

                if (prev['Close'] < prev['SMA20']) and (curr['Close'] > curr['SMA20']) and (curr['Low'] > curr['SMA20']):
                    ref_price = max(prev['High'], prev['Close'])
                    if next_candle['Close'] > ref_price and iv > 16:
                        entry_price = next_candle['Close']
                        sl_price = entry_price * 0.90
                        tp_price = entry_price * 1.05
                        breakout_signals.append({
                            'Time': df.iloc[i + 1]['Date'],
                            'Entry': entry_price,
                            'SL': sl_price,
                            'TP': tp_price,
                            'IV': iv,
                            'Result': None
                        })

            # Paper Trading Simulation
            results = []
            for signal in breakout_signals:
                trade_open = False
                entry = signal['Entry']
                sl = signal['SL']
                tp = signal['TP']
                entry_time = signal['Time']
                exit_time = entry_time + pd.Timedelta(minutes=10)

                for idx, row in df.iterrows():
                    if row['Date'] < entry_time:
                        continue
                    if row['Date'] > exit_time:
                        results.append({**signal, 'Exit': row['Close'], 'Reason': 'Time Exit'})
                        break
                    if row['Low'] <= sl:
                        results.append({**signal, 'Exit': sl, 'Reason': 'Stop Loss Hit'})
                        break
                    if row['High'] >= tp:
                        results.append({**signal, 'Exit': tp, 'Reason': 'Profit Target Hit'})
                        break

            if results:
                result_df = pd.DataFrame(results)
                st.subheader("📊 Paper Trading Results")
                st.dataframe(result_df)
            else:
                st.info("🚫 No trades detected.")

        else:
            st.error("CSV must contain the following columns: Date, Open, High, Low, Close, Volume")
