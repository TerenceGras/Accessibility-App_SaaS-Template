FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Playwright browser dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    wget \
    unzip \
    ca-certificates \
    fonts-liberation \
    fonts-unifont \
    fonts-noto \
    fonts-noto-color-emoji \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xvfb \
    libgbm1 \
    libxss1 \
    libasound2-dev \
    libatspi2.0-0 \
    libgtk-4-1 \
    libxshmfence1 \
    libglu1-mesa \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user first
RUN useradd -m -u 1000 scanner && \
    mkdir -p /home/scanner/.cache && \
    chown -R scanner:scanner /home/scanner/.cache

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download axe-core library
RUN wget -O axe.min.js https://unpkg.com/axe-core@4.8.3/axe.min.js

# Copy application files
COPY . .
RUN chown -R scanner:scanner /app

# Switch to non-root user before installing browsers
USER scanner

# Install Playwright browsers as the scanner user
ENV PLAYWRIGHT_BROWSERS_PATH=/home/scanner/.cache/ms-playwright
RUN playwright install chromium

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
