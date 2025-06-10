import os
import time
import yfinance as yf
import pandas as pd
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Date, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Define SQLAlchemy models
Base = declarative_base()

class Stock(Base):
    __tablename__ = 'stocks'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, unique=True, nullable=False)

class StockPrice(Base):
    __tablename__ = 'stock_prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    date = Column(Date, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    ma_5day = Column(Numeric(10, 2), nullable=True)
    ma_30day = Column(Numeric(10, 2), nullable=True)
    __table_args__ = (UniqueConstraint('stock_id', 'date', name='uq_stock_date'),)

def get_env_variable(name):
    try:
        return os.environ[name]
    except KeyError:
        # Allowing a default for STOCK_SYMBOLS for easier local testing if not set
        if name == 'STOCK_SYMBOLS':
            print(f"Warning: Environment variable {name} not set. Using default 'AAPL,MSFT'.")
            return "AAPL,MSFT" # Default value if not set
        if name in ['FETCH_START_DATE', 'FETCH_END_DATE']:
            print(f"Warning: Optional environment variable {name} not set. Defaulting to None.")
            return None
        raise Exception(f"Environment variable {name} not set.")

def get_or_create_stock_id(symbol: str, db: Session):
    """
    Retrieves the ID of a stock from the 'stocks' table using SQLAlchemy.
    If the stock doesn't exist, it inserts it and returns the new ID.
    """
    try:
        stock = db.query(Stock).filter(Stock.symbol == symbol).first()
        if stock:
            print(f"Found stock ID {stock.id} for symbol {symbol}.")
            return stock.id
        else:
            new_stock = Stock(symbol=symbol)
            db.add(new_stock)
            db.commit()
            db.refresh(new_stock)
            print(f"Created new stock ID {new_stock.id} for symbol {symbol}.")
            return new_stock.id
    except Exception as e:
        db.rollback()
        print(f"Error in get_or_create_stock_id for {symbol} (SQLAlchemy): {e}")
        raise

def process_stock_symbol(symbol: str, db: Session, start_date_str: str = None, end_date_str: str = None):
    """
    Fetches historical stock data for a given symbol using yfinance,
    calculates moving averages, and upserts the latest data point into the stock_prices table using SQLAlchemy.
    Optionally uses start_date_str and end_date_str to define a fetch period.
    """
    print(f"Processing data for stock symbol: {symbol}")
    try:
        stock_id = get_or_create_stock_id(symbol, db)
        if stock_id is None:
            print(f"Could not get or create stock ID for {symbol}. Skipping processing.")
            return

        ticker = yf.Ticker(symbol)
        hist_data = None
        use_default_period = True

        if start_date_str and end_date_str:
            try:
                parsed_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                parsed_end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                if parsed_start_date >= parsed_end_date:
                    print(f"Error: Start date {start_date_str} must be before end date {end_date_str} for symbol {symbol}. Defaulting to 3mo period.")
                else:
                    print(f"Fetching data for {symbol} from {parsed_start_date} to {parsed_end_date}.")
                    hist_data = ticker.history(start=parsed_start_date, end=parsed_end_date)
                    use_default_period = False
            except ValueError as e:
                print(f"Error parsing dates for symbol {symbol} (start: {start_date_str}, end: {end_date_str}): {e}. Defaulting to 3mo period.")
        elif start_date_str or end_date_str:
            # This means one is provided but not the other
            print(f"Error: Both FETCH_START_DATE and FETCH_END_DATE must be provided if one is set for symbol {symbol}. Defaulting to 3mo period.")

        if use_default_period:
            if not (start_date_str or end_date_str): # Only log if no dates were attempted
                print(f"No start/end dates provided or dates were invalid for {symbol}. Defaulting to 3mo period.")
            hist_data = ticker.history(period="3mo")

        if hist_data is None or hist_data.empty: # hist_data could be None if yfinance fails with specific dates
            print(f"Warning: No historical data found for {symbol} for the specified period or default. Skipping.")
            return

        hist_data['MA5'] = hist_data['Close'].rolling(window=5).mean()
        hist_data['MA30'] = hist_data['Close'].rolling(window=30).mean()

        # hist_data.empty check is already done before this block

        processed_count = 0
        for data_date_ts, row_data in hist_data.iterrows():
            try:
                # Convert pandas.Timestamp (data_date_ts from index) to Python datetime.date
                if pd.isnull(data_date_ts):
                    print(f"Warning: Timestamp for date is null for a row in {symbol}. Skipping this row.")
                    continue
                data_date = data_date_ts.to_pydatetime().date()

                price = float(row_data['Close']) if pd.notna(row_data['Close']) else None
                ma5 = float(row_data['MA5']) if pd.notna(row_data['MA5']) else None
                ma30 = float(row_data['MA30']) if pd.notna(row_data['MA30']) else None

                if price is None:
                    print(f"Warning: Price is null for {symbol} on {data_date}. Skipping this record.")
                    continue

                existing_price_entry = db.query(StockPrice).filter_by(stock_id=stock_id, date=data_date).first()

                if existing_price_entry:
                    print(f"Updating data for {symbol} on {data_date}...")
                    existing_price_entry.price = price
                    existing_price_entry.ma_5day = ma5
                    existing_price_entry.ma_30day = ma30
                else:
                    print(f"Inserting new data for {symbol} on {data_date}...")
                    new_price_entry = StockPrice(
                        stock_id=stock_id,
                        date=data_date,
                        price=price,
                        ma_5day=ma5,
                        ma_30day=ma30
                    )
                    db.add(new_price_entry)

                db.commit() # Commit after each upsert as per instruction
                processed_count += 1
                # Optional: More detailed print for each upsert can be verbose, so a summary print is better.
                # price_str = f"{price:.2f}" if isinstance(price, float) else "N/A"
                # ma5_str = f"{ma5:.2f}" if isinstance(ma5, float) else "N/A"
                # ma30_str = f"{ma30:.2f}" if isinstance(ma30, float) else "N/A"
                # print(f"Successfully upserted data for {symbol} on {data_date}: Price={price_str}, MA5={ma5_str}, MA30={ma30_str}")

            except Exception as e_row: # Catch error for specific row processing
                db.rollback()
                print(f"Error processing row for {symbol} on date {data_date_ts}: {e_row}. Skipping this row.")
                continue # Continue to the next row

        if processed_count > 0:
            print(f"Successfully processed and upserted {processed_count} data points for {symbol}.")
        else:
            print(f"No data points were processed/upserted for {symbol} from the fetched history.")

    except Exception as e:
        db.rollback() # Ensure rollback for errors not caught by the per-row handler
        print(f"Error processing stock symbol {symbol} (SQLAlchemy): {e}. Any uncommitted changes for this symbol rolled back. Data from previous symbols (if any) remains committed.")
        # raise # Optionally re-raise if main loop should stop

