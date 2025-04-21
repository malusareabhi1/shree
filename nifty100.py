import streamlit as st
import yfinance as yf
import pandas as pd

# 🔹 Must be first Streamlit command
st.set_page_config(page_title="📈 NIFTY 100 Stocks", layout="wide")

st.title("📊 NIFTY 100 Stocks Live Overview")

# ✅ Define highlight function BEFORE using it
def highlight_change(val):
    try:
        color = 'green' if val > 0 else 'red'
        return f'background-color: {color}; color: white'
    except:
        return ''

# 🔸 NIFTY 100 stock symbols (Yahoo format)
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

# 🔹 Download last 2 days to compute % change
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

# ✅ Use the highlight function here
styled_df = df_stocks.style.applymap(highlight_change, subset=['% Change'])

st.dataframe(styled_df, use_container_width=True)
