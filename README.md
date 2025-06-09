# Hello World Python Docker Application with Postgres

This repository contains a Python application that connects to a PostgreSQL database. Both the application and the database run inside Docker containers managed by Docker Compose. The Python script creates a table (if it doesn't exist) and inserts a "Hello, World!" message into it.

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
git clone <repository-url>
cd <repository-name>
```

### 3. Run with Docker Compose

Open your WSL terminal and navigate to the root directory of this project. Run the following command to build the images (if they don't exist or if `Dockerfile` changed) and start the services:

```bash
docker-compose up --build
```

*   `docker-compose up` will start (or restart) the services defined in `docker-compose.yml`.
*   `--build` forces Docker Compose to rebuild the images (e.g., if you changed `Dockerfile` or `app.py`).
*   You should see logs from both the Python application and the PostgreSQL database. The Python app will attempt to connect to the database, create a table, insert a message, and print the retrieved message.

**Note:** Depending on your Docker installation and user permissions, you might need to prepend `sudo` to Docker Compose commands (e.g., `sudo docker-compose up --build`).

To stop the services, press `Ctrl+C` in the terminal where `docker-compose` is running, or run `docker-compose down` from another terminal in the project directory. To stop and remove volumes (like the Postgres data), use `docker-compose down -v`.

## Debugging in Cursor IDE (or VS Code) with Remote - Containers

The "Remote - Containers" extension provides the best experience for developing and debugging applications inside Docker containers.

1.  **Open the Project in Cursor via WSL:**
    *   Open your WSL terminal.
    *   Navigate to the project directory.
    *   Type `cursor .` (or `code .`) to open the project in Cursor IDE running in WSL mode.

2.  **Reopen in Container:**
    *   Once the project is open, the "Remote - Containers" extension might prompt you to "Reopen in Container". If it does, click it.
    *   If not prompted, open the Command Palette (Ctrl+Shift+P or F1) and type/select: `Remote-Containers: Reopen in Container`.
    *   Cursor IDE will reload and connect to the `python-app` service defined in your `docker-compose.yml`. Your IDE's terminal will now be *inside* the running Python container.

3.  **Debugging the Python Application:**
    *   Open `app.py`.
    *   Go to the "Run and Debug" view (usually a play button icon with a bug on the sidebar).
    *   If you don't have a `launch.json` yet, click on "create a launch.json file" and select "Python" and then "Python File" or "Default". This will create a `.vscode/launch.json` file. A simple configuration like the following should work:
        ```json
        {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Python: Current File",
                    "type": "python",
                    "request": "launch",
                    "program": "${file}", // This will be /app/app.py when running in container
                    "console": "integratedTerminal",
                    "env": {
                        "POSTGRES_USER": "myuser",
                        "POSTGRES_PASSWORD": "mypassword",
                        "POSTGRES_DB": "mydatabase",
                        "POSTGRES_HOST": "postgres-db"
                    }
                }
            ]
        }
        ```
       *Important*: Ensure the `env` variables in `launch.json` match those in `docker-compose.yml` for the `python-app` service. This is because when you debug, VS Code/Cursor might launch a new Python process within the container, and it needs these environment variables.
    *   Set breakpoints in `app.py` (e.g., on the line that prints the retrieved message).
    *   Select the "Python: Current File" configuration from the debug dropdown and click the green play button (Start Debugging).
    *   The debugger should start, and execution should pause at your breakpoints.

## Environment Variables

The application uses the following environment variables, configured in `docker-compose.yml` for the `python-app` service and `launch.json` for debugging:

*   `POSTGRES_USER`: Username for the PostgreSQL database.
*   `POSTGRES_PASSWORD`: Password for the PostgreSQL database.
*   `POSTGRES_DB`: Name of the PostgreSQL database.
*   `POSTGRES_HOST`: Hostname of the PostgreSQL service (should match the service name in `docker-compose.yml`, e.g., `postgres-db`).

The `postgres-db` service in `docker-compose.yml` is also configured with `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` to initialize the database.
