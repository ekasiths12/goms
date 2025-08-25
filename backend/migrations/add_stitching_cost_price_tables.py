"""
Database migration script to add stitching cost and price tracking features.

This migration adds:
1. stitching_costs table for memorizing costs by garment and location
2. stitching_prices table for memorizing prices by garment and customer  
3. stitching_cost field to existing stitching_invoices table
"""

from extensions import db
from sqlalchemy import text

def upgrade():
    """Apply the migration"""
    print("Starting migration: add_stitching_cost_price_tables")
    
    # Create stitching_costs table
    print("Creating stitching_costs table...")
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS stitching_costs (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            garment_name VARCHAR(255) NOT NULL,
            stitching_location VARCHAR(255) NOT NULL,
            cost DECIMAL(10,2) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_garment_location_cost (garment_name, stitching_location)
        )
    """))
    
    # Create stitching_prices table
    print("Creating stitching_prices table...")
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS stitching_prices (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            garment_name VARCHAR(255) NOT NULL,
            customer_id INTEGER NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_garment_customer_price (garment_name, customer_id),
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        )
    """))
    
    # Add stitching_cost column to stitching_invoices table
    print("Adding stitching_cost column to stitching_invoices table...")
    try:
        db.session.execute(text("""
            ALTER TABLE stitching_invoices 
            ADD COLUMN stitching_cost DECIMAL(10,2) DEFAULT 0.00
        """))
        print("Successfully added stitching_cost column")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("stitching_cost column already exists, skipping...")
        else:
            raise e
    
    # Commit all changes
    db.session.commit()
    print("Migration completed successfully!")

def downgrade():
    """Rollback the migration"""
    print("Rolling back migration: add_stitching_cost_price_tables")
    
    # Drop stitching_costs table
    print("Dropping stitching_costs table...")
    db.session.execute(text("DROP TABLE IF EXISTS stitching_costs"))
    
    # Drop stitching_prices table
    print("Dropping stitching_prices table...")
    db.session.execute(text("DROP TABLE IF EXISTS stitching_prices"))
    
    # Remove stitching_cost column from stitching_invoices table
    print("Removing stitching_cost column from stitching_invoices table...")
    try:
        db.session.execute(text("""
            ALTER TABLE stitching_invoices 
            DROP COLUMN stitching_cost
        """))
        print("Successfully removed stitching_cost column")
    except Exception as e:
        if "doesn't exist" in str(e):
            print("stitching_cost column doesn't exist, skipping...")
        else:
            raise e
    
    # Commit all changes
    db.session.commit()
    print("Rollback completed successfully!")

if __name__ == "__main__":
    # This script can be run directly to apply the migration
    from main import create_app
    app = create_app()
    
    with app.app_context():
        upgrade()
