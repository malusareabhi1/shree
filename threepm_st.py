import pandas as pd

def mark_3pm_breakouts(df):
    """
    df: DataFrame with columns ['datetime', 'open', 'high', 'low', 'close']
        datetime should be in pandas datetime64 format, in local timezone or exchange timezone.
    Returns:
        df with extra columns:
          'prev_3pm_high', 'prev_3pm_low', 'break_above', 'break_below'
    """
    df = df.copy()

    # Extract date and time from datetime
    df['date'] = df['datetime'].dt.date
    df['time'] = df['datetime'].dt.time

    # Find 3:00 PM candles for each date
    mask_3pm = df['time'] == pd.to_datetime("15:00:00").time()
    df_3pm = df.loc[mask_3pm, ['date', 'high', 'low']].copy()
    df_3pm = df_3pm.rename(columns={'high':'3pm_high', 'low':'3pm_low'})

    # Shift the 3pm highs and lows by one day to assign as "previous day 3pm high/low" for next day
    df_3pm['date'] = pd.to_datetime(df_3pm['date'])
    df_3pm['next_date'] = df_3pm['date'] + pd.Timedelta(days=1)
    df_3pm = df_3pm.set_index('next_date')[['3pm_high','3pm_low']]

    # Join the previous day's 3pm high/low to the main df by date
    df['date'] = pd.to_datetime(df['date'])
    df = df.join(df_3pm, on='date')

    # Identify breakouts
    df['break_above'] = (df['high'] > df['3pm_high']) & (~df['3pm_high'].isna())
    df['break_below'] = (df['low'] < df['3pm_low']) & (~df['3pm_low'].isna())

    return df

# Usage Example:
# df = pd.read_csv('your_15min_data.csv', parse_dates=['datetime'])
# result_df = mark_3pm_breakouts(df)

# Now result_df contains prev day 3PM high/low and break_above/break_below boolean columns
