#!/usr/bin/env python3
"""
WSGI entry point for Garment Management System
"""

from main import create_app

# Create the Flask application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
