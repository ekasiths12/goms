#!/usr/bin/env python3
"""
WSGI entry point for Garment Management System
"""

import os
import sys

# Set environment variables
os.environ['FLASK_APP'] = 'main.py'
os.environ['FLASK_ENV'] = 'production'

try:
    # Import and create the Flask app
    from main import create_app
    app = create_app()
    print("✅ Flask app created successfully")
except Exception as e:
    print(f"❌ Error creating Flask app: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    raise

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
