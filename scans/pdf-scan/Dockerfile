# Simplified PDF AI Scanner Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PDF processing and image conversion
RUN apt-get update && apt-get install -y \
    curl \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 pdfscanner && \
    mkdir -p /home/pdfscanner/.cache && \
    chown -R pdfscanner:pdfscanner /home/pdfscanner/.cache

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .
RUN chown -R pdfscanner:pdfscanner /app

# Switch to non-root user
USER pdfscanner

# Create directories for temporary files
RUN mkdir -p /home/pdfscanner/temp

# Set environment variables
ENV TEMP_DIR=/home/pdfscanner/temp
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
