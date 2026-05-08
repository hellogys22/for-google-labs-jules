FROM python:3.11-slim

# Install system dependencies for Playwright, yt-dlp, and MoviePy
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps

# Copy project files
COPY . .

CMD ["python", "main.py"]