import psycopg2
import os
import time
import yfinance as yf
import pandas as pd
from datetime import datetime

def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        # Allowing a default for STOCK_SYMBOLS for easier local testing if not set
        if name == 'STOCK_SYMBOLS':
            print(f"Warning: Environment variable {name} not set. Using default 'AAPL,MSFT'.")
            return "AAPL,MSFT" # Default value if not set
        raise Exception(f"Environment variable {name} not set.")

def get_or_create_stock_id(symbol, conn, cur):
    """
    Retrieves the ID of a stock from the 'stocks' table.
    If the stock doesn't exist, it inserts it and returns the new ID.
    """
    try:
        cur.execute("SELECT id FROM stocks WHERE symbol = %s;", (symbol,))
        stock_id_row = cur.fetchone()
        if stock_id_row:
            stock_id = stock_id_row[0]
            print(f"Found stock ID {stock_id} for symbol {symbol}.")
            return stock_id
        else:
            cur.execute("INSERT INTO stocks (symbol) VALUES (%s) RETURNING id;", (symbol,))
            new_stock_id = cur.fetchone()[0]
            conn.commit()
            print(f"Created new stock ID {new_stock_id} for symbol {symbol}.")
            return new_stock_id
    except Exception as e:
        conn.rollback() # Rollback on error
        print(f"Error in get_or_create_stock_id for {symbol}: {e}")
        raise # Re-raise the exception to be caught by the caller

def process_stock_symbol(symbol, conn, cur):
    """
    Fetches historical stock data for a given symbol using yfinance,
    calculates moving averages, and upserts the latest data point into the stock_prices table.
    """
    print(f"Processing data for stock symbol: {symbol}")
    try:
        stock_id = get_or_create_stock_id(symbol, conn, cur)
        if stock_id is None:
            print(f"Could not get or create stock ID for {symbol}. Skipping.")
            return

        ticker = yf.Ticker(symbol)
        # Fetch historical data - "3mo" to ensure enough data for 30-day MA for recent entries
        # and to have a buffer if today is a non-trading day.
        hist_data = ticker.history(period="3mo")

        if hist_data.empty:
            print(f"Warning: No historical data found for {symbol}. Skipping.")
            return

        # Calculate Moving Averages
        hist_data['MA5'] = hist_data['Close'].rolling(window=5).mean()
        hist_data['MA30'] = hist_data['Close'].rolling(window=30).mean()

        if hist_data.empty: # Should be caught by earlier check, but as a safeguard
            print(f"Warning: Historical data became empty after processing for {symbol}. Skipping.")
            return

        # Get the latest valid data point (could be T-1, T-2 etc. if market is closed or yfinance data lags)
        # Iterate backwards from the last row to find a row with price data
        latest_data = None
        for i in range(len(hist_data) -1, -1, -1):
            if pd.notna(hist_data.iloc[i]['Close']):
                latest_data = hist_data.iloc[i]
                break

        if latest_data is None or latest_data.name is None:
            print(f"Warning: Could not find a valid latest data point for {symbol}. Skipping.")
            return

        data_date = latest_data.name.strftime('%Y-%m-%d') # Index is a Timestamp
        # Ensure conversion to Python native float, handle NaNs by converting to None
        price = float(latest_data['Close']) if pd.notna(latest_data['Close']) else None
        ma5 = float(latest_data['MA5']) if pd.notna(latest_data['MA5']) else None
        ma30 = float(latest_data['MA30']) if pd.notna(latest_data['MA30']) else None

        if price is None:
            print(f"Warning: Latest price is null for {symbol} on {data_date}. Skipping.")
            return

        UPSERT_SQL = """
        INSERT INTO stock_prices (stock_id, date, price, ma_5day, ma_30day)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (stock_id, date) DO UPDATE SET
          price = EXCLUDED.price,
          ma_5day = EXCLUDED.ma_5day,
          ma_30day = EXCLUDED.ma_30day;
        """
        cur.execute(UPSERT_SQL, (stock_id, data_date, price, ma5, ma30))
        conn.commit()

        # Safer print formatting
        price_str = f"{price:.2f}" if isinstance(price, float) else "N/A"
        ma5_str = f"{ma5:.2f}" if isinstance(ma5, float) else "N/A"
        ma30_str = f"{ma30:.2f}" if isinstance(ma30, float) else "N/A"
        print(f"Successfully upserted data for {symbol} on {data_date}: Price={price_str}, MA5={ma5_str}, MA30={ma30_str}")

    except Exception as e:
        conn.rollback() # Rollback on error
        print(f"Error processing stock symbol {symbol}: {e}")
        # Optionally re-raise or handle more gracefully depending on desired behavior for batch jobs

def main():
    conn = None
    cur = None
    try:
        db_user = get_env_variable('POSTGRES_USER')
        db_password = get_env_variable('POSTGRES_PASSWORD')
        db_host = get_env_variable('POSTGRES_HOST')
        db_name = get_env_variable('POSTGRES_DB')

        # Retry connection
        for i in range(5):
            try:
                conn = psycopg2.connect(
                    dbname=db_name,
                    user=db_user,
                    password=db_password,
                    host=db_host
                )
                print("Successfully connected to PostgreSQL!")
                break
            except psycopg2.OperationalError as e:
                print(f"Connection attempt {i+1} failed: {e}")
                if i < 4:
                    time.sleep(5)
                else:
                    raise

        if not conn:
            print("Failed to connect to the database after several retries.")
            return

        cur = conn.cursor()

        # Create tables if they don't exist
        cur.execute("""
        CREATE TABLE IF NOT EXISTS stocks (
            id SERIAL PRIMARY KEY,
            symbol TEXT UNIQUE NOT NULL
        );
        """)
        conn.commit()
        print("Table 'stocks' checked/created successfully.")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id SERIAL PRIMARY KEY,
            stock_id INTEGER NOT NULL REFERENCES stocks(id) ON DELETE CASCADE,
            date DATE NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            ma_5day DECIMAL(10, 2),
            ma_30day DECIMAL(10, 2),
            UNIQUE (stock_id, date)
        );
        """)
        conn.commit()
        print("Table 'stock_prices' checked/created successfully.")

        stock_symbols_str = get_env_variable('STOCK_SYMBOLS')
        if not stock_symbols_str:
            # This case should ideally be caught by get_env_variable if no default is set and it raises an error.
            # However, if get_env_variable returns an empty string for some reason:
            print("Error: STOCK_SYMBOLS environment variable is not set or effectively empty.")
            return

        stock_symbols_list = [symbol.strip().upper() for symbol in stock_symbols_str.split(',') if symbol.strip()]

        if not stock_symbols_list:
            print("No stock symbols provided in STOCK_SYMBOLS after stripping.")
            return

        print(f"Processing symbols: {stock_symbols_list}")

        for symbol in stock_symbols_list:
            process_stock_symbol(symbol, conn, cur)

        print("Finished processing all stock symbols.")

    except Exception as e:
        print(f"An error occurred in main: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("PostgreSQL connection closed.")

if __name__ == "__main__":
    main()
