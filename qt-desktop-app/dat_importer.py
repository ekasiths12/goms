import os
import traceback
import logging
from typing import List, Optional, Dict, Any
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# --- DB CONFIG ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'GOMS',
    'password': 'PGOMS',
    'database': 'garment_db',
    'autocommit': True
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise RuntimeError(f"Database connection failed: {e}")

def import_dat_file_core(
    file_path: str,
    selected_customer_ids: Optional[List[str]] = None,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Import a .dat file into the database. Optionally filter by customer IDs.
    Returns a dict with summary, errors, imported_count, skipped_count.
    """
    if logger is None:
        logger = logging.getLogger("dat_importer")
    summary = []
    errors = []
    imported_count = 0
    skipped_count = 0
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        errors.append(f"File read error: {e}")
        return {
            'imported_count': 0,
            'skipped_count': 0,
            'errors': errors,
            'summary': summary,
            'file_path': file_path
        }
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    invoice_line_counts = {}
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(';')]
        if len(parts) < 14:
            errors.append(f"Line {idx+1}: Invalid format (expected 14 fields, got {len(parts)})")
            logger.warning(f"Line {idx+1}: Invalid format: {line}")
            continue
        # Map fields
        tax = parts[0]
        short_name = parts[1]
        customer_id = parts[2]
        date_raw = parts[3]
        invoice_number = parts[4]
        currency = parts[5]
        item_code = parts[6]
        item_details = parts[7]
        fabric_amount = parts[8]
        price_per_unit = parts[9]
        description = parts[11]
        vat = parts[12]
        # Convert padded customer ID
        try:
            customer_id_normalized = str(int(customer_id))
        except ValueError:
            customer_id_normalized = customer_id
        # Filter by customer ID
        if selected_customer_ids and customer_id_normalized not in selected_customer_ids:
            skipped_count += 1
            continue
        # Parse date
        invoice_date = None
        if date_raw and len(date_raw) == 8:
            try:
                invoice_date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
            except Exception:
                invoice_date = None
        # Calculate total value
        try:
            fabric_qty = float(fabric_amount or 0)
            unit_price = float(price_per_unit or 0)
            calculated_total_value = fabric_qty * unit_price
        except (ValueError, TypeError):
            calculated_total_value = 0.0
            logger.warning(f"Line {idx+1}: Could not calculate total value from fabric_amount={fabric_amount}, price_per_unit={price_per_unit}")
        # Ensure customer exists
        cursor.execute("SELECT id FROM customers WHERE customer_id=%s AND short_name=%s", (customer_id_normalized, short_name))
        customer = cursor.fetchone()
        if not customer:
            cursor.execute(
                "INSERT INTO customers (customer_id, short_name, full_name, registration_date, is_active) VALUES (%s, %s, %s, %s, %s)",
                (customer_id_normalized, short_name, short_name, None, True)
            )
            customer_db_id = cursor.lastrowid
        else:
            customer_db_id = customer['id']
        # Handle duplicate invoice numbers
        if invoice_number in invoice_line_counts:
            invoice_line_counts[invoice_number] += 1
        else:
            invoice_line_counts[invoice_number] = 1
        modified_invoice_number = f"{invoice_number}-{invoice_line_counts[invoice_number]:02d}"
        # Insert or update invoice
        cursor.execute("SELECT id FROM invoices WHERE invoice_number=%s AND customer_id=%s", (modified_invoice_number, customer_db_id))
        invoice = cursor.fetchone()
        if not invoice:
            cursor.execute(
                "INSERT INTO invoices (invoice_number, customer_id, invoice_date, total_amount, status, tax_invoice_number) VALUES (%s, %s, %s, %s, %s, %s)",
                (modified_invoice_number, customer_db_id, invoice_date, calculated_total_value, 'open', None)
            )
            invoice_id = cursor.lastrowid
        else:
            invoice_id = invoice['id']
        # Extract color and delivery note
        details_parts = [p.strip() for p in item_details.split('/') if p.strip()]
        color = details_parts[1] if len(details_parts) > 1 else ''
        delivery_note = ''
        if len(details_parts) > 2:
            if details_parts[2] == '0' and len(details_parts) > 3:
                delivery_note = details_parts[3]
            else:
                delivery_note = details_parts[2]
        # Insert invoice line
        try:
            cursor.execute(
                "INSERT INTO invoice_lines (invoice_id, item_name, quantity, unit_price, delivered_location, is_defective, color, delivery_note, yards_sent, yards_consumed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (invoice_id, item_code, float(fabric_amount or 0), float(price_per_unit or 0), None, False, color, delivery_note, float(fabric_amount or 0), 0.0)
            )
            imported_count += 1
        except Exception as e:
            errors.append(f"Line {idx+1}: DB error: {e}")
            logger.error(f"Line {idx+1}: DB error: {e}")
    conn.commit()
    cursor.close()
    conn.close()
    return {
        'imported_count': imported_count,
        'skipped_count': skipped_count,
        'errors': errors,
        'summary': summary,
        'file_path': file_path
    } 