import streamlit as st
import yfinance as yf
import pandas as pd

# Set Streamlit page config first!
st.set_page_config(page_title="📈 NIFTY 100 Stocks", layout="wide")

# Title
st.title("📊 NIFTY 100 Stock Overview")
st.caption("Live Close, % Change, and Volume")

# NIFTY 100 stock symbols (partial for example, full list recommended)
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

    # Add remaining NIFTY 100 tickers here...
]

# Progress bar
progress = st.progress(0)

# Empty list for storing data
stock_data = []

for i, symbol in enumerate(nifty100_symbols):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='1d', interval='1m')
        if not df.empty:
            last = df.iloc[-1]
            first = df.iloc[0]
            close = round(last['Close'], 2)
            change_pct = round(((last['Close'] - first['Close']) / first['Close']) * 100, 2)
            volume = int(last['Volume'])
            stock_data.append({
                "Symbol": symbol.replace(".NS", ""),
                "Close": close,
                "Change %": change_pct,
                "Volume": volume
            })
    except Exception as e:
        st.warning(f"Failed to fetch {symbol}: {e}")

    progress.progress((i + 1) / len(nifty100_symbols))

# Create DataFrame
df_final = pd.DataFrame(stock_data)
df_final = df_final.sort_values(by="Change %", ascending=False)

# Show data table
st.dataframe(df_final, use_container_width=True)
