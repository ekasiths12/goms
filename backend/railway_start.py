#!/usr/bin/env python3
"""
Railway startup script for Garment Management System
"""

import os
import time
from main import create_app, db
from app.models import *

def wait_for_database():
    """Wait for database to be ready"""
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            app = create_app()
            with app.app_context():
                # Test the connection with a simple query using new SQLAlchemy syntax
                with db.engine.connect() as connection:
                    result = connection.execute(db.text('SELECT 1'))
                    result.close()
                print("✅ Database connection successful!")
                return True
        except Exception as e:
            attempt += 1
            print(f"⏳ Waiting for database... (attempt {attempt}/{max_attempts})")
            print(f"   Error: {str(e)[:100]}...")
            time.sleep(3)  # Increased wait time
    
    print("❌ Database connection failed after maximum attempts")
    print("💡 Please check:")
    print("   1. MySQL service is running")
    print("   2. Database credentials are correct")
    print("   3. Network connectivity between services")
    return False

def initialize_database():
    """Initialize database tables and data"""
    try:
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Check if serial_counters table exists and create initial counters
            try:
                # Test if serial_counters table exists
                with db.engine.connect() as connection:
                    result = connection.execute(db.text("SHOW TABLES LIKE 'serial_counters'"))
                    table_exists = result.fetchone() is not None
                    result.close()
                
                if table_exists:
                    # Create initial serial counters
                    serial_types = ['ST', 'GB', 'PL', 'GBN']
                    for serial_type in serial_types:
                        counter = SerialCounter.get_or_create(serial_type)
                        print(f"✅ Serial counter for {serial_type} initialized")
                else:
                    print("⚠️  serial_counters table not found, skipping counter initialization")
                    
            except Exception as e:
                print(f"⚠️  Error initializing serial counters: {e}")
                print("   Continuing without serial counter initialization...")
            
            print("✅ Database initialization completed!")
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting Garment Management System on Railway...")
    
    # Wait for database to be ready
    if not wait_for_database():
        return False
    
    # Initialize database
    if not initialize_database():
        return False
    
    print("✅ Railway startup completed successfully!")
    return True

if __name__ == '__main__':
    success = main()
    if not success:
        exit(1)
