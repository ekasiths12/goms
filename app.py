#!/usr/bin/env python3
"""
Root app.py file for Nixpacks detection
This file helps Nixpacks identify this as a Python project
"""

import os
import sys

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Import and create the Flask app
from backend.main import create_app
app = create_app()

# Run the app if this file is executed directly
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
