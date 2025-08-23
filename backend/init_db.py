#!/usr/bin/env python3
"""
Database initialization script for Garment Management System
"""

from main import create_app, db
from app.models import *
from sqlalchemy import text

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Initialize serial counters with error handling
        try:
            serial_types = ['ST', 'GB', 'PL', 'GBN']
            for serial_type in serial_types:
                counter = SerialCounter.get_or_create(serial_type)
                print(f"✅ Serial counter for {serial_type} initialized")
        except Exception as e:
            print(f"⚠️  Error initializing serial counters: {e}")
            print("   Continuing without serial counter initialization...")
        
        print("✅ Database initialization completed!")

if __name__ == '__main__':
    init_database()
