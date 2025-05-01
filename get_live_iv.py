import streamlit as st
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 minutes (300000 ms)
st_autorefresh(interval=300000, key="iv_refresh")

st.set_page_config(page_title="Live Nifty IV", layout="wide")
st.title("📈 Live Nifty Option Chain IV (Every 5 Minutes)")

@st.cache_data(ttl=300)  # Cache for 5 mins
def fetch_nifty_option_chain():
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/option-chain"
    }
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)  # Set cookie
    response = session.get(url, headers=headers)
    data = response.json()

    df = []
    for item in data['records']['data']:
        strike = item.get('strikePrice')
        ce_iv = item.get('CE', {}).get('impliedVolatility')
        pe_iv = item.get('PE', {}).get('impliedVolatility')
        if ce_iv and pe_iv:
            df.append({'Strike': strike, 'CE IV': ce_iv, 'PE IV': pe_iv})
    return pd.DataFrame(df)

try:
    df_iv = fetch_nifty_option_chain()
    atm_iv = df_iv.loc[df_iv['Strike'].sub(df_iv['Strike'].mean()).abs().idxmin()]
    
    st.subheader(f"✅ Approx ATM Strike: {atm_iv['Strike']}")
    st.write(f"📌 CE IV: {atm_iv['CE IV']} | PE IV: {atm_iv['PE IV']}")
    st.dataframe(df_iv.sort_values(by="Strike").reset_index(drop=True))
except Exception as e:
    st.error("⚠️ Failed to fetch data from NSE. Try again later.")
    st.exception(e)
