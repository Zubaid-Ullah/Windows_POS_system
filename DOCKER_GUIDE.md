# Enterprise Docker Deployment Guide

## 🐳 Overview
This guide explains how to deploy the POS System using Docker, ensuring a consistent environment across any machine (Mac, Windows, Linux).

## 🚀 Auto-Pilot Launcher (Recommended)
We have created a smart script `docker_launcher.py` that handles everything for you.
It works by:
1.  **Checking for Docker**: If missing, it attempts to auto-install it.
2.  **Checking for X11/XQuartz**: Essential for showing the GUI on Mac/Linux. It auto-installs if missing.
3.  **Building the Container**: Compiles your app into a secure standard image.
4.  **Running the App**: Launches the POS directly on your desktop.

**To start, simply run:**
```bash
python3 docker_launcher.py
```

---

## 🛠 Manual Setup (For Advanced Users)

### 1. Prerequisites
-   **Docker Desktop**: Must be installed and running.
-   **XQuartz (Mac Only)**: Required to display the app window.
    -   Install: `brew install --cask xquartz`
    -   Open XQuartz > Preferences > Security > Check "Allow connections from network clients"
    -   Restart Mac.

### 2. Build the Image
Run this in the project directory:
```bash
docker build -t pos-system .
```

### 3. Run the Container
**MacOS (Apple Silicon/Intel):**
```bash
# Allow local X11 connections
xhost +localhost

# Run container
docker run -it --rm \
  -e DISPLAY=host.docker.internal:0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v $(pwd)/data:/app/data \
  pos-system
```

**Windows (PowerShell):**
*Note: Requires VcXsrv (XLaunch) installed on Windows.*
```powershell
docker run -it --rm `
  -e DISPLAY=host.docker.internal:0.0 `
  -v ${PWD}/data:/app/data `
  pos-system
```

## 📁 Data Persistence
The `docker_launcher.py` and manual commands map the local `./data` folder to `/app/data` inside the container. This ensures your **Database** and **Backups** are saved on your actual computer, not lost when the container stops.
