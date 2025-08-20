#!/usr/bin/env python3
"""
Garment Management System Startup Script
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting Garment Management System...")
    
    # Check if DATABASE_URL is set
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        print("💡 Please add a MySQL database service to your Railway project")
        print("💡 Or set DATABASE_URL manually in environment variables")
        sys.exit(1)
    
    print(f"🔗 Database URL: {database_url[:20]}...")
    
    # Change to backend directory
    os.chdir('backend')
    
    # Run database initialization
    print("📊 Initializing database...")
    try:
        subprocess.run([sys.executable, 'railway_start.py'], check=True)
        print("✅ Database initialization completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Database initialization failed: {e}")
        print("💡 Please check your DATABASE_URL and ensure the database is accessible")
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