def main():
    db = None  # Initialize db to None for the finally block
    try:
        db_user = get_env_variable('POSTGRES_USER')
        db_password = get_env_variable('POSTGRES_PASSWORD')
        db_host = get_env_variable('POSTGRES_HOST')
        db_name = get_env_variable('POSTGRES_DB')

        DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"

        engine = None
        # Retry connection for engine
        for i in range(5):
            try:
                engine = create_engine(DATABASE_URL)
                # Try to establish a connection to check if DB is available
                with engine.connect() as connection:
                    print("Successfully connected to PostgreSQL via SQLAlchemy!")
                break
            except Exception as e: # Catch generic sqlalchemy errors for connection
                print(f"SQLAlchemy connection attempt {i+1} failed: {e}")
                if i < 4:
                    time.sleep(5)
                else:
                    print("Failed to connect to the database via SQLAlchemy after several retries.")
                    raise # Re-raise the last exception if all retries fail

        if not engine:
             print("Engine creation failed. Exiting.")
             return

        # Create tables defined by models
        Base.metadata.create_all(bind=engine)
        print("Tables checked/created successfully via SQLAlchemy.")

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Remove old connection logic as it's no longer needed
        # conn_old = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host)
        # cur_old = conn_old.cursor()

        stock_symbols_str = get_env_variable('STOCK_SYMBOLS')
        if not stock_symbols_str:
            print("Error: STOCK_SYMBOLS environment variable is not set or effectively empty.")
            # if conn_old: conn_old.close() # Removed
            # if cur_old: cur_old.close() # Removed
            if db: db.close()
            return

        stock_symbols_list = [symbol.strip().upper() for symbol in stock_symbols_str.split(',') if symbol.strip()]

        if not stock_symbols_list:
            print("No stock symbols provided in STOCK_SYMBOLS after stripping.")
            # if conn_old: conn_old.close() # Removed
            # if cur_old: cur_old.close() # Removed
            if db: db.close()
            return

        print(f"Processing symbols: {stock_symbols_list}")

        fetch_start_date_str = get_env_variable('FETCH_START_DATE')
        fetch_end_date_str = get_env_variable('FETCH_END_DATE')

        for symbol_item in stock_symbols_list:
            process_stock_symbol(symbol_item, db, fetch_start_date_str, fetch_end_date_str) # Updated call

        print("Finished processing all stock symbols.")
        # if conn_old: # Removed
            # conn_old.commit() # Removed

    except Exception as e:
        print(f"An error occurred in main: {e}")
        if db: # db might not be initialized if engine creation fails
            try:
                db.rollback()
                print("SQLAlchemy session rolled back due to error in main.")
            except Exception as rb_exc:
                print(f"Error during SQLAlchemy session rollback in main: {rb_exc}")
        # Old conn_old rollback logic removed

    finally:
        # if 'cur_old' in locals() and cur_old: # Removed
        #     cur_old.close() # Removed
        # if 'conn_old' in locals() and conn_old: # Removed
        #     conn_old.close() # Removed
        #     print("Old PostgreSQL (psycopg2) connection closed.") # Removed
        if db:
            db.close()
            print("SQLAlchemy session closed.")

if __name__ == "__main__":
    main()
