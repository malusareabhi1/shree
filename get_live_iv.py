import requests
import pandas as pd
import streamlit as st
def get_live_iv_from_nse(symbol="NIFTY"):
    """
    Fetches live Implied Volatility (IV) data from NSE Option Chain for the given index.
    
    Parameters:
        symbol (str): "NIFTY" or "BANKNIFTY"
    
    Returns:
        pd.DataFrame: DataFrame with Expiry, Strike, CE IV, PE IV
    """
    url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": f"https://www.nseindia.com/option-chain"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)  # Set cookies

    response = session.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        raise Exception("Failed to fetch option chain data.")

    data = response.json()

    records = []
    for item in data["records"]["data"]:
        strike = item.get("strikePrice")
        expiry = item.get("expiryDate")
        ce_iv = item.get("CE", {}).get("impliedVolatility")
        pe_iv = item.get("PE", {}).get("impliedVolatility")

        if ce_iv is not None and pe_iv is not None:
            records.append({
                "Expiry": expiry,
                "Strike": strike,
                "CE_IV": ce_iv,
                "PE_IV": pe_iv
            })

    return pd.DataFrame(records)

# Example usage:
if __name__ == "__main__":
    df_iv = get_live_iv_from_nse("NIFTY")
    #print(df_iv.head())
    st.write(df_iv.head())
     st.write(df_iv)
