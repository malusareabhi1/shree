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

# Global kite object placeholder
if 'kite' not in st.session_state:
    st.session_state.kite = None
# Page configuration
st.set_page_config(layout="wide", page_title="Trade Strategy Dashboard")
    
# Sidebar navigation
with st.sidebar:
    selected = option_menu(
    menu_title="Trade Strategy",
    options=[
        "Dashboard", "Get Stock Data", "Test Strategy", "Swing Trade Strategy",
        "Intraday Stock Finder", "Trade Log", "Account Info", "Candle Chart", "Strategy Detail", "Project Detail", "KITE API", "API","Alpha Vantage API"
    ],
    icons=[
        "bar-chart", "search", "cpu", "arrow-repeat",
        "search", "clipboard-data", "wallet2", "graph-up", "info-circle", "file-earmark", "code-slash", "code-slash", "code-slash"
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
    import streamlit.components.v1 as components

        # Embed TradingView Ticker Tape widget
        ticker_embed_code = """
        <iframe src="https://www.tradingview.com/widgetembed/?frameElementId=tradingview_e9ab9&symbol=NSE%3ANIFTY%2CNSE%3ABANKNIFTY" 
        width="100%" height="100" style="border: none;"></iframe>
        """

        # Display the ticker in the main area
        st.subheader("📈 Live Market Ticker (Nifty & BankNifty)")
        components.html(ticker_embed_code, height=100)

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
        
    

  
    


elif selected == "Test Strategy":
    st.title("⚙️ Test Trade Strategy")

    uploaded_file = st.file_uploader("Upload CSV file", type="csv")
    capital = st.number_input("Capital Allocation (₹)", value=50000)

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.success("File uploaded successfully")

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

elif selected == "Strategy Detail":
    st.title("ℹ️ Strategy Details")

    st.markdown("""
    **Objective:** Implement a simple strategy based on basic moving averages and volatility.
    
    **Strategy Highlights:**
    - Buy when the price crosses above the moving average and volatility is low.
    - Sell when the price falls below the moving average and volatility is high.
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
