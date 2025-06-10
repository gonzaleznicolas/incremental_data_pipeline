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

## Debugging in Cursor IDE (or VS Code) with Remote - Containers

The "Remote - Containers" extension provides the best experience for developing and debugging.

1.  **Open the Project in Cursor via WSL.** (as previously described)
2.  **Reopen in Container.** (as previously described)
3.  **Debugging the Python Application:**
    *   Open `app.py`.
    *   Go to the "Run and Debug" view.
    *   If you don't have a `launch.json` yet, click on "create a launch.json file," select "Python," and then "Python File." A `.vscode/launch.json` will be created. Ensure it includes the necessary environment variables (it should inherit from `docker-compose.yml` if using "Remote - Containers" correctly, but explicitly setting them for debug configuration is safer):
        ```json
        {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Python: Current File",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}",
                    "console": "integratedTerminal",
                    "env": {
                        "POSTGRES_USER": "myuser",
                        "POSTGRES_PASSWORD": "mypassword",
                        "POSTGRES_DB": "mydatabase",
                        "POSTGRES_HOST": "postgres-db",
                        "STOCK_SYMBOLS": "AAPL,MSFT,GOOGL" // Ensure this matches or is set for debugging
                    }
                }
            ]
        }
        ```
    *   Set breakpoints in `app.py`.
    *   Select the "Python: Current File" configuration and start debugging.

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
