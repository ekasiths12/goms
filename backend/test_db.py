#!/usr/bin/env python3
"""
Database connection test script
"""

import os
import sys
import time

def test_database_connection():
    """Test database connection directly"""
    print("🔍 Testing database connection...")
    
    # Get database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set")
        return False
    
    print(f"🔗 Database URL: {database_url[:30]}...")
    
    try:
        # Import PyMySQL directly
        import pymysql
        
        # Parse the URL
        if database_url.startswith('mysql://'):
            # Remove mysql:// prefix
            connection_string = database_url[8:]
            
            # Parse username:password@host:port/database
            if '@' in connection_string:
                auth_part, rest = connection_string.split('@', 1)
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                else:
                    username, password = auth_part, ''
                
                if '/' in rest:
                    host_port, database = rest.split('/', 1)
                    if ':' in host_port:
                        host, port = host_port.split(':', 1)
                        port = int(port)
                    else:
                        host, port = host_port, 3306
                else:
                    host_port, database = rest, ''
                    if ':' in host_port:
                        host, port = host_port.split(':', 1)
                        port = int(port)
                    else:
                        host, port = host_port, 3306
            else:
                print("❌ Invalid database URL format")
                return False
            
            print(f"🔍 Connection details:")
            print(f"   Host: {host}")
            print(f"   Port: {port}")
            print(f"   Database: {database}")
            print(f"   Username: {username}")
            
            # Test connection
            print("🔌 Attempting connection...")
            connection = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password,
                database=database,
                charset='utf8mb4',
                connect_timeout=10
            )
            
            print("✅ Database connection successful!")
            
            # Test a simple query
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                print(f"✅ Query test successful: {result}")
            
            # Also test SQLAlchemy connection
            print("🔍 Testing SQLAlchemy connection...")
            from main import create_app, db
            app = create_app()
            with app.app_context():
                with db.engine.connect() as connection:
                    result = connection.execute(db.text('SELECT 1'))
                    result.close()
                print("✅ SQLAlchemy connection test successful")
            
            connection.close()
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == '__main__':
    success = test_database_connection()
    if not success:
        sys.exit(1)
