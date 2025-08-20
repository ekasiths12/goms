#!/bin/bash

# Garment Management System Startup Script

echo "🚀 Starting Garment Management System..."

# Change to backend directory
cd backend

# Run database initialization
echo "📊 Initializing database..."
python railway_start.py

# Start the Flask application with Gunicorn
echo "🌐 Starting Flask application..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 main:create_app
