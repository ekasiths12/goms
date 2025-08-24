#!/usr/bin/env python3
"""
Railway startup script for Garment Management System
"""

import os
import sys
from main import create_app, db
from app.models.serial_counter import SerialCounter
from sqlalchemy import text

# Import all models to ensure they're registered with SQLAlchemy
from app.models.customer import Customer
from app.models.invoice import Invoice, InvoiceLine, FabricInventory
from app.models.commission_sale import CommissionSale
from app.models.stitching import StitchingInvoice, GarmentFabric, LiningFabric
from app.models.packing_list import PackingList, PackingListLine
from app.models.group_bill import StitchingInvoiceGroup, StitchingInvoiceGroupLine
from app.models.image import Image
from app.models.stitched_item import StitchedItem
from app.models.customer_id_mapping import CustomerIdMapping
from app.models.delivery_location import DeliveryLocation

def fix_serial_counters():
    """Fix serial_counters table structure if needed"""
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
        print("   Continuing without serial counter fix...")

def main():
    """Main startup function"""
    print("🚀 Starting Garment Management System on Railway...")
    
    # Set up environment
    os.environ.setdefault('FLASK_ENV', 'production')
    os.environ.setdefault('FLASK_DEBUG', 'False')
    
    # Create app
    app = create_app()
    
    with app.app_context():
        # Check database connection
        try:
            db.session.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            sys.exit(1)
        
        # Add debugging here
        result = db.session.execute(text("SHOW TABLES LIKE 'invoice_lines'"))
        if result.fetchone():
            print("✅ invoice_lines table exists")
        else:
            print("❌ invoice_lines table does not exist")
        
        # List all tables
        all_tables = db.session.execute(text("SHOW TABLES")).fetchall()
        print("📋 All tables in database:")
        for table in all_tables:
            print(f"   - {table[0]}")
        
        # Create tables in dependency order to avoid foreign key issues
        from sqlalchemy.exc import OperationalError

        try:
            levels = [
                # Level 1: No dependencies
                [
                    Customer.__table__,
                    SerialCounter.__table__,
                    Image.__table__,
                    StitchedItem.__table__,
                    CustomerIdMapping.__table__,
                    DeliveryLocation.__table__,
                    FabricInventory.__table__,
                ],
                # Level 2: Depend on customers
                [
                    Invoice.__table__,
                    StitchingInvoiceGroup.__table__,
                    PackingList.__table__,
                ],
                # Level 3: Depend on invoices/packing_lists/groups
                [InvoiceLine.__table__],
                # Level 4: Depend on invoice_lines/groups/etc.
                [
                    CommissionSale.__table__,
                    StitchingInvoice.__table__,
                ],
                # Level 5: Depend on stitching_invoices
                [
                    GarmentFabric.__table__,
                    LiningFabric.__table__,
                    PackingListLine.__table__,
                    StitchingInvoiceGroupLine.__table__,
                ],
            ]

            for level in levels:
                db.metadata.create_all(db.engine, tables=level, checkfirst=True)
            print("✅ Database tables created successfully in order!")
        except OperationalError as e:
            print(f"⚠️  Error creating tables: {e}")
        
        # Fix serial counters
        fix_serial_counters()
        
        print("✅ Railway startup completed successfully!")

if __name__ == '__main__':
    main()
