#!/usr/bin/env python3
"""
Migration script to transfer data from Qt app database to new web app database
"""

import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
import json

# Import new app models
from app.models import (
    Customer, Invoice, InvoiceLine, StitchingInvoice, 
    StitchingInvoiceGroup, StitchingInvoiceGroupLine,
    PackingList, PackingListLine, Image, SerialCounter
)

def migrate_qt_to_web_app():
    """Migrate data from Qt app MySQL database to new web app SQLite database"""
    
    # Qt app database connection (MySQL)
    qt_db_config = {
        'host': 'localhost',
        'user': 'root',  # Update with your Qt app database credentials
        'password': '',  # Update with your Qt app database password
        'database': 'garment_manager'  # Update with your Qt app database name
    }
    
    # New web app database connection (SQLite)
    web_app_db_url = 'sqlite:///backend/garment_web_app.db'
    web_app_engine = create_engine(web_app_db_url)
    WebAppSession = sessionmaker(bind=web_app_engine)
    
    try:
        # Connect to Qt app database
        qt_conn = mysql.connector.connect(**qt_db_config)
        qt_cursor = qt_conn.cursor(dictionary=True)
        
        # Connect to new web app database
        web_app_session = WebAppSession()
        
        print("Starting migration...")
        
        # 1. Migrate Customers
        print("Migrating customers...")
        qt_cursor.execute("SELECT * FROM customers")
        customers = qt_cursor.fetchall()
        
        for qt_customer in customers:
            web_customer = Customer(
                customer_id=qt_customer['customer_id'],
                short_name=qt_customer['short_name'],
                full_name=qt_customer['full_name'],
                registration_date=qt_customer['registration_date'],
                is_active=qt_customer['is_active']
            )
            web_app_session.add(web_customer)
        
        web_app_session.commit()
        print(f"Migrated {len(customers)} customers")
        
        # 2. Migrate Images
        print("Migrating images...")
        qt_cursor.execute("SELECT * FROM images")
        images = qt_cursor.fetchall()
        
        for qt_image in images:
            web_image = Image(
                file_path=qt_image['file_path'],
                uploaded_at=qt_image['uploaded_at']
            )
            web_app_session.add(web_image)
        
        web_app_session.commit()
        print(f"Migrated {len(images)} images")
        
        # 3. Migrate Invoices
        print("Migrating invoices...")
        qt_cursor.execute("SELECT * FROM invoices")
        invoices = qt_cursor.fetchall()
        
        for qt_invoice in invoices:
            web_invoice = Invoice(
                invoice_number=qt_invoice['invoice_number'],
                customer_id=qt_invoice['customer_id'],
                invoice_date=qt_invoice['invoice_date'],
                total_amount=qt_invoice['total_amount'],
                status=qt_invoice['status'],
                tax_invoice_number=qt_invoice['tax_invoice_number']
            )
            web_app_session.add(web_invoice)
        
        web_app_session.commit()
        print(f"Migrated {len(invoices)} invoices")
        
        # 4. Migrate Invoice Lines
        print("Migrating invoice lines...")
        qt_cursor.execute("SELECT * FROM invoice_lines")
        invoice_lines = qt_cursor.fetchall()
        
        for qt_line in invoice_lines:
            web_line = InvoiceLine(
                invoice_id=qt_line['invoice_id'],
                item_name=qt_line['item_name'],
                quantity=qt_line['quantity'],
                unit_price=qt_line['unit_price'],
                delivered_location=qt_line['delivered_location'],
                is_defective=qt_line['is_defective'],
                color=qt_line['color'],
                delivery_note=qt_line['delivery_note'],
                yards_sent=qt_line['yards_sent'],
                yards_consumed=qt_line['yards_consumed']
            )
            web_app_session.add(web_line)
        
        web_app_session.commit()
        print(f"Migrated {len(invoice_lines)} invoice lines")
        
        # 5. Migrate Stitching Invoices
        print("Migrating stitching invoices...")
        qt_cursor.execute("SELECT * FROM stitching_invoices")
        stitching_invoices = qt_cursor.fetchall()
        
        for qt_stitching in stitching_invoices:
            web_stitching = StitchingInvoice(
                stitching_invoice_number=qt_stitching['stitching_invoice_number'],
                item_name=qt_stitching['item_name'],
                yard_consumed=qt_stitching['yard_consumed'],
                stitched_item=qt_stitching['stitched_item'],
                size_qty_json=qt_stitching['size_qty_json'],
                price=qt_stitching['price'],
                total_value=qt_stitching['total_value'],
                add_vat=qt_stitching['add_vat'],
                image_id=qt_stitching['image_id'],
                created_at=qt_stitching['created_at'],
                billing_group_id=qt_stitching['billing_group_id'],
                invoice_line_id=qt_stitching['invoice_line_id'],
                total_fabric_cost=qt_stitching['total_fabric_cost'],
                total_lining_cost=qt_stitching['total_lining_cost']
            )
            web_app_session.add(web_stitching)
        
        web_app_session.commit()
        print(f"Migrated {len(stitching_invoices)} stitching invoices")
        
        # 6. Migrate Stitching Invoice Groups
        print("Migrating stitching invoice groups...")
        qt_cursor.execute("SELECT * FROM stitching_invoice_groups")
        groups = qt_cursor.fetchall()
        
        for qt_group in groups:
            web_group = StitchingInvoiceGroup(
                group_number=qt_group['group_number'],
                customer_id=qt_group['customer_id'],
                created_at=qt_group['created_at'],
                invoice_date=qt_group['invoice_date'],
                stitching_comments=qt_group['stitching_comments'],
                fabric_comments=qt_group['fabric_comments']
            )
            web_app_session.add(web_group)
        
        web_app_session.commit()
        print(f"Migrated {len(groups)} stitching invoice groups")
        
        # 7. Migrate Group Lines
        print("Migrating group lines...")
        qt_cursor.execute("SELECT * FROM stitching_invoice_group_lines")
        group_lines = qt_cursor.fetchall()
        
        for qt_line in group_lines:
            web_line = StitchingInvoiceGroupLine(
                group_id=qt_line['group_id'],
                stitching_invoice_id=qt_line['stitching_invoice_id']
            )
            web_app_session.add(web_line)
        
        web_app_session.commit()
        print(f"Migrated {len(group_lines)} group lines")
        
        # 8. Migrate Packing Lists
        print("Migrating packing lists...")
        qt_cursor.execute("SELECT * FROM packing_lists")
        packing_lists = qt_cursor.fetchall()
        
        for qt_pl in packing_lists:
            web_pl = PackingList(
                packing_list_serial=qt_pl['packing_list_serial'],
                customer_id=qt_pl['customer_id'],
                created_at=qt_pl['created_at'],
                tax_invoice_number=qt_pl['tax_invoice_number']
            )
            web_app_session.add(web_pl)
        
        web_app_session.commit()
        print(f"Migrated {len(packing_lists)} packing lists")
        
        # 9. Migrate Packing List Lines
        print("Migrating packing list lines...")
        qt_cursor.execute("SELECT * FROM packing_list_lines")
        pl_lines = qt_cursor.fetchall()
        
        for qt_line in pl_lines:
            web_line = PackingListLine(
                packing_list_id=qt_line['packing_list_id'],
                stitching_invoice_id=qt_line['stitching_invoice_id']
            )
            web_app_session.add(web_line)
        
        web_app_session.commit()
        print(f"Migrated {len(pl_lines)} packing list lines")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        web_app_session.rollback()
    finally:
        qt_cursor.close()
        qt_conn.close()
        web_app_session.close()

if __name__ == "__main__":
    migrate_qt_to_web_app()
