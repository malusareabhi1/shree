import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from streamlit_option_menu import option_menu
import plotly.express as px

# --- Streamlit App Configuration ---
st.set_page_config(page_title="Doctor Trade Dashboard", layout="wide")

# --- Sidebar Navigation ---
with st.sidebar:
    selected = option_menu(
        menu_title="Doctor Trade",
        options=["Dashboard", "Get Stock Data", "Test Strategy", "Trade Log", "Account Info"],
        icons=["bar-chart", "search", "cpu", "clipboard-data", "wallet2"],
        menu_icon="cast",
        default_index=0,
    )

# --- Main Content ---
if selected == "Dashboard":
    st.title("📊 Welcome to Doctor Trade Dashboard")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Available Capital", "₹100,000")
        st.metric("Used Capital", "₹50,000")
    with col2:
        st.metric("Net PnL", "₹12,000")
        st.metric("Hit Ratio", "62%")

elif selected == "Get Stock Data":
    # unchanged get stock data block
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
    from_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
    to_date = st.date_input("To Date", datetime.now())
    interval = st.selectbox("Select Interval", ["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"], index=5)

    if st.button("Fetch Data"):
        st.info(f"Fetching data for {stock} from {from_date} to {to_date} at {interval}")
        try:
            df = yf.download(stock, start=from_date, end=to_date, interval=interval)
            if df.empty:
                st.warning("No data returned. Check symbol or interval.")
            else:
                df.reset_index(inplace=True)
                st.dataframe(df)
                datetime_col = "Datetime" if "Datetime" in df.columns else "Date"
                st.line_chart(df.set_index(datetime_col)["Close"])
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Data as CSV", data=csv, file_name=f"{stock.replace('.','_')}_{interval}.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Error: {e}")

elif selected == "Test Strategy":
    st.title("⚙️ Test Doctor Trade Strategy")

    strategy = st.selectbox("Choose Strategy", ["Simple Diff", "Bollinger ATR"])
    uploaded_file = st.file_uploader("Upload OHLCV CSV (Date,Open,High,Low,Close,Volume)", type=["csv"])
    capital = st.number_input("Capital Allocation (₹)", value=50000)

    if uploaded_file is not None and st.button("Run Backtest"):
        df = pd.read_csv(uploaded_file)
        if 'Date' not in df.columns or 'Close' not in df.columns:
            st.error("CSV must contain 'Date' and 'Close' columns.")
        else:
            df['Date'] = pd.to_datetime(df['Date'])
            df.sort_values('Date', inplace=True)
            df.reset_index(drop=True, inplace=True)

            # Prepare for trades
            trade_log = []
            balance = capital
            equity_curve = []

            if strategy == "Simple Diff":
                # Simple price diff strategy
                df['Signal'] = df['Close'].diff().apply(lambda x: 'BUY' if x>0 else 'SELL')
                df.dropna(subset=['Signal'], inplace=True)
                for idx, row in df.iterrows():
                    if row['Signal'] == 'BUY':
                        entry = row['Close']
                        qty = int(balance // entry)
                        trade_log.append({**row[['Date']].to_dict(), 'Action':'BUY', 'Qty':qty, 'Price':entry, 'PnL':0})
                    else:
                        exitp = row['Close']
                        pnl = (exitp - trade_log[-1]['Price']) * trade_log[-1]['Qty']
                        balance += pnl
                        trade_log.append({**row[['Date']].to_dict(), 'Action':'SELL', 'Qty':trade_log[-1]['Qty'], 'Price':exitp, 'PnL':pnl})
                        equity_curve.append({'Date':row['Date'],'Equity':balance})
            else:
                # Bollinger ATR strategy
                df['MA20'] = df['Close'].rolling(20).mean()
                df['STD20'] = df['Close'].rolling(20).std()
                df['Upper'] = df['MA20'] + 2*df['STD20']
                df['ATR'] = (df['High'] - df['Low']).rolling(14).mean()
                position=False
                stop_loss=0
                for i,row in df.iterrows():
                    if not position and row['Close']>row['Upper']:
                        entry=row['Close']; qty=int(balance//entry)
                        stop_loss=entry-row['ATR']*1.5; position=True
                        trade_log.append({'Date':row['Date'],'Action':'BUY','Qty':qty,'Price':entry,'PnL':0})
                    elif position and (row['Close']<stop_loss or row['Close']<df.at[i-1,'MA20']):
                        exitp=row['Close']; pnl=(exitp-entry)*qty; balance+=pnl; position=False
                        trade_log.append({'Date':row['Date'],'Action':'SELL','Qty':qty,'Price':exitp,'PnL':pnl})
                        equity_curve.append({'Date':row['Date'],'Equity':balance})

            trade_log_df = pd.DataFrame(trade_log)
            equity_df = pd.DataFrame(equity_curve)

            # Metrics
            net_pnl = trade_log_df['PnL'].sum()
            wins=(trade_log_df['PnL']>0).sum(); losses=(trade_log_df['PnL']<0).sum()
            win_rate = wins/(wins+losses)*100 if wins+losses>0 else 0
            avg_pnl=trade_log_df['PnL'].mean() if not trade_log_df.empty else 0

            # Store in session
            st.session_state['trade_log_df']=trade_log_df
            st.session_state['net_pnl']=net_pnl
            st.session_state['used_capital']=capital

            # Display
            st.subheader(f"Results: {strategy}")
            st.metric("Net PnL", f"₹{net_pnl:.2f}")
            st.metric("Win Rate", f"{win_rate:.2f}%")
            st.metric("Avg Profit", f"₹{avg_pnl:.2f}")

            if not equity_df.empty:
                fig=px.line(equity_df,x='Date',y='Equity',title='Equity Curve')
                st.plotly_chart(fig)

            st.subheader("Trade Log")
            st.dataframe(trade_log_df)
            csv=trade_log_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Trade Log",data=csv,file_name="trade_log.csv",mime="text/csv")

elif selected == "Trade Log":
    st.title("📋 Trade Log")
    if 'trade_log_df' in st.session_state:
        df=st.session_state['trade_log_df']
        st.dataframe(df)
    else:
        st.info("Run a strategy to generate trade log.")

elif selected == "Account Info":
    st.title("💼 Account Information")
    starting=100000; net=st.session_state.get('net_pnl',0); used=st.session_state.get('used_capital',0)
    funds=pd.DataFrame({'Metric':['Available','Used','Net PnL'],'Value':[starting+net,used,net]})
    st.table(funds)
    st.write("Open Positions and last order can be derived similarly.")
