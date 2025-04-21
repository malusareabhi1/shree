import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Set page config (MUST BE FIRST)
st.set_page_config(page_title="📈 NIFTY 100 Live & Chart", layout="wide")

st.title("📊 NIFTY 100 Live Data & Stock Chart")

# Helper to color % change
def highlight_change(val):
    try:
        color = 'green' if val > 0 else 'red'
        return f'background-color: {color}; color: white'
    except:
        return ''

# NIFTY 100 stock list
nifty100_symbols = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "LT.NS", "ITC.NS", "SBIN.NS", "AXISBANK.NS",
    "HINDUNILVR.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "MARUTI.NS", "DMART.NS",
    "HCLTECH.NS", "SUNPHARMA.NS", "WIPRO.NS", "ULTRACEMCO.NS", "NTPC.NS", "TITAN.NS", "POWERGRID.NS", "TATASTEEL.NS",
    "JSWSTEEL.NS", "ADANIENT.NS", "ADANIPORTS.NS", "HDFCLIFE.NS", "BAJAJFINSV.NS", "BPCL.NS", "CIPLA.NS", "DIVISLAB.NS",
    "EICHERMOT.NS", "GRASIM.NS", "HINDALCO.NS", "IOC.NS", "M&M.NS", "TECHM.NS", "ONGC.NS", "DRREDDY.NS", "BRITANNIA.NS",
    "COALINDIA.NS", "NESTLEIND.NS", "HEROMOTOCO.NS", "TATAMOTORS.NS", "PIDILITIND.NS", "BAJAJ-AUTO.NS", "ICICIPRULI.NS",
    "INDUSINDBK.NS", "SBILIFE.NS", "SHREECEM.NS", "UPL.NS", "AMBUJACEM.NS", "GAIL.NS", "DABUR.NS", "HAVELLS.NS",
    "BERGEPAINT.NS", "BIOCON.NS", "CHOLAFIN.NS", "DLF.NS", "HINDPETRO.NS", "L&TFH.NS", "MANAPPURAM.NS", "MUTHOOTFIN.NS",
    "NAUKRI.NS", "PETRONET.NS", "PIIND.NS", "SRF.NS", "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "VEDL.NS", "ZOMATO.NS",
    "ICICIGI.NS", "BOSCHLTD.NS", "CANBK.NS", "BANDHANBNK.NS", "INDIGO.NS", "PAGEIND.NS", "LUPIN.NS", "PFC.NS", "PNB.NS",
    "RECLTD.NS", "IDFCFIRSTB.NS", "BEL.NS", "IRCTC.NS", "POLYCAB.NS", "SYNGENE.NS", "ABB.NS", "INDUSTOWER.NS",
    "MARICO.NS", "BANKBARODA.NS", "MCDOWELL-N.NS", "AUBANK.NS", "BHEL.NS", "ATGL.NS", "HAL.NS", "JINDALSTEL.NS"
]

# Load data for last 2 days
data = yf.download(tickers=nifty100_symbols, period="2d", interval="1d", group_by='ticker', progress=False)

stock_data = []
for symbol in nifty100_symbols:
    try:
        df = data[symbol]
        close_yesterday = df['Close'].iloc[0]
        close_today = df['Close'].iloc[1]
        volume_today = df['Volume'].iloc[1]
        pct_change = ((close_today - close_yesterday) / close_yesterday) * 100

        stock_data.append({
            'Symbol': symbol.replace(".NS", ""),
            'Close': round(close_today, 2),
            '% Change': round(pct_change, 2),
            'Volume': int(volume_today)
        })
    except:
        continue

df_stocks = pd.DataFrame(stock_data)
st.subheader("📋 NIFTY 100 Stock Table")
st.dataframe(df_stocks.style.applymap(highlight_change, subset=['% Change']), use_container_width=True)

# --- Chart Section ---
st.subheader("📈 View Stock Chart")

# Select stock and interval
stock_selected = st.selectbox("Select Stock", sorted([s.replace(".NS", "") for s in nifty100_symbols]))
interval = st.selectbox("Select Interval", ["1d", "1h", "15m", "5m", "1m"])  # Note: Smaller intervals only work for shorter periods

# Convert back to Yahoo symbol
stock_symbol = stock_selected + ".NS"

# Download 1 month data
chart_data = yf.download(stock_symbol, period="1mo", interval=interval)

# Plotting
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=chart_data.index,
    open=chart_data['Open'],
    high=chart_data['High'],
    low=chart_data['Low'],
    close=chart_data['Close'],
    name='Price'
))

fig.update_layout(title=f"{stock_selected} - Last 1 Month ({interval})", xaxis_title="Date", yaxis_title="Price (₹)", height=500)
st.plotly_chart(fig, use_container_width=True)
