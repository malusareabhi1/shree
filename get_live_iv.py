import requests
import pandas as pd

def fetch_nifty_option_chain():
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/option-chain"
    }
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)  # set cookies

    response = session.get(url, headers=headers)
    data = response.json()

    records = []
    for d in data['records']['data']:
        if 'CE' in d and 'PE' in d:
            strike = d['strikePrice']
            ce_iv = d['CE'].get('impliedVolatility')
            pe_iv = d['PE'].get('impliedVolatility')
            records.append({'Strike': strike, 'CE_IV': ce_iv, 'PE_IV': pe_iv})
    return pd.DataFrame(records)
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# Auto-refresh every 5 min (300000 ms)
st_autorefresh(interval=300000, key="iv_refresh")

st.title("🔍 Live Nifty Option Chain IV")
df_iv = fetch_nifty_option_chain()
st.dataframe(df_iv)
