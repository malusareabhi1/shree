import mysql.connector
from datetime import datetime

def log_trade(symbol, trade_type, entry_price, exit_price, quantity, pnl, strategy_name):
    conn = mysql.connector.connect(
        host="db.algobot3.supabase.co",
        user="postgres",
        password="algobot3@123",
        database="postgres "
    )
    cursor = conn.cursor()

    sql = """
        INSERT INTO trade_logs 
        (symbol, trade_type, entry_price, exit_price, quantity, pnl, strategy_name, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        symbol, trade_type, entry_price, exit_price,
        quantity, pnl, strategy_name, datetime.now()
    )
    cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()
