FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies with better error handling
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Create necessary directories (these will be mounted as volumes in Railway)
RUN mkdir -p static/uploads static/pdfs static/images

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV RAILWAY_VOLUME_PATH=/app/static

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "start.py"]
