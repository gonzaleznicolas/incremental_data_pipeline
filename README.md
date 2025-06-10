# Python Stock Data Processor with Docker and PostgreSQL

This application fetches historical stock data for a configurable list of symbols using the `yfinance` library, calculates 5-day and 30-day moving averages, and stores these details in a PostgreSQL database. The entire setup runs in Docker containers managed by Docker Compose.

## Core Technologies

*   Python
*   `yfinance` for stock data
*   `pandas` for data manipulation (moving averages)
*   PostgreSQL for data storage
*   Docker & Docker Compose

## Prerequisites

*   Docker Desktop installed on your Windows machine.
*   WSL (Windows Subsystem for Linux) enabled and a Linux distribution installed.
*   Cursor IDE (or VS Code) installed.
*   "Remote - Containers" extension (ms-vscode-remote.remote-containers) installed in Cursor IDE/VS Code.

## Setup and Running the Application

### 1. Configure Docker Desktop for WSL

*   Ensure Docker Desktop is running.
*   Open Docker Desktop settings.
*   Navigate to **Resources > WSL Integration**.
*   Enable integration with your preferred WSL distribution.
*   Apply & Restart.

### 2. Clone the Repository (If you haven't already)

```bash
# git clone <repository-url>
# cd <repository-name>
```

### 3. Configure Stock Symbols

The application processes stock symbols defined in the `STOCK_SYMBOLS` environment variable within the `docker-compose.yml` file. You can modify this list as needed:

File: `docker-compose.yml`
```yaml
services:
  python-app:
    # ... other configurations ...
    environment:
      # ... other env vars ...
      - STOCK_SYMBOLS=AAPL,MSFT,GOOGL # <-- Modify here
    # ...
```
Update the `STOCK_SYMBOLS` line with your desired comma-separated stock symbols.

### 4. Run with Docker Compose

Open your WSL terminal and navigate to the root directory of this project. Run the following command to build the images (if they don't exist or if `Dockerfile`/`requirements.txt` changed) and start the services:

```bash
docker-compose up --build
```

*   This command starts the Python application and the PostgreSQL database.
*   The Python app will fetch data for the configured symbols, calculate moving averages, and store them in the database.
*   You will see logs from both services.

**Note:** Depending on your Docker installation and user permissions, you might need to prepend `sudo` to Docker Compose commands (e.g., `sudo docker-compose up --build`).

To stop the services, press `Ctrl+C` in the terminal where `docker-compose` is running, or run `docker-compose down` from another terminal in the project directory. To stop and remove volumes (including Postgres data), use `docker-compose down -v`.

### 5. Inspecting the Database

After the application has run (e.g., `docker-compose up --build`), you can inspect the PostgreSQL database directly to verify the data.

1.  **Find your Postgres container name:**
    Open a new terminal and list your running Docker containers:
    ```bash
    docker ps
    ```
    Look for the container running the `postgres:13-alpine` image. The name is usually in the last column (e.g., `postgres_db_container` or something similar if you used the `container_name` attribute in `docker-compose.yml`, or a Docker-generated name).

2.  **Connect to the Postgres container using `psql`:**
    Use the container name or ID from the previous step. The default username (`myuser`) and database name (`mydatabase`) are specified in `docker-compose.yml`.
    ```bash
    docker exec -it <your_postgres_container_name_or_id> psql -U myuser -d mydatabase
    ```
    For example, if your container name is `postgres_db_container`:
    ```bash
    docker exec -it postgres_db_container psql -U myuser -d mydatabase
    ```

3.  **Inspect the data using `psql` commands:**
    Once connected, you can use standard SQL queries and `psql` commands:

    *   List all tables:
        ```sql
        \dt
        ```
    *   Describe the `stocks` table schema:
        ```sql
        \d stocks
        ```
    *   Describe the `stock_prices` table schema:
        ```sql
        \d stock_prices
        ```
    *   View all stock symbols:
        ```sql
        SELECT * FROM stocks;
        ```
    *   View all price entries (joining with stocks table for symbol):
        ```sql
        SELECT s.symbol, sp.date, sp.price, sp.ma_5day, sp.ma_30day
        FROM stock_prices sp
        JOIN stocks s ON sp.stock_id = s.id
        ORDER BY s.symbol, sp.date DESC;
        ```
    *   View recent price data for a specific stock (e.g., AAPL):
        ```sql
        SELECT s.symbol, sp.date, sp.price, sp.ma_5day, sp.ma_30day
        FROM stock_prices sp
        JOIN stocks s ON sp.stock_id = s.id
        WHERE s.symbol = 'AAPL'
        ORDER BY sp.date DESC
        LIMIT 10;
        ```
    *   To exit `psql`, type:
        ```sql
        \q
        ```

## Environment Variables

The application uses the following environment variables, configured in `docker-compose.yml` for the `python-app` service and potentially mirrored in `launch.json` for debugging:

*   `POSTGRES_USER`: Username for the PostgreSQL database.
*   `POSTGRES_PASSWORD`: Password for the PostgreSQL database.
*   `POSTGRES_DB`: Name of the PostgreSQL database.
*   `POSTGRES_HOST`: Hostname of the PostgreSQL service (e.g., `postgres-db`).
*   `STOCK_SYMBOLS`: Comma-separated list of stock symbols to process (e.g., `AAPL,MSFT,GOOGL`).

## Database Schema

The application uses two tables in the PostgreSQL database:

1.  **`stocks`**: Stores unique stock symbols and their IDs.
    *   `id`: SERIAL PRIMARY KEY
    *   `symbol`: TEXT UNIQUE NOT NULL

2.  **`stock_prices`**: Stores daily stock price data and calculated moving averages.
    *   `id`: SERIAL PRIMARY KEY
    *   `stock_id`: INTEGER, Foreign Key to `stocks.id` (cascade on delete)
    *   `date`: DATE NOT NULL
    *   `price`: DECIMAL(10, 2) NOT NULL (closing price)
    *   `ma_5day`: DECIMAL(10, 2) (5-day moving average)
    *   `ma_30day`: DECIMAL(10, 2) (30-day moving average)
    *   UNIQUE constraint on `(stock_id, date)` to prevent duplicate entries for the same stock on the same day.
