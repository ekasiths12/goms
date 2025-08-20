from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from main import db
from app.models.invoice import Invoice, InvoiceLine
from app.models.customer import Customer
import traceback

files_bp = Blueprint('files', __name__)

@files_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """Upload garment image - TODO: Implement"""
    return {'message': 'Upload Image endpoint - TODO: Implement'}, 200

@files_bp.route('/download-pdf/<type>/<id>', methods=['GET'])
def download_pdf(type, id):
    """Download PDF - TODO: Implement"""
    return {'message': f'Download PDF endpoint - TODO: Implement for {type} {id}'}, 200

@files_bp.route('/import-dat', methods=['POST'])
def import_dat_file():
    """Import .DAT file with fabric invoice data"""
    try:
        if 'file' not in request.files:
            return {'error': 'No file provided'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': 'No file selected'}, 400
        
        if not file.filename.lower().endswith('.dat'):
            return {'error': 'File must be a .DAT file'}, 400
        
        # Get customer filter if provided
        customer_ids_filter = request.form.get('customer_ids', '').strip()
        selected_customer_ids = None
        if customer_ids_filter:
            selected_customer_ids = [cid.strip() for cid in customer_ids_filter.split(',') if cid.strip()]
        
        # Read and process the file
        result = import_dat_file_core(file, selected_customer_ids)
        
        return jsonify(result)
        
    except Exception as e:
        return {'error': str(e)}, 500

def import_dat_file_core(file, selected_customer_ids=None):
    """
    Import a .DAT file into the database. Optionally filter by customer IDs.
    Returns a dict with summary, errors, imported_count, skipped_count.
    """
    summary = []
    errors = []
    imported_count = 0
    skipped_count = 0
    
    try:
        # Read file content
        content = file.read().decode('utf-8', errors='replace')
        lines = content.split('\n')
        
        invoice_line_counts = {}
        
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            parts = [p.strip() for p in line.split(';')]
            if len(parts) < 14:
                errors.append(f"Line {idx+1}: Invalid format (expected 14 fields, got {len(parts)})")
                continue
            
            # Map fields from .DAT file (exactly like old Qt app)
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
            # total_value = parts[10]  # Don't parse total_value from file (like old Qt app)
            description = parts[11]
            vat = parts[12]
            # parts[13] is unused
            
            # Convert the padded customer ID from .dat file to regular format (like old Qt app)
            # .dat file has customer ID as 8-digit padded (e.g., "00000328")
            # User enters regular format (e.g., "328")
            try:
                # Remove leading zeros and convert to integer, then back to string
                customer_id_normalized = str(int(customer_id))
            except ValueError:
                # If conversion fails, use original customer_id
                customer_id_normalized = customer_id
            
            # Check if customer ID is in selected list (if filtering is active)
            if selected_customer_ids and customer_id_normalized not in selected_customer_ids:
                skipped_count += 1
                continue
            
            # Parse date (YYYYMMDD to YYYY-MM-DD) - like old Qt app
            invoice_date = None
            if date_raw and len(date_raw) == 8:
                try:
                    invoice_date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
                    invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d')
                except Exception:
                    invoice_date = None
            
            # Calculate total value from price × quantity (like old Qt app)
            try:
                fabric_qty = float(fabric_amount or 0)
                unit_price = float(price_per_unit or 0)
                calculated_total_value = fabric_qty * unit_price
            except (ValueError, TypeError):
                calculated_total_value = 0.0
                errors.append(f"Line {idx+1}: Could not calculate total value from fabric_amount={fabric_amount}, price_per_unit={price_per_unit}")
                continue
            
            # Ensure customer exists (like old Qt app)
            customer = Customer.query.filter_by(customer_id=customer_id_normalized, short_name=short_name).first()
            if not customer:
                customer = Customer(
                    customer_id=customer_id_normalized,
                    short_name=short_name,
                    full_name=short_name,
                    registration_date=datetime.now(),
                    is_active=True
                )
                db.session.add(customer)
                db.session.flush()
            
            # Handle duplicate invoice numbers by adding line numbers (like old Qt app)
            if invoice_number in invoice_line_counts:
                invoice_line_counts[invoice_number] += 1
            else:
                invoice_line_counts[invoice_number] = 1
            
            modified_invoice_number = f"{invoice_number}-{invoice_line_counts[invoice_number]:02d}"
            
            # Insert or update invoice (like old Qt app)
            invoice = Invoice.query.filter_by(
                invoice_number=modified_invoice_number,
                customer_id=customer.id
            ).first()
            
            if not invoice:
                invoice = Invoice(
                    invoice_number=modified_invoice_number,
                    customer_id=customer.id,
                    invoice_date=invoice_date,
                    total_amount=calculated_total_value,
                    status='open',
                    tax_invoice_number=tax if tax else None
                )
                db.session.add(invoice)
                db.session.flush()
            
            # Extract color and delivery note from item_details (robust handling like old Qt app)
            details_parts = [p.strip() for p in item_details.split('/') if p.strip()]
            color = details_parts[1] if len(details_parts) > 1 else ''
            delivery_note = ''
            if len(details_parts) > 2:
                if details_parts[2] == '0' and len(details_parts) > 3:
                    delivery_note = details_parts[3]
                else:
                    delivery_note = details_parts[2]
            
            # Insert invoice line (like old Qt app)
            try:
                invoice_line = InvoiceLine(
                    invoice_id=invoice.id,
                    item_name=item_code,
                    quantity=float(fabric_amount or 0),
                    unit_price=float(price_per_unit or 0),
                    delivered_location=None,
                    is_defective=False,
                    color=color,
                    delivery_note=delivery_note,
                    yards_sent=float(fabric_amount or 0),
                    yards_consumed=0.0
                )
                db.session.add(invoice_line)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Line {idx+1}: DB error: {e}")
                continue
        
        db.session.commit()
        
        return {
            'imported_count': imported_count,
            'skipped_count': skipped_count,
            'errors': errors,
            'summary': summary,
            'file_path': file.filename
        }
        
    except Exception as e:
        db.session.rollback()
        errors.append(f"General error: {str(e)}")
        return {
            'imported_count': 0,
            'skipped_count': 0,
            'errors': errors,
            'summary': summary,
            'file_path': file.filename if file else 'unknown'
        }
