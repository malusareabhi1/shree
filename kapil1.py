import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def align_timezone(dt):
    dt = pd.to_datetime(dt)
    if dt.tzinfo is None:
        return dt.tz_localize("UTC").tz_convert("Asia/Kolkata")
    return dt.tz_convert("Asia/Kolkata")

def preprocess_data(df):
    df['Date'] = pd.to_datetime(df['Date'])
    if df['Date'].dt.tz is None:
        df['Date'] = df['Date'].dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    else:
        df['Date'] = df['Date'].dt.tz_convert('Asia/Kolkata')
    df = df[df['Date'].dt.time.between(pd.to_datetime('09:30:00').time(), pd.to_datetime('13:30:00').time())]
    return df

def resample_to_5min(df):
    if df['Date'].diff().dt.total_seconds().median() < 300:
        df = df.resample('5T', on='Date').agg({'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last'}).dropna()
    return df

def calculate_indicators(df):
    df['SMA_20'] = df['Close'].rolling(window=20).mean()
    df['Upper_BB'] = df['SMA_20'] + 2 * df['Close'].rolling(window=20).std()
    df['Lower_BB'] = df['SMA_20'] - 2 * df['Close'].rolling(window=20).std()
    df['Crossed_SMA_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) < df['SMA_20'].shift(1))
    df['Ref_Candle_Up'] = (df['Close'] > df['SMA_20']) & (df['Close'].shift(1) > df['SMA_20'].shift(1))
    return df

def generate_trade_signals(df, iv_threshold=16, iv_data=9.18):
    df['Signal'] = None
    df['Signal_Reason'] = None
    for idx in range(1, len(df)):
        if df['Ref_Candle_Up'].iloc[idx] and iv_data >= iv_threshold:
            if df['Close'].iloc[idx] > df['Close'].iloc[idx - 1]:
                df.at[idx, 'Signal'] = 'BUY'
                df.at[idx, 'Signal_Reason'] = '20 SMA Cross + IV >= 16'
    return df

def execute_trades(df):
    trades = []
    df = df.sort_values('Date').reset_index(drop=True)
    for idx in range(len(df)):
        if df['Signal'].iloc[idx] == 'BUY':
            entry_price = df['Close'].iloc[idx]
            stop_loss = entry_price * 0.90
            profit_target = entry_price * 1.05
            entry_time = align_timezone(df['Date'].iloc[idx])

            trade = {
                'Entry_Time': entry_time,
                'Entry_Price': entry_price,
                'Stop_Loss': stop_loss,
                'Profit_Target': profit_target,
                'Exit_Time': None,
                'Exit_Price': None,
                'Brokerage': 20,
                'PnL': None,
                'Turnover': None,
                'Exit_Reason': None,
                'PnL_After_Brokerage': None,
                'Signal_Reason': '20 SMA Cross + IV >= 16'
            }

            for i in range(idx + 1, len(df)):
                current_price = df.at[i, 'Close']
                current_time = df.at[i, 'Date']
                if current_price >= profit_target:
                    trade.update({
                        'Exit_Time': current_time,
                        'Exit_Price': profit_target,
                        'PnL': profit_target - entry_price,
                        'Turnover': entry_price + profit_target,
                        'PnL_After_Brokerage': profit_target - entry_price - 20,
                        'Exit_Reason': 'Profit Booking'
                    })
                    break
                elif df.at[i, 'Low'] <= stop_loss:
                    trade.update({
                        'Exit_Time': current_time,
                        'Exit_Price': stop_loss,
                        'PnL': stop_loss - entry_price,
                        'Turnover': entry_price + stop_loss,
                        'PnL_After_Brokerage': stop_loss - entry_price - 20,
                        'Exit_Reason': 'Stop Loss Hit'
                    })
                    break
                elif (current_time - entry_time).seconds >= 600:
                    trade.update({
                        'Exit_Time': current_time,
                        'Exit_Price': current_price,
                        'PnL': current_price - entry_price,
                        'Turnover': entry_price + current_price,
                        'PnL_After_Brokerage': current_price - entry_price - 20,
                        'Exit_Reason': 'Time-Based Exit'
                    })
                    break
            trades.append(trade)
    return pd.DataFrame(trades)

def calculate_summary(trade_log_df):
    total_trades = len(trade_log_df)
    wins = trade_log_df[trade_log_df['PnL_After_Brokerage'] > 0]
    losses = trade_log_df[trade_log_df['PnL_After_Brokerage'] < 0]
    win_rate = (len(wins) / total_trades) * 100 if total_trades else 0
    gross_profit = wins['PnL_After_Brokerage'].sum()
    gross_loss = losses['PnL_After_Brokerage'].sum()
    profit_factor = gross_profit / abs(gross_loss) if gross_loss < 0 else float('inf')
    avg_win = wins['PnL_After_Brokerage'].mean() if not wins.empty else 0
    avg_loss = losses['PnL_After_Brokerage'].mean() if not losses.empty else 0
    expectancy = (win_rate/100) * avg_win + (1 - win_rate/100) * avg_loss
    total_turnover = trade_log_df['Turnover'].sum()
    total_brokerage = trade_log_df['Brokerage'].sum()

    return {
        'total_trades': total_trades,
        'win_rate': win_rate,
        'num_wins': len(wins),
        'num_losses': len(losses),
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'expectancy': expectancy,
        'total_turnover': total_turnover,
        'total_brokerage': total_brokerage
    }

def plot_trades(df):
    df['20_SMA'] = df['Close'].rolling(window=20).mean()
    fig = go.Figure(data=[go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='green', decreasing_line_color='red'
    )])
    buy_signals = df[df['Signal'] == 'BUY']
    fig.add_trace(go.Scatter(
        x=buy_signals['Date'], y=buy_signals['Close'], mode='markers', name='Buy Signal',
        marker=dict(symbol='triangle-up', color='green', size=12)
    ))
    fig.add_trace(go.Scatter(
        x=df['Date'], y=df['20_SMA'], mode='lines', name='20 SMA', line=dict(color='blue', width=2)
    ))
    fig.update_layout(
        xaxis_title='Date', yaxis_title='Price (₹)', xaxis_rangeslider_visible=False,
        template='plotly_dark', hovermode='x unified'
    )
    return fig
