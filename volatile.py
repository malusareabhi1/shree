import pandas as pd
import requests
from io import StringIO

url = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"
headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
data = response.text

df = pd.read_csv(StringIO(data))
print(df.columns)  # Debug: See what columns are actually present

# Adjust the column name if needed
if 'Symbol' in df.columns:
    nifty_200 = [symbol + ".NS" for symbol in df['Symbol']]
elif 'SYMBOL' in df.columns:
    nifty_200 = [symbol + ".NS" for symbol in df['SYMBOL']]
else:
    raise ValueError("Column 'Symbol' not found in CSV")

print(nifty_200)
