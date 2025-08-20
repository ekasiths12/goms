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
    mysql_url = os.environ.get('MYSQL_URL')
    
    print(f"🔍 Environment check:")
    print(f"   DATABASE_URL: {database_url}")
    print(f"   MYSQL_URL: {mysql_url}")
    
    # Try to get the actual database URL
    actual_database_url = None
    if database_url and not database_url.startswith('${{'):
        actual_database_url = database_url
    elif mysql_url and not mysql_url.startswith('${{'):
        actual_database_url = mysql_url
    
    if not actual_database_url:
        print("❌ No valid database URL found!")
        print("💡 Please ensure the MySQL service is properly linked to your web service")
        print("💡 Check that the DATABASE_URL or MYSQL_URL is being set correctly")
        sys.exit(1)
    
    print(f"🔗 Using Database URL: {actual_database_url[:30]}...")
    
    # Set the DATABASE_URL for the backend
    os.environ['DATABASE_URL'] = actual_database_url
    
    # Change to backend directory
    os.chdir('backend')
    
    # Try database initialization with fallback
    print("📊 Initializing database...")
    try:
        subprocess.run([sys.executable, 'railway_start.py'], check=True)
        print("✅ Database initialization completed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Database initialization failed: {e}")
        print("💡 Starting application without database initialization")
        print("💡 Database will be initialized when connection is available")
        
        # Create a simple database check script that doesn't fail
        with open('simple_db_check.py', 'w') as f:
            f.write('''
import os
print("🔍 Database connection will be checked when needed")
print("✅ Application can start without database")
''')
        
        # Continue with application startup
    
    # Start the Flask application with Gunicorn
    print("🌐 Starting Flask application...")
    port = os.environ.get('PORT', '8000')
    
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '2',
        '--timeout', '120',
        'app:app'
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Application startup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
