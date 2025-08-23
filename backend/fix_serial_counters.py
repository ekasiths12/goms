#!/usr/bin/env python3
"""
Fix serial_counters table structure to match the expected model
"""

from main import create_app, db
from app.models.serial_counter import SerialCounter
from sqlalchemy import text

def fix_serial_counters_table():
    """Fix the serial_counters table structure"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the table exists and has the wrong structure
            result = db.session.execute(text("SHOW TABLES LIKE 'serial_counters'"))
            if result.fetchone():
                print("🔍 Found existing serial_counters table")
                
                # Check current table structure
                result = db.session.execute(text("DESCRIBE serial_counters"))
                columns = [row[0] for row in result.fetchall()]
                print(f"📋 Current columns: {columns}")
                
                # If the table doesn't have an 'id' column, we need to recreate it
                if 'id' not in columns:
                    print("⚠️  Table missing 'id' column, recreating...")
                    
                    # Drop the existing table
                    db.session.execute(text("DROP TABLE serial_counters"))
                    db.session.commit()
                    print("✅ Dropped old serial_counters table")
                    
                    # Create the table with correct structure
                    db.create_all()
                    print("✅ Created new serial_counters table with correct structure")
                    
                    # Initialize with default values
                    serial_types = ['ST', 'GB', 'PL', 'GBN']
                    for serial_type in serial_types:
                        counter = SerialCounter(serial_type=serial_type, last_value=0)
                        db.session.add(counter)
                    
                    db.session.commit()
                    print("✅ Initialized serial counters with default values")
                    
                else:
                    print("✅ Table structure is correct")
                    
            else:
                print("📝 Creating new serial_counters table")
                db.create_all()
                
                # Initialize with default values
                serial_types = ['ST', 'GB', 'PL', 'GBN']
                for serial_type in serial_types:
                    counter = SerialCounter(serial_type=serial_type, last_value=0)
                    db.session.add(counter)
                
                db.session.commit()
                print("✅ Created and initialized serial counters")
                
            # Verify the fix
            counters = SerialCounter.query.all()
            print(f"✅ Verification: Found {len(counters)} serial counters")
            for counter in counters:
                print(f"   - {counter.serial_type}: {counter.last_value}")
                
        except Exception as e:
            print(f"❌ Error fixing serial counters: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    fix_serial_counters_table()
