import yfinance as yf
import pandas as pd

def is_sma_rising(sma_series):
    return sma_series[-1] > sma_series[-2] > sma_series[-3]

def scan_bhanushali_strategy(stock, interval='1d', period='3mo'):
    df = yf.download(stock, interval=interval, period=period)
    if df.empty or len(df) < 50:
        return None

    df['SMA44'] = df['Close'].rolling(44).mean()

    # Check if last candle crosses SMA and SMA is rising
    if is_sma_rising(df['SMA44'][-5:]):
        last_candle = df.iloc[-1]
        if last_candle['Low'] < last_candle['SMA44'] < last_candle['Close']:
            entry = last_candle['High']
            sl = last_candle['Low']
            rr_2 = entry + 2 * (entry - sl)
            rr_3 = entry + 3 * (entry - sl)
            return {
                'Stock': stock,
                'Entry': round(entry, 2),
                'StopLoss': round(sl, 2),
                'Target_1_2': round(rr_2, 2),
                'Target_1_3': round(rr_3, 2)
            }
    return None

nifty_100 = [
    'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
    'KOTAKBANK.NS', 'ITC.NS', 'LT.NS', 'SBIN.NS', 'BHARTIARTL.NS',
    'ASIANPAINT.NS', 'HINDUNILVR.NS', 'BAJFINANCE.NS', 'AXISBANK.NS', 'HCLTECH.NS',
    'MARUTI.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'WIPRO.NS', 'ULTRACEMCO.NS',
    'NTPC.NS', 'POWERGRID.NS', 'NESTLEIND.NS', 'TECHM.NS', 'BAJAJFINSV.NS',
    'ONGC.NS', 'TATAMOTORS.NS', 'JSWSTEEL.NS', 'COALINDIA.NS', 'HDFCLIFE.NS',
    'GRASIM.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'CIPLA.NS', 'DIVISLAB.NS',
    'BAJAJ-AUTO.NS', 'DRREDDY.NS', 'BPCL.NS', 'EICHERMOT.NS', 'SHREECEM.NS',
    'SBILIFE.NS', 'IOC.NS', 'HEROMOTOCO.NS', 'BRITANNIA.NS', 'INDUSINDBK.NS',
    'TATACONSUM.NS', 'PIDILITIND.NS', 'HINDALCO.NS', 'GAIL.NS', 'DABUR.NS',
    'ICICIPRULI.NS', 'HAVELLS.NS', 'AMBUJACEM.NS', 'VEDL.NS', 'UPL.NS',
    'DLF.NS', 'SIEMENS.NS', 'SRF.NS', 'M&M.NS', 'SBICARD.NS',
    'BERGEPAINT.NS', 'BIOCON.NS', 'LUPIN.NS', 'AUROPHARMA.NS', 'TATAPOWER.NS',
    'MUTHOOTFIN.NS', 'BOSCHLTD.NS', 'COLPAL.NS', 'INDIGO.NS', 'MARICO.NS',
    'ICICIGI.NS', 'GODREJCP.NS', 'PEL.NS', 'TORNTPHARM.NS', 'HINDPETRO.NS',
    'BANKBARODA.NS', 'IDFCFIRSTB.NS', 'PNB.NS', 'CANBK.NS', 'UNIONBANK.NS',
    'RECLTD.NS', 'PFC.NS', 'NHPC.NS', 'NMDC.NS', 'SJVN.NS',
    'IRCTC.NS', 'ABB.NS', 'ADANIGREEN.NS', 'ADANITRANS.NS', 'ZOMATO.NS',
    'PAYTM.NS', 'POLYCAB.NS', 'LTTS.NS', 'LTI.NS', 'MINDTREE.NS',
    'MPHASIS.NS', 'COFORGE.NS', 'TATAELXSI.NS', 'NAVINFLUOR.NS', 'ALKEM.NS'
]

results = []
for stock in nifty_100:
    res = scan_bhanushali_strategy(stock)
    if res:
        results.append(res)

df_result = pd.DataFrame(results)
print(df_result)
