# Jules Setup Instructions for Python Stock Data Processor

This document provides the specific commands and steps for the Jules agent to set up and run the Python Stock Data Processor project.

## 1. Install Docker Engine

These instructions are for a Debian-based Linux system (like Ubuntu).

### 1.1 Uninstall Old Versions (Recommended)

It's good practice to remove any older or conflicting Docker packages:

```bash
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove -y $pkg; done
```

### 1.2 Set Up Docker's APT Repository

```bash
# Update package lists and install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the Docker repository to Apt sources
echo   "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu   $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" |   sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

### 1.3 Install Docker Engine Packages

This installs Docker Engine, CLI, containerd, and essential plugins like Buildx and Docker Compose (plugin version).

```bash
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### 1.4 Verify Docker Installation (Optional)

You can verify the installation by running the hello-world container:

```bash
sudo docker run hello-world
```
This command should download and run a test image, printing a confirmation message.

```

## 2. Install Docker Compose (Standalone - If Not Using Plugin)

The Docker Engine installation in the previous step (`docker-compose-plugin`) should provide the `docker compose` command (notice the space, not a hyphen). This is the recommended way to use Docker Compose.

However, if you need or prefer to install Docker Compose as a standalone binary (which uses `docker-compose` with a hyphen), you can follow these steps. The original project `README.md` refers to a Docker Compose version, implying standalone might be a consideration.

### 2.1 Download Docker Compose Standalone

First, determine the latest release version from the [Docker Compose releases page](https://github.com/docker/compose/releases). As of writing, `v2.27.0` is a recent version, but **you should replace `DOCKER_COMPOSE_VERSION` in the command below with the specific version you need.**

```bash
# Define the version to install
DOCKER_COMPOSE_VERSION="v2.27.0" # CHECK FOR LATEST STABLE VERSION!

# Download the Docker Compose binary
sudo curl -SL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-$(uname -m)" -o /usr/local/bin/docker-compose
```
*(Note: `uname -m` helps select the correct architecture, e.g., x86_64, arm64).*

### 2.2 Apply Executable Permissions

```bash
sudo chmod +x /usr/local/bin/docker-compose
```

### 2.3 Verify Standalone Installation (Optional)

```bash
docker-compose --version
```
This should display the version of the standalone Docker Compose you just installed. If you also have the plugin, `docker compose version` (no hyphen) will show the plugin version.
```

## 3. Configure Docker User Permissions (Recommended)

To allow Jules (or any non-root user) to run `docker` and `docker compose` commands without `sudo`, add the current user to the `docker` group.

```bash
sudo usermod -aG docker $USER
```

**Important:** After running this command, you (Jules) will need to start a new terminal session (or effectively log out and log back in) for the group changes to take effect. If you are in a script or an environment where youcannot log out and log back in, you might need to use `newgrp docker` in the script to switch to the new group for the current shell session, or continue using `sudo` for Docker commands until a new session is started.

After a new session is started, you should be able to run commands like `docker ps` without `sudo`.
```

## 4. Running the Application

Once Docker and Docker Compose (either plugin or standalone) are installed and permissions are set, you can run the application.

### 4.1 Navigate to Project Directory

Ensure you are in the root directory of the cloned project repository where the `docker-compose.yml` file is located.

```bash
# cd /path/to/your/cloned/repository
```
*(Jules: You will typically already be in the correct directory.)*

### 4.2 Configure Stock Symbols (Optional)

The application processes stock symbols defined in the `STOCK_SYMBOLS` environment variable within the `docker-compose.yml` file. You can modify this list if needed before running the application.

File: `docker-compose.yml`
```yaml
services:
  python-app:
    # ... other configurations ...
    environment:
      # ... other env vars ...
      - STOCK_SYMBOLS=AAPL,MSFT,GOOGL # <-- Modify here
      - FETCH_START_DATE=2023-02-01    # Optional
      - FETCH_END_DATE=2023-02-15      # Optional
    # ...
```

### 4.3 Build and Run the Application

To build the Docker images (if they don't exist or need updating) and start the services (Python app and PostgreSQL database), use the following command:

**Recommended (if using Docker Compose plugin):**
```bash
docker compose up --build
```

**Alternative (if using standalone Docker Compose):**
```bash
docker-compose up --build
```

This command will display logs from both the application and the database. The Python app will fetch data, calculate moving averages, and store them.
```

## 5. Inspecting the Database

After the application has run (and ideally processed some data), you can inspect the PostgreSQL database directly.

### 5.1 Find the Postgres Container Name/ID

Open a new terminal (if `docker compose up` is still running in your current one) and list your running Docker containers:

```bash
docker ps
```
Or, if you prefer to use the compose command to list service containers:
```bash
docker compose ps
```
Look for the container running the `postgres:13-alpine` image (or similar, based on `docker-compose.yml`). The name is usually in the last column and might look like `projectname-postgres-1`.

### 5.2 Connect to the Postgres Container

Use the container name or ID from the previous step. The default username (`myuser`) and database name (`mydatabase`) are specified in `docker-compose.yml`.

```bash
docker exec -it <your_postgres_container_name_or_id> psql -U myuser -d mydatabase
```
For example, if your container name is `stock_data_processor-postgres-db-1`:
```bash
docker exec -it stock_data_processor-postgres-db-1 psql -U myuser -d mydatabase
```

### 5.3 Inspect Data with `psql` Commands

Once connected to `psql`, you can use standard SQL queries and `psql` meta-commands:

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
*   View all price entries (example):
    ```sql
    SELECT s.symbol, sp.date, sp.price, sp.ma_5day, sp.ma_30day
    FROM stock_prices sp
    JOIN stocks s ON sp.stock_id = s.id
    ORDER BY s.symbol, sp.date DESC
    LIMIT 10; -- Example: get latest 10 entries
    ```

### 5.4 Exit `psql`

To exit the `psql` interactive terminal, type:
```sql
\q
```
And press Enter.
```

## 6. Stopping the Application

### 6.1 Stopping Active Services

If `docker compose up` is running in your terminal, you can usually stop it by pressing `Ctrl+C`.

### 6.2 Stopping Services and Removing Containers

To stop the services and remove the containers, networks, and (optionally) volumes defined in `docker-compose.yml`, navigate to the project directory and use:

**Recommended (if using Docker Compose plugin):**
```bash
docker compose down
```

**Alternative (if using standalone Docker Compose):**
```bash
docker-compose down
```

### 6.3 Stopping Services and Removing Data Volumes

To stop services, remove containers, AND remove the data volumes (including the PostgreSQL database data, meaning all fetched stock data will be lost), use the `-v` flag:

**Recommended (if using Docker Compose plugin):**
```bash
docker compose down -v
```

**Alternative (if using standalone Docker Compose):**
```bash
docker-compose down -v
```
Use this command with caution if you want to preserve your database contents between runs.
```
