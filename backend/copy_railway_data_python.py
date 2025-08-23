#!/usr/bin/env python3
"""
Python-based script to copy data from Railway database to local database using SQLAlchemy
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime

def get_railway_db_url():
    """Get Railway database URL from environment or user input"""
    railway_url = os.environ.get('RAILWAY_DATABASE_URL')
    
    if not railway_url:
        print("🔍 Railway Database URL not found in environment variables.")
        print("Please provide your Railway database URL:")
        print("Format: mysql://username:password@host:port/database")
        railway_url = input("Railway Database URL: ").strip()
        
        if not railway_url:
            print("❌ No database URL provided. Exiting.")
            sys.exit(1)
    
    # Convert to SQLAlchemy format
    if railway_url.startswith('mysql://'):
        railway_url = railway_url.replace('mysql://', 'mysql+pymysql://', 1)
    
    return railway_url

def get_local_db_url():
    """Get local database URL"""
    return 'mysql+pymysql://GOMS:PGOMS@localhost/garment_db'

def copy_table_data(railway_engine, local_engine, table_name):
    """Copy data from one table to another"""
    try:
        print(f"📋 Copying table: {table_name}")
        
        # Read data from Railway
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, railway_engine)
        
        if df.empty:
            print(f"   ⚠️  Table {table_name} is empty, skipping...")
            return True
        
        print(f"   📊 Found {len(df)} rows")
        
        # Write to local database
        df.to_sql(table_name, local_engine, if_exists='replace', index=False)
        
        print(f"   ✅ Successfully copied {len(df)} rows")
        return True
        
    except Exception as e:
        print(f"   ❌ Error copying table {table_name}: {e}")
        return False

def get_table_list(engine):
    """Get list of tables from database"""
    inspector = inspect(engine)
    return inspector.get_table_names()

def main():
    print("🚂 Railway to Local Database Copy Tool (Python)")
    print("=" * 55)
    
    # Get database URLs
    railway_url = get_railway_db_url()
    local_url = get_local_db_url()
    
    print(f"\n📋 Configuration:")
    print(f"   Railway DB: {railway_url.split('@')[0]}@***")
    print(f"   Local DB: {local_url}")
    
    # Create database engines
    try:
        print("\n🔌 Connecting to databases...")
        railway_engine = create_engine(railway_url)
        local_engine = create_engine(local_url)
        
        # Test connections
        with railway_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ Railway database connected")
        
        with local_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("   ✅ Local database connected")
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)
    
    # Get table list from Railway
    try:
        railway_tables = get_table_list(railway_engine)
        print(f"\n📋 Found {len(railway_tables)} tables in Railway database:")
        for table in railway_tables:
            print(f"   - {table}")
    except Exception as e:
        print(f"❌ Error getting table list: {e}")
        sys.exit(1)
    
    # Confirm before proceeding
    confirm = input(f"\n🤔 Copy all {len(railway_tables)} tables to local database? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        sys.exit(0)
    
    # Copy each table
    print(f"\n🔄 Starting data copy...")
    successful_tables = []
    failed_tables = []
    
    for table in railway_tables:
        if copy_table_data(railway_engine, local_engine, table):
            successful_tables.append(table)
        else:
            failed_tables.append(table)
    
    # Summary
    print(f"\n📊 Copy Summary:")
    print(f"   ✅ Successful: {len(successful_tables)} tables")
    print(f"   ❌ Failed: {len(failed_tables)} tables")
    
    if successful_tables:
        print(f"   📋 Successfully copied tables: {', '.join(successful_tables)}")
    
    if failed_tables:
        print(f"   ❌ Failed tables: {', '.join(failed_tables)}")
    
    if failed_tables:
        print(f"\n💡 Some tables failed to copy. You may need to:")
        print(f"   - Check table permissions")
        print(f"   - Verify table structure compatibility")
        print(f"   - Run the script again for failed tables")
    
    print(f"\n🎉 Data copy completed!")

if __name__ == "__main__":
    main()
