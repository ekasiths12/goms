#!/usr/bin/env python3
"""
Garment Management System Startup Script
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting Garment Management System...")
    
    # Change to backend directory
    os.chdir('backend')
    
    # Run database initialization
    print("📊 Initializing database...")
    try:
        subprocess.run([sys.executable, 'railway_start.py'], check=True)
        print("✅ Database initialization completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    # Start the Flask application with Gunicorn
    print("🌐 Starting Flask application...")
    port = os.environ.get('PORT', '8000')
    
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '2',
        '--timeout', '120',
        'main:create_app'
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Application startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
