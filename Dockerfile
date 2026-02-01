# Use a stable Debian-based image to match system PyQt6
FROM debian:bookworm-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV QT_QPA_PLATFORM=xcb
ENV DISPLAY=:99

# Install system dependencies including Python and PyQt6
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-pyqt6 \
    qt6-base-dev \
    libgl1 \
    libegl1 \
    libdbus-1-3 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-util1 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libfontconfig1 \
    libxrender1 \
    libxi6 \
    libxtst6 \
    libglib2.0-0 \
    xvfb \
    x11vnc \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
# Use system pip to install requirements for the system python3
# Setting PIP_BREAK_SYSTEM_PACKAGES=1 because Debian restricts pip in system python
RUN sed -i '/PyQt6/d' requirements.txt && \
    PIP_BREAK_SYSTEM_PACKAGES=1 python3 -m pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data/backups/auto data/kyc credentials logs

# Expose VNC port
EXPOSE 5900

# Start Xvfb, wait for it, then run x11vnc and the app using system python3
CMD Xvfb :99 -screen 0 1280x1024x24 & \
    sleep 2 && \
    x11vnc -display :99 -nopw -forever -quiet & \
    /usr/bin/python3 main.py
