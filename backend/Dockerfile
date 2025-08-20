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
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static/uploads static/pdfs static/images

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the Railway startup script and then the application
CMD ["sh", "-c", "python railway_start.py && gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 app:app"]
