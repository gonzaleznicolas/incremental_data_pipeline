# Hello World Python Docker Application

This repository contains a simple Python application that prints "Hello, World!" and runs inside a Docker container.

## Prerequisites

*   Docker Desktop installed on your Windows machine.
*   WSL (Windows Subsystem for Linux) enabled and a Linux distribution installed.
*   Cursor IDE installed.

## Setup Instructions

### 1. Configure Docker Desktop for WSL

*   Ensure Docker Desktop is running.
*   Open Docker Desktop settings.
*   Navigate to **Resources > WSL Integration**.
*   Enable integration with your preferred WSL distribution.
*   Apply & Restart.

### 2. Build the Docker Image

Open your WSL terminal and navigate to the root directory of this project. Run the following command to build the Docker image:

```bash
docker build -t hello-world-python .
```
Note: Depending on your Docker installation and user permissions, you might need to prepend `sudo` to Docker commands (e.g., `sudo docker build ...`).

### 3. Run the Docker Container

After the image is built, you can run the container using:

```bash
docker run hello-world-python
```
Note: Depending on your Docker installation and user permissions, you might need to prepend `sudo` to Docker commands (e.g., `sudo docker build ...`).

You should see "Hello, World!" printed to your terminal.

### 4. Debugging in Cursor IDE with WSL and Docker

#### a. Install the Python Extension in Cursor
If you haven't already, install the official Python extension from Microsoft in Cursor IDE.

#### b. Open the Project in Cursor via WSL
   - Open your WSL terminal.
   - Navigate to the project directory.
   - Type `cursor .` (or `code .` if `cursor` is not aliased) to open the project in Cursor IDE running in WSL mode. This is crucial for the Docker integration to work seamlessly with the IDE.

#### c. Configure the Python Interpreter
   - Cursor IDE, when opened in WSL mode connected to your project, should automatically detect the Python environment if you have the Python extension.
   - For debugging a Docker container, we need to tell VS Code/Cursor how to attach to a process running inside the container.

#### d. Create a `launch.json` for Debugging
   - Go to the "Run and Debug" view in Cursor (usually a play button icon with a bug).
   - If you don't have a `launch.json` file, click on "create a launch.json file".
   - Select "Docker: Python - Attach to Process" or if that's not available, choose "Python" and then you might need to manually configure it or look for an option to attach to a remote debugger.

   Given this project's simplicity, the most straightforward way to debug is often to use VS Code's/Cursor's ability to attach to a running Docker container or execute directly within the container's environment. However, for a simple script like this, attaching a debugger might be overkill, but here's how you would generally approach it for more complex applications:

   **Option 1: Attach to a Running Container (More Complex Setup)**
   This usually involves modifying your Dockerfile to include a debug server like `debugpy` and exposing a debug port.

   For `app.py`, you would modify it to:
   ```python
   import debugpy

   # Allow other computers to attach to debugpy.
   # 0.0.0.0 means all interfaces.
   debugpy.listen(("0.0.0.0", 5678))
   print("Debugger is listening on port 5678")
   # Optional: wait for the debugger to attach
   # print("Waiting for debugger attach...")
   # debugpy.wait_for_client()

   print("Hello, World!")
   ```
   And your `Dockerfile` would need to expose the port:
   ```dockerfile
   # Use an official Python runtime as a parent image
   FROM python:3.9-slim

   # Set the working directory in the container
   WORKDIR /app

   //highlight-next-line
   RUN pip install debugpy

   # Copy the current directory contents into the container at /app
   COPY . /app

   # Expose the port
   //highlight-next-line
   EXPOSE 5678

   # Run app.py when the container launches
   CMD ["python", "app.py"]
   ```
   Then, in your `launch.json` in the `.vscode` folder:
   ```json
   {
       "version": "0.2.0",
       "configurations": [
           {
               "name": "Python: Attach to Docker",
               "type": "python",
               "request": "attach",
               "connect": {
                   "host": "localhost", // Or the IP of your Docker container if not localhost
                   "port": 5678
               },
               "pathMappings": [
                   {
                       "localRoot": "${workspaceFolder}",
                       "remoteRoot": "/app" // The WORKDIR in your Dockerfile
                   }
               ],
               "justMyCode": true
           }
       ]
   }
   ```
   You would then:
   1. Rebuild the Docker image: `docker build -t hello-world-python .`
   2. Run the container, mapping the port: `docker run -p 5678:5678 hello-world-python`
   3. In Cursor, go to "Run and Debug", select "Python: Attach to Docker" and click the play button.
   4. Set breakpoints in `app.py`.

   **Option 2: Use VS Code's/Cursor's Remote - Containers extension (Recommended for development)**

   The "Remote - Containers" extension (identifier: `ms-vscode-remote.remote-containers`) by Microsoft is a more integrated way to develop inside a container.
   1. Install the "Remote - Containers" extension in Cursor IDE.
   2. Open the Command Palette (Ctrl+Shift+P) and search for "Remote-Containers: Open Folder in Container...".
   3. Select the project folder. Cursor will ask if you want to use the existing `Dockerfile`. Say yes.
   4. Cursor will then build (or rebuild) the image and start a container, then connect the IDE directly to that container. The terminal in Cursor will be inside the container.
   5. You can then run `app.py` directly or use a simpler Python debug configuration in `launch.json` (like "Python: Current File") because the IDE is effectively *inside* the container's environment.

   For this "Hello, World!" example, using Remote - Containers:
   - After opening the folder in the container, you can simply open `app.py`.
   - Go to the "Run and Debug" view.
   - Click "Run and Debug" and select "Python File" or "Python: Current File".
   - You should be able to set breakpoints and step through `print("Hello, World!")`.

### Summary for Debugging this Project (Simplest Path with Remote - Containers)

1.  **Install "Remote - Containers" extension** in Cursor IDE.
2.  Ensure Docker Desktop is running and WSL integration is enabled.
3.  Open your WSL terminal, navigate to the project folder.
4.  Open the project in Cursor IDE using `cursor .` (or `code .`).
5.  Use the Command Palette (Ctrl+Shift+P) and select **"Remote-Containers: Reopen in Container"**. It will use the existing `Dockerfile`.
6.  Once Cursor reloads and is connected to the container:
    *   Open `app.py`.
    *   Go to the "Run and Debug" panel.
    *   Click the "Run and Debug" button (or "create a launch.json file" if it's the first time).
    *   Choose "Python File" (or a similar option like "Python: Current File").
    *   Set a breakpoint on the `print("Hello, World!")` line.
    *   The debugger should stop at your breakpoint.

This provides a full development environment inside the container, making debugging straightforward.
