# Sandbox VNC Implementation

This directory contains a complete implementation of a Docker-based sandbox with VNC access via a Vue.js frontend.

## Structure

- `docker/`: Contains the Docker backend configuration.
  - `Dockerfile`: Defines the environment (Ubuntu, Xvfb, Fluxbox, x11vnc, websockify).
  - `supervisord.conf`: Manages the processes.
- `frontend/`: A minimal Vue 3 application using `@novnc/novnc`.
- `docker-compose.yml`: Orchestrates the backend services.

## How to Run

### 1. Start the Backend
Navigate to `sandbox/` and run:
```bash
docker-compose up --build
```
This will start the VNC server and the WebSocket proxy.
- VNC Port (TCP): 5900
- WebSocket Port: 6080

### 2. Start the Frontend
Navigate to `sandbox/frontend/` and install dependencies:
```bash
cd frontend
npm install
npm run dev
```
Open your browser at the URL provided by Vite (usually `http://localhost:5173`).

### 3. Connect
Click the "Connect" button in the web interface. You should see the Fluxbox desktop environment running inside the container.
