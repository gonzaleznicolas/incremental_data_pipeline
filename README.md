# Python Stock Data Processor with Docker and PostgreSQL

This application fetches historical stock data for a configurable list of symbols using the `yfinance` library, calculates 5-day and 30-day moving averages, and stores these details in a PostgreSQL database. The entire setup runs in Docker containers managed by Docker Compose.

## Core Technologies

*   Python
*   `yfinance` for stock data
*   `pandas` for data manipulation (moving averages)
*   PostgreSQL for data storage
*   Docker & Docker Compose

## General Prerequisites

Before you begin, ensure you have the following installed and configured on your system:

*   **Git**: For cloning the repository.
*   **Docker Engine**: The core Docker runtime. Ensure the Docker daemon is running.
*   **Docker Compose**: For managing multi-container Docker applications (v2.x or later is recommended).

## Initial Setup

Follow these steps to get the application code and configure it:

### 1. Clone the Repository

If you haven't already, clone the project to your local machine:
```bash
# git clone <repository-url>
# cd <repository-name>
```

### 2. Configure Stock Symbols

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

## Running the Application

Once the initial setup is complete, you can build and run the application using Docker Compose. The primary command is:

```bash
docker-compose up --build
```

This command starts the Python application and the PostgreSQL database. The Python app will fetch data for the configured symbols, calculate moving averages, and store them in the database. You will see logs from both services.

Below are environment-specific considerations:

### For Linux VM / Generic Docker Environment (e.g., Jules)

*   **User Permissions**: To run Docker commands without `sudo`, ensure your user is part of the `docker` group (e.g., run `sudo usermod -aG docker $USER` and then log out and log back in). If you prefer not to do this, prepend `sudo` to your `docker-compose` commands.
*   **Command**: Navigate to the project's root directory in your terminal and execute:
    ```bash
    docker-compose up --build
    ```

### For Windows Subsystem for Linux (WSL) Users

Ensure Docker Desktop is configured to work with your WSL distribution:

*   **WSL Docker Desktop Configuration**:
    *   Ensure Docker Desktop for Windows is running.
    *   Open Docker Desktop settings.
    *   Navigate to **Resources > WSL Integration**.
    *   Enable integration with your preferred WSL distribution.
    *   Apply & Restart.
*   **VS Code Integration (Optional but Recommended for WSL development)**:
    *   Ensure Cursor IDE (or VS Code) is installed on Windows.
    *   Install the "Remote - Containers" extension (ms-vscode-remote.remote-containers) in your IDE.

## Common Next Steps

### Inspecting the Database

After the application has run, you can inspect the PostgreSQL database directly to verify the data:

1.  **Find your Postgres container name:**
    Open a new terminal and list your running Docker containers:
    ```bash
    docker ps
    ```
    Look for the container running the `postgres:13-alpine` image. The name is usually in the last column.

2.  **Connect to the Postgres container using `psql`:**
    Use the container name or ID from the previous step. The default username (`myuser`) and database name (`mydatabase`) are specified in `docker-compose.yml`.
    ```bash
    docker exec -it <your_postgres_container_name_or_id> psql -U myuser -d mydatabase
    ```
    For example, if your container name is `stock_data_processor-postgres-db-1` (name might vary):
    ```bash
    docker exec -it stock_data_processor-postgres-db-1 psql -U myuser -d mydatabase
    ```

3.  **Inspect the data using `psql` commands:**
    Once connected, you can use standard SQL queries and `psql` commands:
    *   List all tables: `\dt`
    *   Describe the `stocks` table schema: `\d stocks`
    *   Describe the `stock_prices` table schema: `\d stock_prices`
    *   View all stock symbols: `SELECT * FROM stocks;`
    *   View all price entries:
        ```sql
        SELECT s.symbol, sp.date, sp.price, sp.ma_5day, sp.ma_30day
        FROM stock_prices sp
        JOIN stocks s ON sp.stock_id = s.id
        ORDER BY s.symbol, sp.date DESC;
        ```
    *   To exit `psql`, type: `\q`

### Stopping the Services

To stop the services, press `Ctrl+C` in the terminal where `docker-compose` is running. Alternatively, from another terminal in the project directory, run:
```bash
docker-compose down
```
To stop the services and remove the data volumes (including Postgres data), use:
```bash
docker-compose down -v
```

## Environment Variables

The application uses the following environment variables, configured in `docker-compose.yml` for the `python-app` service:

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
