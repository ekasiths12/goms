#!/usr/bin/env python3
"""
Script to copy data from Railway database to local database
"""

import os
import sys
import subprocess
import json
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
    
    return railway_url

def get_local_db_url():
    """Get local database URL"""
    return 'mysql://GOMS:PGOMS@localhost/garment_db'

def create_backup_filename():
    """Create a backup filename with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"railway_backup_{timestamp}.sql"

def extract_mysql_credentials(url):
    """Extract MySQL credentials from URL"""
    # Remove mysql:// prefix
    url = url.replace('mysql://', '')
    
    # Split into parts
    if '@' in url:
        credentials, rest = url.split('@', 1)
        if ':' in credentials:
            username, password = credentials.split(':', 1)
        else:
            username = credentials
            password = ''
        
        # Extract host, port, and database
        if '/' in rest:
            host_port, database = rest.split('/', 1)
            if ':' in host_port:
                host, port = host_port.split(':', 1)
            else:
                host = host_port
                port = '3306'
        else:
            host = rest
            port = '3306'
            database = ''
    else:
        print("❌ Invalid database URL format")
        sys.exit(1)
    
    return {
        'username': username,
        'password': password,
        'host': host,
        'port': port,
        'database': database
    }

def dump_railway_database(railway_url, backup_file):
    """Dump Railway database to SQL file"""
    print(f"📦 Dumping Railway database to {backup_file}...")
    
    creds = extract_mysql_credentials(railway_url)
    
    # Build mysqldump command
    cmd = [
        'mysqldump',
        f'--host={creds["host"]}',
        f'--port={creds["port"]}',
        f'--user={creds["username"]}',
        f'--password={creds["password"]}',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--add-drop-database',
        '--create-options',
        creds['database']
    ]
    
    try:
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"✅ Railway database dumped successfully to {backup_file}")
            return True
        else:
            print(f"❌ Error dumping Railway database: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during database dump: {e}")
        return False

def restore_to_local_database(backup_file):
    """Restore SQL file to local database"""
    print("🔄 Restoring data to local database...")
    
    local_creds = extract_mysql_credentials(get_local_db_url())
    
    # Build mysql command
    cmd = [
        'mysql',
        f'--host={local_creds["host"]}',
        f'--port={local_creds["port"]}',
        f'--user={local_creds["username"]}',
        f'--password={local_creds["password"]}',
        local_creds['database']
    ]
    
    try:
        with open(backup_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print("✅ Data restored to local database successfully!")
            return True
        else:
            print(f"❌ Error restoring to local database: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error during database restore: {e}")
        return False

def check_mysql_tools():
    """Check if MySQL tools are available"""
    try:
        subprocess.run(['mysqldump', '--version'], capture_output=True, check=True)
        subprocess.run(['mysql', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    print("🚂 Railway to Local Database Copy Tool")
    print("=" * 50)
    
    # Check if MySQL tools are available
    if not check_mysql_tools():
        print("❌ MySQL tools (mysqldump, mysql) not found.")
        print("Please install MySQL client tools:")
        print("  - macOS: brew install mysql-client")
        print("  - Ubuntu: sudo apt-get install mysql-client")
        print("  - Windows: Download MySQL Workbench or MySQL Shell")
        sys.exit(1)
    
    # Get Railway database URL
    railway_url = get_railway_db_url()
    
    # Create backup filename
    backup_file = create_backup_filename()
    
    print(f"\n📋 Configuration:")
    print(f"   Railway DB: {railway_url.split('@')[0]}@***")
    print(f"   Local DB: {get_local_db_url()}")
    print(f"   Backup file: {backup_file}")
    
    # Confirm before proceeding
    confirm = input("\n🤔 Proceed with copying data? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Operation cancelled.")
        sys.exit(0)
    
    # Step 1: Dump Railway database
    if not dump_railway_database(railway_url, backup_file):
        print("❌ Failed to dump Railway database. Exiting.")
        sys.exit(1)
    
    # Step 2: Restore to local database
    if not restore_to_local_database(backup_file):
        print("❌ Failed to restore to local database. Exiting.")
        sys.exit(1)
    
    print("\n🎉 Data copy completed successfully!")
    print(f"📁 Backup file saved as: {backup_file}")
    print("💡 You can delete the backup file if you don't need it anymore.")

if __name__ == "__main__":
    main()
