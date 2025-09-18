#!/usr/bin/env python3
"""
Database Import Script for Railway Production to Local Development

This script imports the database from Railway production environment
and overwrites the local development database.

Usage:
    python import_production_db.py

Requirements:
    - MySQL client tools (mysqldump, mysql)
    - Python packages: PyMySQL, python-dotenv
    - Local MySQL server running
    - Network access to Railway database
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Railway production database configuration
RAILWAY_CONFIG = {
    'host': 'shortline.proxy.rlwy.net',
    'port': '43260',
    'user': 'root',
    'password': 'GfXdBdQdvLYFhQDjOHDwurszAkmVxLjF',
    'database': 'railway'
}

# Local development database configuration
LOCAL_CONFIG = {
    'host': 'localhost',
    'port': '3306',
    'user': 'GOMS',
    'password': 'PGOMS',
    'database': 'garment_db'
}

def check_requirements():
    """Check if required tools are available"""
    print("🔍 Checking requirements...")
    
    # Check for mysqldump
    if not shutil.which('mysqldump'):
        print("❌ Error: mysqldump not found. Please install MySQL client tools.")
        return False
    
    # Check for mysql
    if not shutil.which('mysql'):
        print("❌ Error: mysql client not found. Please install MySQL client tools.")
        return False
    
    print("✅ MySQL client tools found")
    return True

def test_railway_connection():
    """Test connection to Railway database"""
    print("🔗 Testing Railway database connection...")
    
    try:
        import pymysql
        connection = pymysql.connect(
            host=RAILWAY_CONFIG['host'],
            port=int(RAILWAY_CONFIG['port']),
            user=RAILWAY_CONFIG['user'],
            password=RAILWAY_CONFIG['password'],
            database=RAILWAY_CONFIG['database'],
            connect_timeout=10
        )
        connection.close()
        print("✅ Railway database connection successful")
        return True
    except Exception as e:
        print(f"❌ Railway database connection failed: {e}")
        return False

def test_local_connection():
    """Test connection to local database"""
    print("🔗 Testing local database connection...")
    
    try:
        import pymysql
        connection = pymysql.connect(
            host=LOCAL_CONFIG['host'],
            port=int(LOCAL_CONFIG['port']),
            user=LOCAL_CONFIG['user'],
            password=LOCAL_CONFIG['password'],
            database=LOCAL_CONFIG['database'],
            connect_timeout=10
        )
        connection.close()
        print("✅ Local database connection successful")
        return True
    except Exception as e:
        print(f"❌ Local database connection failed: {e}")
        print("💡 Make sure your local MySQL server is running and the database exists")
        return False

def create_database_backup():
    """Create a backup of the current local database"""
    print("💾 Creating backup of local database...")
    
    backup_file = f"backup_garment_db_{int(__import__('time').time())}.sql"
    backup_path = Path(backup_file)
    
    try:
        cmd = [
            'mysqldump',
            f"--host={LOCAL_CONFIG['host']}",
            f"--port={LOCAL_CONFIG['port']}",
            f"--user={LOCAL_CONFIG['user']}",
            f"--password={LOCAL_CONFIG['password']}",
            '--single-transaction',
            '--routines',
            '--triggers',
            LOCAL_CONFIG['database']
        ]
        
        with open(backup_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"✅ Local database backed up to: {backup_path}")
            return str(backup_path)
        else:
            print(f"❌ Backup failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def export_railway_database():
    """Export database from Railway"""
    print("📤 Exporting database from Railway...")
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False)
    temp_path = temp_file.name
    temp_file.close()
    
    try:
        cmd = [
            'mysqldump',
            f"--host={RAILWAY_CONFIG['host']}",
            f"--port={RAILWAY_CONFIG['port']}",
            f"--user={RAILWAY_CONFIG['user']}",
            f"--password={RAILWAY_CONFIG['password']}",
            '--single-transaction',
            '--routines',
            '--triggers',
            '--set-gtid-purged=OFF',  # Important for Railway
            RAILWAY_CONFIG['database']
        ]
        
        with open(temp_path, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print("✅ Railway database exported successfully")
            return temp_path
        else:
            print(f"❌ Export failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return None

def clear_local_database():
    """Clear all tables in local database"""
    print("🗑️  Clearing local database...")
    
    try:
        import pymysql
        connection = pymysql.connect(
            host=LOCAL_CONFIG['host'],
            port=int(LOCAL_CONFIG['port']),
            user=LOCAL_CONFIG['user'],
            password=LOCAL_CONFIG['password'],
            database=LOCAL_CONFIG['database']
        )
        
        with connection.cursor() as cursor:
            # Disable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # Get all table names
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            # Drop all tables
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
                print(f"  Dropped table: {table}")
            
            # Re-enable foreign key checks
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        connection.commit()
        connection.close()
        print("✅ Local database cleared")
        return True
        
    except Exception as e:
        print(f"❌ Failed to clear local database: {e}")
        return False

def import_to_local_database(sql_file):
    """Import SQL file to local database"""
    print("📥 Importing data to local database...")
    
    try:
        cmd = [
            'mysql',
            f"--host={LOCAL_CONFIG['host']}",
            f"--port={LOCAL_CONFIG['port']}",
            f"--user={LOCAL_CONFIG['user']}",
            f"--password={LOCAL_CONFIG['password']}",
            LOCAL_CONFIG['database']
        ]
        
        with open(sql_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print("✅ Data imported successfully to local database")
            return True
        else:
            print(f"❌ Import failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def cleanup_temp_files(*files):
    """Clean up temporary files"""
    for file_path in files:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
                print(f"🧹 Cleaned up: {file_path}")
            except Exception as e:
                print(f"⚠️  Could not clean up {file_path}: {e}")

def main():
    """Main function"""
    print("🚀 Starting database import from Railway production...")
    print("=" * 60)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Test connections
    if not test_railway_connection():
        print("💡 Make sure you have internet connection and Railway database is accessible")
        sys.exit(1)
    
    if not test_local_connection():
        print("💡 Make sure your local MySQL server is running and the 'garment_db' database exists")
        sys.exit(1)
    
    # Confirm with user
    print("\n⚠️  WARNING: This will completely overwrite your local database!")
    print(f"   Local database: {LOCAL_CONFIG['database']}")
    print(f"   Railway database: {RAILWAY_CONFIG['database']}")
    
    response = input("\nDo you want to continue? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("❌ Operation cancelled by user")
        sys.exit(0)
    
    backup_file = None
    sql_file = None
    
    try:
        # Create backup
        backup_file = create_database_backup()
        if not backup_file:
            print("❌ Failed to create backup. Aborting for safety.")
            sys.exit(1)
        
        # Export from Railway
        sql_file = export_railway_database()
        if not sql_file:
            print("❌ Failed to export from Railway")
            sys.exit(1)
        
        # Clear local database
        if not clear_local_database():
            print("❌ Failed to clear local database")
            sys.exit(1)
        
        # Import to local database
        if not import_to_local_database(sql_file):
            print("❌ Failed to import to local database")
            print(f"💡 You can restore from backup: {backup_file}")
            sys.exit(1)
        
        print("\n" + "=" * 60)
        print("🎉 Database import completed successfully!")
        print(f"📁 Backup saved as: {backup_file}")
        print("💡 Your local database now contains the production data")
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if backup_file:
            print(f"💡 You can restore from backup: {backup_file}")
        sys.exit(1)
    finally:
        # Clean up temporary files
        cleanup_temp_files(sql_file)

if __name__ == "__main__":
    main()
