# Hello World Python Docker Application with Postgres

This repository contains a Python application that connects to a PostgreSQL database. Both the application and the database run inside Docker containers managed by Docker Compose. The Python script creates a table (if it doesn't exist) and inserts a "Hello, World!" message into it.

## Prerequisites

*   Docker Desktop installed on your Windows machine.
*   WSL (Windows Subsystem for Linux) enabled and a Linux distribution installed.

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

## Environment Variables

The application uses the following environment variables, configured in `docker-compose.yml` for the `python-app` service:

*   `POSTGRES_USER`: Username for the PostgreSQL database.
*   `POSTGRES_PASSWORD`: Password for the PostgreSQL database.
*   `POSTGRES_DB`: Name of the PostgreSQL database.
*   `POSTGRES_HOST`: Hostname of the PostgreSQL service (should match the service name in `docker-compose.yml`, e.g., `postgres-db`).

The `postgres-db` service in `docker-compose.yml` is also configured with `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` to initialize the database.
