#!/usr/bin/env python3
"""
Railway Migration Script for Customer ID Mappings
Run this script on Railway to migrate customer IDs from JSON to database
"""

import os
import sys
import json
from datetime import datetime

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import create_app
from extensions import db
from app.models.customer_id_mapping import CustomerIdMapping

def migrate_customer_ids_to_railway():
    """Migrate customer IDs to Railway database"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 Starting Railway customer ID migration...")
            
            # Create the table if it doesn't exist
            db.create_all()
            print("✅ Database tables created/verified")
            
            # Check if we already have data in the table
            existing_count = CustomerIdMapping.query.count()
            if existing_count > 0:
                print(f"⚠️  Customer ID mappings table already has {existing_count} records")
                print("✅ Migration already completed or partially completed")
                return
            
            # Try to load customer IDs from various possible locations
            customer_ids = []
            
            # Try backend directory
            backend_file = os.path.join(os.path.dirname(__file__), 'customer_ids.json')
            if os.path.exists(backend_file):
                try:
                    with open(backend_file, 'r') as f:
                        customer_ids = json.load(f)
                    print(f"📄 Loaded {len(customer_ids)} customer IDs from backend/customer_ids.json")
                except Exception as e:
                    print(f"❌ Error reading backend/customer_ids.json: {e}")
            
            # Try root directory
            if not customer_ids:
                root_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'customer_ids.json')
                if os.path.exists(root_file):
                    try:
                        with open(root_file, 'r') as f:
                            customer_ids = json.load(f)
                        print(f"📄 Loaded {len(customer_ids)} customer IDs from root/customer_ids.json")
                    except Exception as e:
                        print(f"❌ Error reading root/customer_ids.json: {e}")
            
            # If no JSON file found, use default customer IDs
            if not customer_ids:
                print("⚠️  No customer_ids.json file found, using default customer IDs")
                customer_ids = ["280", "322", "325", "327", "328", "332", "355", "360", "362", "363", "365", "371", "375", "384", "387", "396", "397", "398", "410", "416", "425", "429", "430", "433", "441", "451", "454"]
            
            # Migrate customer IDs to database
            migrated_count = 0
            for customer_id in customer_ids:
                # Check if mapping already exists
                existing = CustomerIdMapping.get_by_customer_id(customer_id)
                if not existing:
                    mapping = CustomerIdMapping(customer_id=customer_id)
                    db.session.add(mapping)
                    migrated_count += 1
                    print(f"➕ Added customer ID mapping: {customer_id}")
                else:
                    print(f"⏭️  Skipped existing customer ID: {customer_id}")
            
            # Commit the changes
            db.session.commit()
            print(f"✅ Successfully migrated {migrated_count} customer IDs to Railway database")
            
            # Verify the migration
            total_count = CustomerIdMapping.query.count()
            print(f"📊 Total customer ID mappings in Railway database: {total_count}")
            
            print("\n✅ Railway migration completed successfully!")
            print("🎉 Your application is ready to use with the new customer ID mapping system!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Railway migration failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_customer_ids_to_railway()
