import requests
from bs4 import BeautifulSoup
import json
import time

def get_nifty_option_chain():
    url = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/option-chain"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers)  # Needed to get cookies

    response = session.get(url, headers=headers)
    data = response.json()

    # Example: extract IVs for ATM strike (based on current underlying price)
    underlying_price = data['records']['underlyingValue']
    atm_strike = min(data['records']['data'], key=lambda x: abs(x['strikePrice'] - underlying_price))
    
    ce_iv = atm_strike['CE']['impliedVolatility']
    pe_iv = atm_strike['PE']['impliedVolatility']

    return {
        'Underlying': underlying_price,
        'Strike': atm_strike['strikePrice'],
        'CE_IV': ce_iv,
        'PE_IV': pe_iv
    }

# Continuous check for IV every 60 seconds
def monitor_iv():
    while True:
        iv_data = get_nifty_option_chain()
        print(iv_data)
        print(f"Current Nifty IV: {iv_data}")  # Print or process the IV data
        time.sleep(30)  # Wait for 60 seconds before checking again

# Call the function to start monitoring
monitor_iv()

#iv_data = get_nifty_option_chain()
#print(iv_data)
